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
    "http://localhost:5500",
    "http://127.0.0.1:5500",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or ["http://127.0.0.1:5500"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class EmailClassification(BaseModel):
    category: str
    suggested_response: str


def classify_with_gemini(email_text: str):
    prompt = f"""
        Você é um assistente de email. Analise este email e:

            1. Classifique como 'Produtivo' se requer ação ou 'Improdutivo' se não requer.
            2. Sugira uma resposta apropriada em formato de email profissional e em português. Utilize <br> para quebras de linha.

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
