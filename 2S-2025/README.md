# grafana-sensor-demo

Este repositorio contiene un ejemplo práctico para introducir el monitoreo de datos con Grafana, utilizando Redis como fuente de datos y simulando valores de sensores con múltiples protocolos de comunicación (Redis, HTTP y MQTT).

## Configuraciones disponibles

Este proyecto incluye dos configuraciones de Docker Compose:

### 1. Configuración Simple (`docker-compose-simple.yml`)

-   Solo Redis y Grafana
-   Ideal para empezar rápido
-   Menos recursos consumidos

### 2. Configuración Completa con MQTT (`docker-compose-mqtt.yml`)

-   Redis, Grafana y Mosquitto (MQTT broker)
-   Incluye todos los protocolos de comunicación
-   Para demostraciones completas

## Características

-   Simulación de sensores IoT con valores realistas
-   Almacenamiento de datos en Redis
-   Visualización con Grafana
-   API HTTP REST para acceso a datos
-   Publicación de datos vía MQTT para suscripción en tiempo real
-   Integración con MQTTX para monitoreo MQTT

## Protocolos implementados

### Redis

-   Almacenamiento principal de datos
-   Streams para datos en tiempo real
-   Hashes para últimos valores
-   Listas para históricos recientes

### HTTP (API REST)

-   Endpoints para consulta de datos
-   Modelo petición-respuesta
-   Implementado con Flask
-   Accesible en puerto 5000

### MQTT

-   Publicación de datos en tiempo real
-   Modelo publicación-suscripción
-   Integración con MQTTX para monitoreo
-   Accesible en puerto 1883 (MQTT) y 9001 (WebSockets)

## Uso

### Opción 1: Configuración Simple

Para ejecutar solo Redis y Grafana:

```bash
docker-compose -f docker-compose-simple.yml up -d
```

### Opción 2: Configuración Completa con MQTT

Para ejecutar Redis, Grafana y Mosquitto:

```bash
docker-compose -f docker-compose-mqtt.yml up -d
```

### Configuración del simulador

2. Instale las dependencias del simulador:

```bash
cd simulators
pip install -r requirements.txt
```

3. Ejecute el simulador:

```bash
python app.py
```

4. Acceda a Grafana en http://localhost:3000 (admin/admin123)

## Comandos útiles para Docker Compose

### Detener los contenedores

```bash
# Para la configuración simple
docker-compose -f docker-compose-simple.yml down

# Para la configuración con MQTT
docker-compose -f docker-compose-mqtt.yml down
```

### Ver logs

```bash
# Para la configuración simple
docker-compose -f docker-compose-simple.yml logs -f

# Para la configuración con MQTT
docker-compose -f docker-compose-mqtt.yml logs -f
```

### Reconstruir contenedores

```bash
# Para la configuración simple
docker-compose -f docker-compose-simple.yml up -d --build

# Para la configuración con MQTT
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

5. Configure MQTTX siguiendo las instrucciones en `Mqtt Instrucciones.md`

## Comparación de protocolos

Para ver las diferencias entre los protocolos:

-   **HTTP**: Consulte datos haciendo peticiones a http://localhost:5000/api/sensors
-   **MQTT**: Suscríbase a los temas 'sensors/#' usando MQTTX
-   **Redis**: Visualice los datos en Grafana después de configurar Redis como fuente
