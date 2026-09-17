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

# Listado oficial de anestesiólogos y asignación de clave secreta de 1 dígito
ANESTESIOLOGOS_DB = {
    "ALADINO PATIÑO VALERIA": "1",
    "BEDOYA MOSQUERA JADDY (I)": "2",
    "BENITO REVOLLO ZAPATA JAVIER": "3",
    "GONZALEZ HERNANDEZ JENIFFER": "4",
    "LÓPEZ VIDALES FRANCISCO ANTONIO (I)": "5",
    "LUNA MARTINEZ DARWIN": "6",
    "OCHOA GARCÍA ORLANDO (I)": "7",
    "PINILLA PARDO ALVARO (I)": "8",
    "POLO PANTOJA PAOLA (I)": "9",
    "PUERTO TCHEMODANOVA NATALIA (I)": "1",
    "RODRÍGUEZ BLANCO JONATHAN": "2",
    "ROJAS MORALES CARLOS": "3",
    "SALAZAR MORALES JULIÁN ANDRÉS (I)": "4",
    "SARMIENTO VILLARREAL GUALBERTO (I)": "5",
    "UCROS CARRILLO JOSEPH": "6",
    "VEGA SALÁZAR FERNANDO": "7",
    "VILLALBA GAVIRIA MARÍA CLAUDIA (I)": "8",
    "VILLAREAL MAFIOL LAURA (I)": "9",
    "VILORIA MADRID JOHAN": "1"
}

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
    if not anestesiologo:
        return []
    df = pd.read_csv(DB_SOLICITUDES)
    filtrado = df[(df["Anestesiologo"] == anestesiologo) & (df["Mes"] == mes)]
    return [int(d) for d in filtrado["Dia_Libre"].tolist() if str(d).isdigit()]

def guardar_solicitudes(anestesiologo, mes, dias_seleccionados, clave_ingresada):
    if not anestesiologo:
        return False, "Por favor, seleccione su nombre de la lista."
    
    # Validar clave de 1 dígito
    if ANESTESIOLOGOS_DB.get(anestesiologo) != clave_ingresada:
        return False, "Clave de acceso incorrecta para este especialista."
    
    cerrado, mensaje_cierre = verificar_estado_cierre()
    if cerrado:
        return False, f"Acción denegada: {mensaje_cierre}"
    
    df = pd.read_csv(DB_SOLICITUDES)
    
    # Eliminar registros previos para permitir edición limpia
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

# --- INTERFAZ DE USUARIO ---
st.title("🏥 Sistema de Gestión de Días Libres - Anestesiología")
st.markdown("Selección confidencial de días libres por especialista.")

tab1, tab2 = st.tabs(["👤 Portal Anestesiólogos", "🔒 Portal Administrador"])

# --- PESTAÑA 1: ANESTESIÓLOGOS ---
with tab1:
    st.header("Selección de Días Libres por Especialista")
    st.info("Seleccione su nombre de la lista desplegable, introduzca su clave asignada de un dígito y marque los días que desea libres en el calendario del mes.")
    
    col1, col2 = st.Item = st.columns(2)
    with col1:
        anestesiologo_seleccionado = st.selectbox(
            "Seleccione su Nombre",
            options=[""] + list(ANESTESIOLOGOS_DB.keys())
        )
    with col2:
        clave_input = st.text_input("Clave personal (1 dígito)", type="password", max_chars=1)
        
    mes_input = st.selectbox("Mes de Solicitud", ["2026-10", "2026-11", "2026-12", "2027-01"])
    
    if anestesiologo_seleccionado:
        # Cargar selecciones previas si las hay
        dias_previos = obtener_dias_usuario(anestesiologo_seleccionado, mes_input)
        
        st.subheader(f"Calendario de Días Libres para: {anestesiologo_seleccionado}")
        
        # Selector múltiple interactivo simulando los días del mes (1 al 31)
        dias_disponibles = list(range(1, 32))
        dias_seleccionados = st.multiselect(
            "Marque los días que desea solicitar libres:",
            options=dias_disponibles,
            default=dias_previos,
            format_func=lambda x: f"Día {x}"
        )
        
        if st.button("Guardar / Actualizar mis Días Libres", type="primary"):
            exito, mensaje = guardar_solicitudes(anestesiologo_seleccionado, mes_input, dias_seleccionados, clave_input)
            if exito:
                st.success(mensaje)
            else:
                st.error(mensaje)
    else:
        st.warning("Por favor, seleccione su nombre para desplegar el calendario de días libres.")

# --- PESTAÑA 2: ADMINISTRADOR ---
with tab2:
    st.header("Panel de Control del Administrador")
    st.markdown("Área exclusiva para control de plazos y visualización de la tabla estructurada para el motor de turnos.")
    
    password_input = st.text_input("Contraseña de Administrador", type="password")
    
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
