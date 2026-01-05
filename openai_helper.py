import openai
import os
import streamlit as st
from typing import Optional

def transcribir_audio(audio_file_path: str) -> Optional[str]:
    """Transcribe un archivo de audio usando OpenAI Whisper"""
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            try:
                api_key = st.secrets.get("openai_api_key")
            except:
                pass
        
        if not api_key:
            return None
        
        client = openai.OpenAI(api_key=api_key)
        
        with open(audio_file_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="es"
            )
        
        return transcript.text
    except Exception as e:
        print(f"Error en transcripción: {e}")
        return None

