# Configuración de MQTTX para monitorear los sensores IoT

## Instalación de MQTTX

1. Descargue MQTTX desde su sitio web oficial: [https://mqttx.app/](https://mqttx.app/)
2. Instale la aplicación siguiendo las instrucciones para su sistema operativo.

## Configuración de la conexión

### Utilizando la interfaz de escritorio de MQTTX

1. Abra la aplicación MQTTX
2. Haga clic en el botón "+" para crear una nueva conexión
3. Configure la conexión con los siguientes parámetros:

    - **Nombre**: IoT Sensors Demo
    - **Host**: localhost
    - **Puerto**: 1883
    - **Protocolo**: MQTT

4. Haga clic en "Conectar"

### Utilizando la versión web de MQTTX

1. Vaya a [https://mqttx.app/web](https://mqttx.app/web)
2. Configure la conexión con los siguientes parámetros:

    - **Nombre**: IoT Sensors Demo
    - **Host**: localhost
    - **Puerto**: 9001 (¡Importante! Use el puerto WebSocket)
    - **Protocolo**: ws (WebSocket)

3. Haga clic en "Conectar"

## Suscripción a temas

Para monitorear todos los datos de los sensores, suscríbase a los siguientes temas:

-   `sensors/#` - Para recibir datos de todos los sensores
-   `sensors/temperature` - Solo para datos de temperatura
-   `sensors/humidity` - Solo para datos de humedad
-   `sensors/light` - Solo para datos de luz
-   `sensors/pressure` - Solo para datos de presión
-   `sensors/soil_moisture` - Solo para datos de humedad del suelo
-   `sensors/battery_level` - Solo para datos de nivel de batería
-   `alerts` - Para recibir alertas

## Publicación de mensajes (opcional)

Si desea enviar comandos o configuraciones a los dispositivos, puede publicar mensajes en los siguientes temas:

-   `devices/device_001/commands` - Para enviar comandos al dispositivo
-   `devices/device_001/config` - Para enviar configuraciones al dispositivo

## Diferencias entre HTTP y MQTT

### HTTP (API REST)

-   **Modelo de comunicación**: Petición-Respuesta
-   **Iniciador de la comunicación**: Siempre el cliente (pull)
-   **Estado**: Sin estado (stateless)
-   **Uso de recursos**: Mayor uso de ancho de banda y procesamiento
-   **Endpoints implementados**:
    -   `GET /api/sensors` - Obtiene todos los datos de sensores
    -   `GET /api/sensors/{sensor_type}` - Obtiene datos de un sensor específico
    -   `GET /api/history/{sensor_type}` - Obtiene historial de un sensor

### MQTT

-   **Modelo de comunicación**: Publicación-Suscripción
-   **Iniciador de la comunicación**: Servidor o cliente (push)
-   **Estado**: Mantiene estado de conexión (stateful)
-   **Uso de recursos**: Menor uso de ancho de banda, eficiente para IoT
-   **Temas implementados**:
    -   `sensors/{sensor_type}` - Datos de sensores en tiempo real
    -   `alerts` - Alertas generadas por valores fuera de rango
