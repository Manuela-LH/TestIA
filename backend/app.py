# backend/app.py - VERSIÓN ACTUALIZADA CON google-genai
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import google.genai as genai  # ¡CAMBIADO!
from google.genai import types  # Nuevo import
import os
from pathlib import Path
import PyPDF2
from dotenv import load_dotenv
import json
import uuid

load_dotenv()

app = FastAPI(title="AcademIA - Tutor Virtual")

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Usuarios simulados
fake_users_db = {
    "test@email.com": {
        "password": "test123",
        "api_key": None
    }
}

# Ruta temporal
UPLOAD_DIR = Path("temp_uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Estado de sesiones
user_sessions = {}

def get_gemini_model(api_key):
    """Obtener modelo Gemini con nueva librería"""
    try:
        # Configurar cliente con nueva API
        client = genai.Client(api_key=api_key)
        
        # Modelos disponibles en nueva API
        modelos_a_probar = [
            "gemini-1.5-flash",  # Modelo gratuito recomendado
            "gemini-1.5-pro",    # Alternativa
            "gemini-1.0-pro",    # Compatibilidad
        ]
        
        for modelo in modelos_a_probar:
            try:
                print(f"🔧 Probando modelo: {modelo}")
                # En nueva API, se usa directamente el nombre
                return client.models.generate_content(
                    model=modelo,
                    contents="Test"
                )
            except Exception as e:
                print(f"   ❌ {modelo} falló: {str(e)[:80]}")
                continue
        
        # Si fallan todos, probar con listado
        print("📋 Listando modelos disponibles...")
        try:
            models_response = client.models.list()
            for model in models_response.models:
                print(f"   - {model.name}")
                if 'generateContent' in model.supported_generation_methods:
                    try:
                        return client.models.generate_content(
                            model=model.name,
                            contents="Test"
                        )
                    except:
                        continue
        except Exception as e:
            print(f"   ❌ Error listando: {e}")
        
        raise Exception("No se pudo conectar con ningún modelo")
        
    except Exception as e:
        raise e

# ========== ENDPOINTS ==========

@app.post("/login")
async def login(email: str = Form(...), password: str = Form(...)):
    """Login básico"""
    user = fake_users_db.get(email)
    if not user or user["password"] != password:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    
    session_token = str(uuid.uuid4())
    user_sessions[session_token] = {
        "email": email,
        "api_key": user.get("api_key")
    }
    
    return {"token": session_token, "email": email}

@app.post("/save_api_key")
async def save_api_key(token: str = Form(...), api_key: str = Form(...)):
    """Guardar API Key"""
    if token not in user_sessions:
        raise HTTPException(status_code=401, detail="Sesión inválida")
    
    user_sessions[token]["api_key"] = api_key
    fake_users_db[user_sessions[token]["email"]]["api_key"] = api_key
    
    return {"message": "✅ API Key guardada"}

def extract_text_from_pdf(file_path):
    """Extraer texto de PDF"""
    try:
        text = ""
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                text += page.extract_text() or ""
        return text[:5000] if text else "📄 PDF subido (sin texto extraíble)"
    except Exception as e:
        return f"❌ Error PDF: {str(e)}"

@app.post("/upload_file")
async def upload_file(
    token: str = Form(...),
    file: UploadFile = File(...)
):
    """Subir archivo"""
    if token not in user_sessions:
        raise HTTPException(status_code=401, detail="Sesión inválida")
    
    # Guardar archivo
    file_path = UPLOAD_DIR / file.filename
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    # Extraer texto
    extracted_text = ""
    if file.content_type == "application/pdf":
        extracted_text = extract_text_from_pdf(file_path)
    elif file.content_type == "text/plain":
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                extracted_text = f.read()[:5000]
        except:
            extracted_text = "📝 Archivo de texto subido"
    else:
        extracted_text = f"📎 {file.filename} subido"
    
    # Guardar en sesión
    if "documents" not in user_sessions[token]:
        user_sessions[token]["documents"] = []
    
    user_sessions[token]["documents"].append({
        "filename": file.filename,
        "content": extracted_text[:3000]
    })
    
    return {
        "success": True,
        "message": f"✅ {file.filename} subido",
        "preview": extracted_text[:200] + "..." if len(extracted_text) > 200 else extracted_text
    }

@app.post("/chat")
async def chat_with_gemini(
    token: str = Form(...),
    message: str = Form(...)
):
    """Chat con Gemini - Nueva API"""
    if token not in user_sessions:
        raise HTTPException(status_code=401, detail="Sesión inválida")
    
    user_data = user_sessions[token]
    api_key = user_data.get("api_key")
    
    if not api_key:
        return {"response": "🔑 Por favor, guarda tu API Key de Gemini primero"}
    
    try:
        # Crear cliente con nueva API
        client = genai.Client(api_key=api_key)
        
        # Contexto de documentos
        context = ""
        if "documents" in user_data and user_data["documents"]:
            context = "DOCUMENTOS DEL ESTUDIANTE:\n\n"
            for doc in user_data["documents"][-2:]:
                context += f"--- {doc['filename']} ---\n{doc['content'][:800]}\n\n"
        
        # Construir contenido
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(
                        f"""Eres AcademIA, un tutor virtual para estudiantes universitarios.

{context}

ESTUDIANTE PREGUNTA: {message}

Instrucciones:
1. Responde basándote en los documentos si son relevantes
2. Sé claro, educativo y conciso
3. Responde en español
4. Si no hay información en los documentos, sé un tutor general útil"""
                    )
                ]
            )
        ]
        
        # Configurar generación
        generate_content_config = types.GenerateContentConfig(
            temperature=0.7,
            top_p=0.9,
            max_output_tokens=1000,
        )
        
        # Usar modelo gratuito
        response = client.models.generate_content(
            model="gemini-1.5-flash",  # Modelo gratuito
            contents=contents,
            config=generate_content_config
        )
        
        return {"response": response.text}
        
    except Exception as e:
        error_msg = str(e)
        if "API_KEY" in error_msg or "api_key" in error_msg.lower():
            return {"response": "🔐 API Key inválida. Obtén una nueva en: https://aistudio.google.com"}
        elif "quota" in error_msg.lower():
            return {"response": "⚠️ Límite gratuito alcanzado. Prueba mañana."}
        elif "model" in error_msg.lower() or "404" in error_msg:
            # Intentar con modelo alternativo
            try:
                client = genai.Client(api_key=api_key)
                response = client.models.generate_content(
                    model="gemini-1.0-pro",
                    contents=[types.Content(
                        role="user",
                        parts=[types.Part.from_text(message)]
                    )]
                )
                return {"response": response.text}
            except:
                return {"response": f"🤖 Error de modelo: {error_msg[:150]}"}
        else:
            return {"response": f"⚠️ Error: {error_msg[:150]}"}

