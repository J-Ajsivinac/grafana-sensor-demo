# grafana-sensor-demo

Este repositorio contiene un ejemplo práctico para introducir el monitoreo de datos con Grafana, utilizando Redis como fuente de datos y simulando valores de sensores con múltiples protocolos de comunicación (Redis, HTTP y MQTT).

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

1. Inicie los contenedores:

```bash
docker-compose up -d
```

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

5. Configure MQTTX siguiendo las instrucciones en `Mqtt Instrucciones.md`

## Comparación de protocolos

Para ver las diferencias entre los protocolos:

-   **HTTP**: Consulte datos haciendo peticiones a http://localhost:5000/api/sensors
-   **MQTT**: Suscríbase a los temas 'sensors/#' usando MQTTX
-   **Redis**: Visualice los datos en Grafana después de configurar Redis como fuente
