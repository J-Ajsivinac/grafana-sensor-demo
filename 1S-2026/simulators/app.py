import serial
import json
import time
import redis
import paho.mqtt.client as mqtt
from datetime import datetime

# ── Configuración Redis ───────────────────────────────────────────────────────
redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

# ── Configuración de sensores (metadatos) ─────────────────────────────────────
SENSOR_META = {
    'HC_SR04': {
        'fields': {
            'distancia': {'unit': 'cm', 'sensor_id': 'sensor_hc_sr04_001', 'mqtt_topic': 'sensors/distance'}
        }
    },
    'MQ_GAS': {
        'fields': {
            'raw':    {'unit': 'raw',  'sensor_id': 'sensor_mq_gas_001', 'mqtt_topic': 'sensors/gas_raw'},
            'alarma': {'unit': 'bool', 'sensor_id': 'sensor_mq_alarma_001', 'mqtt_topic': 'sensors/gas_alarm'}
        }
    },
    'POT': {
        'fields': {
            'raw':     {'unit': 'raw', 'sensor_id': 'sensor_pot_raw_001', 'mqtt_topic': 'sensors/pot_raw'},
            'voltaje': {'unit': 'V',   'sensor_id': 'sensor_pot_volt_001', 'mqtt_topic': 'sensors/voltage'}
        }
    },
    'DHT22': {
        'fields': {
            'temperatura': {'unit': '°C', 'sensor_id': 'sensor_dht22_temp_001', 'mqtt_topic': 'sensors/temperature'},
            'humedad':     {'unit': '%',  'sensor_id': 'sensor_dht22_hum_001', 'mqtt_topic': 'sensors/humidity'}
        }
    }
}

DEVICE_ID = 'arduino_wokwi_001'

# Histeresis para estabilizar la alarma MQ con valor raw (ADC 0-1023).
MQ_ALARM_RAW_ON = 500.0
MQ_ALARM_RAW_OFF = 300.0
MQ_ALARM_STATE = 0.0

# ── MQTT Callbacks ────────────────────────────────────────────────────────────
def on_mqtt_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Conexion MQTT establecida")
    else:
        print(f"Error en conexion MQTT, codigo: {rc}")

def on_mqtt_disconnect(client, userdata, rc):
    print(f"Desconectado de MQTT broker con codigo: {rc}")
    if rc != 0:
        print("  Intentando reconectar a MQTT...")
        try:
            client.reconnect()
        except:
            print("  Reconexión fallida, reintentando más tarde")

# ── Configuración MQTT ────────────────────────────────────────────────────────
mqtt_client = mqtt.Client(protocol=mqtt.MQTTv311, userdata=None, transport="tcp")
mqtt_client.on_connect = on_mqtt_connect
mqtt_client.on_disconnect = on_mqtt_disconnect

# ── Parser de línea serial ────────────────────────────────────────────────────
def parse_line(line: str):
    if ':' not in line:
        return None, None

    sensor_name, _, fields_str = line.partition(':')
    sensor_name = sensor_name.strip()

    if sensor_name not in SENSOR_META:
        return None, None

    fields = {}
    for pair in fields_str.split(','):
        if '=' not in pair:
            continue
        key, _, val = pair.partition('=')
        key = key.strip()
        if key == 'error':  # ignorar líneas de error
            return None, None
        try:
            fields[key.strip()] = float(val.strip())
        except ValueError:
            pass  # ignorar valores no numéricos

    return sensor_name, fields if fields else None


def normalize_mq_alarm(fields: dict):
    """Ajusta la alarma MQ usando raw + histeresis, independiente del pin DOUT."""
    global MQ_ALARM_STATE

    raw_value = fields.get('raw')
    if raw_value is None:
        return fields

    if raw_value >= MQ_ALARM_RAW_ON:
        MQ_ALARM_STATE = 1.0
    elif raw_value <= MQ_ALARM_RAW_OFF:
        MQ_ALARM_STATE = 0.0

    fields['alarma'] = MQ_ALARM_STATE

    return fields