@app.get("/test_gemini")
async def test_gemini(api_key: str = None):
    """Probar conexión con nueva API"""
    try:
        if not api_key:
            return {"error": "Proporciona api_key en query param: ?api_key=TU_KEY"}
        
        client = genai.Client(api_key=api_key)
        
        # Probar diferentes modelos
        test_results = []
        test_models = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-1.0-pro"]
        
        for model_name in test_models:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=[types.Content(
                        role="user",
                        parts=[types.Part.from_text("Hola, prueba de conexión")]
                    )]
                )
                test_results.append({
                    "model": model_name,
                    "status": "✅ FUNCIONA",
                    "response": response.text[:100]
                })
                break
            except Exception as e:
                test_results.append({
                    "model": model_name,
                    "status": "❌ FALLA",
                    "error": str(e)[:100]
                })
        
        return {
            "api_key_preview": api_key[:10] + "...",
            "tests": test_results,
            "libreria": "google-genai (nueva)",
            "recomendacion": "Usa 'gemini-1.5-flash' para gratis"
        }
        
    except Exception as e:
        return {"error": str(e)}

@app.get("/health")
async def health():
    """Endpoint de salud"""
    return {
        "status": "ok",
        "service": "AcademIA Tutor",
        "version": "2.0",
        "libreria": "google-genai",
        "modelo_gratuito": "gemini-1.5-flash"
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 AcademIA Tutor Virtual - Nueva API")
    print("📚 Usando google-genai (actualizado)")
    print("🌐 http://localhost:8000")
    print("🔧 Endpoint test: /test_gemini?api_key=TU_KEY")
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)