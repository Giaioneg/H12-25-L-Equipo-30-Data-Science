# Usa una imagen ligera de Python
FROM python:3.9-slim

# Evita que Python genere archivos .pyc y fuerza salida en consola
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema necesarias para compilar (gcc suele ser necesario para numpy/pandas)
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements e instalar
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código y los artefactos
COPY . .

# Exponer el puerto de FastAPI
EXPOSE 8000

# Comando para arrancar la API
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]