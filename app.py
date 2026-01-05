import streamlit as st
import os
from datetime import datetime, date
from database import Database
from openai_helper import transcribir_audio, transcribir_y_extraer, analizar_foto_factura, generar_analisis_inteligente
import base64
import pandas as pd
from io import BytesIO
import tempfile
import json

# Configuración de página
st.set_page_config(
    page_title="Paseos - Gastos Compartidos",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS personalizado ultra moderno con colores vivos
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&display=swap');
    
    :root {
        --primary: #6366f1;
        --secondary: #ec4899;
        --accent: #14b8a6;
        --warning: #f59e0b;
        --success: #10b981;
        --danger: #ef4444;
        --dark: #0f172a;
        --light: #f8fafc;
    }
    
    * {
        font-family: 'Space Grotesk', sans-serif !important;
    }
    
    .stApp {
        background: linear-gradient(160deg, #0f172a 0%, #1e1b4b 50%, #312e81 100%);
    }
    
    .main .block-container {
        padding: 0.5rem 1rem !important;
        max-width: 100% !important;
    }
    
    /* Header principal */
    .main-header {
        background: linear-gradient(135deg, #6366f1 0%, #ec4899 50%, #f59e0b 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 2.5rem;
        font-weight: 700;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    
    .sub-header {
        color: #94a3b8;
        text-align: center;
        font-size: 1rem;
        margin-bottom: 1rem;
    }
    
    /* Tarjetas modernas */
    .modern-card {
        background: linear-gradient(145deg, rgba(30,27,75,0.9) 0%, rgba(49,46,129,0.8) 100%);
        border: 1px solid rgba(99,102,241,0.3);
        border-radius: 16px;
        padding: 1rem;
        margin: 0.5rem 0;
        backdrop-filter: blur(10px);
        box-shadow: 0 8px 32px rgba(0,0,0,0.3);
    }
    
    .modern-card-glow {
        background: linear-gradient(145deg, rgba(30,27,75,0.95) 0%, rgba(49,46,129,0.9) 100%);
        border: 1px solid rgba(236,72,153,0.5);
        border-radius: 16px;
        padding: 1rem;
        margin: 0.5rem 0;
        box-shadow: 0 0 20px rgba(236,72,153,0.2), 0 8px 32px rgba(0,0,0,0.3);
    }
    
    /* Badges de estado */
    .badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .badge-primary {
        background: linear-gradient(135deg, #6366f1, #8b5cf6);
        color: white;
    }
    
    .badge-success {
        background: linear-gradient(135deg, #10b981, #14b8a6);
        color: white;
    }
    
    .badge-warning {
        background: linear-gradient(135deg, #f59e0b, #fbbf24);
        color: #0f172a;
    }
    
    .badge-danger {
        background: linear-gradient(135deg, #ef4444, #f87171);
        color: white;
    }
    
    /* Items de gastos */
    .gasto-card {
        background: linear-gradient(135deg, rgba(99,102,241,0.15) 0%, rgba(236,72,153,0.1) 100%);
        border-left: 4px solid #6366f1;
        border-radius: 12px;
        padding: 0.75rem 1rem;
        margin: 0.5rem 0;
        transition: all 0.3s ease;
    }
    
    .gasto-card:hover {
        transform: translateX(5px);
        border-left-color: #ec4899;
    }
    
    .gasto-valor {
        font-size: 1.25rem;
        font-weight: 700;
        background: linear-gradient(135deg, #10b981, #14b8a6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .gasto-concepto {
        color: #e2e8f0;
        font-weight: 500;
        font-size: 0.95rem;
    }
    
    .gasto-meta {
        color: #94a3b8;
        font-size: 0.8rem;
    }
    
    /* Items de deudas */
    .deuda-card {
        background: linear-gradient(135deg, rgba(239,68,68,0.15) 0%, rgba(245,158,11,0.1) 100%);
        border: 1px solid rgba(245,158,11,0.3);
        border-radius: 12px;
        padding: 0.75rem 1rem;
        margin: 0.5rem 0;
    }
    
    .deuda-monto {
        font-size: 1.1rem;
        font-weight: 700;
        color: #fbbf24;
    }
    
    .deuda-texto {
        color: #e2e8f0;
        font-size: 0.9rem;
    }
    
    /* Balance */
    .balance-positive {
        background: linear-gradient(135deg, #10b981, #14b8a6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700;
        font-size: 1.5rem;
    }
    
    .balance-negative {
        background: linear-gradient(135deg, #ef4444, #f87171);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700;
        font-size: 1.5rem;
    }
    
    /* Métricas compactas */
    .metric-card {
        background: linear-gradient(145deg, rgba(30,27,75,0.9) 0%, rgba(49,46,129,0.8) 100%);
        border-radius: 12px;
        padding: 0.75rem;
        text-align: center;
        border: 1px solid rgba(99,102,241,0.2);
    }
    
    .metric-value {
        font-size: 1.3rem;
        font-weight: 700;
        color: #f8fafc;
    }
    
    .metric-label {
        font-size: 0.7rem;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* Participantes */
    .participant-chip {
        display: inline-flex;
        align-items: center;
        background: linear-gradient(135deg, rgba(99,102,241,0.3), rgba(139,92,246,0.2));
        border: 1px solid rgba(139,92,246,0.4);
        border-radius: 25px;
        padding: 0.35rem 0.75rem;
        margin: 0.2rem;
        font-size: 0.85rem;
        color: #e2e8f0;
    }
    
    .participant-avatar {
        width: 24px;
        height: 24px;
        border-radius: 50%;
        background: linear-gradient(135deg, #ec4899, #f59e0b);
        display: inline-flex;
        align-items: center;
        justify-content: center;
        margin-right: 0.5rem;
        font-size: 0.7rem;
        font-weight: 700;
        color: white;
    }
    
    /* Textos */
    h1, h2, h3 {
        color: #f8fafc !important;
        font-weight: 600;
    }
    
    h1 { font-size: 1.75rem !important; }
    h2 { font-size: 1.25rem !important; }
    h3 { font-size: 1rem !important; color: #cbd5e1 !important; }
    
    p, span, label, .stMarkdown {
        color: #e2e8f0 !important;
    }
    
    /* Botones */
    .stButton > button {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #ec4899 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.6rem 1.2rem !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(99,102,241,0.3) !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(99,102,241,0.4) !important;
    }
    
    /* Inputs */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stDateInput > div > div > input {
        background: rgba(30,27,75,0.8) !important;
        border: 1px solid rgba(99,102,241,0.4) !important;
        border-radius: 10px !important;
        color: #f8fafc !important;
        padding: 0.6rem !important;
    }
    
    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus {
        border-color: #ec4899 !important;
        box-shadow: 0 0 0 2px rgba(236,72,153,0.2) !important;
    }
    
    .stSelectbox > div > div {
        background: rgba(30,27,75,0.8) !important;
        border: 1px solid rgba(99,102,241,0.4) !important;
        border-radius: 10px !important;
    }
    
    .stSelectbox > div > div > div {
        color: #f8fafc !important;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background: rgba(30,27,75,0.6);
        border-radius: 12px;
        padding: 0.25rem;
        gap: 0.25rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border-radius: 10px;
        color: #94a3b8;
        font-weight: 500;
        padding: 0.5rem 1rem;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
        color: white !important;
    }
    
    /* Expanders */
    .streamlit-expanderHeader {
        background: rgba(30,27,75,0.6) !important;
        border-radius: 10px !important;
        color: #e2e8f0 !important;
        font-weight: 500 !important;
    }
    
    .streamlit-expanderContent {
        background: rgba(30,27,75,0.4) !important;
        border-radius: 0 0 10px 10px !important;
    }
    
    /* Sliders */
    .stSlider > div > div > div > div {
        background: linear-gradient(135deg, #6366f1, #ec4899) !important;
    }
    
    /* Sidebar */
    .css-1d391kg, [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f172a 0%, #1e1b4b 100%) !important;
    }
    
    /* File uploader */
    .stFileUploader > div {
        background: rgba(30,27,75,0.6) !important;
        border: 2px dashed rgba(99,102,241,0.4) !important;
        border-radius: 12px !important;
    }
    
    /* Info boxes */
    .stAlert {
        background: rgba(30,27,75,0.8) !important;
        border: 1px solid rgba(99,102,241,0.3) !important;
        border-radius: 12px !important;
        color: #e2e8f0 !important;
    }
    
    /* Metrics de Streamlit */
    [data-testid="stMetricValue"] {
        color: #f8fafc !important;
        font-weight: 700 !important;
    }
    
    [data-testid="stMetricLabel"] {
        color: #94a3b8 !important;
    }
    
    /* Dividers */
    hr {
        border-color: rgba(99,102,241,0.2) !important;
    }
    
    /* Responsive */
    @media (max-width: 768px) {
        .main .block-container {
            padding: 0.25rem 0.5rem !important;
        }
        
        h1 { font-size: 1.5rem !important; }
        h2 { font-size: 1.1rem !important; }
        
        .metric-value { font-size: 1.1rem; }
        
        .gasto-card, .deuda-card {
            padding: 0.6rem 0.8rem;
        }
    }
    
    /* Animaciones sutiles */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .modern-card, .gasto-card, .deuda-card {
        animation: fadeIn 0.3s ease-out;
    }
    
    /* Scrollbar personalizada */
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }
    
    ::-webkit-scrollbar-track {
        background: #1e1b4b;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #6366f1, #8b5cf6);
        border-radius: 3px;
    }
</style>
""", unsafe_allow_html=True)

# Inicializar base de datos
@st.cache_resource
def get_database():
    return Database()

db = get_database()

# Sistema de autenticación
def init_session_state():
    if 'usuario_id' not in st.session_state:
        st.session_state.usuario_id = None
    if 'usuario_nombre' not in st.session_state:
        st.session_state.usuario_nombre = None
    if 'paseo_actual' not in st.session_state:
        st.session_state.paseo_actual = None

init_session_state()

def login_page():
    """Página de login/registro"""
    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        st.markdown("""
        <div style='text-align: center; padding: 1rem 0;'>
            <div class='main-header'>🚗 Paseos</div>
            <p class='sub-header'>Divide gastos con tus amigos de forma fácil</p>
        </div>
        """, unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["🔐 Entrar", "✨ Crear Cuenta"])
        
        with tab1:
            st.markdown("### Iniciar Sesión")
            username = st.text_input("Usuario", key="login_username")
            password = st.text_input("Contraseña", type="password", key="login_password")
            
            if st.button("Entrar", key="btn_login"):
                usuario = db.verificar_usuario(username, password)
                if usuario:
                    st.session_state.usuario_id = usuario['id']
                    st.session_state.usuario_nombre = usuario['nombre']
                    st.rerun()
                else:
                    st.error("Usuario o contraseña incorrectos")
        
        with tab2:
            st.markdown("### Crear Cuenta")
            new_username = st.text_input("Usuario", key="reg_username")
            new_password = st.text_input("Contraseña", type="password", key="reg_password")
            nombre = st.text_input("Nombre Completo", key="reg_nombre")
            email = st.text_input("Email (opcional)", key="reg_email")
            
            if st.button("Registrarse", key="btn_register"):
                if new_username and new_password and nombre:
                    if db.crear_usuario(new_username, new_password, nombre, email):
                        st.success("¡Cuenta creada exitosamente! Ahora puedes iniciar sesión.")
                    else:
                        st.error("El usuario ya existe")
                else:
                    st.error("Por favor completa todos los campos obligatorios")

def main_page():
    """Página principal de la aplicación"""
    usuario_id = st.session_state.usuario_id
    usuario_nombre = st.session_state.usuario_nombre
    
    # Sidebar con información del usuario
    with st.sidebar:
        inicial = usuario_nombre[0].upper() if usuario_nombre else "?"
        st.markdown(f"""
        <div style='text-align: center; padding: 1rem 0;'>
            <div style='width: 60px; height: 60px; border-radius: 50%; 
                        background: linear-gradient(135deg, #ec4899, #f59e0b); 
                        display: flex; align-items: center; justify-content: center;
                        margin: 0 auto 0.5rem; font-size: 1.5rem; font-weight: 700; color: white;'>
                {inicial}
            </div>
            <h3 style='margin: 0; color: #f8fafc;'>{usuario_nombre}</h3>
            <p style='color: #94a3b8; font-size: 0.85rem;'>ID: #{usuario_id}</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div style='background: rgba(99,102,241,0.2); border-radius: 10px; padding: 0.75rem; margin: 0.5rem 0;'>
            <p style='color: #e2e8f0; font-size: 0.8rem; margin: 0;'>
                📤 Comparte tu ID con amigos para que te agreguen a sus paseos
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🚪 Cerrar Sesión", key="btn_logout"):
            st.session_state.usuario_id = None
            st.session_state.usuario_nombre = None
            st.session_state.paseo_actual = None
            st.rerun()
    
    # Obtener paseos del usuario
    paseos = db.get_paseos_usuario(usuario_id)
    
    # Selector de paseo
    if paseos:
        paseo_nombres = [f"{p['nombre']} (ID: {p['id']})" for p in paseos]
        paseo_seleccionado = st.selectbox(
            "Selecciona un Paseo",
            ["Nuevo Paseo"] + paseo_nombres,
            key="selector_paseo"
        )
        
        if paseo_seleccionado == "Nuevo Paseo":
            crear_paseo_section(usuario_id)
        else:
            paseo_id = int(paseo_seleccionado.split("ID: ")[1].split(")")[0])
            st.session_state.paseo_actual = paseo_id
            paseo_actual = next(p for p in paseos if p['id'] == paseo_id)
            mostrar_paseo(paseo_id, paseo_actual, usuario_id)
    else:
        st.info("No tienes paseos. Crea uno nuevo para comenzar.")
        crear_paseo_section(usuario_id)

def crear_paseo_section(usuario_id):
    """Sección para crear un nuevo paseo"""
    st.markdown("""
    <div class='modern-card'>
        <h3 style='color: #f8fafc; margin-bottom: 1rem;'>🚀 Crear Nuevo Paseo</h3>
    </div>
    """, unsafe_allow_html=True)
    
    nombre = st.text_input("🏷️ Nombre del Paseo", placeholder="Ej: Viaje a Cartagena 2024")
    descripcion = st.text_area("📝 Descripción (opcional)", placeholder="Agrega detalles del paseo...", height=80)
    
    if st.button("✨ Crear Paseo", key="btn_crear_paseo"):
        if nombre:
            paseo_id = db.crear_paseo(nombre, descripcion, usuario_id)
            st.success(f"🎉 ¡Paseo '{nombre}' creado exitosamente!")
            st.rerun()
        else:
            st.error("⚠️ Por favor ingresa un nombre para el paseo")

def mostrar_paseo(paseo_id, paseo_info, usuario_id):
    """Muestra la información de un paseo"""
    st.markdown(f"## 🚗 {paseo_info['nombre']}")
    if paseo_info.get('descripcion'):
        st.caption(paseo_info['descripcion'])
    
    # Tabs principales
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["💳 Gastos", "📊 Resumen", "💸 Deudas", "👥 Equipo", "🏷️ Categorías"])
    
    with tab1:
        mostrar_gastos(paseo_id, usuario_id)
    
    with tab2:
        mostrar_resumen(paseo_id, usuario_id)
    
    with tab3:
        mostrar_deudas(paseo_id, usuario_id)
    
    with tab4:
        mostrar_participantes(paseo_id, usuario_id)
    
    with tab5:
        mostrar_categorias(paseo_id)

def mostrar_gastos(paseo_id, usuario_id):
    """Muestra y permite agregar gastos"""
    st.markdown("""
    <div class='modern-card'>
        <h3 style='color: #f8fafc; margin: 0 0 0.5rem 0;'>➕ Nuevo Gasto</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Formulario de gasto compacto
    col1, col2, col3 = st.columns([2, 2, 3])
    with col1:
        # Usar valor extraído automáticamente si existe
        valor_default = float(st.session_state.get('valor_extraido', 0))
        valor = st.number_input("💵 Valor (COP)", min_value=0.0, value=valor_default, step=1000.0, format="%.0f")
    with col2:
        fecha = st.date_input("📅 Fecha", value=date.today())
    with col3:
        tipo_gasto = st.selectbox("📎 Tipo", ["🎤 Audio", "📸 Foto"])
        tipo_gasto = tipo_gasto.split(" ")[1]  # Extraer solo el texto sin emoji
    
    # Limpiar transcripción si cambia el tipo
    if 'tipo_gasto_anterior' not in st.session_state:
        st.session_state['tipo_gasto_anterior'] = tipo_gasto
    if st.session_state['tipo_gasto_anterior'] != tipo_gasto:
        # Limpiar todos los valores temporales al cambiar tipo
        keys_to_clear = ['transcripcion_temp', 'concepto_extraido', 'valor_extraido', 'categoria_extraida', 
                        'audio_temp', 'audio_procesado_size', 'foto_temp', 'foto_procesada_size', 'nueva_categoria_nombre']
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
        st.session_state['tipo_gasto_anterior'] = tipo_gasto
    
    # Subida de archivos según el tipo
    archivo_subido = None
    transcripcion_texto = None
    
    # Concepto - se actualiza con el valor extraído automáticamente o la transcripción
    concepto_default = st.session_state.get('concepto_extraido', '') or st.session_state.get('transcripcion_temp', '')
    concepto = st.text_input("📝 Concepto", value=concepto_default, key="concepto_input", placeholder="Describe el gasto...")
    
    if tipo_gasto == "Audio":
        st.markdown("""
        <div style='background: rgba(99,102,241,0.1); border-radius: 10px; padding: 0.75rem; margin: 0.5rem 0;'>
            <p style='color: #e2e8f0; font-size: 0.85rem; margin: 0;'>
                🎤 <strong>Graba</strong> un audio con tu micrófono describiendo el gasto
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Grabar audio desde el micrófono
        audio_grabado = st.audio_input("🎙️ Presiona para grabar", key="audio_recorder")
        
        if audio_grabado:
            st.audio(audio_grabado)
            
            # Verificar si ya procesamos este audio
            audio_bytes = audio_grabado.getvalue()
            audio_size = len(audio_bytes)
            
            if st.session_state.get('audio_procesado_size') != audio_size:
                # Audio nuevo - procesar automáticamente
                with st.spinner("🤖 Procesando audio automáticamente..."):
                    # Guardar temporalmente
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                        tmp_file.write(audio_bytes)
                        tmp_path = tmp_file.name
                    
                    # Transcribir y extraer información
                    resultado = transcribir_y_extraer(tmp_path, None)
                    
                    if resultado:
                        st.session_state['transcripcion_temp'] = resultado['transcripcion']
                        # Agregar nombre del usuario al concepto
                        usuario_nombre = st.session_state.get('usuario_nombre', '')
                        concepto_con_usuario = f"{resultado['concepto']} - {usuario_nombre}" if usuario_nombre else resultado['concepto']
                        st.session_state['concepto_extraido'] = concepto_con_usuario
                        st.session_state['valor_extraido'] = resultado['valor']
                        st.session_state['categoria_extraida'] = resultado['categoria']
                        st.session_state['audio_temp'] = audio_bytes
                        st.session_state['audio_procesado_size'] = audio_size
                        os.unlink(tmp_path)
                        st.rerun()
                    else:
                        st.error("❌ Error al procesar el audio")
                        os.unlink(tmp_path)
            
            # Guardar audio grabado para usar después
            archivo_subido = audio_grabado
        
        # Mostrar información extraída si existe
        if 'transcripcion_temp' in st.session_state and st.session_state['transcripcion_temp']:
            concepto_ext = st.session_state.get('concepto_extraido', '')
            valor_ext = st.session_state.get('valor_extraido', 0)
            
            st.markdown(f"""
            <div style='background: rgba(16,185,129,0.15); border: 1px solid rgba(16,185,129,0.3); 
                        border-radius: 12px; padding: 1rem; margin: 0.5rem 0;'>
                <p style='color: #10b981; font-weight: 600; margin: 0 0 0.5rem 0;'>🤖 Información extraída:</p>
                <div style='display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 0.5rem;'>
                    <div>
                        <span style='color: #94a3b8; font-size: 0.75rem;'>📝 Concepto:</span>
                        <p style='color: #f8fafc; margin: 0; font-weight: 600; font-size: 1.1rem;'>{concepto_ext}</p>
                    </div>
                    <div style='text-align: right;'>
                        <span style='color: #94a3b8; font-size: 0.75rem;'>💵 Valor:</span>
                        <p style='color: #10b981; margin: 0; font-weight: 700; font-size: 1.3rem;'>${valor_ext:,.0f}</p>
                    </div>
                </div>
                <p style='color: #64748b; margin: 0.5rem 0 0 0; font-style: italic; font-size: 0.8rem;'>🎤 "{st.session_state['transcripcion_temp']}"</p>
            </div>
            """, unsafe_allow_html=True)
    
    elif tipo_gasto == "Foto":
        st.markdown("""
        <div style="background: rgba(16, 185, 129, 0.2); border-radius: 12px; padding: 12px; margin-bottom: 15px;">
            <p style="margin: 0; font-size: 0.9rem; color: #a7f3d0;">
                📷 <strong>Toma una foto</strong> de la factura/recibo y extraeremos automáticamente la información
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Cámara para tomar foto
        foto_camara = st.camera_input("📷 Tomar foto de factura", key="camera_factura")
        
        if foto_camara:
            st.image(foto_camara, width=300)
            archivo_subido = foto_camara
            
            # Verificar si ya procesamos esta foto
            foto_bytes = foto_camara.getvalue()
            foto_size = len(foto_bytes)
            
            if st.session_state.get('foto_procesada_size') != foto_size:
                # Foto nueva - procesar automáticamente
                with st.spinner("🤖 Analizando factura automáticamente..."):
                    # Convertir a base64
                    imagen_base64 = base64.b64encode(foto_bytes).decode('utf-8')
                    
                    # Analizar con GPT-4 Vision
                    resultado = analizar_foto_factura(imagen_base64)
                    
                    if resultado and (resultado['concepto'] or resultado['valor'] > 0):
                        # Agregar nombre del usuario al concepto
                        usuario_nombre = st.session_state.get('usuario_nombre', '')
                        concepto_con_usuario = f"{resultado['concepto']} - {usuario_nombre}" if usuario_nombre else resultado['concepto']
                        st.session_state['concepto_extraido'] = concepto_con_usuario
                        st.session_state['valor_extraido'] = resultado['valor']
                        st.session_state['foto_temp'] = foto_bytes
                        st.session_state['foto_procesada_size'] = foto_size
                        st.success("✅ Factura analizada correctamente")
                        st.rerun()
                    else:
                        st.warning("⚠️ No se pudo extraer información. Ingresa los datos manualmente.")
    
    # Sin categorías - la información del lugar va en el concepto
    categoria_id = None
    
    # División del gasto - seleccionar participantes
    st.markdown("### 👥 ¿Entre quiénes se divide?")
    participantes = db.get_participantes_paseo(paseo_id)
    
    # Checkboxes para seleccionar participantes (todos marcados por defecto)
    participantes_seleccionados = []
    cols = st.columns(min(len(participantes), 3))
    for i, participante in enumerate(participantes):
        with cols[i % 3]:
            if st.checkbox(participante['nombre'], value=True, key=f"check_{participante['id']}"):
                participantes_seleccionados.append(participante['id'])
    
    # Calcular división automática en partes iguales
    divisiones = {}
    if participantes_seleccionados:
        porcentaje_cada_uno = 100 // len(participantes_seleccionados)
        resto = 100 % len(participantes_seleccionados)
        for i, pid in enumerate(participantes_seleccionados):
            # El primero recibe el resto para que sume 100%
            divisiones[pid] = porcentaje_cada_uno + (resto if i == 0 else 0)
        
        # Mostrar división
        if valor > 0:
            st.markdown(f"""
            <div style='background: rgba(16,185,129,0.1); border-radius: 8px; padding: 10px; margin-top: 10px;'>
                <p style='color: #a7f3d0; margin: 0; font-size: 0.85rem;'>
                    💰 Cada uno paga: <strong>${valor/len(participantes_seleccionados):,.0f}</strong> 
                    ({len(participantes_seleccionados)} personas)
                </p>
            </div>
            """, unsafe_allow_html=True)
    
    total_porcentaje = sum(divisiones.values()) if divisiones else 0
    
    if st.button("💾 Guardar Gasto", key="btn_guardar_gasto"):
        if concepto and valor > 0 and len(participantes_seleccionados) > 0:
            # Guardar archivo si existe
            archivo_path = None
            tipo_archivo_final = None
            
            # Verificar si hay audio grabado en session_state
            if 'audio_temp' in st.session_state and tipo_gasto == "Audio":
                os.makedirs("uploads", exist_ok=True)
                archivo_path = f"uploads/{paseo_id}_{datetime.now().timestamp()}_grabacion.wav"
                with open(archivo_path, "wb") as f:
                    f.write(st.session_state['audio_temp'])
                tipo_archivo_final = "audio"
            elif archivo_subido:
                os.makedirs("uploads", exist_ok=True)
                # Determinar extensión del archivo
                if hasattr(archivo_subido, 'name'):
                    ext = archivo_subido.name.split('.')[-1]
                    archivo_path = f"uploads/{paseo_id}_{datetime.now().timestamp()}_{archivo_subido.name}"
                else:
                    archivo_path = f"uploads/{paseo_id}_{datetime.now().timestamp()}_archivo.wav"
                with open(archivo_path, "wb") as f:
                    f.write(archivo_subido.getvalue())
                tipo_archivo_final = tipo_gasto.lower()
            
            # Usar transcripción si existe
            transcripcion_final = st.session_state.get('transcripcion_temp', None)
            
            gasto_id = db.crear_gasto(
                paseo_id, usuario_id, concepto, valor,
                datetime.combine(fecha, datetime.min.time()),
                tipo_archivo_final,
                archivo_path,
                transcripcion_final,
                None  # Sin categorías - la info del lugar va en el concepto
            )
            
            # Crear divisiones
            divisiones_list = []
            for part_id, porcentaje in divisiones.items():
                divisiones_list.append({
                    'usuario_id': part_id,
                    'porcentaje': porcentaje,
                    'monto': valor * (porcentaje / 100)
                })
            
            db.crear_division_gasto(gasto_id, divisiones_list)
            
            # Limpiar estado temporal
            keys_to_clear = ['transcripcion_temp', 'tipo_gasto_anterior', 'audio_temp', 
                           'concepto_extraido', 'valor_extraido', 'categoria_extraida', 'nueva_categoria_nombre',
                           'audio_procesado_size', 'foto_temp', 'foto_procesada_size']
            for key in keys_to_clear:
                if key in st.session_state:
                    del st.session_state[key]
            
            st.success("🎉 ¡Gasto guardado y dividido exitosamente!")
            st.rerun()
        else:
            if not concepto:
                st.error("Por favor ingresa un concepto")
            elif valor <= 0:
                st.error("El valor debe ser mayor a 0")
            elif len(participantes_seleccionados) == 0:
                st.error("Selecciona al menos un participante")
    
    # Lista de gastos
    st.markdown("---")
    st.markdown("### 📋 Gastos Registrados")
    
    # Filtro por categoría
    categorias_filtro = db.get_categorias_paseo(paseo_id)
    filtro_opciones = {"🔄 Todas las categorías": None}
    for cat in categorias_filtro:
        filtro_opciones[f"{cat['icono']} {cat['nombre'].split(' ', 1)[-1] if ' ' in cat['nombre'] else cat['nombre']}"] = cat['id']
    
    col_filtro1, col_filtro2 = st.columns([3, 1])
    with col_filtro1:
        filtro_categoria = st.selectbox(
            "Filtrar por categoría",
            options=list(filtro_opciones.keys()),
            key="filtro_categoria",
            label_visibility="collapsed"
        )
    
    categoria_filtro_id = filtro_opciones[filtro_categoria]
    gastos = db.get_gastos_paseo(paseo_id, categoria_filtro_id)
    
    # Mostrar resumen por categorías
    resumen_categorias = db.get_gastos_por_categoria(paseo_id)
    if resumen_categorias:
        st.markdown("<div style='display: flex; flex-wrap: wrap; gap: 0.5rem; margin: 0.5rem 0;'>", unsafe_allow_html=True)
        for cat in resumen_categorias:
            if cat['total'] > 0:
                st.markdown(f"""
                <div style='background: {cat['color']}20; border: 1px solid {cat['color']}50; 
                            border-radius: 20px; padding: 0.3rem 0.7rem; display: inline-flex; 
                            align-items: center; gap: 0.3rem;'>
                    <span>{cat['icono']}</span>
                    <span style='color: #e2e8f0; font-size: 0.8rem;'>${cat['total']:,.0f}</span>
                </div>
                """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    if gastos:
        for gasto in gastos:
            fecha_str = datetime.fromisoformat(gasto['fecha']).strftime('%d/%m/%Y')
            tipo_icon = {"audio": "🎤", "foto": "📸", "video": "🎬", "texto": "📝"}.get(gasto['tipo_archivo'], "💰")
            
            # Mostrar categoría si existe
            cat_badge = ""
            if gasto.get('categoria_nombre'):
                cat_color = gasto.get('categoria_color', '#6366f1')
                cat_icono = gasto.get('categoria_icono', '📦')
                cat_nombre = gasto['categoria_nombre'].split(' ', 1)[-1] if ' ' in gasto['categoria_nombre'] else gasto['categoria_nombre']
                cat_badge = f"<span style='background: {cat_color}30; color: {cat_color}; padding: 0.15rem 0.5rem; border-radius: 10px; font-size: 0.7rem; margin-left: 0.5rem;'>{cat_icono} {cat_nombre}</span>"
            
            # Contenedor del gasto con botones visibles
            col_gasto, col_acciones = st.columns([4, 1])
            
            with col_gasto:
                st.markdown(f"""
                <div class='gasto-card'>
                    <div style='display: flex; justify-content: space-between; align-items: flex-start;'>
                        <div>
                            <span class='gasto-concepto'>{tipo_icon} {gasto['concepto']}{cat_badge}</span>
                            <div class='gasto-meta'>👤 {gasto['usuario_nombre']} • 📅 {fecha_str}</div>
                        </div>
                        <div class='gasto-valor'>${gasto['valor']:,.0f}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            with col_acciones:
                if st.button("✏️", key=f"edit_{gasto['id']}", help="Editar"):
                    st.session_state[f"editing_{gasto['id']}"] = not st.session_state.get(f"editing_{gasto['id']}", False)
                    st.rerun()
                if st.button("🗑️", key=f"delete_{gasto['id']}", help="Eliminar"):
                    db.eliminar_gasto(gasto['id'])
                    st.rerun()
            
            # Formulario de edición (visible si está activado)
            if st.session_state.get(f"editing_{gasto['id']}", False):
                with st.container():
                    st.markdown("---")
                    nuevo_concepto = st.text_input("📝 Concepto", value=gasto['concepto'], key=f"edit_concepto_{gasto['id']}")
                    col_e1, col_e2 = st.columns(2)
                    with col_e1:
                        nuevo_valor = st.number_input("💵 Valor", value=float(gasto['valor']), key=f"edit_valor_{gasto['id']}")
                    with col_e2:
                        nueva_fecha = st.date_input("📅 Fecha", value=datetime.fromisoformat(gasto['fecha']).date(), key=f"edit_fecha_{gasto['id']}")
                    
                    col_save, col_cancel = st.columns(2)
                    with col_save:
                        if st.button("💾 Guardar", key=f"save_{gasto['id']}"):
                            db.actualizar_gasto(
                                gasto['id'],
                                nuevo_concepto,
                                nuevo_valor,
                                datetime.combine(nueva_fecha, datetime.min.time())
                            )
                            st.session_state[f"editing_{gasto['id']}"] = False
                            st.rerun()
                    with col_cancel:
                        if st.button("❌ Cancelar", key=f"cancel_{gasto['id']}"):
                            st.session_state[f"editing_{gasto['id']}"] = False
                            st.rerun()
                    st.markdown("---")
    else:
        st.markdown("""
        <div class='modern-card' style='text-align: center; padding: 2rem;'>
            <span style='font-size: 3rem;'>📝</span>
            <p style='color: #94a3b8; margin-top: 1rem;'>No hay gastos registrados aún</p>
            <p style='color: #6366f1; font-size: 0.9rem;'>¡Agrega tu primer gasto arriba!</p>
        </div>
        """, unsafe_allow_html=True)

def mostrar_resumen(paseo_id, usuario_id):
    """Muestra el resumen de gastos del usuario con análisis inteligente"""
    resumen = db.get_resumen_usuario_paseo(usuario_id, paseo_id)
    gastos = db.get_gastos_paseo(paseo_id)
    participantes = db.get_participantes_paseo(paseo_id)
    deudas = db.calcular_deudas_paseo(paseo_id)
    
    # Métricas con diseño moderno
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-label'>💳 Pagado</div>
            <div class='metric-value' style='color: #10b981;'>${resumen['total_pagado']:,.0f}</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-label'>📤 Debe</div>
            <div class='metric-value' style='color: #f59e0b;'>${resumen['total_debe']:,.0f}</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        balance_color = '#10b981' if resumen['balance'] >= 0 else '#ef4444'
        balance_icon = '📈' if resumen['balance'] >= 0 else '📉'
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-label'>{balance_icon} Balance</div>
            <div class='metric-value' style='color: {balance_color};'>${resumen['balance']:,.0f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Botón de descarga Excel
    if gastos:
        # Preparar datos para Excel
        df_gastos = pd.DataFrame([{
            'Fecha': g.get('fecha', ''),
            'Concepto': g.get('concepto', ''),
            'Valor': g.get('valor', 0),
            'Pagado por': g.get('pagador_nombre', ''),
            'Tipo': g.get('tipo_archivo', 'Manual')
        } for g in gastos])
        
        df_deudas = pd.DataFrame([{
            'Deudor': d.get('deudor_nombre', ''),
            'Acreedor': d.get('pagador_nombre', ''),
            'Monto': d.get('total', 0)
        } for d in deudas]) if deudas else pd.DataFrame()
        
        df_participantes = pd.DataFrame([{
            'Nombre': p.get('nombre', ''),
            'Pagó': db.get_resumen_usuario_paseo(p['id'], paseo_id)['total_pagado'],
            'Debe': db.get_resumen_usuario_paseo(p['id'], paseo_id)['total_debe'],
            'Balance': db.get_resumen_usuario_paseo(p['id'], paseo_id)['balance']
        } for p in participantes])
        
        # Crear Excel en memoria
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_gastos.to_excel(writer, sheet_name='Gastos', index=False)
            df_participantes.to_excel(writer, sheet_name='Participantes', index=False)
            if not df_deudas.empty:
                df_deudas.to_excel(writer, sheet_name='Deudas', index=False)
        output.seek(0)
        
        st.download_button(
            label="📥 Descargar Excel",
            data=output,
            file_name=f"paseo_{paseo_id}_gastos.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    
    # Análisis inteligente automático
    if gastos:
        st.markdown("---")
        st.markdown("### 🤖 Análisis Inteligente")
        
        # Usar cache para no regenerar cada vez
        cache_key = f"analisis_{paseo_id}_{len(gastos)}"
        
        if cache_key not in st.session_state:
            with st.spinner("🧠 Analizando gastos con IA..."):
                # Preparar gastos con nombre del pagador
                gastos_con_pagador = []
                for g in gastos:
                    gasto_info = dict(g)
                    # Obtener nombre del pagador
                    pagador = next((p for p in participantes if p['id'] == g.get('usuario_id')), None)
                    gasto_info['pagador_nombre'] = pagador['nombre'] if pagador else 'Desconocido'
                    gastos_con_pagador.append(gasto_info)
                
                analisis = generar_analisis_inteligente(gastos_con_pagador, participantes, deudas)
                if analisis:
                    st.session_state[cache_key] = analisis
        
        if cache_key in st.session_state:
            st.markdown(f"""
            <div style='background: rgba(99,102,241,0.1); border-radius: 12px; padding: 1rem; border: 1px solid rgba(99,102,241,0.3);'>
            """, unsafe_allow_html=True)
            st.markdown(st.session_state[cache_key])
            st.markdown("</div>", unsafe_allow_html=True)
    
    # Resumen por participante (colapsado)
    st.markdown("---")
    st.markdown("### 👥 Detalle por Participante")
    for participante in participantes:
        resumen_part = db.get_resumen_usuario_paseo(participante['id'], paseo_id)
        balance_color = '#10b981' if resumen_part['balance'] >= 0 else '#ef4444'
        with st.expander(f"👤 {participante['nombre']}"):
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.markdown(f"**💳 Pagó:** <span style='color:#10b981'>${resumen_part['total_pagado']:,.0f}</span>", unsafe_allow_html=True)
            with col_b:
                st.markdown(f"**📤 Debe:** <span style='color:#f59e0b'>${resumen_part['total_debe']:,.0f}</span>", unsafe_allow_html=True)
            with col_c:
                st.markdown(f"**📊 Balance:** <span style='color:{balance_color}'>${resumen_part['balance']:,.0f}</span>", unsafe_allow_html=True)

def mostrar_deudas(paseo_id, usuario_id):
    """Muestra las deudas entre usuarios"""
    deudas = db.calcular_deudas_paseo(paseo_id)
    
    if deudas:
        # Mis deudas primero
        mis_deudas = [d for d in deudas if d['deudor_id'] == usuario_id or d['pagador_id'] == usuario_id]
        if mis_deudas:
            st.markdown("### 🔥 Mis Deudas")
            for deuda in mis_deudas:
                es_deudor = deuda['deudor_id'] == usuario_id
                icono = "📤" if es_deudor else "📥"
                color = "#ef4444" if es_deudor else "#10b981"
                st.markdown(f"""
                <div class='deuda-card'>
                    <div style='display: flex; justify-content: space-between; align-items: center;'>
                        <div>
                            <span style='font-size: 1.2rem;'>{icono}</span>
                            <span class='deuda-texto'>
                                {'Debes a' if es_deudor else 'Te debe'} <strong>{deuda['pagador_nombre'] if es_deudor else deuda['deudor_nombre']}</strong>
                            </span>
                        </div>
                        <div class='deuda-monto' style='color: {color};'>${deuda['total']:,.0f}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                with st.expander("📋 Ver conceptos"):
                    for concepto in deuda['conceptos']:
                        st.markdown(f"• {concepto['concepto']}: <span style='color:#fbbf24'>${concepto['monto']:,.0f}</span>", unsafe_allow_html=True)
        
        # Todas las deudas
        st.markdown("### 📊 Todas las Deudas")
        for deuda in deudas:
            st.markdown(f"""
            <div class='deuda-card'>
                <div style='display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;'>
                    <div class='deuda-texto'>
                        <span class='badge badge-danger'>{deuda['deudor_nombre']}</span>
                        → 
                        <span class='badge badge-success'>{deuda['pagador_nombre']}</span>
                    </div>
                    <div class='deuda-monto'>${deuda['total']:,.0f}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class='modern-card' style='text-align: center; padding: 2rem;'>
            <span style='font-size: 3rem;'>🎉</span>
            <p style='color: #10b981; font-weight: 600; margin-top: 1rem;'>¡No hay deudas pendientes!</p>
        </div>
        """, unsafe_allow_html=True)

def mostrar_participantes(paseo_id, usuario_id):
    """Muestra y permite agregar participantes"""
    st.markdown("### 👥 Participantes del Paseo")
    participantes = db.get_participantes_paseo(paseo_id)
    
    if participantes:
        st.markdown("<div style='display: flex; flex-wrap: wrap; gap: 0.5rem;'>", unsafe_allow_html=True)
        for participante in participantes:
            inicial = participante['nombre'][0].upper()
            st.markdown(f"""
            <div class='participant-chip'>
                <div class='participant-avatar'>{inicial}</div>
                <span>{participante['nombre']}</span>
                <span style='color: #94a3b8; font-size: 0.75rem; margin-left: 0.5rem;'>#{participante['id']}</span>
            </div>
            """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("No hay participantes aún")
    
    st.markdown("---")
    st.markdown("### Agregar Participante")
    
    tab1, tab2 = st.tabs(["Por Username", "Por ID"])
    
    with tab1:
        st.info("Busca un usuario por su nombre de usuario")
        username_buscar = st.text_input("Nombre de usuario", key="buscar_username")
        if st.button("Buscar Usuario", key="btn_buscar"):
            if username_buscar:
                usuario_encontrado = db.buscar_usuario_por_username(username_buscar)
                if usuario_encontrado:
                    st.success(f"Usuario encontrado: {usuario_encontrado['nombre']} (ID: {usuario_encontrado['id']})")
                    if st.button("Agregar este Usuario", key=f"add_{usuario_encontrado['id']}"):
                        if db.agregar_participante(paseo_id, usuario_encontrado['id']):
                            st.success("Participante agregado exitosamente")
                            st.rerun()
                        else:
                            st.error("No se pudo agregar (puede que ya esté agregado)")
                else:
                    st.error("Usuario no encontrado")
            else:
                st.warning("Ingresa un nombre de usuario")
    
    with tab2:
        st.info("Agrega un participante usando su ID de usuario")
        nuevo_usuario_id = st.number_input("ID del Usuario", min_value=1, step=1, key="input_usuario_id")
        if st.button("Agregar por ID", key="btn_agregar_id"):
            if db.agregar_participante(paseo_id, int(nuevo_usuario_id)):
                st.success("Participante agregado exitosamente")
                st.rerun()
            else:
                st.error("No se pudo agregar el participante (puede que ya esté agregado o el ID no exista)")

def mostrar_categorias(paseo_id):
    """Muestra y permite gestionar las categorías del paseo"""
    st.markdown("### 🏷️ Categorías de Gastos")
    
    categorias = db.get_categorias_paseo(paseo_id)
    resumen = db.get_gastos_por_categoria(paseo_id)
    
    # Crear diccionario de resumen para acceso rápido
    resumen_dict = {r['id']: r for r in resumen}
    
    if categorias:
        st.markdown("<div style='display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 0.75rem;'>", unsafe_allow_html=True)
        for cat in categorias:
            total = resumen_dict.get(cat['id'], {}).get('total', 0)
            cantidad = resumen_dict.get(cat['id'], {}).get('cantidad_gastos', 0)
            st.markdown(f"""
            <div style='background: linear-gradient(135deg, {cat['color']}20, {cat['color']}10); 
                        border: 1px solid {cat['color']}40; border-radius: 12px; padding: 1rem; text-align: center;'>
                <div style='font-size: 2rem;'>{cat['icono']}</div>
                <div style='color: #f8fafc; font-weight: 600; font-size: 0.9rem;'>{cat['nombre'].split(' ', 1)[-1] if ' ' in cat['nombre'] else cat['nombre']}</div>
                <div style='color: {cat['color']}; font-weight: 700; font-size: 1.1rem;'>${total:,.0f}</div>
                <div style='color: #94a3b8; font-size: 0.75rem;'>{cantidad} gasto(s)</div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("No hay categorías creadas")
    
    st.markdown("---")
    st.markdown("### ➕ Crear Nueva Categoría")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        nueva_cat_nombre = st.text_input("Nombre", placeholder="Ej: Souvenirs", key="nueva_cat_nombre")
    with col2:
        iconos_disponibles = ["🎁", "🎮", "🎬", "🎪", "🏖️", "⚽", "🎳", "🎨", "📚", "🎵", "🍕", "🍺", "🧴", "👕", "💇", "🔧", "📱", "💻"]
        nuevo_icono = st.selectbox("Icono", iconos_disponibles, key="nuevo_cat_icono")
    with col3:
        colores_disponibles = {
            "Rojo": "#ef4444",
            "Naranja": "#f97316",
            "Ámbar": "#f59e0b",
            "Verde": "#10b981",
            "Teal": "#14b8a6",
            "Azul": "#3b82f6",
            "Índigo": "#6366f1",
            "Púrpura": "#8b5cf6",
            "Rosa": "#ec4899",
            "Gris": "#6b7280"
        }
        nuevo_color_nombre = st.selectbox("Color", list(colores_disponibles.keys()), key="nuevo_cat_color")
        nuevo_color = colores_disponibles[nuevo_color_nombre]
    
    if st.button("✨ Crear Categoría", key="btn_crear_categoria"):
        if nueva_cat_nombre:
            nombre_completo = f"{nuevo_icono} {nueva_cat_nombre}"
            resultado = db.crear_categoria(paseo_id, nombre_completo, nuevo_icono, nuevo_color)
            if resultado > 0:
                st.success(f"🎉 Categoría '{nueva_cat_nombre}' creada exitosamente")
                st.rerun()
            else:
                st.error("❌ Ya existe una categoría con ese nombre")
        else:
            st.error("⚠️ Ingresa un nombre para la categoría")
    
    # Lista de categorías existentes para eliminar
    if categorias:
        st.markdown("---")
        st.markdown("### 🗑️ Eliminar Categoría")
        cat_eliminar_opciones = {f"{c['icono']} {c['nombre'].split(' ', 1)[-1] if ' ' in c['nombre'] else c['nombre']}": c['id'] for c in categorias}
        cat_a_eliminar = st.selectbox("Selecciona categoría a eliminar", list(cat_eliminar_opciones.keys()), key="cat_eliminar")
        
        st.warning("⚠️ Los gastos de esta categoría no se eliminarán, solo quedarán sin categoría.")
        if st.button("🗑️ Eliminar", key="btn_eliminar_categoria"):
            db.eliminar_categoria(cat_eliminar_opciones[cat_a_eliminar])
            st.success("Categoría eliminada")
            st.rerun()

# Routing principal
if st.session_state.usuario_id is None:
    login_page()
else:
    main_page()

