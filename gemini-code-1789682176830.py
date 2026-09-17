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

# Funciones de backend y lógica de festivos en Colombia
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
st.markdown("Plataforma de selección confidencial de días libres con calendario matricial interactivo.")

tab1, tab2 = st.tabs(["👤 Portal Anestesiólogos", "🔒 Portal Administrador"])

# --- PESTAÑA 1: ANESTESIÓLOGOS ---
with tab1:
    st.header("Selección de Días Libres en Calendario")
    st.info("Selecciona tu nombre e introduce tu clave de 1 dígito para acceder al calendario mensual y marcar tus días libres.")
    
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
        st.subheader(f"📅 Matriz de Calendario para {mes_input}")
        
        # Verificar estado de cierre antes de permitir la edición
        cerrado, mensaje_cierre = verificar_estado_cierre()
        if cerrado:
            st.warning(f"🔒 {mensaje_cierre} Ya no es posible modificar los días seleccionados.")
        
        anio_sel, mes_sel = map(int, mes_input.split("-"))
        festivos_col = obtener_festivos_colombia(anio_sel)
        dias_previos = obtener_dias_usuario(anestesiologo_seleccionado, mes_input)
        
        # Construir el calendario en formato de tabla (Semanas: Lunes a Domingo)
        cal = calendar.Calendar(firstweekday=0)
        semanas_mes = cal.monthdayscalendar(anio_sel, mes_sel)
        
        filas_tabla = []
        for semana in semanas_mes:
            fila = {}
            for i, dia in enumerate(["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]):
                num_dia = semana[i]
                if num_dia == 0:
                    fila[dia] = None  # Espacio vacío del mes anterior/siguiente
                else:
                    f_actual = date(anio_sel, mes_sel, num_dia)
                    es_festivo = f_actual in festivos_col
                    es_fin = f_actual.weekday() >= 5
                    
                    # Etiqueta descriptiva dentro de la celda de la tabla
                    texto_celda = f"Día {num_dia}"
                    if es_festivo:
                        texto_celda += " 🌟 [Festivo]"
                    elif es_fin:
                        texto_celda += " 🏖️ [Fin de semana]"
                        
                    # Guardamos si está seleccionado previamente
                    fila[dia] = True if num_dia in dias_previos else False
            filas_tabla.append(fila)
            
        # Mapeo estructurado para reconstruir la tabla visual
        # Como Streamlit data_editor requiere tipos uniformes, usamos un enfoque por filas donde cada semana muestra los días
        # Optimizaremos creando una tabla donde cada fila es una semana con columnas booleanas de selección
        
        st.markdown("💡 **Instrucciones:** Marca la casilla **'Seleccionar'** en los días del mes que deseas libres. Los días festivos y fines de semana están señalados para tu comodidad.")
        
        # Generar DataFrame amigable para la matriz de calendario
        matriz_datos = []
        for s_idx, semana in enumerate(semanas_mes):
            fila_info = {"Semana": f"Semana {s_idx + 1}"}
            for d_idx, nombre_col in enumerate(["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]):
                num_dia = semana[d_idx]
                if num_dia == 0:
                    fila_info[f"{nombre_col}"] = None
                else:
                    f_actual = date(anio_sel, mes_sel, num_dia)
                    tag = f"Día {num_dia}"
                    if f_actual in festivos_col:
                        tag += " (🌟 Festivo)"
                    elif f_actual.weekday() >= 5:
                        tag += " (🏖️ Fin de semana)"
                    else:
                        tag += " (💼 Hábil)"
                    
                    # Guardamos un diccionario o tupla con el estado de selección
                    # Para simplificar el data_editor, creamos columnas individuales por día del mes
                    pass

        # Construcción directa de tabla interactiva de selección de días del 1 al último día del mes
        ultimo_dia = calendar.monthrange(anio_sel, mes_sel)[1]
        
        datos_editor = []
        for d in range(1, ultimo_dia + 1):
            f_actual = date(anio_sel, mes_sel, d)
            nombre_dia = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"][f_actual.weekday()]
            
            tipo_dia = "Día Hábil 💼"
            if f_actual in festivos_col:
                tipo_dia = "🌟 FESTIVO OFICIAL COLOMBIA"
            elif f_actual.weekday() >= 5:
                tipo_dia = "🏖️ Fin de Semana"
                
            datos_editor.append({
                "Día": d,
                "Semana / Día": nombre_dia,
                "Tipo": tipo_dia,
                "Solicitar Libre": True if d in dias_previos else False
            })
            
        df_calendario = pd.DataFrame(datos_editor)
        
        # Editor interactivo en tabla
        df_editado = st.data_editor(
            df_calendario,
            column_config={
                "Día": st.column_config.NumberColumn("Día del Mes", disabled=True),
                "Semana / Día": st.column_config.TextColumn("Día de la Semana", disabled=True),
                "Tipo": st.column_config.TextColumn("Clasificación", disabled=True),
                "Solicitar Libre": st.column_config.CheckboxColumn("✨ Marcar como Libre", default=False)
            },
            disabled=False if not cerrado else True,
            hide_index=True,
            use_container_width=True
        )
        
        if not cerrado:
            if st.button("Guardar / Actualizar mis Días Libres", type="primary"):
                # Extraer los días donde la casilla 'Solicitar Libre' quedó marcada como True
                dias_seleccionados_finales = df_editado[df_editado["Solicitar Libre"] == True]["Día"].tolist()
                
                exito, mensaje = guardar_solicitudes(anestesiologo_seleccionado, mes_input, dias_seleccionados_finales)
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
