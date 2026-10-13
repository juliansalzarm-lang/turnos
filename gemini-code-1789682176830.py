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

# Inyectar estilos CSS institucionales y forzar cuadrícula horizontal en celulares
st.markdown("""
    <style>
        :root {
            --primary-color: #209699;
            --primary-light: rgba(32, 150, 153, 0.12);
            --primary-hover: #197a7d;
        }

        h1, h2, h3 {
            color: #209699 !important;
        }

        .stButton > button[kind="primary"], div.stButton > button {
            background-color: #209699 !important;
            color: white !important;
            border: none !important;
            border-radius: 6px !important;
            font-weight: 600;
        }
        .stButton > button[kind="primary"]:hover, div.stButton > button:hover {
            background-color: #197a7d !important;
        }

        input[type="checkbox"] {
            transform: scale(1.4);
            margin-right: 4px;
            cursor: pointer;
            accent-color: #209699;
        }
        div.stCheckbox > label {
            font-size: 12px !important;
            font-weight: 500;
            padding: 1px;
        }

        .stAlert {
            background-color: rgba(32, 150, 153, 0.08) !important;
            border-left: 5px solid #209699 !important;
        }

        .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
            font-size: 16px;
            font-weight: 600;
            color: #209699;
        }

        /* --- FORZAR VISTA DE CUADRÍCULA DE 7 COLUMNAS EN DISPOSITIVOS MÓVILES (VERTICAL Y HORIZONTAL) --- */
        @media (max-width: 768px) {
            .block-container {
                padding-left: 0.3rem !important;
                padding-right: 0.3rem !important;
                padding-top: 0.5rem !important;
            }
            /* Evitar que Streamlit apile las columnas del calendario verticalmente */
            [data-testid="stHorizontalBlock"] {
                display: flex !important;
                flex-direction: row !important;
                flex-wrap: nowrap !important;
            }
            [data-testid="column"] {
                flex: 1 1 0% !important;
                min-width: 0px !important;
                padding: 1px !important;
            }
            /* Reducir texto para ajustar las 7 columnas en pantallas pequeñas */
            div[data-testid="column"] p {
                font-size: 8px !important;
                padding: 0px !important;
                white-space: nowrap !important;
                overflow: hidden;
                text-overflow: ellipsis;
            }
            div.stCheckbox > label {
                font-size: 9px !important;
                padding: 0px !important;
            }
            input[type="checkbox"] {
                transform: scale(1.1);
                margin-right: 1px;
            }
        }
    </style>
""", unsafe_allow_html=True)

# Archivos de persistencia de datos
DB_SOLICITUDES = "solicitudes_dias_libres.csv"
DB_CONFIG = "config_admin.json"

# Listado oficial de anestesiólogos con clave personal única de hasta 2 dígitos (Sin Orlando Ochoa)
ANESTESIOLOGOS_DB = {
    "ALADINO PATIÑO VALERIA": "11",
    "BEDOYA MOSQUERA JADDY (I)": "12",
    "BENITO REVOLLO ZAPATA JAVIER": "13",
    "GONZALEZ HERNANDEZ JENIFFER": "14",
    "LÓPEZ VIDALES FRANCISCO ANTONIO (I)": "15",
    "LUNA MARTINEZ DARWIN": "16",
    "PINILLA PARDO ALVARO (I)": "17",
    "POLO PANTOJA PAOLA (I)": "18",
    "PUERTO TCHEMODANOVA NATALIA (I)": "19",
    "RODRÍGUEZ BLANCO JONATHAN": "20",
    "ROJAS MORALES CARLOS": "21",
    "SALAZAR MORALES JULIÁN ANDRÉS (I)": "22",
    "SARMIENTO VILLARREAL GUALBERTO (I)": "23",
    "UCROS CARRILLO JOSEPH": "24",
    "VEGA SALÁZAR FERNANDO": "25",
    "VILLALBA GAVIRIA MARÍA CLAUDIA (I)": "26",
    "VILLAREAL MAFIOL LAURA (I)": "27",
    "VILORIA MADRID JOHAN": "28"
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
    g
