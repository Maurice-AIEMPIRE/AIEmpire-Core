from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
import os
import logging
from kimi_client import KimiClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("kimi_bridge_server")

app = FastAPI(title="Kimi Bridge API", description="Hybrid Intelligence Bridge (Ollama + Moonshot)")

# Initialize Client
client = KimiClient()

class Message(BaseModel):
    role: str
    content: str
    
class ChatRequest(BaseModel):
    messages: List[Message]
    temperature: Optional[float] = 0.7
    model: Optional[str] = None
    use_local: Optional[bool] = True

@app.get("/health")
async def health_check():
    return {"status": "ok", "local_model": client.local_model, "api_model": client.api_model}

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    try:
        # Convert Pydantic messages to dict
        messages_dict = [{"role": m.role, "content": m.content} for m in request.messages]
        
        response = await client.chat(
            messages=messages_dict,
            model=request.model,
            temperature=request.temperature,
            use_local=request.use_local
        )
        return response
    except ValueError as e:
        # Missing provider — return clear setup instructions
        detail = (
            f"{str(e)}\n\n"
            "Loesungen:\n"
            "  1. ollama serve   (Lokales Ollama starten)\n"
            "  2. MOONSHOT_API_KEY in .env setzen\n"
            "  3. python antigravity/setup_check.py   (Diagnose)"
        )
        logger.error(f"No provider: {str(e)}")
        raise HTTPException(status_code=503, detail=detail)
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.getenv("KIMI_BRIDGE_PORT", 8090))
    uvicorn.run(app, host="0.0.0.0", port=port)
