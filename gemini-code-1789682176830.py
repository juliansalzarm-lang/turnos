import streamlit as st
import pandas as pd
from datetime import datetime
import os
import json

# Configuración de la página
st.set_page_config(
    page_title="Gestión de Días Libres - Anestesiología",
    page_icon="🏥",
    layout="wide"
)

# Archivos de persistencia de datos
DB_SOLICITUDES = "solicitudes_dias_libres.csv"
DB_CONFIG = "config_admin.json"

# Inicializar archivos si no existen
if not os.path.exists(DB_SOLICITUDES):
    df_init = pd.DataFrame(columns=["Anestesiologo", "Mes", "Dia_Libre", "Timestamp"])
    df_init.to_csv(DB_SOLICITUDES, index=False)

if not os.path.exists(DB_CONFIG):
    config_init = {"fecha_limite": "2026-12-31 23:59", "cierre_manual": False}
    with open(DB_CONFIG, "w") as f:
        json.dump(config_init, f)

# Funciones de backend
def cargar_config():
    with open(DB_CONFIG, "r") as f:
        return json.load(f)

def guardar_config(fecha_limite, cierre_manual):
    config = {"fecha_limite": fecha_limite, "cierre_manual": cierre_manual}
    with open(DB_CONFIG, "w") as f:
        json.dump(config, f)

def verificar_estado_cierre():
    config = cargar_config()
    if config["cierre_manual"]:
        return True, "El administrador ha cerrado manualmente la recepción de solicitudes."
    
    try:
        limite = datetime.strptime(config["fecha_limite"], "%Y-%m-%d %H:%M")
        if datetime.now() > limite:
            return True, f"El plazo de solicitud expiró el {config['fecha_limite']}."
    except Exception as e:
        pass
    
    return False, "Plazo abierto."

def obtener_dias_usuario(anestesiologo, mes):
    if not anestesiologo.strip():
        return []
    df = pd.read_csv(DB_SOLICITUDES)
    filtrado = df[(df["Anestesiologo"] == anestesiologo) & (df["Mes"] == mes)]
    return [int(d) for d in filtrado["Dia_Libre"].tolist() if str(d).isdigit()]

def guardar_solicitudes(anestesiologo, mes, dias_seleccionados):
    if not anestesiologo.strip():
        return False, "Por favor, ingrese su nombre y apellido."
    
    cerrado, mensaje_cierre = verificar_estado_cierre()
    if cerrado:
        return False, f"Acción denegada: {mensaje_cierre}"
    
    df = pd.read_csv(DB_SOLICITUDES)
    
    # Eliminar registros previos de este usuario para este mes (permite editar/sobrescribir)
    df = df[~((df["Anestesiologo"] == anestesiologo) & (df["Mes"] == mes))]
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    nuevos_registros = []
    
    for dia in dias_seleccionados:
        nuevos_registros.append({
            "Anestesiologo": anestesiologo,
            "Mes": mes,
            "Dia_Libre": dia,
            "Timestamp": timestamp
        })
    
    if nuevos_registros:
        df_nuevos = pd.DataFrame(nuevos_registros)
        df = pd.concat([df, df_nuevos], ignore_index=True)
        
    df.to_csv(DB_SOLICITUDES, index=False)
    return True, f"¡Solicitudes actualizadas con éxito para {mes}!"

# --- INTERFAZ DE USUARIO (STREAMLIT) ---
st.title("🏥 Sistema de Gestión de Días Libres - Anestesiología")
st.markdown("Plataforma interactiva para la selección confidencial de días libres y la administración del servicio.")

tab1, tab2 = st.tabs(["👤 Portal Anestesiólogos", "🔒 Portal Administrador"])

# --- PESTAÑA 1: ANESTESIÓLOGOS ---
with tab1:
    st.header("Selección de Días Libres")
    st.info("Seleccione su nombre, el mes de interés y marque los días que desea libres. Si ya había guardado selecciones previas, estas aparecerán marcadas y podrá modificarlas antes de la fecha límite.")
    
    col1, col2 = st.columns(2)
    with col1:
        nombre_input = st.text_input("Nombre y Apellido del Anestesiólogo", placeholder="Ej. Dr. Juan Pérez")
    with col2:
        mes_input = st.selectbox("Mes de Solicitud", ["2026-10", "2026-11", "2026-12", "2027-01"])
    
    # Cargar días seleccionados previamente por este usuario para este mes
    dias_previos = obtener_dias_usuario(nombre_input, mes_input) if nombre_input else []
    
    # Selector dinámico de días del 1 al 31
    dias_disponibles = list(range(1, 32))
    dias_seleccionados = st.multiselect(
        "Seleccione los días del mes que desea libres:",
        options=dias_disponibles,
        default=dias_previos,
        format_func=lambda x: f"Día {x}"
    )
    
    if st.button("Guardar / Actualizar mis Días Libres", type="primary"):
        exito, mensaje = guardar_solicitudes(nombre_input, mes_input, dias_seleccionados)
        if exito:
            st.success(mensaje)
        else:
            st.error(mensaje)

# --- PESTAÑA 2: ADMINISTRADOR ---
with tab2:
    st.header("Panel de Control del Administrador")
    st.markdown("Área exclusiva para la gestión de plazos y visualización de la tabla consolidada destinada al motor de turnos.")
    
    password_input = st.text_input("Contraseña de Administrador", type="password")
    
    # Contraseña por defecto para pruebas: admin123
    if password_input == "admin123":
        st.success("Acceso concedido.")
        
        config_actual = cargar_config()
        
        st.subheader("Configuración de Cierre")
        with st.form("form_config"):
            nueva_fecha_limite = st.text_input("Fecha y Hora Límite (Formato: YYYY-MM-DD HH:MM)", value=config_actual["fecha_limite"])
            nuevo_cierre_manual = st.checkbox("Cierre Manual Inmediato (Bloquea solicitudes de inmediato)", value=config_actual["cierre_manual"])
            
            btn_guardar_config = st.form_submit_button("Actualizar Reglas")
            if btn_guardar_config:
                guardar_config(nueva_fecha_limite, nuevo_cierre_manual)
                st.success("¡Configuración de cierre actualizada correctamente!")
        
        st.divider()
        st.subheader("Consolidado Global de Solicitudes (Estructura para IA)")
        
        if os.path.exists(DB_SOLICITUDES):
            df_total = pd.read_csv(DB_SOLICITUDES)
            st.dataframe(df_total, use_container_width=True)
            
            # Botón de descarga CSV para alimentar el siguiente Gem / IA de turnos
            csv_data = df_total.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Descargar CSV Consolidado para la IA de Turnos",
                data=csv_data,
                file_name="consolidado_dias_libres_anestesiologia.csv",
                mime="text/csv",
            )
        else:
            st.warning("Aún no hay registros de solicitudes guardados.")
            
    elif password_input != "":
        st.error("Contraseña incorrecta.")