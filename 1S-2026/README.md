# Wokwi IoT Sensors Demo - 1S-2026

> **Conference-Ready IoT Demo** with Grafana, Redis, MQTT, and Wokwi simulation

Este proyecto contiene una demostración práctica **profesional y lista para conferencia** de monitoreo de datos IoT con Grafana, utilizando Redis como fuente de datos y simulando valores de sensores con Wokwi, integrado con MQTT para comunicación en tiempo real.

## Caracteristicas Principales

-   **100% Reproducible**: Todo auto-provisionado (datasources, dashboards, alertas)
-   **Dashboard Profesional**: Architecture header, stat panels con sparklines, gauges, service status
-   **Alerting System**: Alertas nativas de Grafana con notificaciones por email
-   **Health Checks**: Todos los servicios con verificacion automatica de salud
-   **Fixed Versions**: Grafana 10.4.0, Redis 7, Mosquitto 2.0 (estabilidad garantizada)
-   **Simulacion con Wokwi**: Simulacion real de Arduino UNO con sensores (HC-SR04, MQ Gas, Potenciometro, DHT22)
-   **MQTT**: Publicacion de datos en tiempo real para suscripcion
-   **Auto-Provisioning**: Datasources y dashboards se configuran automaticamente

## Sensores Simulados en Wokwi

| Sensor | Tipo | Datos |
|--------|------|-------|
| HC-SR04 | Ultrasónico | Distancia (cm) |
| MQ Gas | Gas | Valor raw (0-1023), Alarma (bool) |
| Potenciómetro | Analógico | Valor raw (0-1023), Voltaje (V) |
| DHT22 | Temperatura/Humedad | Temperatura (°C), Humedad (%) |

## Estructura del Proyecto

```
1S-2026/
├── docker-compose-mqtt.yml      # Redis + Grafana + Mosquitto
├── docker-compose-simple.yml    # Redis + Grafana (simple)
├── read.py                      # Lector serial desde Wokwi → Redis
├── sketch/                      # Código Arduino para Wokwi
│   ├── sketch.ino               # Código Arduino
│   ├── diagram.json             # Diagrama de conexiones Wokwi
│   └── wokwi.toml               # Configuración Wokwi
├── simulators/                  # Simulador Python alternativo
│   ├── app.py                   # App que lee Wokwi + Redis + MQTT
│   └── requirements.txt         # Dependencias Python
├── grafana/                     # Dashboards preconfigurados
│   ├── dashboard-simple.json    # Dashboard básico (Redis)
│   └── grafana-dashboard-mqtt.json  # Dashboard MQTT
└── mosquitto/                   # Configuración MQTT
    └── config/
        └── mosquitto.conf       # Configuración del broker
```

## Quick Start

**Start everything in 5 minutes:**

```powershell
# 1. Start services
docker-compose -f docker-compose-mqtt.yml up -d

# 2. Start Wokwi simulation (see sketch/diagram.json)

# 3. Start data reader
pip install redis pyserial
python read.py

# 4. Open Grafana: http://localhost:3000 (admin/admin123)
```

📖 **Full guide:** See [`QUICK_START.md`](QUICK_START.md) for quick reference or [`DEMO_GUIDE.md`](DEMO_GUIDE.md) for complete documentation.

## Uso

### 1. Iniciar los servicios con Docker Compose

#### Opción A: Configuración Completa (Recomendada)

```bash
docker-compose -f docker-compose-mqtt.yml up -d
```

Esto inicia Redis, Grafana y Mosquitto (MQTT broker).

#### Opción B: Configuración Simple

```bash
docker-compose -f docker-compose-simple.yml up -d
```

Solo Redis y Grafana.

### 2. Iniciar la simulación en Wokwi

