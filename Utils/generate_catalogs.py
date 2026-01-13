import pandas as pd
import joblib
import json
import os

# --- CONFIGURACIÓN ---
DATA_PATH = 'Data/full_data_flightdelay.csv'
ARTIFACTS_DIR = 'artifacts'
os.makedirs(ARTIFACTS_DIR, exist_ok=True)

def generar_inteligencia_total():
    print("🚀 INICIANDO ESCANEO TOTAL DE AEROLÍNEAS Y RUTAS...")

    # 1. CARGA ROBUSTA (La técnica que ya validamos que funciona)
    # Cargamos solo las columnas necesarias para generar la inteligencia
    cols_necesarias = [
        'CARRIER_NAME', 'DEPARTING_AIRPORT', 'DEP_TIME_BLK', 
        'NUMBER_OF_SEATS', 'PLANE_AGE', 
        'FLT_ATTENDANTS_PER_PASS', 'GROUND_SERV_PER_PASS',
        'CONCURRENT_FLIGHTS'
    ]
    
    try:
        print("📂 Leyendo dataset maestro...")
        # Detectar separador
        with open(DATA_PATH, 'r', encoding='utf-8-sig') as f:
            linea = f.readline()
        sep = ';' if ';' in linea else ','

        df = pd.read_csv(
            DATA_PATH, 
            usecols=cols_necesarias, 
            sep=sep, 
            skipinitialspace=True, 
            encoding='utf-8-sig',
            engine='python'
        )
        # Limpiar nombres de columnas y strings
        df.columns = df.columns.str.strip()
        df['CARRIER_NAME'] = df['CARRIER_NAME'].str.strip()
        df['DEPARTING_AIRPORT'] = df['DEPARTING_AIRPORT'].str.strip()
        
    except Exception as e:
        print(f"❌ Error fatal cargando CSV: {e}")
        return

    print(f"✅ Datos cargados: {df.shape[0]} registros.")

    # --- PASO 2: GENERAR CATÁLOGOS (Para el Front-End) ---
    print("\n📋 Generando Catálogos para el Front-End...")
    
    unique_carriers = sorted(df['CARRIER_NAME'].unique().tolist())
    unique_airports = sorted(df['DEPARTING_AIRPORT'].unique().tolist())
    
    catalogs = {
        "valid_carriers": unique_carriers,
        "valid_airports": unique_airports,
        "count_carriers": len(unique_carriers),
        "count_airports": len(unique_airports)
    }
    
    # Guardar como JSON (Legible para humanos y Java)
    with open(f'{ARTIFACTS_DIR}/catalogs.json', 'w', encoding='utf-8') as f:
        json.dump(catalogs, f, indent=4)
        
    print(f"   -> Encontradas {len(unique_carriers)} Aerolíneas únicas.")
    print(f"   -> Encontrados {len(unique_airports)} Aeropuertos únicos.")
    print(f"   -> Archivo 'catalogs.json' guardado.")

    # --- PASO 3: SMART LOOKUPS (El Cerebro Operativo) ---
    print("\n🧠 Aprendiendo perfiles operativos de CADA Aerolínea...")
    
    # Agrupamos por Aerolínea Y Aeropuerto
    # Esto calcula el promedio automáticos para AA en JFK, pero también para DL en LAX, etc.
    ops_lookup = df.groupby(['CARRIER_NAME', 'DEPARTING_AIRPORT'])[
        ['NUMBER_OF_SEATS', 'PLANE_AGE', 'FLT_ATTENDANTS_PER_PASS', 'GROUND_SERV_PER_PASS']
    ].median().to_dict('index')
    
    joblib.dump(ops_lookup, f'{ARTIFACTS_DIR}/smart_ops_lookup.joblib')
    print(f"   -> Perfiles operativos guardados para {len(ops_lookup)} rutas únicas.")

    # --- PASO 4: TRAFFIC LOOKUPS (Cerebro de Tráfico) ---
    print("\n🚦 Aprendiendo patrones de tráfico...")
    
    traffic_lookup = df.groupby(['DEPARTING_AIRPORT', 'DEP_TIME_BLK'])[
        ['CONCURRENT_FLIGHTS']
    ].median().to_dict('index')
    
    joblib.dump(traffic_lookup, f'{ARTIFACTS_DIR}/smart_traffic_lookup.joblib')
    print(f"   -> Patrones de tráfico guardados ({len(traffic_lookup)} combinaciones).")

    # --- VALIDACIÓN FINAL ---
    print("\n🔎 PRUEBA DE CALIDAD:")
    print("Muestreo de 3 Aerolíneas aleatorias detectadas:")
    import random
    muestras = random.sample(unique_carriers, min(3, len(unique_carriers)))
    for c in muestras:
        # Buscamos un aeropuerto donde opere esta aerolínea
        rutas_aerolinea = [k for k in ops_lookup.keys() if k[0] == c]
        if rutas_aerolinea:
            ruta = rutas_aerolinea[0]
            print(f"   * {c} (en {ruta[1]}): Avión típico ~{ops_lookup[ruta]['NUMBER_OF_SEATS']} asientos.")

    print("\n🎉 TODO LISTO. Entrega la carpeta 'artifacts' al equipo de Back-End.")

if __name__ == "__main__":
    generar_inteligencia_total()