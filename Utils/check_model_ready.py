import requests
import time
import sys

# URL de tu API (ajustar según el entorno, localhost para pruebas entre contenedores)
URL = "http://localhost:8000/predict"
# Payload dummy para probar que el modelo RESPONDE, no solo que la API prende
DUMMY_PAYLOAD = {
  "MONTH": 1, "DAY_OF_WEEK": 1, "DISTANCE_GROUP": 1, "SEGMENT_NUMBER": 1,
  "CONCURRENT_FLIGHTS": 1, "PRCP": 0, "TMAX": 20, "AWND": 5, "PLANE_AGE": 5,
  "AIRPORT_FLIGHTS_MONTH": 100, "CARRIER_NAME": "AA",
  "DEPARTING_AIRPORT": "JFK", "DEP_TIME_BLK": "0800-0859"
}

MAX_RETRIES = 30  # Intentar por 30 veces
SLEEP_TIME = 5    # Esperar 5 segundos entre intentos (Total 2.5 min de espera)

print("🕵️‍♂️ INICIO: Esperando a que el modelo de Data Science cargue...")

for i in range(MAX_RETRIES):
    try:
        response = requests.post(URL, json=DUMMY_PAYLOAD, timeout=5)
        
        # Si devuelve 503, la API está viva pero el modelo sigue cargando (ver tu main.py)
        if response.status_code == 503:
            print(f"⏳ Intento {i+1}/{MAX_RETRIES}: API viva, pero modelo cargando...")
        
        # Si devuelve 200, ¡éxito total!
        elif response.status_code == 200:
            print("✅ ¡MODELO LISTO! El servicio de Data Science está operativo.")
            print(f"   Respuesta de prueba: {response.json()}")
            sys.exit(0) # Salir con éxito (código 0)
            
        else:
            print(f"⚠️ Alerta: La API devolvió código {response.status_code}")

    except requests.exceptions.ConnectionError:
        print(f"❌ Intento {i+1}/{MAX_RETRIES}: No se puede conectar (¿API caída?)")
    
    time.sleep(SLEEP_TIME)

print("💀 ERROR CRÍTICO: El modelo no cargó a tiempo. Abortando.")
sys.exit(1) # Salir con error para que el pipeline de despliegue falle