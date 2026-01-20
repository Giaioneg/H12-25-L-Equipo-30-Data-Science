import pandas as pd
import json
import joblib
import os

# --- CONFIGURACIÓN ---
CSV_PATH = 'Data/full_data_flightdelay.csv'
ARTIFACTS_DIR = 'artifacts'
OUTPUT_JSON = 'artifacts/frontend_options_REAL.json'

def generar_mapeo():
    print("🚀 Iniciando generador (Modo Solo Nombres)...")

    # 1. Cargar el "Cerebro" (Joblibs)
    # Esto es vital para asegurar que solo exportamos lo que el modelo conoce
    try:
        carrier_map = joblib.load(f'{ARTIFACTS_DIR}/CARRIER_NAME_risk_map.joblib')
        airport_map = joblib.load(f'{ARTIFACTS_DIR}/DEPARTING_AIRPORT_risk_map.joblib')
        
        valid_carriers = set(carrier_map.keys())
        valid_airports = set(airport_map.keys())
        print(f"✅ Modelo cargado. Conoce {len(valid_carriers)} aerolíneas y {len(valid_airports)} aeropuertos.")
    except Exception as e:
        print(f"❌ Error cargando joblibs: {e}")
        print("Asegúrate de ejecutar esto en la carpeta correcta.")
        return

    # 2. Cargar CSV (Solo las columnas que existen)
    print("📂 Cargando CSV...")
    try:
        cols = ['CARRIER_NAME', 'DEPARTING_AIRPORT'] 
        df = pd.read_csv(CSV_PATH, usecols=cols)
    except Exception as e:
        print(f"❌ Error leyendo CSV: {e}")
        return

    # 3. Generar Lista de Aerolíneas
    print("✈️ Procesando Aerolíneas...")
    carriers_list = []
    
    # Obtenemos los nombres únicos directamente
    unique_carriers = df['CARRIER_NAME'].dropna().unique()
    
    for name in unique_carriers:
        # SOLO agregamos si el modelo conoce este nombre
        if name in valid_carriers:
            carriers_list.append({
                "label": name,  # Ej: "JetBlue Airways" (Se verá así en la lista)
                "value": name   # Ej: "JetBlue Airways" (Se enviará así al backend)
            })
    
    # Ordenar alfabéticamente
    carriers_list.sort(key=lambda x: x['label'])

    # 4. Generar Lista de Aeropuertos
    print("🏢 Procesando Aeropuertos...")
    airports_list = []
    
    unique_airports = df['DEPARTING_AIRPORT'].dropna().unique()

    for name in unique_airports:
        if name in valid_airports:
            airports_list.append({
                "label": name,
                "value": name
            })
    
    airports_list.sort(key=lambda x: x['label'])

    # 5. Guardar JSON Final
    final_json = {
        "carriers": carriers_list,
        "airports": airports_list
    }

    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(final_json, f, indent=4, ensure_ascii=False)

    print(f"\n✨ ¡ÉXITO! Archivo generado: {OUTPUT_JSON}")
    print(f"   -> Aerolíneas exportadas: {len(carriers_list)}")
    print(f"   -> Aeropuertos exportados: {len(airports_list)}")
    print("\n👉 Instrucciones:")
    print("1. Copia 'frontend_options_REAL.json' a la carpeta 'assets/frontend_options.json' de tu Frontend.")
    print("2. (Opcional) Si tu backend usa carga dinámica, cópialo también a 'artifacts/frontend_options.json'.")

if __name__ == "__main__":
    generar_mapeo()