import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Configuración visual
sns.set_theme(style="whitegrid")
DATA_PATH = 'Data/full_data_flightdelay.csv'
OUTPUT_DIR = 'eda_reports'

# Crear carpeta para guardar los gráficos
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

print("--- INICIANDO ANÁLISIS EXPLORATORIO (EDA) ---")

# 1. Cargar datos
print("1. Cargando datos...")
cols = [
    'MONTH', 'DAY_OF_WEEK', 'DEP_DEL15', 'DEP_TIME_BLK', 'DISTANCE_GROUP', 
    'SEGMENT_NUMBER', 'CONCURRENT_FLIGHTS', 'CARRIER_NAME', 'DEPARTING_AIRPORT', 
    'PRCP', 'TMAX', 'AWND', 'AIRPORT_FLIGHTS_MONTH', 'PLANE_AGE'
]
try:
    df = pd.read_csv(DATA_PATH, usecols=cols)
except FileNotFoundError:
    print(f"❌ Error: No encuentro el archivo {DATA_PATH}")
    exit()

# 2. Vistazo General
print("\n--- INFORMACIÓN BÁSICA ---")
print(f"Total de vuelos: {df.shape[0]}")
print(f"Total de columnas: {df.shape[1]}")
print("\nValores nulos (huecos en los datos):")
print(df.isnull().sum())

# 3. Análisis del Objetivo (¿Cuántos se retrasan?)
print("\n--- BALANCE DE RETRASOS ---")
conteo = df['DEP_DEL15'].value_counts(normalize=True) * 100
print(f"Vuelos a tiempo (0): {conteo[0]:.1f}%")
print(f"Vuelos retrasados (1): {conteo.get(1, 0):.1f}%")

# GRÁFICO 1: Pastel de Retrasos
plt.figure(figsize=(6, 6))
plt.pie(conteo, labels=['A Tiempo', 'Retrasado'], autopct='%1.1f%%', colors=['#4CAF50', '#FF5722'])
plt.title('Porcentaje de Vuelos Retrasados')
plt.savefig(f'{OUTPUT_DIR}/1_distribucion_retrasos.png')
print("✅ Gráfico 1 guardado: Distribución de retrasos")
plt.close()

# 4. Análisis por Aerolínea
# Calculamos el % de retrasos por cada aerolínea
risk_carrier = df.groupby('CARRIER_NAME')['DEP_DEL15'].mean().sort_values(ascending=False)

# GRÁFICO 2: Ranking de Aerolíneas
plt.figure(figsize=(10, 6))
sns.barplot(x=risk_carrier.values, y=risk_carrier.index, palette="viridis")
plt.title('Ranking: ¿Qué aerolíneas se retrasan más?')
plt.xlabel('% de Retrasos (Promedio)')
plt.savefig(f'{OUTPUT_DIR}/2_ranking_aerolineas.png')
print("✅ Gráfico 2 guardado: Ranking de aerolíneas")
plt.close()

# 5. Análisis del Clima y Tráfico
# Vamos a ver la correlación (qué variables suben juntas)
# Filtramos solo columnas numéricas para el mapa de calor
cols_num = ['DEP_DEL15', 'PRCP', 'TMAX', 'AWND', 'CONCURRENT_FLIGHTS', 'AIRPORT_FLIGHTS_MONTH']
corr = df[cols_num].corr()

# GRÁFICO 3: Mapa de Calor
plt.figure(figsize=(8, 6))
sns.heatmap(corr, annot=True, cmap='coolwarm', fmt=".2f")
plt.title('Mapa de Calor: ¿Qué afecta a los retrasos?')
plt.savefig(f'{OUTPUT_DIR}/3_correlaciones_clima.png')
print("✅ Gráfico 3 guardado: Correlaciones")
plt.close()

# 6. Análisis por Hora del Día
# Ordenamos los bloques horarios
df['DEP_TIME_BLK'] = sorted(df['DEP_TIME_BLK'])
risk_time = df.groupby('DEP_TIME_BLK')['DEP_DEL15'].mean()

# GRÁFICO 4: Retrasos por Hora
plt.figure(figsize=(12, 5))
risk_time.plot(kind='line', marker='o', color='purple')
plt.title('Evolución de Retrasos a lo largo del día')
plt.ylabel('% Probabilidad de Retraso')
plt.xticks(rotation=45)
plt.grid(True)
plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/4_retrasos_por_hora.png')
print("✅ Gráfico 4 guardado: Retrasos por hora")
plt.close()

print(f"\n✨ ¡Listo! Revisa la carpeta '{OUTPUT_DIR}' para ver tus gráficos.")