import os
import pandas as pd
import numpy as np
import joblib
import zipfile
import xgboost as xgb
from sklearn.model_selection import train_test_split, RandomizedSearchCV
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score, roc_auc_score
from scipy.stats import uniform, randint
import gc

# --- CONFIGURACIÓN ---
DATA_ZIP_PATH = 'Data/full_data_flightdelay.csv.zip'
DATA_CSV_PATH = 'Data/full_data_flightdelay.csv'
ARTIFACTS_DIR = 'artifacts'
os.makedirs(ARTIFACTS_DIR, exist_ok=True)

print("--- INICIANDO ENTRENAMIENTO MEJORADO (XGBoost) ---")

# 1. DESCOMPRIMIR Y CARGAR DATOS
if not os.path.exists(DATA_CSV_PATH):
    print("Descomprimiendo datos...")
    with zipfile.ZipFile(DATA_ZIP_PATH, 'r') as zip_ref:
        zip_ref.extractall('Data')

print("Cargando datos (Sampled for MVP to avoid OOM)...")
cols = [
    'MONTH', 'DAY_OF_WEEK', 'DEP_DEL15', 'DEP_TIME_BLK', 'DISTANCE_GROUP',
    'SEGMENT_NUMBER', 'CONCURRENT_FLIGHTS', 'CARRIER_NAME', 'DEPARTING_AIRPORT',
    'PRCP', 'TMAX', 'AWND', 'SNOW', 'SNWD', 'AIRPORT_FLIGHTS_MONTH', 'PLANE_AGE'
]

# Leemos el CSV
# Use a smaller sample to fit in memory
df = pd.read_csv(DATA_CSV_PATH, usecols=cols)
df = df.dropna(subset=['DEP_DEL15']).fillna(0)

# Sample 10% of the data to avoid OOM in sandbox (Simulating limited resource environment mentioned in prompt)
# "Se recomienda dejar el modelo ligero y el alcance controlado, para no sobrepasar los límites de always free de OCI."
df = df.sample(frac=0.1, random_state=42)

# 2. FEATURE ENGINEERING
print("Generando features...")

# 2.1 Cyclic Encoding para variables temporales
# Mes (1-12)
df['MONTH_SIN'] = np.sin(2 * np.pi * df['MONTH'] / 12)
df['MONTH_COS'] = np.cos(2 * np.pi * df['MONTH'] / 12)

# Día de la semana (1-7)
df['DAY_SIN'] = np.sin(2 * np.pi * df['DAY_OF_WEEK'] / 7)
df['DAY_COS'] = np.cos(2 * np.pi * df['DAY_OF_WEEK'] / 7)

# 3. DIVISIÓN DE DATOS (Train/Test)
X = df.drop(columns=['DEP_DEL15'])
y = df['DEP_DEL15']

del df
gc.collect()

# Stratified split para mantener la proporción de retrasos
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

print(f"Train size: {X_train.shape}, Test size: {X_test.shape}")

# 4. TARGET ENCODING (Seguro: Fit en Train, Transform en Train/Test)
print("Aplicando Target Encoding...")
cat_cols = ['CARRIER_NAME', 'DEPARTING_AIRPORT', 'DEP_TIME_BLK']

# Guardamos la media global para casos desconocidos
global_mean = y_train.mean()
joblib.dump(global_mean, f'{ARTIFACTS_DIR}/global_mean_improved.joblib')

# DataFrame temporal para calcular promedios
train_temp = X_train.copy()
train_temp['TARGET'] = y_train

for col in cat_cols:
    # Calcular mapa de riesgo
    risk_map = train_temp.groupby(col)['TARGET'].mean().to_dict()

    # Guardar mapa
    joblib.dump(risk_map, f'{ARTIFACTS_DIR}/{col}_risk_map_improved.joblib')

    # Aplicar mapeo
    X_train.loc[:, col + '_RISK'] = X_train[col].map(risk_map).fillna(global_mean)
    X_test.loc[:, col + '_RISK'] = X_test[col].map(risk_map).fillna(global_mean)

del train_temp
gc.collect()

# Selección final de features
features_finales = [
    'MONTH_SIN', 'MONTH_COS', 'DAY_SIN', 'DAY_COS',
    'DISTANCE_GROUP', 'SEGMENT_NUMBER', 'CONCURRENT_FLIGHTS',
    'PRCP', 'TMAX', 'AWND', 'SNOW', 'SNWD', 'PLANE_AGE',
    'AIRPORT_FLIGHTS_MONTH', 'CARRIER_NAME_RISK',
    'DEPARTING_AIRPORT_RISK', 'DEP_TIME_BLK_RISK'
]

X_train_final = X_train[features_finales]
X_test_final = X_test[features_finales]

del X_train, X_test
gc.collect()

# 5. MODELADO CON XGBOOST
print("Entrenando modelo XGBoost...")

# Configuración básica de XGBoost
# scale_pos_weight ayuda con el desbalance (aprox. ratio neg/pos)
ratio = float(np.sum(y_train == 0)) / np.sum(y_train == 1)
clf = xgb.XGBClassifier(
    objective='binary:logistic',
    n_jobs=1,
    random_state=42,
    scale_pos_weight=ratio,
    eval_metric='logloss'
)

# Búsqueda de hiperparámetros
param_dist = {
    'n_estimators': randint(50, 150),
    'max_depth': randint(3, 8),
    'learning_rate': uniform(0.01, 0.2),
    'subsample': uniform(0.6, 0.4),
    'colsample_bytree': uniform(0.6, 0.4)
}

# Randomized Search
search = RandomizedSearchCV(
    clf,
    param_distributions=param_dist,
    n_iter=2,
    scoring='f1',
    cv=2,
    verbose=1,
    n_jobs=1, # Reduce parallelism to save memory
    random_state=42
)

search.fit(X_train_final, y_train)

best_model = search.best_estimator_
print(f"Mejores parámetros: {search.best_params_}")

# 6. EVALUACIÓN
print("\n--- RESULTADOS DEL MEJOR MODELO ---")
y_pred = best_model.predict(X_test_final)
y_prob = best_model.predict_proba(X_test_final)[:, 1]

acc = accuracy_score(y_test, y_pred)
f1 = f1_score(y_test, y_pred)
roc_auc = roc_auc_score(y_test, y_prob)

print(f"Accuracy: {acc:.4f}")
print(f"F1-Score: {f1:.4f}")
print(f"ROC-AUC:  {roc_auc:.4f}")
print("\nReporte de Clasificación:")
print(classification_report(y_test, y_pred))

# 7. EXPORTACIÓN
print("\nGuardando modelo...")
joblib.dump(best_model, f'{ARTIFACTS_DIR}/flight_delay_xgb.joblib')

print(f"✅ Modelo guardado en: {ARTIFACTS_DIR}/flight_delay_xgb.joblib")
