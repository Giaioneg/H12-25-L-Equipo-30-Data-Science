import pandas as pd
import json
import os

# --- CONFIGURACIÓN ---
CSV_PATH = 'Data/full_data_flightdelay.csv'  
ARTIFACTS_DIR = 'artifacts'
OUTPUT_FILE = 'frontend_options.json'

# --- 1. DICCIONARIO MAESTRO DE AEROLÍNEAS (Nombre en CSV -> Código IATA) ---
CARRIER_MAPPING = {
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
    "Atlantic Southeast Airlines": "EV", # Código IATA histórico para ASA
    "American Eagle Airlines Inc.": "MQ",
    "Comair Inc.": "OH",
    "Mesa Airlines Inc.": "YV",
    "Endeavor Air Inc.": "9E",
    "Midwest Airline, Inc.": "YX", 
    "Allegiant Air": "G4"
}

# --- 2. DICCIONARIO MAESTRO DE AEROPUERTOS (IATA -> Nombre en CSV) ---
# Mapeo inverso para detectar códigos. 
# Si el nombre del CSV contiene "Atlanta", le asignamos "ATL".
IATA_AIRPORTS = {
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
    "HBU": "Houston Intercontinental",
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
    "JAX": "Jacksonville International",
    "LIT": "Adams Field",
    "ALB": "Albany International",
    "ABQ": "Albuquerque International Sunport",
    "ANC": "Anchorage International",
    "BHM": "Birmingham Airport",
    "BOI": "Boise Air Terminal",
    "CHS": "Charleston International",
    "DSM": "Des Moines Municipal",
    "ELP": "El Paso International",
    "OMA": "Eppley Airfield",
    "FLL": "Fort Lauderdale-Hollywood International", # ¡Importante!
    "GRR": "Kent County",
    "OGG": "Kahului Airport",
    "KOA": "Keahole",
    "LIH": "Lihue Airport",
    "LGB": "Long Beach Daugherty Field", # A veces LGB
    "MSY": "Louis Armstrong New Orleans International",
    "TYS": "McGhee Tyson",
    "MYR": "Myrtle Beach International",
    "ORF": "Norfolk International",
    "XNA": "Northwest Arkansas Regional",
    "ONT": "Ontario International",
    "PVD": "Theodore Francis Green State", # Providence
    "RNO": "Reno/Tahoe International",
    "RIC": "Richmond International",
    "ROC": "Rochester Monroe County",
    "GEG": "Spokane International",
    "SYR": "Syracuse Hancock International",
    "TUS": "Tucson International",
    "TUL": "Tulsa International",
    "OKC": "Will Rogers World",
    "SDF": "Standiford Field", # Louisville
    "SFB": "Sanford NAS",
    "DAL": "Dallas Love Field",
    "GSP": "Greenville-Spartanburg",
    "BUR": "Hollywood-Burbank Midpoint",
    "DAY": "James M Cox/Dayton International",
    "PSP": "Palm Springs International",
    "PNS": "Pensacola Regional",
    "GSO": "Piedmont Triad International",
    "CMH": "Port Columbus International",
    "PWM": "Portland International Jetport",
    "SJU": "Puerto Rico International",
    "SAV": "Savannah/Hilton Head International",
    "MSN": "Truax Field"
}

def generate_from_csv():
    print(f"📂 Leyendo CSV desde: {CSV_PATH} ...")
    
    if not os.path.exists(CSV_PATH):
        print(f"❌ Error: No encuentro el archivo {CSV_PATH}.")
        print("   -> Por favor, edita la variable CSV_PATH en el script.")
        return

    # Leemos solo las columnas necesarias para hacerlo rápido
    try:
        df = pd.read_csv(CSV_PATH, usecols=['CARRIER_NAME', 'DEPARTING_AIRPORT'])
    except ValueError:
        print("⚠️ Advertencia: Las columnas 'CARRIER_NAME' o 'DEPARTING_AIRPORT' no están en el CSV.")
        print("   -> Intentando leer todo el CSV para ver qué columnas hay...")
        df = pd.read_csv(CSV_PATH, nrows=5)
        print(f"   -> Columnas encontradas: {list(df.columns)}")
        return

    # Obtener únicos
    unique_carriers = sorted(df['CARRIER_NAME'].unique().astype(str))
    unique_airports = sorted(df['DEPARTING_AIRPORT'].unique().astype(str))

    print(f"📊 Datos encontrados en CSV: {len(unique_carriers)} Aerolíneas, {len(unique_airports)} Aeropuertos.")

    frontend_data = {
        "airports": [],
        "carriers": []
    }

    # --- PROCESAR AEROLÍNEAS ---
    print("\n--- ✈️ REPORTE DE AEROLÍNEAS ---")
    mapped_count = 0
    for carrier in unique_carriers:
        code = CARRIER_MAPPING.get(carrier, "XX")
        
        status = "✅" if code != "XX" else "⚠️ SIN CÓDIGO"
        print(f"{status} {carrier} -> {code}")

        if code != "XX":
            label = f"{code} - {carrier}"
            mapped_count += 1
        else:
            label = carrier

        frontend_data["carriers"].append({
            "label": label,
            "value": carrier,
            "code": code
        })
    
    print(f"   -> Total mapeadas correctamente: {mapped_count}/{len(unique_carriers)}")

    # --- PROCESAR AEROPUERTOS ---
    # Invertimos diccionario para búsqueda rápida: Nombre -> Código
    name_to_iata = {v: k for k, v in IATA_AIRPORTS.items()}

    print("\n--- 🌍 REPORTE DE AEROPUERTOS (Muestra) ---")
    mapped_air_count = 0
    for airport in unique_airports:
        code = name_to_iata.get(airport, "USA") # USA = Genérico
        
        if code != "USA":
            label = f"{code} - {airport}"
            mapped_air_count += 1
        else:
            label = f"USA - {airport}"

        frontend_data["airports"].append({
            "label": label,
            "value": airport,
            "code": code,
            "search_term": f"{code} {airport}"
        })
    
    print(f"   -> Total aeropuertos con IATA detectado: {mapped_air_count}/{len(unique_airports)}")
    if mapped_air_count < len(unique_airports):
        print("   -> Nota: Los aeropuertos marcados como 'USA' son válidos, solo que no tienen código IATA en nuestro diccionario manual.")

    # --- GUARDAR JSON ---
    os.makedirs(ARTIFACTS_DIR, exist_ok=True)
    out_path = os.path.join(ARTIFACTS_DIR, OUTPUT_FILE)
    
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(frontend_data, f, indent=4)

    print(f"\n💾 Archivo generado: {out_path}")
    print("🚀 ¡Sube este archivo a tu servidor (artifacts/) y a tu Frontend (public/assets/)!")

if __name__ == "__main__":
    generate_from_csv()