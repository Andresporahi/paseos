import openai
import os
import streamlit as st
from typing import Optional, Dict
import json
import re

def get_openai_client():
    """Obtiene el cliente de OpenAI con la API key"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        try:
            api_key = st.secrets.get("openai_api_key")
        except:
            pass
    
    if not api_key:
        return None
    
    return openai.OpenAI(api_key=api_key)

def transcribir_audio(audio_file_path: str) -> Optional[str]:
    """Transcribe un archivo de audio usando OpenAI Whisper"""
    try:
        client = get_openai_client()
        if not client:
            return None
        
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

def extraer_info_gasto(texto: str, categorias: list = None) -> Dict:
    """
    Extrae concepto y valor de un texto usando GPT.
    El concepto debe incluir el nombre del lugar si se menciona.
    Ejemplo: "Almuerzo en Crepes cuarenta mil" -> {concepto: "Almuerzo en Crepes", valor: 40000}
    """
    try:
        client = get_openai_client()
        if not client:
            return {"concepto": texto, "valor": 0, "categoria": None}
        
        prompt = f"""Analiza el siguiente texto que describe un gasto y extrae la información.
El texto está en español y puede contener números escritos en palabras.

Texto: "{texto}"

IMPORTANTE: El concepto debe incluir el nombre del lugar/restaurante/establecimiento si se menciona.

Responde SOLO con un JSON válido con esta estructura exacta:
{{
    "concepto": "descripción del gasto INCLUYENDO el nombre del lugar si se menciona",
    "valor": número entero en pesos colombianos (sin puntos ni comas),
    "categoria": null
}}

Ejemplos:
- "Almuerzo en Crepes cuarenta mil" -> concepto: "Almuerzo en Crepes & Waffles", valor: 40000
- "Café en Juan Valdez quince mil" -> concepto: "Café en Juan Valdez", valor: 15000
- "Gasolina cincuenta mil" -> concepto: "Gasolina", valor: 50000
- "Uber al aeropuerto treinta mil" -> concepto: "Uber al aeropuerto", valor: 30000

Conversión de números:
- "mil" = 1000
- "cinco mil" = 5000
- "diez mil" = 10000
- "quince mil" = 15000
- "veinte mil" = 20000
- "veinticinco mil" = 25000
- "treinta mil" = 30000
- "treinta y cinco mil" = 35000
- "cuarenta mil" = 40000
- "cincuenta mil" = 50000
- "cien mil" = 100000

Si no puedes determinar el valor, usa 0.
Si el texto menciona "50k" o "50 lucas", interpreta que son miles de pesos."""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Eres un asistente que extrae información de gastos de texto en español. Siempre respondes con JSON válido."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=200
        )
        
        respuesta = response.choices[0].message.content.strip()
        
        # Limpiar la respuesta de markdown si existe
        if respuesta.startswith("```"):
            respuesta = re.sub(r'^```json?\s*', '', respuesta)
            respuesta = re.sub(r'\s*```$', '', respuesta)
        
        resultado = json.loads(respuesta)
        
        # Asegurar que valor sea un número
        if isinstance(resultado.get('valor'), str):
            resultado['valor'] = int(re.sub(r'[^\d]', '', resultado['valor']) or 0)
        
        return resultado
        
    except Exception as e:
        print(f"Error extrayendo información: {e}")
        return {"concepto": texto, "valor": 0, "categoria": None}

def transcribir_y_extraer(audio_file_path: str, categorias: list = None) -> Dict:
    """
    Transcribe audio y extrae información del gasto automáticamente.
    Retorna: {transcripcion, concepto, valor, categoria}
    """
    transcripcion = transcribir_audio(audio_file_path)
    
    if not transcripcion:
        return None
    
    info = extraer_info_gasto(transcripcion, categorias)
    
    return {
        "transcripcion": transcripcion,
        "concepto": info.get("concepto", transcripcion),
        "valor": info.get("valor", 0),
        "categoria": info.get("categoria")
    }

