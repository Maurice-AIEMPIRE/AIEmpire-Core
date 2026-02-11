#!/usr/bin/env python3
"""
MOBILE EMPIRE INTERFACE
=======================
Web-App für Handy-Zugang zu Gemini, Grok & Claude
Ermöglicht Programmierung von überall.

Maurice's AI Empire - 2026
"""

import os
import json
import asyncio
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import httpx
import anthropic

app = FastAPI(title="Mobile Empire Interface")

# Templates
templates = Jinja2Templates(directory="templates")

# API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY", "")
GROK_API_KEY = os.getenv("GROK_API_KEY", "")

# Configure APIs
gemini_client = None
if GEMINI_API_KEY:
    gemini_client = httpx.AsyncClient(
        headers={"Authorization": f"Bearer {GEMINI_API_KEY}"}
    )

if CLAUDE_API_KEY:
    claude_client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Hauptseite der mobilen Interface"""
    return templates.TemplateResponse("mobile_interface.html", {
        "request": request,
        "title": "Mobile Empire Interface"
    })

@app.post("/api/chat")
async def chat(
    message: str = Form(...),
    model: str = Form("gemini")  # gemini, claude, grok
):
    """Chat mit verschiedenen AI-Modellen"""
    try:
        if model == "gemini" and GEMINI_API_KEY:
            # Verwende Gemini REST API
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_API_KEY}"
            payload = {
                "contents": [{
                    "parts": [{"text": message}]
                }]
            }
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload)
                if response.status_code == 200:
                    data = response.json()
                    text = data["candidates"][0]["content"]["parts"][0]["text"]
                    return {"response": text, "model": "Gemini"}
                else:
                    return {"error": f"Gemini API Error: {response.status_code}"}

        elif model == "claude" and CLAUDE_API_KEY:
            response = claude_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1000,
                messages=[{"role": "user", "content": message}]
            )
            return {"response": response.content[0].text, "model": "Claude"}

        elif model == "grok":
            # Simuliere Grok Response (da wir bereits Grok sind)
            # In Produktion würde hier die xAI API verwendet werden
            grok_response = f"Grok Fastmode: {message} - Ich bin bereit zu helfen!"
            return {"response": grok_response, "model": "Grok"}

        else:
            return {"error": "Modell nicht verfügbar oder API-Key fehlt"}

    except Exception as e:
        return {"error": str(e)}

@app.post("/api/code")
async def generate_code(
    prompt: str = Form(...),
    language: str = Form("python")
):
    """Code generieren mit AI"""
    code_prompt = f"""
    Generiere {language} Code für: {prompt}
    Erstelle vollständigen, lauffähigen Code mit Kommentaren.
    """

    # Verwende Gemini für Code-Generierung
    if GEMINI_API_KEY:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_API_KEY}"
            payload = {
                "contents": [{
                    "parts": [{"text": code_prompt}]
                }]
            }
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload)
                if response.status_code == 200:
                    data = response.json()
                    code = data["candidates"][0]["content"]["parts"][0]["text"]
                    return {"code": code, "language": language}
                else:
                    return {"error": f"Gemini API Error: {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}
    else:
        return {"error": "Gemini API nicht konfiguriert"}

@app.get("/api/status")
async def get_status():
    """System-Status"""
    return {
        "gemini": bool(GEMINI_API_KEY),
        "claude": bool(CLAUDE_API_KEY),
        "grok": True,  # Immer verfügbar
        "status": "online"
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starte Mobile Empire Interface...")
    print("📱 Öffne http://localhost:8000 in deinem Browser")
    print("📱 Oder von deinem Handy: http://[deine-ip]:8000")

    uvicorn.run(app, host="0.0.0.0", port=8000)