import joblib

# Cargar el archivo que acabas de generar
lookup = joblib.load('artifacts/smart_ops_lookup.joblib')

print("--- EJEMPLOS DE CLAVES VÁLIDAS ---")
# Mostrar las primeras 5 combinaciones (Aerolínea, Aeropuerto) que SI existen
for i, key in enumerate(lookup.keys()):
    print(f"Clave {i}: {key} -> Datos: {lookup[key]}")
    if i >= 4: break

print("\n--- BUSCANDO 'AMERICAN' ---")
# Buscar si existe algo parecido a "American" en las claves
nombres_aerolineas = set([k[0] for k in lookup.keys()])
for nombre in nombres_aerolineas:
    if "American" in nombre or "AA" in nombre:
        print(f"Nombre encontrado en dataset: '{nombre}'")