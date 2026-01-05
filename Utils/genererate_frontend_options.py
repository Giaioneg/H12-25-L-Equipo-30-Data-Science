import joblib
import json
import os
import pandas as pd

ARTIFACTS_DIR = 'artifacts'

# 1. Diccionario Manual: IATA -> Nombre en TU Dataset
# He mapeado los más importantes basándome en los nombres de tu CSV.
iata_mapping = {
    "ATL": "Atlanta Municipal",
    "ORD": "Chicago O'Hare International",
    "LAX": "Los Angeles International",
    "DFW": "Dallas Fort Worth Regional",
    "DEN": "Stapleton International", # Ojo: A veces Denver aparece así en datasets viejos
    "JFK": "John F. Kennedy International",
    "SFO": "San Francisco International",
    "CLT": "Douglas Municipal",
    "LAS": "McCarran International",
    "PHX": "Phoenix Sky Harbor International",
    "MIA": "Miami International",
    "MCO": "Orlando International",
    "EWR": "Newark Liberty International",
    "SEA": "Seattle International",
    "MSP": "Minneapolis-St Paul International",
    "DTW": "Detroit Metro Wayne County",
    "PHL": "Philadelphia International",
    "BOS": "Logan International",
    "LGA": "LaGuardia",
    "BWI": "Friendship International", # Nombre antiguo de Baltimore
    "IAD": "Washington Dulles International",
    "DCA": "Ronald Reagan Washington National",
    "MDW": "Chicago Midway International",
    "SLC": "Salt Lake City International",
    "SAN": "San Diego International Lindbergh Fl",
    "TPA": "Tampa International",
    "PDX": "Portland International",
    "HNL": "Honolulu International"
}

def generar_opciones_frontend():
    print("🎨 Generando opciones inteligentes para el Frontend...")
    
    # Cargar los aeropuertos reales que existen en el modelo (del script anterior)
    try:
        with open(f'{ARTIFACTS_DIR}/catalogs.json', 'r') as f:
            data = json.load(f)
            valid_airports = data['valid_airports']
            valid_carriers = data['valid_carriers']
    except:
        print("❌ Error: Ejecuta primero 'generate_full_intelligence.py' para tener catalogs.json")
        return

    frontend_data = {
        "airports": [],
        "carriers": []
    }

    # --- 1. PROCESAR AEROPUERTOS ---
    # Estrategia: "JFK - John F. Kennedy (New York)"
    
    # Invertimos el mapa para buscar fácil: Nombre -> IATA
    name_to_iata = {v: k for k, v in iata_mapping.items()}

    for airport_name in valid_airports:
        # Buscamos si tenemos el código IATA mapeado
        code = name_to_iata.get(airport_name, "???") # ??? si no es de los top 50
        
        # Creamos una etiqueta amigable para el usuario
        # Ejemplo: "ATL | Atlanta Municipal"
        if code != "???":
            label = f"{code} - {airport_name}"
        else:
            label = airport_name # Si no tenemos código, mostramos solo el nombre
            
        frontend_data["airports"].append({
            "label": label,          # LO QUE VE EL USUARIO ("JFK - John F. Kennedy")
            "value": airport_name,   # LO QUE SE ENVÍA AL BACKEND ("John F. Kennedy International")
            "search_term": f"{code} {airport_name}" # Texto oculto para el buscador
        })

    # --- 2. PROCESAR AEROLÍNEAS ---
    # Estrategia: "AA - American Airlines"
    # Mapeo rápido de aerolíneas comunes
    carrier_codes = {
        "American Airlines Inc.": "AA",
        "Delta Air Lines Inc.": "DL",
        "Southwest Airlines Co.": "WN",
        "United Air Lines Inc.": "UA",
        "JetBlue Airways": "B6",
        "Alaska Airlines Inc.": "AS",
        "Spirit Air Lines": "NK",
        "Frontier Airlines Inc.": "F9"
    }
    
    for carrier_name in valid_carriers:
        code = carrier_codes.get(carrier_name, "")
        if code:
            label = f"{code} - {carrier_name}"
        else:
            label = carrier_name
            
        frontend_data["carriers"].append({
            "label": label,
            "value": carrier_name
        })

    # Guardar archivo final
    with open(f'{ARTIFACTS_DIR}/frontend_options.json', 'w', encoding='utf-8') as f:
        json.dump(frontend_data, f, indent=4)
        
    print("✅ Archivo 'frontend_options.json' generado.")
    print("   -> Contiene etiquetas 'label' (para humanos) y 'value' (para el modelo).")

if __name__ == "__main__":
    generar_opciones_frontend()