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

def analizar_foto_factura(imagen_base64: str) -> Dict:
    """
    Analiza una foto de factura/recibo usando GPT-4 Vision.
    Extrae: concepto (nombre del establecimiento + descripción), valor total
    """
    try:
        client = get_openai_client()
        if not client:
            return {"concepto": "", "valor": 0}
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "Eres un asistente experto en leer facturas y recibos. Extraes información de gastos en pesos colombianos."
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": """Analiza esta foto de factura/recibo y extrae:
1. El nombre del establecimiento/restaurante/tienda
2. Una descripción breve de lo que se compró
3. El valor TOTAL a pagar (en pesos colombianos)

Responde SOLO con un JSON válido:
{
    "concepto": "descripción incluyendo nombre del lugar",
    "valor": número entero del total (sin puntos ni comas ni símbolos),
    "establecimiento": "nombre del establecimiento"
}

Si no puedes leer el valor, usa 0.
Si no puedes identificar el establecimiento, usa "Compra"."""
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{imagen_base64}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ],
            max_tokens=300
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
        
        # Construir concepto con establecimiento si existe
        establecimiento = resultado.get('establecimiento', '')
        concepto = resultado.get('concepto', '')
        if establecimiento and establecimiento.lower() not in concepto.lower():
            concepto = f"{concepto} en {establecimiento}"
        
        return {
            "concepto": concepto,
            "valor": resultado.get("valor", 0)
        }
        
    except Exception as e:
        print(f"Error analizando foto: {e}")
        return {"concepto": "", "valor": 0}

def generar_analisis_inteligente(gastos: list, participantes: list, deudas: list) -> str:
    """
    Genera un análisis inteligente del paseo usando ChatGPT.
    Incluye: resumen, división por concepto, quién debe a quién y recomendaciones.
    """
    try:
        client = get_openai_client()
        if not client:
            return None
        
        # Preparar datos para el análisis
        gastos_texto = "\n".join([
            f"- {g.get('concepto', 'Sin concepto')}: ${g.get('valor', 0):,.0f} (pagó: {g.get('pagador_nombre', 'Desconocido')}, fecha: {g.get('fecha', 'N/A')})"
            for g in gastos
        ])
        
        participantes_texto = ", ".join([p.get('nombre', 'Desconocido') for p in participantes])
        
        deudas_texto = "\n".join([
            f"- {d.get('deudor_nombre', '?')} debe a {d.get('pagador_nombre', '?')}: ${d.get('total', 0):,.0f}"
            for d in deudas
        ]) if deudas else "No hay deudas pendientes."
        
        total_gastos = sum(g.get('valor', 0) for g in gastos)
        num_participantes = len(participantes)
        
        prompt = f"""Analiza los gastos de este paseo y genera un resumen inteligente en español.

PARTICIPANTES ({num_participantes}): {participantes_texto}

GASTOS TOTALES: ${total_gastos:,.0f} COP

LISTA DE GASTOS:
{gastos_texto}

DEUDAS ACTUALES:
{deudas_texto}

Genera un análisis con este formato exacto:

## 📊 Resumen del Paseo

**Total gastado:** ${total_gastos:,.0f} COP
**Por persona (promedio):** ${total_gastos/num_participantes if num_participantes > 0 else 0:,.0f} COP

## 🏪 Gastos por Concepto/Lugar
(Agrupa los gastos similares y muestra el total de cada grupo)

## 💰 Lo que debe cada persona
(Para cada participante, lista cuánto debe en total y a quién, simplificando las deudas)

## 💡 Recomendación de pago
(Sugiere la forma más simple de saldar las deudas, minimizando transferencias)

Sé conciso, usa emojis y formatea los números con separadores de miles."""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Eres un asistente financiero experto en dividir gastos de viajes grupales. Respondes en español con formato Markdown limpio."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1500
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        print(f"Error generando análisis: {e}")
        return None

