import json
import difflib

# --- CONFIGURACIÓN ---
OLD_JSON = 'artifacts/frontend_options.json'       # El que tiene los códigos (B6, JFK)
REAL_JSON = 'artifacts/frontend_options_REAL.json' # El que tiene los nombres correctos para el modelo
OUTPUT_JSON = 'artifacts/frontend_options_FINAL.json'

def cargar_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def buscar_codigo(nombre_real, lista_antigua):
    """
    Intenta encontrar el código IATA buscando similitudes entre el nombre real
    y los nombres del archivo antiguo.
    """
    nombre_real_norm = nombre_real.lower()
    
    for item in lista_antigua:
        nombre_viejo = item['value'].lower()
        codigo = item.get('code', '')
        
        if not codigo: continue

        # 1. Coincidencia exacta
        if nombre_real_norm == nombre_viejo:
            return codigo
            
        # 2. Contención (ej: "JetBlue" está en "JetBlue Airways")
        if nombre_viejo in nombre_real_norm or nombre_real_norm in nombre_viejo:
            return codigo
            
    return None

def mezclar_listas(lista_real, lista_antigua, tipo):
    print(f"🔄 Procesando {tipo}...")
    lista_final = []
    
    count_con_codigo = 0
    
    for item_real in lista_real:
        nombre_real = item_real['value']
        
        # Buscamos si este nombre tiene un código en el archivo viejo
        codigo = buscar_codigo(nombre_real, lista_antigua)
        
        if codigo:
            # ¡BINGO! Tenemos código + nombre real
            lista_final.append({
                "label": f"{codigo} - {nombre_real}", # Para que se vea bonito
                "value": nombre_real,                 # EL IMPORTANTE (Para el modelo)
                "code": codigo                        # Para buscar por código
            })
            count_con_codigo += 1
        else:
            # Si no encontramos código, dejamos solo el nombre
            print(f"   ⚠️ Sin código para: {nombre_real}")
            lista_final.append({
                "label": nombre_real,
                "value": nombre_real,
                "code": "" 
            })
            
    # Ordenamos para que se vea bien
    lista_final.sort(key=lambda x: x['label'])
    print(f"   ✅ {count_con_codigo}/{len(lista_real)} recuperaron su código.")
    return lista_final

def main():
    print("🚀 Iniciando mezcla de JSONs...")
    
    try:
        data_old = cargar_json(OLD_JSON)
        data_real = cargar_json(REAL_JSON)
    except FileNotFoundError:
        print("❌ Error: Asegúrate de tener 'frontend_options.json' y 'frontend_options_REAL.json' en la carpeta.")
        return

    final_data = {
        "carriers": mezclar_listas(data_real['carriers'], data_old['carriers'], "Aerolíneas"),
        "airports": mezclar_listas(data_real['airports'], data_old['airports'], "Aeropuertos")
    }

    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(final_data, f, indent=4, ensure_ascii=False)

    print(f"\n✨ ¡HECHO! Archivo generado: {OUTPUT_JSON}")
    print("👉 Este archivo tiene:\n   1. Códigos visuales (JFK)\n   2. Nombres técnicos correctos para el modelo.")

if __name__ == "__main__":
    main()