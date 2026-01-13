from re import A
import joblib
import json

# Configuración
ARTIFACTS_PATH = 'artifacts/'

# Cargar el joblib
ops = joblib.load('artifacts/smart_ops_lookup.joblib')

# Convertir claves de tupla ('AA', 'JFK') a string "AA_JFK" para JSON
ops_json = {}
for key, val in ops.items():
    # key es ('CARRIER', 'AIRPORT')
    str_key = f"{key[0]}_{key[1]}" 
    ops_json[str_key] = val

with open(f'{ARTIFACTS_PATH}/smart_ops.json', 'w') as f:
    # Guardar como JSON
    json.dump(ops_json, f)

print("✅ smart_ops.json generado en artifacts/. Cópialo a src/main/resources en Java.")