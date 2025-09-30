# main.py
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from .model import preprocess
from .utils import extract_text_from_pdf, extract_text_from_txt
from google import genai
from google.genai import types
from dotenv import load_dotenv
import os
import shutil
import json
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware





load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client()  # uses GEMINI_API_KEY env

app = FastAPI(title="Inbox Assistant Backend")

origins = [
    "https://phamaralbr.github.io",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class EmailClassification(BaseModel):
    category: str
    suggested_response: str


def classify_with_gemini(email_text: str):
    prompt = f"""
        Você é um assistente especializado em análise e resposta de emails corporativos para uma grande empresa do setor financeiro, que recebe diariamente um alto volume de mensagens. 
        Seu objetivo é automatizar a triagem e a resposta inicial, liberando a equipe de tarefas repetitivas.

        Tarefas:

        1. **Classificação do Email**
        - Classifique o email recebido como:
            - **Produtivo**: requer uma ação ou resposta específica, como solicitações de suporte, dúvidas sobre o sistema, pedidos de atualização de status, envio de documentos ou requisições em aberto.
            - **Improdutivo**: não requer ação imediata ou resposta relevante, como mensagens de felicitações (ex.: Feliz Natal, parabéns), agradecimentos genéricos, conversas informais, ou mensagens sem relação direta com atividades da empresa.

        2. **Resposta Sugerida**
        - Com base na classificação e no conteúdo do email:
            - Se for **Produtivo**: sugira uma resposta em formato de email profissional, em português, mantendo objetividade e cordialidade.
            - Se for **Improdutivo**: sugira uma resposta curta e educada, reconhecendo a mensagem, mas sem comprometer ações desnecessárias.
        - Use `<br>` para marcar quebras de linha no texto da resposta.
        - Adapte o tom ao contexto corporativo.
        
        Email:  {email_text}
    """
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_schema": EmailClassification,
        },
    )


    try:
        return json.loads(response.text)
    except json.JSONDecodeError as e:
        print("JSON parsing error from AI:", e)
        print("Raw AI response:", response.text)

        raise HTTPException(
            status_code=502,
            detail={
                "error": "Falha ao interpretar a resposta da AI. Pode ser limite de uso ou resposta inesperada.",
                "raw_ai_response": response.text
            }
        )


@app.post("/classify")
async def classify_email(
    text: str = Form(None),
    file: UploadFile = File(None)
):
    email_text = ""

    if text:
        email_text = text
    elif file:
        # Handle PDF or TXT files
        temp_path = f"temp/{file.filename}"
        os.makedirs("temp", exist_ok=True)
        with open(temp_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        if file.filename.endswith(".pdf"):
            email_text = extract_text_from_pdf(temp_path)
        else:
            email_text = extract_text_from_txt(temp_path)
        os.remove(temp_path)
    else:
        return {"error": "Nenhum texto ou arquivo enviado."}

    clean_text = preprocess(email_text)
    result = classify_with_gemini(clean_text)
    return result
