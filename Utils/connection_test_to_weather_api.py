import socket
import requests
import sys

TARGET = "api.open-meteo.com"
PORT = 443
URL = "https://api.open-meteo.com/v1/forecast?latitude=40.71&longitude=-74.01&daily=temperature_2m_max"

print(f"🕵️‍♂️ INICIANDO DIAGNÓSTICO DE RED HACIA: {TARGET}\n")

# 1. PRUEBA DE DNS (¿Sabemos la IP?)
try:
    ip = socket.gethostbyname(TARGET)
    print(f"✅ 1. DNS: ÉXITO. La IP es {ip}")
except Exception as e:
    print(f"❌ 1. DNS: FALLO. No se puede resolver el nombre. ({e})")
    sys.exit() # Si no hay DNS, no seguimos

# 2. PRUEBA DE PUERTO (¿Podemos tocar la puerta 443?)
try:
    sock = socket.create_connection((TARGET, PORT), timeout=5)
    print(f"✅ 2. TCP/SOCKET: ÉXITO. Puerto {PORT} abierto y accesible.")
    sock.close()
except Exception as e:
    print(f"❌ 2. TCP/SOCKET: FALLO. El Firewall te está bloqueando el puerto {PORT}. ({e})")

# 3. PRUEBA HTTPS ESTÁNDAR (¿Python confía en el certificado?)
try:
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(URL, headers=headers, timeout=5)
    print(f"✅ 3. HTTPS (Seguro): ÉXITO. Código {res.status_code}")
except requests.exceptions.SSLError:
    print(f"❌ 3. HTTPS (Seguro): FALLO SSL. Tu red intercepta certificados (Proxy corporativo/Antivirus).")
except Exception as e:
    print(f"❌ 3. HTTPS (Seguro): FALLO GENERAL. ({e})")

# 4. PRUEBA HTTPS INSEGURA (¿Funciona si ignoramos seguridad?)
try:
    res = requests.get(URL, headers=headers, timeout=5, verify=False)
    if res.status_code == 200:
        print(f"✅ 4. HTTPS (Inseguro/Verify=False): ÉXITO. ¡Esta es la solución!")
    else:
        print(f"❌ 4. HTTPS (Inseguro): FALLO. Código {res.status_code}")
except Exception as e:
    print(f"❌ 4. HTTPS (Inseguro): FALLO TOTAL. Ni ignorando SSL funciona. ({e})")

print("\n--- DIAGNÓSTICO FINALIZADO ---")