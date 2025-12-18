import joblib
import numpy as np
import onnxruntime as rt
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# --- CARGA DE ARTEFACTOS ---
ARTIFACTS_DIR = 'artifacts'
risk_maps = {}
sess = None
input_name = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global risk_maps, sess, input_name
    print("🔄 INICIO: Intentando cargar artefactos...")  # <--- NUEVO
    try:
        # Cargar mapas
        print("   -> Cargando mapa CARRIER...") 
        risk_maps['CARRIER_NAME'] = joblib.load(f'{ARTIFACTS_DIR}/CARRIER_NAME_risk_map.joblib')
        
        print("   -> Cargando mapa AIRPORT...")
        risk_maps['DEPARTING_AIRPORT'] = joblib.load(f'{ARTIFACTS_DIR}/DEPARTING_AIRPORT_risk_map.joblib')
        
        print("   -> Cargando mapa TIME...")
        risk_maps['DEP_TIME_BLK'] = joblib.load(f'{ARTIFACTS_DIR}/DEP_TIME_BLK_risk_map.joblib')
        
        # Cargar modelo
        print("   -> Cargando modelo ONNX...")
        sess = rt.InferenceSession(f"{ARTIFACTS_DIR}/flight_delay_rf.onnx")
        input_name = sess.get_inputs()[0].name
        
        print("✅ ÉXITO: Todo cargado correctamente.")
    except Exception as e:
        print(f"❌ ERROR FATAL cargando artefactos: {e}")
        # Importante: Si falla, esto imprimirá el error real en la consola
    yield

app = FastAPI(title="Flight Delay API", lifespan=lifespan)

# --- ESQUEMA DE DATOS ---
class FlightData(BaseModel):
    MONTH: int
    DAY_OF_WEEK: int
    DISTANCE_GROUP: int
    SEGMENT_NUMBER: int
    CONCURRENT_FLIGHTS: int
    PRCP: float
    TMAX: float
    AWND: float
    PLANE_AGE: int
    AIRPORT_FLIGHTS_MONTH: int
    CARRIER_NAME: str       # Ej: "AA"
    DEPARTING_AIRPORT: str  # Ej: "JFK"
    DEP_TIME_BLK: str       # Ej: "0600-0659"

@app.get("/")
def health_check():
    return {"status": "ok", "model": "Flight Delay Random Forest"}

@app.post("/predict")
def predict_delay(data: FlightData):
    if sess is None:
        raise HTTPException(status_code=503, detail="Modelo no cargado.")
        

    # 1. Transformación de datos (Target Encoding)
    # Si llega un aeropuerto nuevo que no conocemos, usamos 0.15 (riesgo promedio)
    c_risk = risk_maps['CARRIER_NAME'].get(data.CARRIER_NAME, 0.15)
    a_risk = risk_maps['DEPARTING_AIRPORT'].get(data.DEPARTING_AIRPORT, 0.15)
    t_risk = risk_maps['DEP_TIME_BLK'].get(data.DEP_TIME_BLK, 0.15)

    # 2. Vector para el modelo (Orden estricto)
    features = [
        data.MONTH, data.DAY_OF_WEEK, data.DISTANCE_GROUP, data.SEGMENT_NUMBER,
        data.CONCURRENT_FLIGHTS, data.PRCP, data.TMAX, data.AWND, data.PLANE_AGE,
        data.AIRPORT_FLIGHTS_MONTH, c_risk, a_risk, t_risk
    ]

    # 3. Predicción con ONNX
    input_data = np.array([features], dtype=np.float32)
    # ONNX devuelve [etiqueta, lista_de_mapas_de_probabilidad]
    res = sess.run(None, {input_name: input_data})
    
    probability = res[1][0][1] # Probabilidad de retraso (Clase 1)
    
    # Umbral personalizado definido por Data Science
    threshold = 0.55
    prediction = 1 if probability > threshold else 0

    return {
        "is_delayed": bool(prediction),
        "probability": round(probability, 4),
        "threshold": threshold
    }