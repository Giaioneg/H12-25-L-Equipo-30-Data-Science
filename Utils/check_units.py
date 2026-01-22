import pandas as pd

# Ajusta la ruta a tu CSV
csv_path = 'Data/full_data_flightdelay.csv'

try:
    # Leemos solo la columna TMAX para ir rápido
    df = pd.read_csv(csv_path, usecols=['TMAX'])
    
    max_temp = df['TMAX'].max()
    min_temp = df['TMAX'].min()
    mean_temp = df['TMAX'].mean()
    
    print(f"📊 Estadísticas de TMAX en el CSV original:")
    print(f"   -> Máxima: {max_temp}")
    print(f"   -> Mínima: {min_temp}")
    print(f"   -> Promedio: {mean_temp:.1f}")
    
    print("\n🕵️‍♂️ VEREDICTO:")
    if max_temp > 55:
        print("   🇺🇸 Es FAHRENHEIT (°F).")
        print("   (Porque en la Tierra rara vez hace más de 55°C, pero es normal 90°F)")
    else:
        print("   🌍 Es CELSIUS (°C).")

except Exception as e:
    print(f"❌ Error leyendo CSV: {e}")