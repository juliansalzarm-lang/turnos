import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import calendar
import os
import json

# Configuración de la página
st.set_page_config(
    page_title="Gestión de Días Libres - Anestesiología",
    page_icon="🏥",
    layout="wide"
)

# Inyectar estilos CSS personalizados para hacer las casillas más grandes y táctiles
st.markdown("""
    <style>
        input[type="checkbox"] {
            transform: scale(1.5);
            margin-right: 10px;
            cursor: pointer;
        }
        div.stCheckbox > label {
            font-size: 15px !important;
            font-weight: 500;
            padding: 4px;
        }
    </style>
""", unsafe_allow_html=True)

# Archivos de persistencia de datos
DB_SOLICITUDES = "solicitudes_dias_libres.csv"
DB_CONFIG = "config_admin.json"

# Listado oficial de anestesiólogos y su clave secreta de 1 dígito
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

# Funciones de backend y cálculo de festivos en Colombia
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
    except Exception:
        pass
    return False, "Plazo abierto."

def obtener_dias_usuario(anestesiologo, mes):
    if not anestesiologo:
        return []
    df = pd.read_csv(DB_SOLICITUDES)
    filtrado = df[(df["Anestesiologo"] == anestesiologo) & (df["Mes"] == mes)]
    return [int(d) for d in filtrado["Dia_Libre"].tolist() if str(d).isdigit()]

def obtener_pascua(anio):
    a = anio % 19
    b = anio // 100
    c = anio % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    mes = (h + l - 7 * m + 114) // 31
    dia = ((h + l - 7 * m + 114) % 31) + 1
    return date(anio, mes, dia)

def siguiente_lunes(fec):
    d_sem = fec.weekday()
    if d_sem == 0:
        return fec
    return fec + timedelta(days=(7 - d_sem))

def obtener_festivos_colombia(anio):
    festivos = {
        date(anio, 1, 1),   # Año Nuevo
        date(anio, 5, 1),   # Día del Trabajo
        date(anio, 7, 20),  # Independencia
        date(anio, 8, 7),   # Batalla de Boyacá
        date(anio, 12, 8),  # Inmaculada Concepción
        date(anio, 12, 25)  # Navidad
    }
    moviles = [
        date(anio, 1, 6),   # Reyes Magos
        date(anio, 3, 19),  # San José
        date(anio, 6, 29),  # San Pedro y San Pablo
        date(anio, 8, 15),  # Asunción de la Virgen
        date(anio, 10, 12), # Día de la Raza
        date(anio, 11, 1),  # Todos los Santos
        date(anio, 11, 11)  # Independencia de Cartagena
    ]
    for m in moviles:
        festivos.add(siguiente_lunes(m))
        
    pascua = obtener_pascua(anio)
    festivos.add(pascua + timedelta(days=-3)) # Jueves Santo
    festivos.add(pascua + timedelta(days=-2)) # Viernes Santo
    festivos.add(siguiente_lunes(pascua + timedelta(days=43))) # Ascensión del Señor
    festivos.add(siguiente_lunes(pascua + timedelta(days=64))) # Corpus Christi
    festivos.add(siguiente_lunes(pascua + timedelta(days=71))) # Sagrado Corazón
    
    return festivos

def guardar_solicitudes(anestesiologo, mes, dias_seleccionados):
    cerrado, mensaje_cierre = verificar_estado_cierre()
    if cerrado:
        return False, f"Acción denegada: {mensaje_cierre}"
    
    df = pd.read_csv(DB_SOLICITUDES)
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
    return True, f"¡Solicitudes guardadas y actualizadas con éxito para {mes}!"

# --- INTERFAZ DE USUARIO ---
st.title("🏥 Sistema de Gestión de Días Libres - Anestesiología")
st.markdown("Selección confidencial de días libres con vista de calendario matricial (Domingo a Sábado).")

tab1, tab2 = st.tabs(["👤 Portal Anestesiólogos", "🔒 Portal Administrador"])

