import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Configuración
DATA_PATH = 'Data/full_data_flightdelay.csv'

def auditar_geografia():
    print("🌍 Iniciando Auditoría Geográfica...")
    
    # 1. Cargar datos clave
    cols = ['CARRIER_NAME', 'DEPARTING_AIRPORT', 'PREVIOUS_AIRPORT', 'LATITUDE', 'LONGITUDE']
    try:
        df = pd.read_csv(DATA_PATH, usecols=cols)
    except Exception as e:
        print(f"Error cargando: {e}")
        return

    # --- 1. ANÁLISIS DE AEROLÍNEAS ---
    print("\n" + "="*40)
    print("✈️ AEROLÍNEAS OPERANDO")
    print("="*40)
    carriers = df['CARRIER_NAME'].unique()
    print(f"Total: {len(carriers)}")
    print("Nombres:", sorted(carriers))
    
    # Check rápido de aerolíneas internacionales conocidas
    internacionales = ['IBERIA', 'LATAM', 'BRITISH', 'LUFTHANSA', 'EMIRATES', 'GOL', 'AZUL']
    encontradas = [c for c in carriers if any(i in c.upper() for i in internacionales)]
    
    if encontradas:
        print(f"⚠️ ¡OJO! Posibles internacionales detectadas: {encontradas}")
    else:
        print("ℹ️ Parece que todas son domésticas de EE.UU. (Southwest, Delta, American, etc.)")

    # --- 2. ANÁLISIS DE AEROPUERTOS (ORIGEN) ---
    print("\n" + "="*40)
    print("📍 AEROPUERTOS DE SALIDA (ORIGEN)")
    print("="*40)
    airports = df['DEPARTING_AIRPORT'].unique()
    print(f"Total Aeropuertos Únicos: {len(airports)}")
    print("Ejemplos (Top 10):")
    print(df['DEPARTING_AIRPORT'].value_counts().head(10).to_string())

    # --- 3. MAPA DE COORDENADAS (La prueba de fuego) ---
    print("\nGenerando mapa de cobertura...")
    plt.figure(figsize=(12, 6))
    
    # Pintamos los puntos
    plt.scatter(df['LONGITUDE'], df['LATITUDE'], alpha=0.1, s=1, c='blue')
    
    # Límites aproximados
    plt.title('Mapa de Cobertura de tus Datos')
    plt.xlabel('Longitud')
    plt.ylabel('Latitud')
    plt.grid(True)
    
    # Referencias visuales rápidas
    plt.text(-98, 39, 'EE.UU.', fontsize=20, color='red', ha='center')
    plt.text(-3, 40, 'ESPAÑA?', fontsize=12, color='green', ha='center') # Madrid aprox
    plt.text(-50, -15, 'BRASIL?', fontsize=12, color='green', ha='center') # Brasilia aprox
    
    # Ajustar vista para ver si hay algo fuera de USA
    # USA Continental está aprox entre Long -125 y -65, Lat 25 y 50
    plt.axvline(-65, color='black', linestyle='--') # Límite Este de USA
    plt.axvline(-125, color='black', linestyle='--') # Límite Oeste de USA
    
    print("ℹ️ Revisa la ventana del gráfico.")
    print("   - Si todos los puntos azules están cerca del texto 'EE.UU.', es dataset doméstico.")
    print("   - Si ves puntos cerca de las marcas de España o Brasil, ¡tienes datos internacionales!")
    
    plt.show()

if __name__ == "__main__":
    auditar_geografia()