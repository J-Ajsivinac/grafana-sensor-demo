import serial
import json
import redis
from datetime import datetime

# ── Configuración Redis ───────────────────────────────────────────────────────
redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

# ── Configuración de sensores (metadatos) ─────────────────────────────────────
SENSOR_META = {
    'HC_SR04': {
        'fields': {
            'distancia': {'unit': 'cm',  'sensor_id': 'sensor_hc_sr04_001'}
        }
    },
    'MQ_GAS': {
        'fields': {
            'raw':    {'unit': 'raw',    'sensor_id': 'sensor_mq_gas_001'},
            'alarma': {'unit': 'bool',   'sensor_id': 'sensor_mq_alarma_001'}
        }
    },
    'POT': {
        'fields': {
            'raw':     {'unit': 'raw',   'sensor_id': 'sensor_pot_raw_001'},
            'voltaje': {'unit': 'V',     'sensor_id': 'sensor_pot_volt_001'}
        }
    },
    'DHT22': {
        'fields': {
            'temperatura': {'unit': '°C', 'sensor_id': 'sensor_dht22_temp_001'},
            'humedad':     {'unit': '%',  'sensor_id': 'sensor_dht22_hum_001'}
        }
    }
}

DEVICE_ID = 'arduno_wokwi_001'

# ── Parser de línea serial ────────────────────────────────────────────────────
def parse_line(line: str):
    """
    Parsea líneas con formato  SENSOR:campo=valor,campo=valor
    Retorna (sensor_name, dict_de_campos) o (None, None) si no matchea.

    Ejemplos válidos:
        HC_SR04:distancia=23.4
        MQ_GAS:raw=512,alarma=0
        POT:raw=300,voltaje=1.46
        DHT22:temperatura=25.3,humedad=60.1
        DHT22:error=1          ← se ignora (no hay valor numérico útil)
    """
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
        if key == 'error':          # ignorar líneas de error
            return None, None
        try:
            fields[key.strip()] = float(val.strip())
        except ValueError:
            pass                    # ignorar valores no numéricos

    return sensor_name, fields if fields else None


# ── Guardado en Redis ─────────────────────────────────────────────────────────
def save_to_redis(sensor_name: str, fields: dict):
    timestamp     = datetime.now().isoformat()
    meta_fields   = SENSOR_META[sensor_name]['fields']

    for field_name, value in fields.items():
        if field_name not in meta_fields:
            continue

        meta = meta_fields[field_name]
        # Clave Redis usa sensor_name + field para separar cada magnitud
        redis_key = f"{sensor_name}_{field_name}".lower()

        sensor_data = {
            'timestamp':   timestamp,
            'sensor_id':   meta['sensor_id'],
            'sensor_type': f"{sensor_name}/{field_name}",
            'value':       value,
            'unit':        meta['unit'],
            'device_id':   DEVICE_ID,
        }

        # 1. Stream para datos en tiempo real
        stream_key = f'sensors:{redis_key}:stream'
        redis_client.xadd(stream_key, sensor_data)

        # 2. Hash para último valor
        hash_key = f'sensors:{redis_key}:latest'
        redis_client.hset(hash_key, mapping=sensor_data)

        # 3. Lista con TTL para histórico reciente (últimos 1000)
        list_key = f'sensors:{redis_key}:history'
        redis_client.lpush(list_key, json.dumps(sensor_data))
        redis_client.ltrim(list_key, 0, 999)

        print(f"  ✓ [{sensor_name}] {field_name}={value} {meta['unit']}  →  Redis OK")


# ── Loop principal ────────────────────────────────────────────────────────────
def main():
    ser = serial.serial_for_url(
        "rfc2217://localhost:4000?ign_set_control=1",
        baudrate=9600,
        timeout=1
    )
    print("✓ Conectado a Wokwi — leyendo simulación...")
    print("✓ Redis conectado en localhost:6379\n")

    first_sensor_seen = None
    block_delimiter = 'HC_SR04'  # Sensor que marca el inicio de un nuevo bloque

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

        # if sensor_name and fields:
        #     save_to_redis(sensor_name, fields)

    

if __name__ == '__main__':
    main()