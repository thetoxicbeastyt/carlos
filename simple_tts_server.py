import os
import sys
import json
import time
import threading
from pathlib import Path
from typing import Dict, Any

try:
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel
    import uvicorn
    import requests
    import pygame
    import tempfile
    import subprocess
    from gtts import gTTS
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Installing required packages...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "fastapi", "uvicorn", "pydantic", "requests", "pygame", "gTTS"])
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel
    import uvicorn
    import requests
    import pygame
    import tempfile
    from gtts import gTTS

app = FastAPI(title="Simple TTS Server", version="1.0.0")

class TTSRequest(BaseModel):
    text_input: str
    character_voice_gen: str = "default"
    language: str = "en"

@app.get("/")
async def root():
    return {"message": "Simple TTS Server Running"}

@app.get("/api/voices")
async def get_voices():
    return {"voices": ["default", "male", "female"]}

@app.get("/api/status")
async def get_status():
    return {"status": "running", "version": "1.0.0"}

@app.post("/api/tts-generate")
async def generate_tts(request: TTSRequest):
    try:
        # Create temporary file for audio
        temp_dir = Path("temp_audio")
        temp_dir.mkdir(exist_ok=True)
        
        # Generate speech using gTTS
        tts = gTTS(text=request.text_input, lang=request.language)
        output_path = temp_dir / f"carlos_tts_{int(time.time())}.mp3"
        tts.save(str(output_path))
        
        return {
            "status": "success",
            "output_file_path": str(output_path),
            "message": "Audio generated successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    print("Starting Simple TTS Server on port 7851...")
    uvicorn.run(app, host="0.0.0.0", port=7851)
