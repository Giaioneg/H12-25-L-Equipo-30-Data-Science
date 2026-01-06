import joblib
import numpy as np
import onnxruntime as rt
import os
import zipfile
import requests
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime

from sympy import false

# --- CONFIGURACIÓN ---
ARTIFACTS_DIR = 'artifacts'
ONNX_FILENAME = 'flight_delay_rf_weighted.onnx'
ZIP_FILENAME = 'flight_delay_rf_weighted.onnx.zip'

# Variables Globales (Estado de la App)
risk_maps = {}
smart_ops_lookup = {}
smart_traffic_lookup = {}
static_defaults = {}
airport_coords = {} # <--- AQUÍ SE CARGARÁN AUTOMÁTICAMENTE
sess = None
input_name = None
global_mean = 0.18

# --- MODELO DE DATOS ---
class FlightRequest(BaseModel):
    CARRIER_NAME: str
    DEPARTING_AIRPORT: str
    FECHA: str
    HORA: str
    # Opcionales
    PRCP: float | None = None
    SNOW: float | None = None
    AWND: float | None = None

# --- FUNCIÓN DE CLIMA (USANDO LAS COORDENADAS CARGADAS) ---
def get_live_weather(airport_name, flight_date_str):
    # Usamos el diccionario cargado dinámicamente
    coords = airport_coords.get(airport_name)
    
    if not coords:
        print(f"⚠️ No tengo coordenadas para: {airport_name}")
        return None 

    try:
        # Validar fecha (Open-Meteo solo da 7 días)
        flight_date = datetime.strptime(flight_date_str, "%Y-%m-%d")
        today = datetime.now()
        delta = (flight_date - today).days

        if delta < 0 or delta > 7:
            return None 

        lat = coords['lat']
        lon = coords['lon']
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=precipitation_sum,snowfall_sum,windspeed_10m_max&timezone=auto"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) FlightDelayApp/1.0"
        }
        
        session = requests.Session()
        session.trust_env = False

        res = session.get(url, headers=headers, timeout=10, verify=False)
        data = res.json()

        # Buscar índice del día
        fechas_api = data.get('daily', {}).get('time', [])
        idx = -1
        for i, f_api in enumerate(fechas_api):
            if f_api == flight_date_str:
                idx = i
                break
        
        if idx == -1: return None

        # Conversión de Unidades
        rain_mm = data['daily']['precipitation_sum'][idx] or 0.0
        snow_cm = data['daily']['snowfall_sum'][idx] or 0.0
        wind_kmh = data['daily']['windspeed_10m_max'][idx] or 0.0

        prcp_in = rain_mm / 25.4
        snow_in = snow_cm / 2.54
        awnd_mph = wind_kmh / 1.609

        return prcp_in, snow_in, awnd_mph
    except Exception as e:
        print(f"Error Clima: {e}")
        return None

