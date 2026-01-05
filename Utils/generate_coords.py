import pandas as pd
import joblib
import os

DATA_PATH = 'Data/full_data_flightdelay.csv'
ARTIFACTS_DIR = 'artifacts'
os.makedirs(ARTIFACTS_DIR, exist_ok=True)

def generar_coordenadas():
    print("🌍 Extrayendo coordenadas de los aeropuertos del dataset...")
    
    cols = ['DEPARTING_AIRPORT', 'LATITUDE', 'LONGITUDE']
    
    try:
        # Leemos solo las columnas necesarias para ir rápido
        df = pd.read_csv(DATA_PATH, usecols=cols, sep=None, engine='python')
        
        # Eliminamos duplicados: Queremos 1 fila por aeropuerto
        unique_airports = df.drop_duplicates(subset=['DEPARTING_AIRPORT'])
        
        # Creamos el diccionario: { "JFK": {"lat": 40.6, "lon": -73.7}, ... }
        coords_dict = {}
        
        for _, row in unique_airports.iterrows():
            airport = row['DEPARTING_AIRPORT'].strip()
            lat = row['LATITUDE']
            lon = row['LONGITUDE']
            
            # Validación básica
            if pd.notna(lat) and pd.notna(lon):
                coords_dict[airport] = {"lat": lat, "lon": lon}
        
        # Guardar
        output_path = f'{ARTIFACTS_DIR}/airport_coords.joblib'
        joblib.dump(coords_dict, output_path)
        
        print(f"✅ ¡Listo! Coordenadas guardadas para {len(coords_dict)} aeropuertos en:")
        print(f"   -> {output_path}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    generar_coordenadas()