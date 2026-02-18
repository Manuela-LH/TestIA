from fastapi import FastAPI
from pydantic import BaseModel
import requests

app = FastAPI()

class ChatRequest(BaseModel):
    api_key: str
    message: str

@app.post("/chat")
def chat_with_gemini(data: ChatRequest):
    url = (
        "https://generativelanguage.googleapis.com/v1beta/"
        "models/gemini-2.5-flash:generateContent"
        f"?key={data.api_key}"
    )

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": data.message}
                ]
            }
        ]
    }

    response = requests.post(url, json=payload)

    if response.status_code != 200:
        return {"error": "Error conectando con Gemini API"}

    result = response.json()
    text = result["candidates"][0]["content"]["parts"][0]["text"]

    return {"reply": text}