1. Abre [Wokwi](https://wokwi.com/) y carga el proyecto desde `sketch/diagram.json`
2. Inicia la simulación
3. Wokwi expone el puerto serial en `localhost:4000`

### 3. Ejecutar el lector de datos

#### Opción A: read.py (solo Redis)

Lee datos desde Wokwi y los guarda en Redis:

```bash
pip install redis pyserial
python read.py
```

#### Opción B: simulators/app.py (Redis + MQTT)

Lee datos desde Wokwi, los guarda en Redis y los publica en MQTT:

```bash
cd simulators
pip install -r requirements.txt
python app.py
```

### 4. Acceder a Grafana

-   URL: http://localhost:3000
-   Usuario: `admin`
-   Contraseña: `admin123`

#### Configurar Redis como fuente de datos en Grafana

1. Ve a **Connections** → **Add new connection**
2. Busca **Redis** y selecciónalo
3. Configura:
    -   URL: `localhost:6379`
    -   Pool size: `5`
4. Guarda y prueba la conexión

#### Importar dashboards

1. Ve a **Dashboards** → **Import**
2. Carga el archivo JSON desde `grafana/dashboard-simple.json` o `grafana/grafana-dashboard-mqtt.json`
3. Selecciona la fuente de datos Redis que configuraste

## Comandos útiles para Docker Compose

### Detener los contenedores

```bash
# Para la configuración completa
docker-compose -f docker-compose-mqtt.yml down

# Para la configuración simple
docker-compose -f docker-compose-simple.yml down
```

### Ver logs

```bash
# Para la configuración completa
docker-compose -f docker-compose-mqtt.yml logs -f

# Para la configuración simple
docker-compose -f docker-compose-simple.yml logs -f
```

### Reconstruir contenedores

```bash
# Para la configuración completa
docker-compose -f docker-compose-mqtt.yml up -d --build
```

## ¿Cuál configuración usar?

-   **`docker-compose-simple.yml`**: Usa esta configuración si:
    -   Estás empezando y quieres algo rápido
    -   Solo necesitas Redis y Grafana
    -   Tienes recursos limitados
    -   No necesitas MQTT

-   **`docker-compose-mqtt.yml`**: Usa esta configuración si:
    -   Quieres la experiencia completa
    -   Necesitas probar funcionalidades MQTT
    -   Vas a hacer demostraciones completas
    -   Tienes suficientes recursos en tu máquina

## Comparación de protocolos

### Redis

-   **Modelo**: Almacenamiento en memoria
-   **Estructuras usadas**:
    -   `sensors:{tipo}:stream` - Redis Streams para datos en tiempo real
    -   `sensors:{tipo}:latest` - Redis Hashes para último valor
    -   `sensors:{tipo}:history` - Redis Lists para histórico (últimos 1000)
    -   `alerts:stream` - Stream de alertas

### MQTT

-   **Modelo**: Publicación-Suscripción (push)
-   **Temas disponibles**:
    -   `sensors/temperature` - Temperatura
    -   `sensors/humidity` - Humedad
    -   `sensors/distance` - Distancia
    -   `sensors/gas_raw` - Sensor de gas (raw)
    -   `sensors/gas_alarm` - Alarma de gas
    -   `sensors/pot_raw` - Potenciómetro (raw)
    -   `sensors/voltage` - Voltaje
    -   `alerts` - Alertas
-   **Puertos**: 1883 (TCP), 9001 (WebSockets)

## Monitoreo con MQTTX

Sigue las instrucciones en `Mqtt Instrucciones.md` para configurar MQTTX y suscribirte a los temas MQTT.

## Solución de problemas

### Wokwi no conecta

-   Asegúrate de que la simulación de Wokwi esté corriendo
-   Verifica que el puerto 4000 esté accesible: `telnet localhost 4000`

### Redis no conecta

-   Verifica que el contenedor esté corriendo: `docker ps | grep redis`
-   Reinicia: `docker-compose -f docker-compose-mqtt.yml restart redis`

### MQTT no conecta

-   Verifica que Mosquitto esté corriendo: `docker ps | grep mosquitto`
-   Verifica logs: `docker-compose -f docker-compose-mqtt.yml logs mosquitto`