# --- PESTAÑA 1: ANESTESIÓLOGOS ---
with tab1:
    st.header("Calendario de Solicitud de Días Libres")
    st.info("Selecciona tu nombre e introduce tu clave de 1 dígito para visualizar el calendario mensual en formato de cuadrícula.")
    
    col1, col2 = st.columns(2)
    with col1:
        anestesiologo_seleccionado = st.selectbox(
            "Seleccione su Nombre",
            options=[""] + list(ANESTESIOLOGOS_DB.keys())
        )
    with col2:
        clave_input = st.text_input("Clave personal (1 dígito)", type="password", max_chars=1)
        
    mes_input = st.selectbox("Mes de Solicitud", ["2026-10", "2026-11", "2026-12", "2027-01", "2027-02", "2027-03"])
    
    # Validar acceso por credenciales
    acceso_concedido = False
    if anestesiologo_seleccionado and clave_input:
        if ANESTESIOLOGOS_DB.get(anestesiologo_seleccionado) == clave_input:
            acceso_concedido = True
            st.success(f"¡Bienvenido(a), {anestesiologo_seleccionado}! Acceso autorizado.")
        else:
            st.error("❌ Clave de acceso incorrecta para este especialista.")
            
    if acceso_concedido:
        st.divider()
        
        cerrado, mensaje_cierre = verificar_estado_cierre()
        if cerrado:
            st.warning(f"🔒 {mensaje_cierre} El periodo de selección está cerrado.")
        
        anio_sel, mes_sel = map(int, mes_input.split("-"))
        festivos_col = obtener_festivos_colombia(anio_sel)
        dias_previos = obtener_dias_usuario(anestesiologo_seleccionado, mes_input)
        
        # Diccionario de meses en español
        meses_espanol = {
            1: "ENERO", 2: "FEBRERO", 3: "MARZO", 4: "ABRIL", 
            5: "MAYO", 6: "JUNIO", 7: "JULIO", 8: "AGOSTO", 
            9: "SEPTIEMBRE", 10: "OCTUBRE", 11: "NOVIEMBRE", 12: "DICIEMBRE"
        }
        nombre_mes_str = meses_espanol.get(mes_sel, "")
        st.markdown(f"### 📅 {nombre_mes_str} {anio_sel}")
        st.markdown("*(💼 Hábil | ☀️ Festivo | 🏖️ Fin de semana)*")
        
        # Configurar calendario empezando en Domingo (firstweekday=6)
        cal = calendar.Calendar(firstweekday=6)
        semanas_mes = cal.monthdayscalendar(anio_sel, mes_sel)
        
        # Cabecera en español (DOM, LUE, MAR, MIÉ, JUE, VIE, SÁB)
        dias_semana_nombres = ["DOM", "LUE", "MAR", "MIÉ", "JUE", "VIE", "SÁB"]
        cols_header = st.columns(7)
        for idx, nombre_d in enumerate(dias_semana_nombres):
            with cols_header[idx]:
                if idx == 0:  # Domingo en rojo
                    st.markdown(f"<p style='text-align: center; color: #ff4b4b; font-weight: bold;'>{nombre_d}</p>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<p style='text-align: center; font-weight: bold;'>{nombre_d}</p>", unsafe_allow_html=True)
                    
        # Inicializar o recuperar estado de selección en session_state para la cuadrícula
        state_key = f"sel_{anestesiologo_seleccionado}_{mes_input}"
        if state_key not in st.session_state:
            st.session_state[state_key] = {d: (d in dias_previos) for s in semanas_mes for d in s if d != 0}

        # Renderizar cada semana como una fila de 7 columnas
        nuevos_seleccionados = []
        for semana in semanas_mes:
            cols_semana = st.columns(7)
            for idx, num_dia in enumerate(semana):
                with cols_semana[idx]:
                    if num_dia == 0:
                        st.markdown("<p style='text-align: center; color: #d3d3d3;'>--</p>", unsafe_allow_html=True)
                    else:
                        f_actual = date(anio_sel, mes_sel, num_dia)
                        es_domingo_o_sabado = (idx == 0 or idx == 6)
                        es_festivo = f_actual in festivos_col
                        
                        # Sin la palabra 'Día', mostrando solo número y clasificación
                        if es_festivo:
                            etiqueta_dia = f"{num_dia} ☀️ [Festivo]"
                        elif es_domingo_o_sabado:
                            etiqueta_dia = f"{num_dia} 🏖️ [Fin de semana]"
                        else:
                            etiqueta_dia = f"{num_dia} 💼 [Hábil]"
                            
                        estado_actual = st.session_state[state_key].get(num_dia, num_dia in dias_previos)
                        
                        seleccionado = st.checkbox(
                            f"{etiqueta_dia}",
                            value=estado_actual,
                            key=f"check_{mes_input}_{num_dia}",
                            disabled=cerrado
                        )
                        st.session_state[state_key][num_dia] = seleccionado
                        
                        if seleccionado:
                            nuevos_seleccionados.append(num_dia)

        st.divider()
        if not cerrado:
            if st.button("💾 Guardar / Actualizar mis Días Libres", type="primary"):
                exito, mensaje = guardar_solicitudes(anestesiologo_seleccionado, mes_input, nuevos_seleccionados)
                if exito:
                    st.success(mensaje)
                    st.balloons()
                else:
                    st.error(mensaje)

# --- PESTAÑA 2: ADMINISTRADOR ---
with tab2:
    st.header("Panel de Control del Administrador")
    st.markdown("Área exclusiva para control de plazos y visualización de la tabla consolidada para el motor de turnos.")
    
    password_admin = st.text_input("Contraseña de Administrador", type="password")
    
    if password_admin == "admin123":
        st.success("Acceso de Administrador concedido.")
        
        config_actual = cargar_config()
        
        st.subheader("Configuración de Cierre")
        with st.form("form_config"):
            nueva_fecha_limite = st.text_input("Fecha y Hora Límite (Formato: YYYY-MM-DD HH:MM)", value=config_actual["fecha_limite"])
            nuevo_cierre_manual = st.checkbox("Cierre Manual Inmediato (Bloquea solicitudes)", value=config_actual["cierre_manual"])
            
            btn_guardar_config = st.form_submit_button("Actualizar Reglas")
            if btn_guardar_config:
                guardar_config(nueva_fecha_limite, nuevo_cierre_manual)
                st.success("¡Configuración actualizada correctamente!")
        
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
            
    elif password_admin != "":
        st.error("Contraseña de administrador incorrecta.")
