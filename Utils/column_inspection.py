import pandas as pd

DATA_PATH = 'Data/full_data_flightdelay.csv'

print("🔍 INSPECCIONANDO COLUMNAS REALES DEL ARCHIVO...")

# Leemos solo la primera fila, sin filtros, para ver la realidad cruda
# Usamos el motor de python que es más flexible para detectar el separador
try:
    df_raw = pd.read_csv(DATA_PATH, nrows=0, sep=None, engine='python')
    cols_reales = list(df_raw.columns)

    print(f"\nEl archivo tiene {len(cols_reales)} columnas.")
    print("Aquí están EXACTAMENTE como las ve Pandas (fíjate en los espacios dentro de las comillas):")
    print("-" * 60)
    print(cols_reales)
    print("-" * 60)

    # Verificación automática de tus columnas nuevas
    mis_columnas_nuevas = [
        'SNOW', 'SNWD', 'NUMBER_OF_SEATS', 
        'FLT_ATTENDANTS_PER_PASS', 'GROUND_SERV_PER_PASS', 'PREVIOUS_AIRPORT'
    ]
    
    print("\nVerificando tus columnas nuevas una por una:")
    for col in mis_columnas_nuevas:
        if col in cols_reales:
            print(f"✅ {col}: Encontrada")
        else:
            # Buscamos si existe algo parecido (con espacios)
            parecido = [c for c in cols_reales if col in c]
            if parecido:
                print(f"❌ {col}: NO EXACTA. ¿Quizás quisiste decir '{parecido[0]}'?")
            else:
                print(f"❌ {col}: NO EXISTE en absoluto.")

except Exception as e:
    print(f"Error leyendo el archivo: {e}")