# ── Guardado en Redis y MQTT ─────────────────────────────────────────────────
def save_to_redis_and_mqtt(sensor_name: str, fields: dict):
    if sensor_name == 'MQ_GAS':
        fields = normalize_mq_alarm(fields)

    timestamp = datetime.now().isoformat()
    meta_fields = SENSOR_META[sensor_name]['fields']

    for field_name, value in fields.items():
        if field_name not in meta_fields:
            continue

        meta = meta_fields[field_name]
        redis_key = f"{sensor_name}_{field_name}".lower()

        sensor_data = {
            'timestamp':   timestamp,
            'sensor_id':   meta['sensor_id'],
            'sensor_type': f"{sensor_name}/{field_name}",
            'value':       value,
            'unit':        meta['unit'],
            'device_id':   DEVICE_ID,
        }

        # 1. Stream para datos en tiempo real (Redis - General)
        stream_key = f'sensors:{redis_key}:stream'
        redis_client.xadd(stream_key, sensor_data)

        # 2. Hash para último valor (Redis - General)
        hash_key = f'sensors:{redis_key}:latest'
        redis_client.hset(hash_key, mapping=sensor_data)

        # 3. Lista con TTL para histórico reciente (últimos 1000)
        list_key = f'sensors:{redis_key}:history'
        redis_client.lpush(list_key, json.dumps(sensor_data))
        redis_client.ltrim(list_key, 0, 999)

        # 4. Datos específicos de MQTT en Redis
        mqtt_data = dict(sensor_data)
        mqtt_data['protocol'] = 'mqtt'
        mqtt_stream_key = f'sensors:{redis_key}:mqtt:stream'
        mqtt_latest_key = f'sensors:{redis_key}:mqtt:latest'
        redis_client.xadd(mqtt_stream_key, mqtt_data)
        redis_client.hset(mqtt_latest_key, mapping=mqtt_data)

        # 5. Publicar en MQTT
        mqtt_topic = meta.get('mqtt_topic', f'sensors/{redis_key}')
        mqtt_client.publish(mqtt_topic, json.dumps(mqtt_data))

        # 6. Verificar alertas
        check_alerts(sensor_name, field_name, value, sensor_data)

        print(f"  OK [{sensor_name}] {field_name}={value} {meta['unit']}  ->  Redis + MQTT OK")

# ── Verificación de alertas ───────────────────────────────────────────────────
def check_alerts(sensor_name: str, field_name: str, value: float, sensor_data: dict):
    """Verifica y genera alertas para valores fuera de rango"""
    alerts_config = {
        ('DHT22', 'temperatura'): {'min': 18, 'max': 30},
        ('DHT22', 'humedad'): {'min': 40, 'max': 80},
        ('HC_SR04', 'distancia'): {'min': 5, 'max': 200},
    }

    config_key = (sensor_name, field_name)
    if config_key in alerts_config:
        limits = alerts_config[config_key]
        alert_data = None

        if value < limits['min']:
            alert_data = {
                **sensor_data,
                'alert_type': 'LOW_VALUE',
                'severity': 'WARNING',
                'message': f'{sensor_name}/{field_name} muy bajo: {value}'
            }
        elif value > limits['max']:
            alert_data = {
                **sensor_data,
                'alert_type': 'HIGH_VALUE',
                'severity': 'WARNING',
                'message': f'{sensor_name}/{field_name} muy alto: {value}'
            }

        if alert_data:
            # Enviar alerta a Redis
            redis_client.xadd('alerts:stream', alert_data)
            # Enviar alerta a MQTT
            mqtt_client.publish('alerts', json.dumps(alert_data))
            print(f"  ALERTA: {alert_data['message']}")

# ── Loop principal ────────────────────────────────────────────────────────────
def main():
    # Conectar a MQTT
    try:
        mqtt_client.connect("localhost", 1883, 60)
        mqtt_client.loop_start()
        print("Conectado a MQTT broker en localhost:1883")
    except Exception as e:
        print(f"Error al conectar con MQTT broker: {e}")

    # Conectar a Wokwi y Redis
    ser = serial.serial_for_url(
        "rfc2217://localhost:4000?ign_set_control=1",
        baudrate=9600,
        timeout=1
    )
    print("Conectado a Wokwi -- leyendo simulacion...")
    print("Redis conectado en localhost:6379\n")

    first_sensor_seen = None
    block_delimiter = 'HC_SR04'  # Sensor que marca el inicio de un nuevo bloque

    try:
        while True:
            raw = ser.readline().decode("utf-8", errors="ignore").strip()
            if not raw:
                continue

            ts = datetime.now().strftime('%H:%M:%S')

            sensor_name, fields = parse_line(raw)
            if sensor_name == block_delimiter:
                if first_sensor_seen is not None:
                    print()  # Salto de línea entre bloques
                first_sensor_seen = True

            print(f"[{ts}] {raw}")

            if sensor_name and fields:
                save_to_redis_and_mqtt(sensor_name, fields)

    except KeyboardInterrupt:
        print("\nSimulacion detenida por el usuario")
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
        ser.close()
    except Exception as e:
        print(f"\nError: {e}")
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
        ser.close()

if __name__ == '__main__':
    main()
