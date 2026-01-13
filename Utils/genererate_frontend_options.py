import json
import os

ARTIFACTS_DIR = 'artifacts'

# 1. DICCIONARIO MAESTRO DE AEROPUERTOS (IATA -> Nombre Modelo)
iata_mapping = {
    "ATL": "Atlanta Municipal",
    "ORD": "Chicago O'Hare International",
    "LAX": "Los Angeles International",
    "DFW": "Dallas Fort Worth Regional",
    "DEN": "Stapleton International", 
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
    "BWI": "Friendship International",
    "IAD": "Washington Dulles International",
    "DCA": "Ronald Reagan Washington National",
    "MDW": "Chicago Midway International",
    "SLC": "Salt Lake City International",
    "SAN": "San Diego International Lindbergh Fl",
    "TPA": "Tampa International",
    "PDX": "Portland International",
    "HNL": "Honolulu International",
    "HOU": "William P Hobby",
    "STL": "Lambert-St. Louis International",
    "BNA": "Nashville International",
    "AUS": "Austin - Bergstrom International",
    "OAK": "Metropolitan Oakland International",
    "MSY": "Louis Armstrong New Orleans International",
    "RDU": "Raleigh-Durham International",
    "MCI": "Kansas City International",
    "SJC": "San Jose International",
    "SMF": "Sacramento International",
    "SNA": "Orange County",
    "RSW": "Southwest Florida International",
    "HBU": "Houston Intercontinental", # A veces IAH
    "PIT": "Pittsburgh International",
    "SAT": "San Antonio International",
    "CVG": "Cincinnati/Northern Kentucky International",
    "MKE": "General Mitchell Field",
    "IND": "Indianapolis Muni/Weir Cook",
    "MEM": "Memphis International",
    "CLE": "Cleveland-Hopkins International",
    "BUF": "Greater Buffalo International",
    "BDL": "Bradley International",
    "PBI": "Palm Beach International",
    "JAX": "Jacksonville International"
}

# 2. DICCIONARIO MAESTRO DE AEROLÍNEAS (Nombre Modelo -> IATA)
# ¡Aquí agregué las que faltaban!
carrier_codes = {
    "American Airlines Inc.": "AA",
    "Delta Air Lines Inc.": "DL",
    "Southwest Airlines Co.": "WN",
    "United Air Lines Inc.": "UA",
    "JetBlue Airways": "B6",
    "Alaska Airlines Inc.": "AS",
    "Spirit Air Lines": "NK",
    "Frontier Airlines Inc.": "F9",
    "Hawaiian Airlines Inc.": "HA",
    "SkyWest Airlines Inc.": "OO",
    "Atlantic Southeast Airlines": "EV",
    "American Eagle Airlines Inc.": "MQ",
    "Comair Inc.": "OH",
    "Mesa Airlines Inc.": "YV",
    "Endeavor Air Inc.": "9E",
    "Midwest Airline, Inc.": "YX",
    "Allegiant Air": "G4",
    "Envoy Air": "MQ", # A veces aparece con este nombre moderno
    "ExpressJet": "EV" # A veces aparece así
}

def generar_opciones_frontend():
    print("🎨 Generando opciones inteligentes para el Frontend...")
    
    path_catalogs = f'{ARTIFACTS_DIR}/catalogs.json'
    if not os.path.exists(path_catalogs):
        print(f"❌ Error: No encuentro '{path_catalogs}'. Ejecuta primero los scripts de data science.")
        return

    with open(path_catalogs, 'r') as f:
        data = json.load(f)
        valid_airports = data['valid_airports']
        valid_carriers = data['valid_carriers']

    frontend_data = {
        "airports": [],
        "carriers": []
    }

    # --- 1. PROCESAR AEROPUERTOS ---
    name_to_iata = {v: k for k, v in iata_mapping.items()}

    for airport_name in valid_airports:
        code = name_to_iata.get(airport_name, "USA") # "USA" como genérico si no lo conocemos
        
        # Etiqueta para el humano
        if code != "USA":
            label = f"{code} - {airport_name}"
        else:
            label = f"USA - {airport_name}"
            
        frontend_data["airports"].append({
            "label": label,          # Lo que se ve: "ATL - Atlanta..."
            "value": airport_name,   # Lo que se envía: "Atlanta Municipal"
            "code": code,            # ¡NUEVO! Para que el backend no sufra
            "search_term": f"{code} {airport_name}"
        })

    # --- 2. PROCESAR AEROLÍNEAS ---
    for carrier_name in valid_carriers:
        code = carrier_codes.get(carrier_name, "XX")
        
        if code != "XX":
            label = f"{code} - {carrier_name}"
        else:
            label = carrier_name
            
        frontend_data["carriers"].append({
            "label": label,
            "value": carrier_name,
            "code": code  # ¡NUEVO!
        })

    # Guardar
    output_path = f'{ARTIFACTS_DIR}/frontend_options.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(frontend_data, f, indent=4)
        
    print(f"✅ Archivo '{output_path}' generado con éxito.")
    print(f"   -> {len(frontend_data['airports'])} Aeropuertos procesados.")
    print(f"   -> {len(frontend_data['carriers'])} Aerolíneas procesadas (Todas con código).")

if __name__ == "__main__":
    generar_opciones_frontend()