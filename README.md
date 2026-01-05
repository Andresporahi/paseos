# 🚗 Paseos - App de Gastos Compartidos

Aplicación web móvil para gestionar gastos y cobros de paseos entre amigos, desarrollada con Streamlit.

**Repositorio:** [https://github.com/Andresporahi/paseos](https://github.com/Andresporahi/paseos)

## Características

- 📱 **Diseño móvil responsive** con colores vivos y degradados modernos
- 👥 **Múltiples usuarios** con sistema de autenticación
- 🎤 **Transcripción de audio** usando OpenAI Whisper
- 📸 **Subida de archivos**: audio, fotos y videos
- 💰 **División de gastos** entre participantes
- 📊 **Cálculo automático de deudas** entre usuarios
- 🗓️ **Gestión de fechas** y edición de gastos
- 💾 **Base de datos SQLite** para persistencia

## Instalación

1. Clona el repositorio:
```bash
git clone https://github.com/Andresporahi/paseos.git
cd paseos
```

2. Instala las dependencias:
```bash
pip install -r requirements.txt
```

3. Configura la API key de OpenAI:
   - Copia el archivo template: `cp .streamlit/secrets.toml.example .streamlit/secrets.toml`
   - Edita `.streamlit/secrets.toml` y agrega tu API key:
```toml
openai_api_key = "tu-api-key-aqui"
```

## Uso

1. Ejecuta la aplicación:
```bash
streamlit run app.py
```

2. Abre tu navegador en `http://localhost:8501`

3. En tu celular, accede a la misma URL desde la red local

## Funcionalidades

### Autenticación
- Registro de nuevos usuarios
- Inicio de sesión seguro

### Paseos
- Crear nuevos paseos
- Agregar participantes
- Ver todos los paseos del usuario

### Gastos
- Agregar gastos con texto, audio, foto o video
- Transcribir audios automáticamente
- Editar concepto, valor y fecha
- Dividir gastos entre participantes por porcentaje

### Resumen y Deudas
- Ver resumen personal de gastos
- Ver balance (pagado vs debe)
- Ver todas las deudas del paseo
- Detalle de conceptos por deuda

## Estructura del Proyecto

```
Paseos/
├── app.py                 # Aplicación principal Streamlit
├── database.py            # Gestión de base de datos
├── openai_helper.py       # Integración con OpenAI
├── requirements.txt       # Dependencias
├── .streamlit/
│   ├── config.toml        # Configuración de Streamlit
│   └── secrets.toml       # API keys (no commitear)
└── uploads/               # Archivos subidos (generado automáticamente)
```

## Notas

- La base de datos se crea automáticamente en `paseos.db`
- Los archivos subidos se guardan en la carpeta `uploads/`
- Para uso en producción, considera usar una base de datos más robusta y almacenamiento en la nube

## Tecnologías

- **Streamlit**: Framework web
- **SQLite**: Base de datos
- **OpenAI API**: Transcripción de audio
- **Python 3.8+**