# --- CICLO DE VIDA (CARGA DE ARTEFACTOS) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    global risk_maps, sess, input_name, smart_ops_lookup, smart_traffic_lookup, static_defaults, global_mean, airport_coords
    
    print("🚀 INICIANDO API...")

    # 1. Descomprimir ONNX si hace falta
    onnx_path = os.path.join(ARTIFACTS_DIR, ONNX_FILENAME)
    zip_path = os.path.join(ARTIFACTS_DIR, ZIP_FILENAME)
    if not os.path.exists(onnx_path) and os.path.exists(zip_path):
        print("📦 Descomprimiendo modelo...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(ARTIFACTS_DIR)

    # 2. Cargar ONNX
    try:
        print("🧠 Cargando Modelo...")
        sess = rt.InferenceSession(onnx_path)
        input_name = sess.get_inputs()[0].name
    except Exception as e:
        print(f"❌ ERROR FATAL cargando modelo: {e}")
        # No matamos la app aquí, pero fallará al predecir si sess es None

    # 3. Cargar Lookups y Mapas
    try:
        print("📂 Cargando Mapas de Riesgo y Datos...")
        risk_maps['CARRIER_NAME'] = joblib.load(f'{ARTIFACTS_DIR}/CARRIER_NAME_risk_map.joblib')
        risk_maps['DEPARTING_AIRPORT'] = joblib.load(f'{ARTIFACTS_DIR}/DEPARTING_AIRPORT_risk_map.joblib')
        risk_maps['DEP_TIME_BLK'] = joblib.load(f'{ARTIFACTS_DIR}/DEP_TIME_BLK_risk_map.joblib')
        
        # Cargar Previous Airport si existe (opcional)
        path_prev = f'{ARTIFACTS_DIR}/PREVIOUS_AIRPORT_risk_map.joblib'
        if os.path.exists(path_prev):
            risk_maps['PREVIOUS_AIRPORT'] = joblib.load(path_prev)

        smart_ops_lookup = joblib.load(f'{ARTIFACTS_DIR}/smart_ops_lookup.joblib')
        smart_traffic_lookup = joblib.load(f'{ARTIFACTS_DIR}/smart_traffic_lookup.joblib')
        global_mean = joblib.load(f'{ARTIFACTS_DIR}/global_mean.joblib')

        # --- NUEVO: CARGAR COORDENADAS AUTOMÁTICAS ---
        path_coords = f'{ARTIFACTS_DIR}/airport_coords.joblib'
        if os.path.exists(path_coords):
            airport_coords = joblib.load(path_coords)
            print(f"🌍 Coordenadas cargadas para {len(airport_coords)} aeropuertos.")
        else:
            print("⚠️ No encontré airport_coords.joblib. Ejecuta 'generate_coords.py'.")

        # Cargar Defaults
        if os.path.exists(f'{ARTIFACTS_DIR}/static_defaults.joblib'):
            static_defaults = joblib.load(f'{ARTIFACTS_DIR}/static_defaults.joblib')
        else:
            static_defaults = {
                'NUMBER_OF_SEATS': 150, 'PLANE_AGE': 12, 
                'FLT_ATTENDANTS_PER_PASS': 0.009, 'GROUND_SERV_PER_PASS': 0.001,
                'CONCURRENT_FLIGHTS': 20
            } # <--- AQUÍ FALTABA CERRAR LA LLAVE EN TU CÓDIGO ANTERIOR

    except Exception as e:
        print(f"⚠️ Advertencia cargando archivos auxiliares: {e}")

    print("✅ API LISTA")
    yield

app = FastAPI(lifespan=lifespan)

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/predict")
def predict_flight(data: FlightRequest):
    # Uso de HTTPException: Si el modelo no cargó, lanzamos error 503
    if sess is None:
        raise HTTPException(status_code=503, detail="El modelo no está cargado en el servidor.")

    # 1. Procesar Fecha
    try:
        dt = datetime.strptime(data.FECHA, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de fecha inválido. Usa YYYY-MM-DD")

    month = dt.month
    day_of_week = dt.weekday() + 1
    
    try:
        hour = int(data.HORA.split(':')[0])
        time_blk = f"{hour:02d}00-{hour:02d}59"
    except:
        time_blk = "1200-1259" # Fallback

    # 2. Clima
    source_info = "Histórico (Promedio)"
    
    if data.PRCP is not None:
        final_prcp = data.PRCP
        final_snow = data.SNOW if data.SNOW else 0.0
        final_awnd = data.AWND if data.AWND else 0.0
        source_info = "Simulación Manual"
    else:
        live = get_live_weather(data.DEPARTING_AIRPORT, data.FECHA)
        if live:
            final_prcp, final_snow, final_awnd = live
            source_info = "Tiempo Real (Open-Meteo)"
        else:
            # Fallback estacional
            final_prcp = 0.08
            final_snow = 0.5 if month in [12, 1, 2] else 0.0
            final_awnd = 12.0 if month in [12, 1, 2] else 8.0

    # 3. Inferencia de Datos Faltantes
    op_key = (data.CARRIER_NAME, data.DEPARTING_AIRPORT)
    ops_data = smart_ops_lookup.get(op_key, {})
    
    traffic_key = (data.DEPARTING_AIRPORT, time_blk)
    traffic_data = smart_traffic_lookup.get(traffic_key, {})

    val_seats = ops_data.get('NUMBER_OF_SEATS', static_defaults.get('NUMBER_OF_SEATS', 150))
    val_attendants = ops_data.get('FLT_ATTENDANTS_PER_PASS', static_defaults.get('FLT_ATTENDANTS_PER_PASS', 0.009))
    val_ground = ops_data.get('GROUND_SERV_PER_PASS', static_defaults.get('GROUND_SERV_PER_PASS', 0.001))
    val_plane_age = ops_data.get('PLANE_AGE', static_defaults.get('PLANE_AGE', 12))
    val_concurrent = traffic_data.get('CONCURRENT_FLIGHTS', static_defaults.get('CONCURRENT_FLIGHTS', 20))
    
    # 4. Riesgos
    risk_carrier = risk_maps['CARRIER_NAME'].get(data.CARRIER_NAME, global_mean)
    risk_airport = risk_maps['DEPARTING_AIRPORT'].get(data.DEPARTING_AIRPORT, global_mean)
    risk_time = risk_maps['DEP_TIME_BLK'].get(time_blk, global_mean)
    risk_prev = risk_maps.get('PREVIOUS_AIRPORT', {}).get('UNKNOWN', global_mean)

    # 5. Vector Final
    features = [
        month, day_of_week, 4, 1, val_concurrent,
        final_prcp, 25.0, final_awnd, val_plane_age, 2000,
        risk_carrier, risk_airport, risk_time,
        final_snow, 0.0, val_seats,
        val_attendants, val_ground,
        risk_prev
    ]

    # 6. Predicción
    input_tensor = np.array([features], dtype=np.float32)
    results = sess.run(None, {input_name: input_tensor})
    prob_delay = float(results[1][0].get(1, 0.0))

    return {
        "prediction": "RETRASADO" if prob_delay > 0.68 else "PUNTUAL",
        "probability": round(prob_delay, 2),
        "details": f"Clima: {source_info} | Riesgo Ruta: {risk_airport:.2f}",
        "weather_used": {"rain": final_prcp, "wind": final_awnd}
    }