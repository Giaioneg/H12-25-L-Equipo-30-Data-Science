import joblib
from matplotlib.pylab import f
import numpy as np
import onnxruntime as rt
import os
import zipfile
import json
import requests
import pytz
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
from timezonefinder import TimezoneFinder
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

tf = TimezoneFinder()    

# --- 2. FUNCIONES AUXILIARES ---
def get_live_weather(airport_name, flight_date_str):
    print(f"\n Buscando clima para: '{airport_name}' en fecha '{flight_date_str}'")

    coords = airport_coords.get(airport_name)
    if not coords: 
        print(f"    ERROR: No tengo coordenadas para '{airport_name}'.")
        print(f"    Ejemplos de claves que si tengo: {list(airport_coords.keys())[:5]}")
        
        return None
    print(f"   Coordenadas encontradas: {coords}")

    lat = coords['lat']
    lon = coords['lon']
     
    try:
        timezone_str = tf.timezone_at(lng=lon, lat=lat)
        flight_date = datetime.strptime(flight_date_str, "%Y-%m-%d").date()
        today = datetime.now().date()
        delta = (flight_date - today).days

        if not timezone_str:
            # Fallback seguro si el aeropuerto está en medio del mar (raro)
            timezone_str = "UTC"

        local_tz = pytz.timezone(timezone_str)

        flight_dt_naive = datetime.strptime(flight_date_str, "%Y-%m-%d")
        flight_dt_local = local_tz.localize(flight_dt_naive)

        now_in_airport = datetime.now(local_tz)

        delta = (flight_dt_local.date() - now_in_airport.date()).days

        print(f"Aeropuerto: {airport_name} | Zona: {timezone_str}")
        print(f"Vuelo (Local): {flight_dt_local.date()} | Hoy (Local): {now_in_airport.date()}")
        print(f"⏱Delta días: {delta}")
        
        # Solo buscamos clima si es hoy o en los proximos 7 dias
        if delta < 0 or delta > 7: 
            print("    Fecha fuera de rango para pronostico (Usando historico).")
            return None 
        
        lat = coords['lat']; lon = coords['lon']
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=precipitation_sum,snowfall_sum,windspeed_10m_max,temperature_2m_max&timezone={timezone_str}"
        headers = {"User-Agent": "FlightDelayApp/1.0"}
        
        # MEJORA: Timeout bajado a 1.5s para no bloquear la demo si falla
        res = requests.get(url, headers=headers, timeout=1.5, verify=False)

        if res.status_code != 200:
            print(f"   Error API Clima: Status {res.status_code}")
            return None
        
        data = res.json()
        fechas_api = data.get('daily', {}).get('time', [])


        idx = -1
        for i, f_api in enumerate(fechas_api):
            if f_api == flight_date_str: 
                idx = i; break


        if idx == -1: 
            print(f"   La fecha {flight_date_str} no esta en la respuesta de la API.")
            return None
        
        temp_c = data['daily']['temperature_2m_max'][idx]
        print(f"   🌡️ Temperatura real: {temp_c}°C")

        prcp_mm = data['daily']['precipitation_sum'][idx]
        snow_mm = data['daily']['snowfall_sum'][idx]
        wind_mph = data['daily']['windspeed_10m_max'][idx]

        print(f" Clima: {prcp_mm}mm Lluvia, {snow_mm}mm Nieve, {temp_c}°C Temp, {wind_mph}km/h Viento")

        return (prcp_mm, snow_mm, wind_mph, temp_c) 

    except Exception as e:
        print(f"   Excepcion buscando clima: {e}")
        return None

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

@app.get("/")
def health_check():
    return {
        "status": "online",
        "service": "Flight Delay API",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/favicon.ico")
def favicon():
    return "" # Para que deje de molestar con 404

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
        final_prcp_mm, final_snow_mm, final_awnd_kmh, final_tmax_c = live
    else:
        final_prcp_mm, final_snow_mm, final_awnd_kmh, final_tmax_c = 0.08, 0.0, 8.0, 25.0

    final_prcp_in = final_prcp_mm / 25.4  # Convertir mm a pulgadas

    final_snow_in = final_snow_mm / 25.4  # Convertir mm a pulgadas

    final_awnd_mph = final_awnd_kmh / 1.609  # Convertir km/h a mph

    # Convertir TMAX de °C a °F
    final_tmax_f_for_model = (final_tmax_c * 9/5) + 32    

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
        month, 
        day_of_week, 
        4, 
        1, 
        val_concurrent,
        final_prcp_in, 
        final_tmax_f_for_model, 
        final_awnd_mph, 
        val_plane_age, 
        2000,
        risk_carrier, 
        risk_airport, 
        risk_time,
        final_snow_in, 
        0.0, 
        val_seats,
        val_attendants, 
        val_ground,
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
    weather_parts = []

    weather_parts.append(f"🌡️ {final_tmax_c:.0f}°C | {final_tmax_f_for_model:.0f}°F")

    weather_parts.append(f"Lluvia: {final_prcp_mm}mm | {final_prcp_in:.2f}\"")

    if final_snow_in > 0.01:
        weather_parts.append(f"Nieve: {final_snow_mm}mm | {final_snow_in:.2f}\"")

    weather_parts.append(f"Viento: {final_awnd_kmh:.1f}km/h | {final_awnd_mph:.1f}mp/h")

    info_clima = ", ".join(weather_parts)
   
    info_clima_detallado = f"{source_info} {info_clima}"

    return {
        "prediction": "RETRASADO" if prob_delay > 0.55 else "PUNTUAL", # Umbral ajustado
        "probability": round(prob_delay, 2),  # <--- CORREGIDO: "probability" (ingles)
        "details": f"Riesgo Aeropuerto: {round(risk_airport, 2)} | {info_clima_detallado}",
        "enriched_data": {

            # Precipitation
            "PRCP_MM": final_prcp_mm,
            "PRCP_IN": final_prcp_in,

            # Snow
            "SNOW_MM": final_snow_mm,
            "SNOW_IN": final_snow_in,

            # Temperature
            "TMAX_C": final_tmax_c,
            "TMAX_F": final_tmax_f_for_model,

            # Wind
            "AWND_KMH": final_awnd_kmh,
            "AWND_MPH": final_awnd_mph,

            # Lookups
            "CONCURRENT_FLIGHTS": float(val_concurrent)
        }
    }