import streamlit as st
import os
from datetime import datetime, date
from database import Database
from openai_helper import transcribir_audio
import tempfile
import json

# Configuración de página
st.set_page_config(
    page_title="Paseos - Gastos Compartidos",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS personalizado con colores vivos y degradados
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap');
    
    * {
        font-family: 'Poppins', sans-serif;
    }
    
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
    }
    
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    .card {
        background: white;
        border-radius: 20px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
    }
    
    .card-header {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        padding: 1rem;
        border-radius: 15px;
        margin: -1.5rem -1.5rem 1rem -1.5rem;
        font-weight: 700;
        font-size: 1.2rem;
    }
    
    .card-success {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
    }
    
    .card-warning {
        background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
    }
    
    .card-info {
        background: linear-gradient(135deg, #30cfd0 0%, #330867 100%);
    }
    
    .btn-primary {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.75rem 2rem;
        border-radius: 25px;
        font-weight: 600;
        cursor: pointer;
        transition: transform 0.2s;
    }
    
    .btn-primary:hover {
        transform: scale(1.05);
    }
    
    .gasto-item {
        background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
        padding: 1rem;
        border-radius: 15px;
        margin: 0.5rem 0;
        border-left: 5px solid #667eea;
    }
    
    .deuda-item {
        background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
        padding: 1rem;
        border-radius: 15px;
        margin: 0.5rem 0;
    }
    
    .balance-positive {
        color: #00c851;
        font-weight: 700;
        font-size: 1.5rem;
    }
    
    .balance-negative {
        color: #ff4444;
        font-weight: 700;
        font-size: 1.5rem;
    }
    
    h1, h2, h3 {
        color: white;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 0.5rem 1.5rem;
        font-weight: 600;
        width: 100%;
    }
    
    .stTextInput>div>div>input {
        border-radius: 15px;
        border: 2px solid #667eea;
    }
    
    .stSelectbox>div>div>select {
        border-radius: 15px;
        border: 2px solid #667eea;
    }
    
    .stDateInput>div>div>input {
        border-radius: 15px;
        border: 2px solid #667eea;
    }
    
    .stNumberInput>div>div>input {
        border-radius: 15px;
        border: 2px solid #667eea;
    }
    
    @media (max-width: 768px) {
        .main {
            padding: 0.5rem;
        }
        
        .card {
            padding: 1rem;
            margin: 0.5rem 0;
        }
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
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h1 style='text-align: center;'>🚗 Paseos</h1>", unsafe_allow_html=True)
        st.markdown("<h2 style='text-align: center; color: white;'>Gastos Compartidos</h2>", unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["Iniciar Sesión", "Registrarse"])
        
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
        st.markdown(f"### 👤 {usuario_nombre}")
        usuario_info = db.get_usuario(usuario_id)
        if usuario_info:
            st.info(f"**Tu ID de Usuario:** {usuario_id}\n\nComparte este ID con tus amigos para que te agreguen a sus paseos.")
        if st.button("Cerrar Sesión", key="btn_logout"):
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
    st.markdown("### 🆕 Crear Nuevo Paseo")
    nombre = st.text_input("Nombre del Paseo")
    descripcion = st.text_area("Descripción (opcional)")
    
    if st.button("Crear Paseo"):
        if nombre:
            paseo_id = db.crear_paseo(nombre, descripcion, usuario_id)
            st.success(f"¡Paseo '{nombre}' creado exitosamente!")
            st.rerun()
        else:
            st.error("Por favor ingresa un nombre para el paseo")

def mostrar_paseo(paseo_id, paseo_info, usuario_id):
    """Muestra la información de un paseo"""
    st.markdown(f"# {paseo_info['nombre']}")
    if paseo_info['descripcion']:
        st.markdown(f"*{paseo_info['descripcion']}*")
    
    # Tabs principales
    tab1, tab2, tab3, tab4 = st.tabs(["➕ Gastos", "📊 Resumen", "💰 Deudas", "👥 Participantes"])
    
    with tab1:
        mostrar_gastos(paseo_id, usuario_id)
    
    with tab2:
        mostrar_resumen(paseo_id, usuario_id)
    
    with tab3:
        mostrar_deudas(paseo_id, usuario_id)
    
    with tab4:
        mostrar_participantes(paseo_id, usuario_id)

def mostrar_gastos(paseo_id, usuario_id):
    """Muestra y permite agregar gastos"""
    st.markdown("### Agregar Nuevo Gasto")
    
    # Formulario de gasto
    col1, col2 = st.columns(2)
    with col1:
        valor = st.number_input("Valor (COP)", min_value=0.0, step=1000.0, format="%.0f")
    with col2:
        fecha = st.date_input("Fecha", value=date.today())
        tipo_gasto = st.selectbox("Tipo de Registro", ["Texto", "Audio", "Foto", "Video"])
    
    # Limpiar transcripción si cambia el tipo
    if 'tipo_gasto_anterior' not in st.session_state:
        st.session_state['tipo_gasto_anterior'] = tipo_gasto
    if st.session_state['tipo_gasto_anterior'] != tipo_gasto:
        if 'transcripcion_temp' in st.session_state:
            del st.session_state['transcripcion_temp']
        st.session_state['tipo_gasto_anterior'] = tipo_gasto
    
    # Subida de archivos según el tipo
    archivo_subido = None
    transcripcion_texto = None
    
    # Concepto - se actualiza si hay transcripción
    concepto_default = st.session_state.get('transcripcion_temp', '')
    concepto = st.text_input("Concepto", value=concepto_default, key="concepto_input")
    
    if tipo_gasto == "Audio":
        archivo_subido = st.file_uploader("Grabar o subir audio", type=["wav", "mp3", "m4a", "ogg"], key="audio_upload")
        if archivo_subido:
            st.audio(archivo_subido)
            if st.button("Transcribir Audio", key="btn_transcribir"):
                with st.spinner("Transcribiendo audio..."):
                    # Guardar temporalmente
                    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{archivo_subido.name.split('.')[-1]}") as tmp_file:
                        tmp_file.write(archivo_subido.getvalue())
                        tmp_path = tmp_file.name
                    
                    transcripcion_texto = transcribir_audio(tmp_path)
                    if transcripcion_texto:
                        st.success("Audio transcrito exitosamente")
                        st.session_state['transcripcion_temp'] = transcripcion_texto
                        st.rerun()  # Recargar para actualizar el campo de concepto
                    else:
                        st.error("Error al transcribir el audio")
                    os.unlink(tmp_path)
    
    elif tipo_gasto == "Foto":
        archivo_subido = st.file_uploader("Subir foto", type=["jpg", "jpeg", "png"], key="foto_upload")
        if archivo_subido:
            st.image(archivo_subido)
    
    elif tipo_gasto == "Video":
        archivo_subido = st.file_uploader("Subir video", type=["mp4", "mov", "avi"], key="video_upload")
        if archivo_subido:
            st.video(archivo_subido)
    
    # División del gasto (antes de guardar)
    st.markdown("### Dividir Gasto")
    participantes = db.get_participantes_paseo(paseo_id)
    divisiones = {}
    total_porcentaje = 0
    
    for participante in participantes:
        porcentaje_default = 100 // len(participantes) if len(participantes) > 0 else 100
        porcentaje = st.slider(
            f"{participante['nombre']} (%)",
            0, 100, porcentaje_default,
            key=f"div_{participante['id']}"
        )
        divisiones[participante['id']] = porcentaje
        total_porcentaje += porcentaje
    
    if total_porcentaje != 100:
        st.warning(f"⚠️ El total debe ser 100% (actual: {total_porcentaje}%)")
    
    if st.button("Guardar Gasto", key="btn_guardar_gasto"):
        if concepto and valor > 0 and total_porcentaje == 100:
            # Guardar archivo si existe
            archivo_path = None
            if archivo_subido:
                os.makedirs("uploads", exist_ok=True)
                archivo_path = f"uploads/{paseo_id}_{datetime.now().timestamp()}_{archivo_subido.name}"
                with open(archivo_path, "wb") as f:
                    f.write(archivo_subido.getvalue())
            
            # Usar transcripción si existe
            transcripcion_final = st.session_state.get('transcripcion_temp', None)
            
            gasto_id = db.crear_gasto(
                paseo_id, usuario_id, concepto, valor,
                datetime.combine(fecha, datetime.min.time()),
                tipo_gasto.lower() if archivo_subido else None,
                archivo_path,
                transcripcion_final
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
            if 'transcripcion_temp' in st.session_state:
                del st.session_state['transcripcion_temp']
            if 'tipo_gasto_anterior' in st.session_state:
                del st.session_state['tipo_gasto_anterior']
            
            st.success("¡Gasto guardado y dividido exitosamente!")
            st.rerun()
        else:
            if not concepto:
                st.error("Por favor ingresa un concepto")
            elif valor <= 0:
                st.error("El valor debe ser mayor a 0")
            elif total_porcentaje != 100:
                st.error("La división debe sumar exactamente 100%")
    
    # Lista de gastos
    st.markdown("---")
    st.markdown("### 📋 Gastos Registrados")
    gastos = db.get_gastos_paseo(paseo_id)
    
    if gastos:
        for gasto in gastos:
            with st.expander(f"💰 {gasto['concepto']} - ${gasto['valor']:,.0f} COP"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.write(f"**Pagado por:** {gasto['usuario_nombre']}")
                    st.write(f"**Fecha:** {datetime.fromisoformat(gasto['fecha']).strftime('%d/%m/%Y')}")
                with col2:
                    if gasto['tipo_archivo']:
                        st.write(f"**Tipo:** {gasto['tipo_archivo']}")
                        if gasto['archivo_path'] and os.path.exists(gasto['archivo_path']):
                            if gasto['tipo_archivo'] == 'audio':
                                st.audio(gasto['archivo_path'])
                            elif gasto['tipo_archivo'] == 'foto':
                                st.image(gasto['archivo_path'])
                            elif gasto['tipo_archivo'] == 'video':
                                st.video(gasto['archivo_path'])
                with col3:
                    if gasto['transcripcion']:
                        st.write(f"**Transcripción:** {gasto['transcripcion']}")
                
                # Divisiones
                divisiones = db.get_divisiones_gasto(gasto['id'])
                st.write("**División:**")
                for div in divisiones:
                    st.write(f"- {div['usuario_nombre']}: {div['porcentaje']}% (${div['monto']:,.0f} COP)")
                
                # Editar gasto
                if st.button(f"Editar", key=f"edit_{gasto['id']}"):
                    st.session_state[f"editing_{gasto['id']}"] = True
                
                if st.session_state.get(f"editing_{gasto['id']}", False):
                    nuevo_concepto = st.text_input("Concepto", value=gasto['concepto'], key=f"edit_concepto_{gasto['id']}")
                    nuevo_valor = st.number_input("Valor", value=float(gasto['valor']), key=f"edit_valor_{gasto['id']}")
                    nueva_fecha = st.date_input("Fecha", value=datetime.fromisoformat(gasto['fecha']).date(), key=f"edit_fecha_{gasto['id']}")
                    
                    col_edit1, col_edit2 = st.columns(2)
                    with col_edit1:
                        if st.button("Guardar Cambios", key=f"save_{gasto['id']}"):
                            db.actualizar_gasto(
                                gasto['id'],
                                nuevo_concepto,
                                nuevo_valor,
                                datetime.combine(nueva_fecha, datetime.min.time())
                            )
                            st.session_state[f"editing_{gasto['id']}"] = False
                            st.rerun()
                    with col_edit2:
                        if st.button("Cancelar", key=f"cancel_{gasto['id']}"):
                            st.session_state[f"editing_{gasto['id']}"] = False
                            st.rerun()
                    
                    if st.button("Eliminar Gasto", key=f"delete_{gasto['id']}"):
                        db.eliminar_gasto(gasto['id'])
                        st.rerun()
    else:
        st.info("No hay gastos registrados aún")

def mostrar_resumen(paseo_id, usuario_id):
    """Muestra el resumen de gastos del usuario"""
    resumen = db.get_resumen_usuario_paseo(usuario_id, paseo_id)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Pagado", f"${resumen['total_pagado']:,.0f} COP")
    with col2:
        st.metric("Total Debe", f"${resumen['total_debe']:,.0f} COP")
    with col3:
        balance_class = "balance-positive" if resumen['balance'] >= 0 else "balance-negative"
        st.markdown(f"<div class='{balance_class}'>Balance: ${resumen['balance']:,.0f} COP</div>", unsafe_allow_html=True)
    
    # Resumen de todos los participantes
    st.markdown("### Resumen por Participante")
    participantes = db.get_participantes_paseo(paseo_id)
    for participante in participantes:
        resumen_part = db.get_resumen_usuario_paseo(participante['id'], paseo_id)
        with st.expander(f"👤 {participante['nombre']}"):
            st.write(f"**Pagado:** ${resumen_part['total_pagado']:,.0f} COP")
            st.write(f"**Debe:** ${resumen_part['total_debe']:,.0f} COP")
            st.write(f"**Balance:** ${resumen_part['balance']:,.0f} COP")

def mostrar_deudas(paseo_id, usuario_id):
    """Muestra las deudas entre usuarios"""
    deudas = db.calcular_deudas_paseo(paseo_id)
    
    if deudas:
        st.markdown("### 💸 Deudas Pendientes")
        for deuda in deudas:
            if deuda['deudor_id'] == usuario_id or deuda['pagador_id'] == usuario_id:
                st.markdown(f"""
                <div class="deuda-item">
                    <h4>{deuda['deudor_nombre']} debe ${deuda['total']:,.0f} COP a {deuda['pagador_nombre']}</h4>
                </div>
                """, unsafe_allow_html=True)
                
                with st.expander("Ver detalles"):
                    for concepto in deuda['conceptos']:
                        st.write(f"- {concepto['concepto']}: ${concepto['monto']:,.0f} COP")
    else:
        st.info("No hay deudas pendientes")
    
    # Todas las deudas (para administradores)
    st.markdown("### 📊 Todas las Deudas del Paseo")
    if deudas:
        for deuda in deudas:
            st.markdown(f"""
            <div class="deuda-item">
                <strong>{deuda['deudor_nombre']}</strong> debe 
                <strong>${deuda['total']:,.0f} COP</strong> a 
                <strong>{deuda['pagador_nombre']}</strong>
            </div>
            """, unsafe_allow_html=True)
            
            with st.expander("Ver conceptos"):
                for concepto in deuda['conceptos']:
                    st.write(f"• {concepto['concepto']}: ${concepto['monto']:,.0f} COP")

def mostrar_participantes(paseo_id, usuario_id):
    """Muestra y permite agregar participantes"""
    st.markdown("### 👥 Participantes del Paseo")
    participantes = db.get_participantes_paseo(paseo_id)
    
    if participantes:
        for participante in participantes:
            st.markdown(f"• **{participante['nombre']}** (@{participante['username']}) - ID: {participante['id']}")
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

# Routing principal
if st.session_state.usuario_id is None:
    login_page()
else:
    main_page()

