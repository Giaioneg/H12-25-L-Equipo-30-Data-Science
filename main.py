import joblib
import numpy as np
import onnxruntime as rt
import os
import zipfile
import json
import requests
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime

# --- CONFIGURACION ---
ARTIFACTS_DIR = 'artifacts'
ONNX_FILENAME = 'flight_delay_rf_weighted.onnx'
ZIP_FILENAME = 'flight_delay_rf_weighted.onnx.zip'
OPTIONS_FILENAME = 'frontend_options.json' 

# Variables Globales (Se mantienen intactas como pediste)
risk_maps = {}
smart_ops_lookup = {}
smart_traffic_lookup = {}
static_defaults = {}
airport_coords = {} 
sess = None
input_name = None
global_mean = 0.18 # Valor por defecto seguro

# Diccionarios dinamicos
AIRPORT_MAPPING = {}
CARRIER_MAPPING = {}

# --- MODELO DE DATOS ---
class FlightRequest(BaseModel):
    CARRIER_NAME: str
    DEPARTING_AIRPORT: str
    DATE: str
    TIME: str
    # Opcionales
    PRCP: float | None = None
    SNOW: float | None = None
    AWND: float | None = None

# --- 2. FUNCIONES AUXILIARES ---
def get_live_weather(airport_name, flight_date_str):
    coords = airport_coords.get(airport_name)
    if not coords: return None 
    try:
        flight_date = datetime.strptime(flight_date_str, "%Y-%m-%d")
        today = datetime.now()
        delta = (flight_date - today).days
        
        # Solo buscamos clima si es hoy o en los proximos 7 dias
        if delta < 0 or delta > 7: return None 
        
        lat = coords['lat']; lon = coords['lon']
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=precipitation_sum,snowfall_sum,windspeed_10m_max&timezone=auto"
        headers = {"User-Agent": "FlightDelayApp/1.0"}
        
        # MEJORA: Timeout bajado a 1.5s para no bloquear la demo si falla
        res = requests.get(url, headers=headers, timeout=1.5, verify=False)
        
        data = res.json()
        fechas_api = data.get('daily', {}).get('time', [])
        idx = -1
        for i, f_api in enumerate(fechas_api):
            if f_api == flight_date_str: idx = i; break
        if idx == -1: return None
        return (data['daily']['precipitation_sum'][idx]/25.4, 
                data['daily']['snowfall_sum'][idx]/2.54, 
                data['daily']['windspeed_10m_max'][idx]/1.609)
    except: return None

