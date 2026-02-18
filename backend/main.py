from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google import genai

app = FastAPI()

# Permitir conexión desde frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    api_key: str
    message: str

@app.post("/chat")
def chat(data: ChatRequest):
    try:
        # Cliente dinámico con la API Key del usuario
        client = genai.Client(api_key=data.api_key)

        response = client.models.generate_content(
            model="gemini-1.5-pro-latest",
            contents=data.message
        )

        return {"reply": response.text}

    except Exception as e:
        print("ERROR GEMINI:", e)
        return {"error": str(e)}
