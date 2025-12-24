import streamlit as st
import requests
import json

# Configuración de la página
st.set_page_config(page_title="Flight Delay Predictor", page_icon="✈️")

st.title("✈️ ¿Se retrasará mi vuelo?")
st.write("Herramienta de predicción para el Hackathon.")

# Formulario de entrada (Simplificado para la demo)
col1, col2 = st.columns(2)

with col1:
    carrier = st.selectbox("Aerolínea", ["AA", "DL", "UA", "WN"])
    origin = st.text_input("Aeropuerto Origen (Código IATA)", "JFK")
    month = st.slider("Mes", 1, 12, 12)
    day_week = st.slider("Día de la semana (1=Lun)", 1, 7, 5)

with col2:
    dep_time = st.selectbox("Bloque Horario", ["0600-0659", "1000-1059", "1400-1459", "1800-1859"])
    distance = st.number_input("Grupo de Distancia (1-11)", 1, 11, 4)
    # Valores por defecto para el resto (promedios) para no aburrir al usuario
    prcp = st.number_input("Precipitación (pulgadas)", 0.0, 5.0, 0.0)

# Botón de predicción
if st.button("Predecir Retraso"):
    # Construir el JSON completo (rellenando datos faltantes con promedios)
    payload = {
        "MONTH": month,
        "DAY_OF_WEEK": day_week,
        "DISTANCE_GROUP": distance,
        "SEGMENT_NUMBER": 3,
        "CONCURRENT_FLIGHTS": 50,
        "PRCP": prcp,
        "TMAX": 25.0,
        "AWND": 10.0,
        "PLANE_AGE": 10,
        "AIRPORT_FLIGHTS_MONTH": 2000,
        "CARRIER_NAME": carrier,
        "DEPARTING_AIRPORT": origin,
        "DEP_TIME_BLK": dep_time
    }

    try:
        # Llamar a tu propia API (asegúrate que main.py esté corriendo)
        response = requests.post("http://localhost:8000/predict", json=payload)
        
        if response.status_code == 200:
            result = response.json()
            prob = result['probability'] * 100
            
            if result['is_delayed']:
                st.error(f"🚨 ALTA PROBABILIDAD DE RETRASO: {prob:.1f}%")
            else:
                st.success(f"✅ VUELO A TIEMPO: Probabilidad de retraso solo del {prob:.1f}%")
        else:
            st.error("Error en la API")
    except Exception as e:
        st.error(f"No se pudo conectar con la API: {e}")        