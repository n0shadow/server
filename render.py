from fastapi import FastAPI, File, UploadFile, HTTPException, Header, status
from typing import Annotated
import httpx
import os
import requests
from pydantic import BaseModel

app = FastAPI()

API_KEY_ESTE_SERVIDOR = os.getenv("API_KEY_RENDER")
URL_SERVIDOR_DESTINO = os.getenv("URL")
API_KEY_SERVIDOR_DESTINO = str(os.getenv("API_KEY_DESTINO"))
T_TOKEN = os.getenv("T_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

@app.post("/file/{username}")
async def create_upload_file(
    username: str,
    file: UploadFile = File(...),
    x_api_key: Annotated[str | None, Header()] = None
):
    if x_api_key is None or x_api_key != API_KEY_ESTE_SERVIDOR:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key inválida ou ausente para este servidor. Forneça a chave no cabeçalho 'x-api-key'.",
        )

    if not str(file.filename).endswith(".txt"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Apenas arquivos .txt são permitidos para encaminhamento.",
        )

    async with httpx.AsyncClient() as client:
        try:
            headers_destino = {
                "x-api-key": API_KEY_SERVIDOR_DESTINO
            }
            file_content = await file.read()
            files_para_encaminhar = {'file': (file.filename, file_content, 'text/plain')}

            url_completa_destino = f"{URL_SERVIDOR_DESTINO}/file/{username}"

            response_destino = await client.post(
                url_completa_destino,
                headers=headers_destino,
                files=files_para_encaminhar
            )

            response_destino.raise_for_status()

            return response_destino.json()

        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Erro do servidor de destino: {e.response.text}"
            )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Não foi possível conectar ao servidor de destino: {e}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erro inesperado durante o encaminhamento: {e}"
            )
        finally:
            await file.close()

    
class ClickData(BaseModel):
    page: str

@app.post("/click")
async def click_handler(
    click_data: ClickData,
    x_api_key: Annotated[str | None, Header()] = None
):
    if x_api_key is None or x_api_key != API_KEY_ESTE_SERVIDOR:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key inválida ou ausente para este servidor. Forneça a chave no cabeçalho 'x-api-key'.",
        )
    
    MENSAGEM = f"🚨 Notificação de clique recebida na página: {click_data.page}"

    url = f"https://api.telegram.org/bot{T_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": MENSAGEM
    }

    response = requests.post(url, data=data)
    if response.status_code == 200:
        return {"message": "Notificação enviada com sucesso!"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Falha ao enviar notificação."
        )

@app.get("/")
async def read_root():
    return {"message": "Hello world!"}