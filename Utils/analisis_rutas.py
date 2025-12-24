import pandas as pd

# Configuración
DATA_PATH = 'Data/full_data_flightdelay.csv'

def auditar_rutas():
    print("📂 Cargando dataset para auditoría de rutas...")
    
    # 1. Cargamos solo las columnas necesarias para no saturar la memoria
    # Buscamos columnas que suenen a Destino. Generalmente es 'ARRIVING_AIRPORT', 'DEST', o 'DEST_AIRPORT_ID'
    # Como no sé el nombre exacto de tu columna de destino, cargaremos el header primero
    preview = pd.read_csv(DATA_PATH, nrows=0)
    cols = list(preview.columns)
    
    # Intentamos adivinar la columna de destino
    posibles_destinos = [c for c in cols if 'DEST' in c or 'ARRIV' in c]
    col_destino = posibles_destinos[0] if posibles_destinos else None
    
    cols_to_load = ['CARRIER_NAME', 'DEPARTING_AIRPORT']
    if col_destino:
        cols_to_load.append(col_destino)
        print(f"✅ Columna de destino detectada: {col_destino}")
    else:
        print("⚠️ No se encontró una columna obvia de 'Destino'. Solo analizaremos Origen.")

    # Cargar datos
    df = pd.read_csv(DATA_PATH, usecols=cols_to_load)

    print("\n" + "="*40)
    print("✈️ REPORTE DE AEROLÍNEAS Y RUTAS")
    print("="*40)

    # --- 1. AEROLÍNEAS ---
    aerolineas = df['CARRIER_NAME'].unique()
    print(f"\n🔹 Total de Aerolíneas encontradas: {len(aerolineas)}")
    print("Lista completa de aerolíneas:")
    print(sorted(aerolineas))

    # --- 2. AEROPUERTOS DE SALIDA (Origen) ---
    origenes = df['DEPARTING_AIRPORT'].unique()
    print(f"\n🔹 Total de Aeropuertos de Salida: {len(origenes)}")
    print(f"Top 10 Aeropuertos con más salidas:")
    print(df['DEPARTING_AIRPORT'].value_counts().head(10).to_string())

    # --- 3. AEROPUERTOS DE LLEGADA (Destino) ---
    if col_destino:
        destinos = df[col_destino].unique()
        print(f"\n🔹 Total de Aeropuertos de Destino: {len(destinos)}")
        
        # --- 4. RUTAS ÚNICAS ---
        # Creamos una columna temporal de Ruta
        df['RUTA'] = df['DEPARTING_AIRPORT'].astype(str) + " -> " + df[col_destino].astype(str)
        total_rutas = df['RUTA'].nunique()
        print(f"\n🔹 Total de Rutas Únicas operadas: {total_rutas}")
        print("Top 10 Rutas más frecuentes:")
        print(df['RUTA'].value_counts().head(10).to_string())

        # --- 5. DETECCIÓN INTERNACIONAL (Simple) ---
        # Los aeropuertos de USA suelen ser códigos de 3 letras.
        # Vamos a ver si hay algo raro.
        print("\n🔎 Muestreo de códigos de destino (para ver si hay internacionales):")
        print(df[col_destino].unique()[:20]) # Muestra los primeros 20
    
    print("\n" + "="*40)

if __name__ == "__main__":
    auditar_rutas()