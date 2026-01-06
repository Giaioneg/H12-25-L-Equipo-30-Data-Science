# ✈️ FlightOnTime - Sistema de Predicción de Retrasos en Vuelos

## 📋 Tabla de Contenidos

- [Descripción General](#-descripción-general)
- [Objetivo del Proyecto](#-objetivo-del-proyecto)
- [Métricas de Rendimiento](#-métricas-de-rendimiento)
- - [Arquitectura del Sistema](#arquitectura-del-sistema-%EF%B8%8F)
- [Flujo de Predicción](#flujo-de-predicción)
- [Dataset y Preparación](#-dataset-y-preparación)
- [Fuente de Datos](#fuente-de-datos)
- [Variables Originales Utilizadas](#variables-originales-utilizadas)
- [Preprocesamiento Aplicado](#preprocesamiento-aplicado)
- [Modelo de Machine Learning](#-modelo-de-machine-learning)
- [Algoritmo: Random Forest Classifier](#algoritmo-random-forest-classifier)
- [Hiperparámetros Optimizados](#hiperparámetros-optimizados)
- [Manejo del Desbalance de Clases](#manejo-del-desbalance-de-clases)
- [Formato de Exportación: ONNX](#formato-de-exportación-onnx)
- [Importancia de Variables (Top 10)](#importancia-de-variables-top-10)
- [API REST (Backend)](#-api-rest-backend)
- [Tecnología: FastAPI](#tecnología-fastapi)
- [Estructura del Request](#estructura-del-request)
- [Estructura de la Respuesta](#estructura-de-la-respuesta)
- [Lógica de Inferencia del Clima](#lógica-de-inferencia-del-clima)
- [Manejo de Errores](#manejo-de-errores)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Archivos Críticos para Producción](#archivos-críticos-para-producción)
- [Instalación y Configuración](#instalación-y-configuración)
- [Uso del Sistema](#-uso-del-sistema)
- [Endpoints de la API](#-endpoints-de-la-api)
- [Integración con Frontend](#-integración-con-frontend)
- [CORS y seguridad](#cors-y-seguridad)
- [Troubleshooting](#-troubleshooting)

---

---

## 📖 Descripción General

**FlightOnTime** es un sistema de predicción de retrasos en vuelos comerciales desarrollado para el mercado estadounidense. Utiliza Machine Learning (Random Forest optimizado) para predecir si un vuelo se retrasará más de 15 minutos basándose en:

- Datos históricos de vuelos
- Información operativa de aerolíneas
- Condiciones meteorológicas (integración con API externa)
- Patrones de tráfico aeroportuario

### 🎯 Objetivo del Proyecto

Proporcionar a pasajeros y operadores aeroportuarios una herramienta de predicción confiable que permita:

- Tomar decisiones informadas sobre viajes
- Optimizar recursos operativos
- Mejorar la experiencia del pasajero

### 📊 Métricas de Rendimiento

- **Accuracy General**: 76.77%
- **Recall (Detección de Retrasos)**: 42% (clase minoritaria)
- **Precision (Evitar Falsas Alarmas)**: 86% (clase mayoritaria)
- **Umbral Óptimo**: 0.68 (calibrado para balance)

---

## Arquitectura del Sistema 🏗️

```text
┌─────────────────┐
│   FRONTEND      │  (HTML + JavaScript)
│   (Usuario)     │  
└────────┬────────┘
         │ HTTP POST /predict
         ▼
┌─────────────────┐
│   FASTAPI       │  (main.py - Puerto 8000)
│   Middleware    │  • Validación de Datos
│                 │  • CORS Habilitado
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌─────────┐ ┌──────────────┐
│ ONNX    │ │ ARTEFACTOS   │
│ MODELO  │ │ (Joblib)     │
│ (Infr.) │ │ • Risk Maps  │
│         │ │ • Lookups    │
└─────────┘ └──────────────┘
    │
    ▼
┌─────────────────┐
│ Open-Meteo API  │  (Clima en Tiempo Real)
└─────────────────┘
```

### Flujo de Predicción

1. **Usuario** ingresa: Aerolínea, Aeropuerto, Fecha, Hora
2. **Frontend** valida y envía JSON al Backend
3. **Backend (FastAPI)**:
   - Normaliza la fecha (extrae mes, día de semana)
   - Consulta clima en tiempo real (si disponible)
   - Busca datos operativos en Smart Lookups
   - Traduce categorías a riesgos numéricos (Target Encoding)
4. **Modelo ONNX** procesa el vector de 19 características
5. **Respuesta** incluye:
   - Predicción: "PUNTUAL" o "RETRASADO"
   - Probabilidad: 0.0 - 1.0
   - Detalles: Fuente del clima, riesgo de la ruta

---

## 📊 Dataset y Preparación

### Fuente de Datos

**Dataset Oficial**: [2019 Airline Delays and Cancellations (Kaggle)](https://www.kaggle.com/datasets/threnjen/2019-airline-delays-and-cancellations)

**Características del Dataset**:

- **Registros**: 6,489,062 vuelos
- **Período**: Año 2019 (datos pre-pandemia)
- **Alcance Geográfico**: Estados Unidos continental
- **Aerolíneas**: 17 operadores principales
- **Aeropuertos**: 96 hubs principales

### Variables Originales Utilizadas

| Variable | Descripción | Tipo |
| --- | --- | --- |
| `DEP_DEL15` | Retraso >15 min (Target) | Binario (0/1) |
| `CARRIER_NAME` | Nombre de la aerolínea | Categórico |
| `DEPARTING_AIRPORT` | Aeropuerto de origen | Categórico |
| `MONTH` | Mes del año | Numérico (1-12) |
| `DAY_OF_WEEK` | Día de la semana | Numérico (1-7) |
| `DEP_TIME_BLK` | Bloque horario | Categórico |
| `DISTANCE_GROUP` | Grupo de distancia | Numérico (1-11) |
| `PRCP` | Precipitación (pulgadas) | Numérico |
| `TMAX` | Temperatura máxima (°F) | Numérico |
| `AWND` | Velocidad del viento (mph) | Numérico |
| `SNOW` | Nieve (pulgadas) | Numérico |
| `PLANE_AGE` | Edad del avión (años) | Numérico |
| `NUMBER_OF_SEATS` | Capacidad del avión | Numérico |
| `CONCURRENT_FLIGHTS` | Tráfico simultáneo | Numérico |

### Preprocesamiento Aplicado

#### 1. **Limpieza de Datos**

```python
# Eliminación de valores nulos en el target
df = df.dropna(subset=['DEP_DEL15'])

# Imputación de valores faltantes (meteorológicos)
df = df.fillna(0)
```

#### 2. **Target Encoding (Clave Anti-Leakage)**

**Problema**: Las variables categóricas (aerolínea, aeropuerto) tienen alta cardinalidad.

**Solución**: Codificación basada en el riesgo histórico de retrasos:

```python
# CRÍTICO: Calculamos el riesgo SOLO en datos de entrenamiento
train_temp = X_train.copy()
train_temp['DEP_DEL15'] = y_train

# Mapa de riesgo por aerolínea
risk_map = train_temp.groupby('CARRIER_NAME')['DEP_DEL15'].mean().to_dict()

# Aplicamos el mapa a Train Y Test
X_train['CARRIER_NAME_RISK'] = X_train['CARRIER_NAME'].map(risk_map).fillna(global_mean)
X_test['CARRIER_NAME_RISK'] = X_test['CARRIER_NAME'].map(risk_map).fillna(global_mean)
```

**Ventaja**: El modelo aprende que "Aerolínea X en Aeropuerto Y" tiene un riesgo histórico del 28%, sin necesidad de One-Hot Encoding.

#### 3. **Gestión de Variables Nuevas (Smart Lookups)**

Para datos de producción donde no conocemos detalles del avión:

```python
# Lookup: "Si vuelo con AA desde JFK, ¿qué avión usan típicamente?"
smart_ops_lookup = df.groupby(['CARRIER_NAME', 'DEPARTING_AIRPORT'])[
    ['NUMBER_OF_SEATS', 'PLANE_AGE', 'FLT_ATTENDANTS_PER_PASS']
].median().to_dict('index')
```

**Guardado**: `artifacts/smart_ops_lookup.joblib`

---

## 🤖 Modelo de Machine Learning

### Algoritmo: Random Forest Classifier

**Justificación de Elección**:

- ✅ Maneja relaciones no lineales (clima vs retrasos)
- ✅ Robusto ante valores atípicos
- ✅ Proporciona importancia de variables (explicabilidad)
- ✅ No requiere escalado de features

### Hiperparámetros Optimizados

```python
RandomForestClassifier(
    n_estimators=100,        # 100 árboles (balance velocidad/precisión)
    max_depth=14,            # Profundidad limitada (evita overfitting)
    min_samples_leaf=15,     # Mínimo 15 muestras por hoja
    class_weight={0: 1, 1: 3},  # Peso 3x a retrasos (clase minoritaria)
    random_state=42,         # Reproducibilidad
    n_jobs=-1                # Paralelización
)
```

### Manejo del Desbalance de Clases

**Problema**: Solo el 19% de vuelos se retrasan (desbalance 81/19).

**Solución Implementada**:

```python
class_weight={0: 1, 1: 3}  # Penalización 3x por retraso no detectado
```

**Impacto**:

- Sin peso: Recall 25% (pierde 75% de retrasos)
- Con peso 3x: Recall 42% (mejora +68%)

### Formato de Exportación: ONNX

**¿Por qué ONNX?**

- Inferencia 3-5x más rápida que Joblib
- Independiente de la versión de scikit-learn
- Compatible con backends Java/C++ (futuras migraciones)

**Conversión**:

```python
from skl2onnx import convert_sklearn
from skl2onnx.common.data_types import FloatTensorType

initial_type = [('float_input', FloatTensorType([None, 19]))]
onnx_model = convert_sklearn(model, initial_types=initial_type)

with open('artifacts/flight_delay_rf_weighted.onnx', 'wb') as f:
    f.write(onnx_model.SerializeToString())
```

### Importancia de Variables (Top 10)

```text
1. DEPARTING_AIRPORT_RISK  - 18.2%  (Riesgo del aeropuerto)
2. CARRIER_NAME_RISK       - 15.7%  (Historial de la aerolínea)
3. DEP_TIME_BLK_RISK       - 12.4%  (Hora del día)
4. CONCURRENT_FLIGHTS      - 9.8%   (Congestión)
5. AWND                    - 8.1%   (Viento)
6. PRCP                    - 7.3%   (Lluvia)
7. SNOW                    - 6.5%   (Nieve)
8. MONTH                   - 5.9%   (Estacionalidad)
9. PLANE_AGE               - 5.2%   (Edad del avión)
10. NUMBER_OF_SEATS        - 4.8%   (Tamaño del avión)
```

**Insight Clave**: El 46% de la predicción depende de **dónde** y **con quién** vuelas.

---

## 🔌 API REST (Backend)

### Tecnología: FastAPI

**Stack Técnico**:

- **Framework**: FastAPI 0.104+
- **Servidor ASGI**: Uvicorn
- **Runtime de Modelo**: ONNX Runtime
- **Validación**: Pydantic v2

### Estructura del Request

```json
{
  "CARRIER_NAME": "American Airlines Inc.",
  "DEPARTING_AIRPORT": "John F. Kennedy International",
  "FECHA": "2026-01-15",
  "HORA": "14:30",
  "PRCP": null,     // Opcional: Forzar clima manual
  "SNOW": null,     // Opcional
  "AWND": null      // Opcional
}
```

**Validación Automática** (Pydantic):

```python
class FlightRequest(BaseModel):
    CARRIER_NAME: str
    DEPARTING_AIRPORT: str
    FECHA: str  # Formato YYYY-MM-DD
    HORA: str   # Formato HH:MM
    PRCP: float | None = None
    SNOW: float | None = None
    AWND: float | None = None
```

### Estructura de la Respuesta

```json
{
  "prediction": "RETRASADO",
  "probability": 0.73,
  "details": "Clima: Tiempo Real (Open-Meteo) | Riesgo Ruta: 0.24",
  "weather_used": {
    "rain": 0.45,
    "wind": 18.2
  }
}
```

### Lógica de Inferencia del Clima

```python
def get_live_weather(airport_name, flight_date_str):
    # 1. Buscar coordenadas del aeropuerto
    coords = airport_coords.get(airport_name)
    if not coords:
        return None  # Fallback a datos históricos
    
    # 2. Validar que la fecha esté dentro de 7 días (límite de Open-Meteo)
    flight_date = datetime.strptime(flight_date_str, "%Y-%m-%d")
    delta = (flight_date - datetime.now()).days
    if delta < 0 or delta > 7:
        return None
    
    # 3. Llamada a la API
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
    res = requests.get(url, verify=False)  # IMPORTANTE: verify=False si hay firewall corporativo
    
    # 4. Conversión de unidades (Métrico -> Imperial)
    rain_mm = data['daily']['precipitation_sum'][idx]
    prcp_in = rain_mm / 25.4  # mm a pulgadas
    
    return prcp_in, snow_in, awnd_mph
```

### Manejo de Errores

```python
@app.post("/predict")
def predict_flight(data: FlightRequest):
    # 1. Validación de Modelo Cargado
    if sess is None:
        raise HTTPException(
            status_code=503, 
            detail="El modelo no está cargado en el servidor."
        )
    
    # 2. Validación de Fecha
    try:
        dt = datetime.strptime(data.FECHA, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(
            status_code=400, 
            detail="Formato de fecha inválido. Usa YYYY-MM-DD"
        )
    
    # 3. Datos Faltantes (Graceful Degradation)
    if data.PRCP is None:
        # Intenta clima real, sino usa histórico
        live = get_live_weather(data.DEPARTING_AIRPORT, data.FECHA)
        if live:
            final_prcp, final_snow, final_awnd = live
        else:
            # Fallback estacional
            final_prcp = 0.5 if dt.month in [12, 1, 2] else 0.08
```

---

## 📁 Estructura del Proyecto

```text
H12-25-L-Equipo-30-Data-Science/
│
├── artifacts/                          # 🔒 CRÍTICO - Artefactos del Modelo
│   ├── flight_delay_rf_weighted.onnx   # Modelo ONNX (Principal)
│   ├── flight_delay_rf_weighted.onnx.zip  # Comprimido (GitHub)
│   ├── *_risk_map.joblib               # Mapas de Target Encoding
│   ├── smart_ops_lookup.joblib         # Datos operativos por ruta
│   ├── smart_traffic_lookup.joblib     # Patrones de tráfico
│   ├── airport_coords.joblib           # Coordenadas geográficas
│   ├── catalogs.json                   # Listas de aerolíneas/aeropuertos válidos
│   ├── frontend_options.json           # Opciones con códigos IATA
│   └── FlightDataDTO.java              # Clase Java generada
│
├── Data/                                # 📊 Dataset Original (NO subir)
│   └── full_data_flightdelay.csv       # 6.5M registros (~2GB)
│
├── Utils/                               # 🛠️ Scripts de Utilidad
│   ├── eda.py                          # Análisis exploratorio
│   ├── generate_coords.py              # Extractor de coordenadas
│   ├── generate_smart_lookup.py        # Generador de lookups
│   ├── generate_java.py                # Generador de DTOs Java
│   └── check_model_ready.py            # Health check del modelo
│
├── public/                              # 🌐 Frontend Web
│   ├── index.html                      # Página principal
│   ├── css/style.css                   # Estilos
│   ├── js/script.js                    # Lógica del cliente
│   └── assets/
│       └── frontend_options.json       # Copia de artifacts/
│
├── main.py                              # 🚀 API REST (FastAPI)
├── Prediction-model.ipynb               # 📓 Notebook de entrenamiento
├── requirements.txt                     # 📦 Dependencias Python
├── dockerfile                           # 🐳 Configuración Docker
├── .gitignore                          # 🚫 Archivos ignorados
└── README.md                            # 📖 Este archivo
```

### Archivos Críticos para Producción

| Archivo | Propósito | Tamaño | Regenerable |
| --- | --- | --- | --- |
| `flight_delay_rf_weighted.onnx` | Modelo de inferencia | ~40MB | ❌ No (requiere re-entrenamiento) |
| `*_risk_map.joblib` | Codificación de categorías | ~5KB c/u | ❌ No (depende de datos de entrenamiento) |
| `smart_ops_lookup.joblib` | Datos operativos | ~200KB | ✅ Sí (desde CSV) |
| `airport_coords.joblib` | Coordenadas GPS | ~15KB | ✅ Sí (desde CSV) |
| `catalogs.json` | Validación de inputs | ~8KB | ✅ Sí (desde CSV) |

---

## Instalación y Configuración

### Requisitos del Sistema

- **Python**: 3.9 - 3.11 (ONNX Runtime no soporta 3.12+)
- **RAM**: Mínimo 2GB disponibles
- **Disco**: 500MB (con modelo descomprimido)
- **Sistema Operativo**: Windows, Linux, macOS

### Instalación Paso a Paso

#### 1. Clonar el Repositorio

```bash
git clone https://github.com/No-Country-simulation/H12-25-L-Equipo-30-Data-Science.git
cd H12-25-L-Equipo-30-Data-Science
```

#### 2. Crear Entorno Virtual

```bash
# Windows
python -m venv .venv
.\.venv\Scripts\activate

# Linux/Mac
python3 -m venv .venv
source .venv/bin/activate
```

#### 3. Instalar Dependencias

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Dependencias Críticas**:

```txt
pandas==2.1.4
numpy==1.26.2
scikit-learn==1.3.2
onnx==1.15.0
onnxruntime==1.16.3
fastapi==0.104.1
uvicorn==0.24.0
pydantic==2.5.2
requests==2.31.0
```

#### 4. Descargar el Dataset (Solo para Re-entrenamiento)

```bash
# Opción 1: Kaggle CLI
kaggle datasets download -d threnjen/2019-airline-delays-and-cancellations
unzip 2019-airline-delays-and-cancellations.zip -d Data/

# Opción 2: Descarga Manual
# https://www.kaggle.com/datasets/threnjen/2019-airline-delays-and-cancellations
# Colocar full_data_flightdelay.csv en /Data
```

#### 5. Descomprimir el Modelo (Si es necesario)

```bash
cd artifacts
unzip flight_delay_rf_weighted.onnx.zip
cd ..
```

#### 6. Iniciar la API

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Salida Esperada**:

```text
🚀 INICIANDO API...
📦 Descomprimiendo modelo... (si aplica)
🧠 Cargando Modelo...
📂 Cargando Mapas de Riesgo y Datos...
🌍 Coordenadas cargadas para 96 aeropuertos.
✅ API LISTA
INFO:     Uvicorn running on http://0.0.0.0:8000
```

#### 7. Verificar que el Modelo Esté Listo

```bash
# En otra terminal (con el entorno activado)
python Utils/check_model_ready.py
```

**Salida Exitosa**:

```text
🕵️‍♂️ INICIO: Esperando a que el modelo de Data Science cargue...
✅ ¡MODELO LISTO! El servicio de Data Science está operativo.
   Respuesta de prueba: {'prediction': 'PUNTUAL', 'probability': 0.15}
```

---

## 🚀 Uso del Sistema

### Opción 1: Interfaz Web (Recomendada para Usuarios)

1. **Abrir el HTML en un Navegador**:

   ```bash
   # Si tienes Python instalado (servidor simple)
   cd public
   python -m http.server 8080
   ```

   Navega a: `http://localhost:8080`

2. **Completar el Formulario**:
   - **Aerolínea**: Escribe "American" → Autocompleta a "AA - American Airlines Inc."
   - **Aeropuerto**: Escribe "JFK" → Autocompleta a "JFK - John F. Kennedy International"
   - **Fecha**: Selecciona una fecha dentro de los próximos 7 días (para clima real)
   - **Hora**: Formato 24 horas (Ej: 14:30)

3. **Interpretar Resultados**:
   - **Verde (✅ PUNTUAL)**: Probabilidad < 68%
   - **Rojo (⚠️ ALTO RIESGO)**: Probabilidad ≥ 68%

### Opción 2: Swagger UI (Para Desarrolladores)

1. **Acceder a la Documentación Interactiva**:

   ```text
   http://localhost:8000/docs
   ```

2. **Probar el Endpoint `/predict`**:
   - Click en "POST /predict"
   - Click en "Try it out"
   - Pegar JSON de ejemplo:

   ```json
   {
     "CARRIER_NAME": "Delta Air Lines Inc.",
     "DEPARTING_AIRPORT": "Atlanta Municipal",
     "FECHA": "2026-01-10",
     "HORA": "08:00"
   }
   ```

   - Click en "Execute"

### Opción 3: cURL (Línea de Comandos)

```bash
curl -X POST "http://localhost:8000/predict" \
-H "Content-Type: application/json" \
-d '{
  "CARRIER_NAME": "Southwest Airlines Co.",
  "DEPARTING_AIRPORT": "Chicago O'\''Hare International",
  "FECHA": "2026-01-08",
  "HORA": "18:30"
}'
```

### Opción 4: Python Requests

```python
import requests
import json

url = "http://localhost:8000/predict"
payload = {
    "CARRIER_NAME": "United Air Lines Inc.",
    "DEPARTING_AIRPORT": "San Francisco International",
    "FECHA": "2026-01-12",
    "HORA": "10:15"
}

response = requests.post(url, json=payload)
print(json.dumps(response.json(), indent=2))
```

---

## 📡 Endpoints de la API

### `POST /predict`

**Descripción**: Predice si un vuelo se retrasará basándose en datos operativos y meteorológicos.

**URL**: `http://localhost:8000/predict`

**Método**: POST

**Headers**:

```http
Content-Type: application/json
```

**Body (JSON)**:

```json
{
  "CARRIER_NAME": "string (requerido)",
  "DEPARTING_AIRPORT": "string (requerido)",
  "FECHA": "string YYYY-MM-DD (requerido)",
  "HORA": "string HH:MM (requerido)",
  "PRCP": "float (opcional)",
  "SNOW": "float (opcional)",
  "AWND": "float (opcional)"
}
```

**Respuesta Exitosa (200 OK)**:

```json
{
  "prediction": "RETRASADO",
  "probability": 0.73,
  "details": "Clima: Tiempo Real (Open-Meteo) | Riesgo Ruta: 0.24",
  "weather_used": {
    "rain": 0.45,
    "wind": 18.2
  }
}
```

**Errores Comunes**:

| Código | Causa | Solución |
| -------- | ------- | ---------- |
| **400** | Formato de fecha inválido | Usar YYYY-MM-DD |
| **503** | Modelo no cargado | Esperar ~30s al inicio del servidor |
| **500** | Error interno (lookup faltante) | Verificar que existan todos los archivos en `artifacts/` |

### `GET /docs`

**Descripción**: Documentación interactiva de Swagger UI.

**URL**: `http://localhost:8000/docs`

### `GET /redoc`

**Descripción**: Documentación alternativa (ReDoc).

**URL**: `http://localhost:8000/redoc`

---

## 🌐 Integración con Frontend

### Archivos de Catálogo

#### `artifacts/frontend_options.json`

**Propósito**: Proporcionar listas de aerolíneas y aeropuertos válidos con códigos IATA para autocomplete.

**Estructura**:

```json
{
  "airports": [
    {
      "label": "JFK - John F. Kennedy International",
      "value": "John F. Kennedy International",
      "code": "JFK"
    }
  ],
  "carriers": [
    {
      "label": "AA - American Airlines Inc.",
      "value": "American Airlines Inc."
    }
  ]
}
```

**Uso en JavaScript**:

```javascript
fetch('assets/frontend_options.json')
  .then(res => res.json())
  .then(data => {
    setupAutocomplete("airport-input", "airport-list", 
                      "airport-real-value", data.airports);
  });
```

### Autocomplete Inteligente

**Características**:

- Búsqueda por código IATA: "JFK" → John F. Kennedy
- Búsqueda por nombre: "Kennedy" → John F. Kennedy
- Resaltado de coincidencias: **JFK** - John F. Kennedy
- Envía el nombre completo al backend (no el código)

**Implementación**:

```javascript
function setupAutocomplete(inputId, listId, hiddenId, dataArray) {
    const input = document.getElementById(inputId);
    const hidden = document.getElementById(hiddenId);
    
    input.addEventListener("input", function() {
        const val = this.value.toUpperCase();
        const matches = dataArray.filter(item => 
            item.label.toUpperCase().includes(val) || 
            (item.code && item.code.includes(val))
        );
        
        matches.forEach(item => {
            div.addEventListener("click", function() {
                input.value = item.label;      // Lo que ve el usuario
                hidden.value = item.value;     // Lo que se envía al API
            });
        });
    });
}
```

### CORS y Seguridad

**Configuración Actual** (Desarrollo):

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ⚠️ Cambiar en producción
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Recomendación para Producción**:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://flightontime.com",
        "https://www.flightontime.com"
    ],
    allow_credentials=True,
    allow_methods=["POST", "GET"],
    allow_headers=["Content-Type"],
)
```

---

## 🐛 Troubleshooting

### Problema: "El modelo no está cargado" (503)

**Causa**: El servidor acaba de iniciar y ONNX Runtime está cargando el modelo.

**Solución**:

```bash
# Esperar 30 segundos y reintentar
# O ejecutar el health check
python Utils/check_model_ready.py
```

### Problema: "ModuleNotFoundError: No module named 'onnxruntime'"

**Causa**: Dependencias no instaladas o entorno virtual no activado.

**Solución**:

```bash
# Activar entorno
.\.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Reinstalar
pip install onnxruntime==1.16.3
```

### Problema: "FileNotFoundError: artifacts/flight_delay_rf_weighted.onnx"

**Causa**: El modelo no fue descomprimido.

**Solución**:

```bash
cd artifacts
unzip flight_delay_rf_weighted.onnx.zip
```

### Problema: "API de clima devuelve timeout"

**Causa**: Firewall corporativo o proxy bloqueando Open-Meteo.

**Solución**:

```python
# En main.py, línea ~120
res = session.get(url, headers=headers, timeout=10, verify=False)
```

**Alternativa**: Forzar clima manual en el request:

```json
{
  "CARRIER_NAME": "...",
  "DEPARTING_AIRPORT": "...",
  "FECHA": "2026-01-10",
  "HORA": "14:00",
  "PRCP": 0.5,
  "AWND": 15.0
}
