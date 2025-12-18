# ✈️ Flight Delay Prediction System

Este proyecto implementa un sistema de Machine Learning para predecir retrasos en vuelos comerciales (delays > 15 min).
Utiliza un **Random Forest** optimizado, exportado a formato **ONNX** para alta performance en inferencia, y servido mediante una API REST con **FastAPI**.

---

## 📂 Estructura del Proyecto

```text

├── artifacts/                  # [GENERADO] Aquí se guardan los modelos y mapas
│   ├── flight_delay_rf.onnx    # Modelo entrenado en formato ONNX
│   ├── *_risk_map.joblib       # Mapas para Target Encoding (Aeropuertos, Aerolíneas, etc.)
├── Data/
│   └── full_data_flightdelay.csv # Dataset original (Input)
├── train_export.py             # Script de entrenamiento y exportación
├── main.py                     # API para servir el modelo
├── requirements.txt            # Dependencias del proyecto
└── README.md                   # Documentación del proyecto
```

---

## 🛠️ Requisitos

### Crear el entorno

```bash
python -m venv .venv
```

#### Activarlo

Windows:

```bash
.\.venv\Scripts\activate
```

Instala las dependencias necesarias:

```bash
pip install -r requirements.txt
```

---

### Uso del Modelo

Cargar el JSON de ejemplo:

```json
    {
  "MONTH": 12,
  "DAY_OF_WEEK": 5,
  "DISTANCE_GROUP": 4,
  "SEGMENT_NUMBER": 6,
  "CONCURRENT_FLIGHTS": 75,
  "PRCP": 0.8,
  "TMAX": 32.0,
  "AWND": 15.5,
  "PLANE_AGE": 18,
  "AIRPORT_FLIGHTS_MONTH": 3500,
  "CARRIER_NAME": "AA",
  "DEPARTING_AIRPORT": "ORD",
  "DEP_TIME_BLK": "1800-1859"
}
```

---

Entrar en [http://127.0.0.1:8000/docs#/default/predict_delay_predict_post]
