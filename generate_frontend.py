import json
import os

ARTIFACTS_DIR = 'artifacts'

# --- 1. DICCIONARIOS DE TRADUCCIÓN (MAPEO MANUAL) ---
# Como el dataset original no trae los códigos, se los asignamos aquí.
# He incluido los más importantes de EE.UU. que suelen aparecer en estos datasets.

iata_airports = {
    "Atlanta Municipal": "ATL",
    "John F. Kennedy International": "JFK",
    "Los Angeles International": "LAX",
    "Chicago O'Hare International": "ORD",
    "Miami International": "MIA",
    "San Francisco International": "SFO",
    "Dallas Fort Worth Regional": "DFW",
    "Stapleton International": "DEN", # Nombre antiguo de Denver
    "Newark Liberty International": "EWR",
    "Orlando International": "MCO",
    "McCarran International": "LAS",
    "Logan International": "BOS",
    "Phoenix Sky Harbor International": "PHX",
    "Seattle International": "SEA",
    "Douglas Municipal": "CLT",
    "Detroit Metro Wayne County": "DTW",
    "Minneapolis-St Paul International": "MSP",
    "Philadelphia International": "PHL",
    "LaGuardia": "LGA",
    "Friendship International": "BWI", # Baltimore
    "Washington Dulles International": "IAD",
    "Ronald Reagan Washington National": "DCA",
    "Chicago Midway International": "MDW",
    "Salt Lake City International": "SLC",
    "San Diego International Lindbergh Fl": "SAN",
    "Tampa International": "TPA",
    "Portland International": "PDX",
    "Honolulu International": "HNL",
    "William P Hobby": "HOU",
    "Houston Intercontinental": "IAH"
}

iata_carriers = {
    "American Airlines Inc.": "AA",
    "Delta Air Lines Inc.": "DL",
    "Southwest Airlines Co.": "WN",
    "United Air Lines Inc.": "UA",
    "JetBlue Airways": "B6",
    "Alaska Airlines Inc.": "AS",
    "Spirit Air Lines": "NK",
    "Frontier Airlines Inc.": "F9",
    "Hawaiian Airlines Inc.": "HA",
    "SkyWest Airlines Inc.": "OO"
}

def generar_json_frontend():
    print("🎨 Generando 'frontend_options.json'...")

    # 1. Cargar el catálogo real del modelo (lo que el modelo SÍ conoce)
    try:
        with open(f'{ARTIFACTS_DIR}/catalogs.json', 'r', encoding='utf-8') as f:
            catalogs = json.load(f)
            valid_airports = catalogs['valid_airports']
            valid_carriers = catalogs['valid_carriers']
    except FileNotFoundError:
        print("❌ Error: No existe 'catalogs.json'. Ejecuta primero 'generate_full_intelligence.py'.")
        return

    frontend_data = {
        "airports": [],
        "carriers": []
    }

    # 2. Procesar Aeropuertos
    for name in valid_airports:
        # Buscamos el código. Si no está en mi lista manual, ponemos "USA" genérico
        code = iata_airports.get(name, "USA") 
        
        # Formato exacto que pide tu Frontend
        item = {
            "label": f"{code} - {name}",  # Lo que ve el usuario
            "value": name,                # Lo que se envía al modelo
            "code": code                  # Para que el buscador filtre por código
        }
        frontend_data["airports"].append(item)

    # 3. Procesar Aerolíneas
    for name in valid_carriers:
        code = iata_carriers.get(name, "")
        label = f"{code} - {name}" if code else name
        
        item = {
            "label": label,
            "value": name
        }
        frontend_data["carriers"].append(item)

    # 4. Guardar JSON
    output_path = f'{ARTIFACTS_DIR}/frontend_options.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(frontend_data, f, indent=4)

    print(f"✅ Archivo generado exitosamente: {output_path}")
    print("   Copia este archivo en tu proyecto web o haz que el HTML lo cargue.")

if __name__ == "__main__":
    generar_json_frontend()