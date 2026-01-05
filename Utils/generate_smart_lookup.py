import pandas as pd
import joblib
import os

DATA_PATH = 'Data/full_data_flightdelay.csv'
ARTIFACTS_DIR = 'artifacts'

def generar_lookup_inteligente():
    print("🧠 Generando Base de Conocimiento de Operaciones...")
    
    # Carga inteligente del CSV con solo las columnas necesarias
    cols = [
        'CARRIER_NAME', 'DEPARTING_AIRPORT', 'DEP_TIME_BLK', # Claves de búsqueda
        'NUMBER_OF_SEATS', 'PLANE_AGE',                      # Datos del Avión
        'FLT_ATTENDANTS_PER_PASS', 'GROUND_SERV_PER_PASS',   # Datos de Personal
        'CONCURRENT_FLIGHTS'                                 # Datos de Tráfico
    ]
    
    try:
        df = pd.read_csv(DATA_PATH, usecols=cols, sep=None, engine='python', skipinitialspace=True, encoding='utf-8-sig')
    except:
        print("Error cargando CSV.")
        return

    # 1. AGRUPAR POR AEROLÍNEA Y AEROPUERTO
    # "Dime cómo son los aviones de American Airlines cuando salen de JFK"
    print("   -> Calculando perfiles operativos por Aerolínea y Ruta...")
    
    # Usamos la mediana para evitar valores locos
    smart_lookup = df.groupby(['CARRIER_NAME', 'DEPARTING_AIRPORT'])[
        ['NUMBER_OF_SEATS', 'PLANE_AGE', 'FLT_ATTENDANTS_PER_PASS', 'GROUND_SERV_PER_PASS']
    ].median().to_dict('index')

    # 2. AGRUPAR TRÁFICO POR AEROPUERTO Y HORA
    # "Dime cuánto tráfico hay en JFK a las 8 AM"
    print("   -> Calculando congestión por Aeropuerto y Hora...")
    traffic_lookup = df.groupby(['DEPARTING_AIRPORT', 'DEP_TIME_BLK'])[
        ['CONCURRENT_FLIGHTS']
    ].median().to_dict('index')

    # 3. GUARDAR
    joblib.dump(smart_lookup, f'{ARTIFACTS_DIR}/smart_ops_lookup.joblib')
    joblib.dump(traffic_lookup, f'{ARTIFACTS_DIR}/smart_traffic_lookup.joblib')
    
    print("✅ Artefactos Inteligentes generados.")
    print("Ejemplo: Si vuelo con 'AA' desde 'JFK', el sistema sabe que uso este avión:")
    try:
        print(smart_lookup.get(('AA', 'JFK'), "No hay datos exactos, usaremos promedio"))
    except:
        pass

if __name__ == "__main__":
    generar_lookup_inteligente()