def load_mappings_from_json():
    """Lee frontend_options.json y genera los diccionarios de traduccion dinamicamente"""
    path = os.path.join(ARTIFACTS_DIR, OPTIONS_FILENAME)
    if not os.path.exists(path):
        print(f"Advertencia: No encontre {OPTIONS_FILENAME}. Usando mapeos vacios.")
        return

    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Cargar Aeropuertos
        count_air = 0
        for item in data.get('airports', []):
            if 'code' in item and 'value' in item:
                AIRPORT_MAPPING[item['code']] = item['value']
                AIRPORT_MAPPING[item['value']] = item['value']
                count_air += 1

        # Cargar Aerolineas
        count_car = 0
        for item in data.get('carriers', []):
            label = item.get('label', '')
            val = item.get('value', '')
            if ' - ' in label:
                code = label.split(' - ')[0]
                CARRIER_MAPPING[code] = val
                count_car += 1
            CARRIER_MAPPING[val] = val

        print(f"Mapeos dinamicos cargados: {count_air} Aeropuertos, {count_car} Aerolineas.")
        
    except Exception as e:
        print(f"Error leyendo JSON de opciones: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    global risk_maps, sess, input_name, smart_ops_lookup, smart_traffic_lookup, static_defaults, global_mean, airport_coords
    
    load_mappings_from_json()

    onnx_path = os.path.join(ARTIFACTS_DIR, ONNX_FILENAME)
    zip_path = os.path.join(ARTIFACTS_DIR, ZIP_FILENAME)
    if not os.path.exists(onnx_path) and os.path.exists(zip_path):
        with zipfile.ZipFile(zip_path, 'r') as zip_ref: zip_ref.extractall(ARTIFACTS_DIR)

    try:
        sess = rt.InferenceSession(onnx_path)
        input_name = sess.get_inputs()[0].name
        
        # Carga de artefactos
        risk_maps['CARRIER_NAME'] = joblib.load(f'{ARTIFACTS_DIR}/CARRIER_NAME_risk_map.joblib')
        risk_maps['DEPARTING_AIRPORT'] = joblib.load(f'{ARTIFACTS_DIR}/DEPARTING_AIRPORT_risk_map.joblib')
        risk_maps['DEP_TIME_BLK'] = joblib.load(f'{ARTIFACTS_DIR}/DEP_TIME_BLK_risk_map.joblib')
        if os.path.exists(f'{ARTIFACTS_DIR}/PREVIOUS_AIRPORT_risk_map.joblib'):
            risk_maps['PREVIOUS_AIRPORT'] = joblib.load(f'{ARTIFACTS_DIR}/PREVIOUS_AIRPORT_risk_map.joblib')
            
        smart_ops_lookup = joblib.load(f'{ARTIFACTS_DIR}/smart_ops_lookup.joblib')
        smart_traffic_lookup = joblib.load(f'{ARTIFACTS_DIR}/smart_traffic_lookup.joblib')
        
        # Intentamos cargar la media global entrenada, si falla usamos la fija
        try:
            global_mean = joblib.load(f'{ARTIFACTS_DIR}/global_mean.joblib')
        except:
            print("No se pudo cargar global_mean.joblib, usando valor por defecto 0.18")
        
        if os.path.exists(f'{ARTIFACTS_DIR}/airport_coords.joblib'):
            airport_coords = joblib.load(f'{ARTIFACTS_DIR}/airport_coords.joblib')
            
        if os.path.exists(f'{ARTIFACTS_DIR}/static_defaults.joblib'):
            static_defaults = joblib.load(f'{ARTIFACTS_DIR}/static_defaults.joblib')
        else:
            static_defaults = {'NUMBER_OF_SEATS': 150, 'PLANE_AGE': 12, 'FLT_ATTENDANTS_PER_PASS': 0.009, 'GROUND_SERV_PER_PASS': 0.001, 'CONCURRENT_FLIGHTS': 20}

        print("API LISTA Y CARGADA")
    except Exception as e:
        print(f"ERROR CARGANDO ARTEFACTOS: {e}")

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

    print("\n --- DIAGNOSTICO DE PREDICCION ---")
    print(f"1. Recibido del Frontend: Carrier='{data.CARRIER_NAME}', Airport='{data.DEPARTING_AIRPORT}'")

    # 1. PROCESAR FECHA (Usando data.DATE, no fecha_partida)
    try:
        # El frontend manda "YYYY-MM-DD" (ej: 2025-01-20)
        dt = datetime.strptime(data.DATE, "%Y-%m-%d")
        fecha_str = data.DATE
        month = dt.month
        day_of_week = dt.weekday() + 1
        
        # Procesar hora (data.TIME viene como "HH:MM")
        hour = int(data.TIME.split(':')[0])
        time_blk = f"{hour:02d}00-{hour:02d}59"
    except Exception as e:
        print(f"Error procesando fecha/hora: {e}")
        month, day_of_week, hour = 1, 1, 12
        time_blk = "1200-1259"
        fecha_str = "2026-01-01"

    # 2. TRADUCCION (Usando nombres en INGLES del modelo)
    # data.DEPARTING_AIRPORT y data.CARRIER_NAME son los correctos
    nombre_aeropuerto = AIRPORT_MAPPING.get(data.DEPARTING_AIRPORT.upper(), data.DEPARTING_AIRPORT)
    nombre_aerolinea = CARRIER_MAPPING.get(data.CARRIER_NAME.upper(), data.CARRIER_NAME)
    
    print(f"2. Traducido a: Carrier='{nombre_aerolinea}', Airport='{nombre_aeropuerto}'")

    # 3. CLIMA
    live = get_live_weather(nombre_aeropuerto, fecha_str)
    if live:
        final_prcp, final_snow, final_awnd = live
    else:
        final_prcp, final_snow, final_awnd = 0.08, 0.0, 8.0

    # 4. LOOKUPS (Busquedas inteligentes)
    op_key = (nombre_aerolinea, nombre_aeropuerto)
    ops_data = smart_ops_lookup.get(op_key, {})
    
    traffic_key = (nombre_aeropuerto, time_blk)
    traffic_data = smart_traffic_lookup.get(traffic_key, {})

    val_seats = ops_data.get('NUMBER_OF_SEATS', static_defaults.get('NUMBER_OF_SEATS', 150))
    val_attendants = ops_data.get('FLT_ATTENDANTS_PER_PASS', static_defaults.get('FLT_ATTENDANTS_PER_PASS', 0.009))
    val_ground = ops_data.get('GROUND_SERV_PER_PASS', static_defaults.get('GROUND_SERV_PER_PASS', 0.001))
    val_plane_age = ops_data.get('PLANE_AGE', static_defaults.get('PLANE_AGE', 12))
    val_concurrent = traffic_data.get('CONCURRENT_FLIGHTS', static_defaults.get('CONCURRENT_FLIGHTS', 20))
    
    # 5. RIESGOS (Usando mapas cargados)
    risk_carrier = risk_maps.get('CARRIER_NAME', {}).get(nombre_aerolinea, global_mean)
    risk_airport = risk_maps.get('DEPARTING_AIRPORT', {}).get(nombre_aeropuerto, global_mean)
    risk_time = risk_maps.get('DEP_TIME_BLK', {}).get(time_blk, global_mean)
    
    # Manejo seguro de Previous Airport
    print(f"3. Buscando '{nombre_aeropuerto}' en el mapa...")
    if 'PREVIOUS_AIRPORT' in risk_maps:
        risk_prev = risk_maps['PREVIOUS_AIRPORT'].get('UNKNOWN', global_mean)
        print(f"    ENCONTRADO! Valor: {risk_airport}")
    else:
        print(f"    NO ENCONTRADO. Usando default: {global_mean}")
        print("    Quizas quisiste decir alguno de estos?:")
        risk_prev = global_mean
        mapa_aeropuertos = risk_maps.get('DEPARTING_AIRPORT', {})
        for k in list(mapa_aeropuertos.keys())[:50]: # Imprimimos los primeros 50 para ver
             if "Birmingham" in k:
                 print(f"      -> '{k}'") # Fijate si tiene espacios extra aqui
    
        print("--------------------------------------\n")

    # 6. VECTOR DE ENTRADA (Orden ESTRICTO del modelo ONNX)
    features = [
        month, day_of_week, 4, 1, val_concurrent,
        final_prcp, 25.0, final_awnd, val_plane_age, 2000,
        risk_carrier, risk_airport, risk_time,
        final_snow, 0.0, val_seats,
        val_attendants, val_ground,
        risk_prev
    ]

    # 7. PREDECIR
    try:
        if sess:
            input_tensor = np.array([features], dtype=np.float32)
            results = sess.run(None, {input_name: input_tensor})
            # El modelo devuelve un mapa en la posicion 1. Buscamos la prob de clase 1 (Retraso)
            prob_delay = float(results[1][0].get(1, 0.0))
        else:
            print("Modelo no cargado (sess es None)")
            prob_delay = 0.5
    except Exception as e:
        print(f"Error en inferencia ONNX: {e}")
        prob_delay = global_mean

    # 8. RESPUESTA JSON (Corregida para el Frontend)
    source_info = "Tiempo Real:" if live else "Historico:"
    info_clima_detallado = f"{source_info} (Lluvia: {final_prcp:.2f}\", Viento: {final_awnd:.1f}mph)"

    return {
        "prediction": "RETRASADO" if prob_delay > 0.55 else "PUNTUAL", # Umbral ajustado
        "probability": round(prob_delay, 2),  # <--- CORREGIDO: "probability" (ingles)
        "details": f"Riesgo Aeropuerto: {round(risk_airport, 2)} | {info_clima_detallado}",
        "enriched_data": {
            "PRCP": final_prcp,
            "TMAX": 25.0,
            "AWND": final_awnd,
            "SNOW": final_snow,
            "CONCURRENT_FLIGHTS": float(val_concurrent)
        }
    }