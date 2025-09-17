import redis
import json
import time
import random
import math
import threading
from datetime import datetime
from flask import Flask, jsonify
import paho.mqtt.client as mqtt

# Inicializar Flask para HTTP API
app = Flask(__name__)

class IoTSensorSimulator:
    def __init__(self):
        # Conexión a Redis
        self.redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
        
        # Configuración de MQTT
        self.mqtt_client = mqtt.Client(protocol=mqtt.MQTTv311, userdata=None, transport="tcp")
        self.mqtt_client.on_connect = self.on_mqtt_connect
        self.mqtt_client.on_disconnect = self.on_mqtt_disconnect
        
        # Configuración de sensores
        self.sensors = {
            'temperature': {'min': 15, 'max': 35, 'unit': '°C'},
            'humidity': {'min': 30, 'max': 90, 'unit': '%'},
            'light': {'min': 0, 'max': 1000, 'unit': 'lux'},
            'pressure': {'min': 980, 'max': 1030, 'unit': 'hPa'},
            'soil_moisture': {'min': 20, 'max': 80, 'unit': '%'},
            'battery_level': {'min': 50, 'max': 100, 'unit': '%'}
        }
        
        # Estados base para generar valores realistas
        self.base_values = {
            'temperature': 22,
            'humidity': 60,
            'light': 500,
            'pressure': 1013,
            'soil_moisture': 50,
            'battery_level': 85
        }
        
        # Ultimos valores generados (para la API HTTP)
        self.latest_values = {}
        
        print(" -Simulador de sensores IoT iniciado")
        print(" - Conectado a Redis en localhost:6379")
        
        # Iniciar conexión MQTT
        try:
            self.mqtt_client.connect("localhost", 1883, 60)
            self.mqtt_client.loop_start()
            print(" - Conectado a MQTT broker en localhost:1883")
        except Exception as e:
            print(f" - Error al conectar con MQTT broker: {e}")
    
    def on_mqtt_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print(" - Conexión MQTT establecida")
        else:
            print(f" - Error en conexión MQTT, código: {rc}")
    
    def on_mqtt_disconnect(self, client, userdata, rc):
        print(f" - Desconectado de MQTT broker con código: {rc}")
        if rc != 0:
            print(" - Intentando reconectar a MQTT...")
            try:
                self.mqtt_client.reconnect()
            except:
                print(" - Reconexión fallida, reintentando más tarde")

    def generate_realistic_value(self, sensor_type, timestamp):
        """Genera valores realistas"""
        base = self.base_values[sensor_type]
        config = self.sensors[sensor_type]
        
        # Simulamos ciclos diarios para algunos sensores
        hour = datetime.fromtimestamp(timestamp).hour
        
        if sensor_type == 'temperature':
            # Temperatura sigue un patrn diario
            daily_cycle = 5 * math.sin((hour - 6) * math.pi / 12)
            noise = random.uniform(-7, 10)
            value = base + daily_cycle + noise
            
        elif sensor_type == 'light':
            # Luminosidad alta durante el dia, baja en la noche
            if 6 <= hour <= 18:
                value = base + random.uniform(-100, 200)
            else:
                value = random.uniform(0, 50)
                
        elif sensor_type == 'humidity':
            # Humedad inversamente relacionada con temperatura
            temp_effect = -0.5 * (self.base_values['temperature'] - 22)
            value = base + temp_effect + random.uniform(-5, 5)
            
        elif sensor_type == 'battery_level':
            # Bateria se descarga lentamente
            self.base_values['battery_level'] -= random.uniform(0, 0.1)
            value = max(self.base_values['battery_level'], config['min'])
            
        else:
            # Otros sensores con variacion random
            value = base + random.uniform(-5, 5)
        
        # Verificar limites
        value = max(config['min'], min(config['max'], value))
        return round(value, 2)

    def send_sensor_data(self):
        """Envía datos de todos los sensores a Redis, MQTT y almacena para HTTP"""
        timestamp = time.time()
        current_time = datetime.fromtimestamp(timestamp).isoformat()
        
        for sensor_type in self.sensors:
            value = self.generate_realistic_value(sensor_type, timestamp)
            
            # Estructura de datos para cada sensor
            sensor_data = {
                'timestamp': current_time,
                'sensor_id': f'sensor_{sensor_type}_001',
                'sensor_type': sensor_type,
                'value': value,
                'unit': self.sensors[sensor_type]['unit'],
                'device_id': 'device_001',
                'location': 'India_02'
            }
            
            # Guardar el último valor para la API HTTP
            self.latest_values[sensor_type] = sensor_data
            
            # Datos para MQTT (copia para mantener separado)
            mqtt_data = dict(sensor_data)
            mqtt_data['protocol'] = 'mqtt'
            
            # Datos para HTTP (copia para mantener separado)
            http_data = dict(sensor_data)
            http_data['protocol'] = 'http'
            
            # 1. Stream para datos en tiempo real (Redis - General)
            stream_key = f'sensors:{sensor_type}:stream'
            self.redis_client.xadd(stream_key, sensor_data)
            
            # 2. Hash para último valor (Redis - General)
            hash_key = f'sensors:{sensor_type}:latest'
            self.redis_client.hset(hash_key, mapping=sensor_data)
            
            # 3. Lista con TTL para histórico reciente (Redis - General)
            list_key = f'sensors:{sensor_type}:history'
            self.redis_client.lpush(list_key, json.dumps(sensor_data))
            self.redis_client.ltrim(list_key, 0, 999)  # Mantener últimos 1000
            
            # 4. Almacenar datos específicos de MQTT
            mqtt_stream_key = f'sensors:{sensor_type}:mqtt:stream'
            mqtt_latest_key = f'sensors:{sensor_type}:mqtt:latest'
            self.redis_client.xadd(mqtt_stream_key, mqtt_data)
            self.redis_client.hset(mqtt_latest_key, mapping=mqtt_data)
            
            # 5. Almacenar datos específicos de HTTP
            http_stream_key = f'sensors:{sensor_type}:http:stream'
            http_latest_key = f'sensors:{sensor_type}:http:latest'
            self.redis_client.xadd(http_stream_key, http_data)
            self.redis_client.hset(http_latest_key, mapping=http_data)
            
            # 6. Publicar en MQTT
            mqtt_topic = f'sensors/{sensor_type}'
            self.mqtt_client.publish(mqtt_topic, json.dumps(mqtt_data))
            
            # 7. Alertas si valores están fuera de rango
            self.check_alerts(sensor_type, value, sensor_data)

    def check_alerts(self, sensor_type, value, sensor_data):
        """Verifica y genera alertas para valores fuera de rango"""
        alerts = {
            'temperature': {'min': 18, 'max': 30},
            'humidity': {'min': 40, 'max': 80},
            'battery_level': {'min': 60, 'max': 100}
        }
        
        if sensor_type in alerts:
            limits = alerts[sensor_type]
            alert_data = None
            
            if value < limits['min']:
                alert_data = {
                    **sensor_data,
                    'alert_type': 'LOW_VALUE',
                    'severity': 'WARNING',
                    'message': f'{sensor_type} muy bajo: {value}'
                }
            elif value > limits['max']:
                alert_data = {
                    **sensor_data,
                    'alert_type': 'HIGH_VALUE',
                    'severity': 'WARNING',
                    'message': f'{sensor_type} muy alto: {value}'
                }
            
            if alert_data:
                # Enviar alerta a Redis
                self.redis_client.xadd('alerts:stream', alert_data)
                
                # Enviar alerta a MQTT
                self.mqtt_client.publish('alerts', json.dumps(alert_data))
                
                print(f"ALERTA: {alert_data['message']}")

    def run_simulation(self, interval=2):
        """Ejecuta la simulación continuamente"""
        print(f"Iniciando simulación (intervalo: {interval}s)")
        print("Presiona Ctrl+C para detener")
        
        try:
            while True:
                self.send_sensor_data()
                
                current_time = datetime.now().strftime('%H:%M:%S')
                # Mostrar datos de la clave general (compatibilidad)
                temp = self.redis_client.hget('sensors:temperature:latest', 'value')
                humidity = self.redis_client.hget('sensors:humidity:latest', 'value')
                light = self.redis_client.hget('sensors:light:latest', 'value')
                
                # Comparar valores MQTT vs HTTP para temperatura
                temp_mqtt = self.redis_client.hget('sensors:temperature:mqtt:latest', 'value') or '0'
                temp_http = self.redis_client.hget('sensors:temperature:http:latest', 'value') or '0'
                
                print(f"[{current_time}]  * {temp}°C | * {humidity}% | * {light}lux")
                print(f"[{current_time}]  * Temp MQTT: {temp_mqtt}°C | HTTP: {temp_http}°C")
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\nSimulación detenida")
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()

simulator = None

@app.route('/api/sensors', methods=['GET'])
def get_all_sensors():
    """Devuelve todos los datos de sensores más recientes"""
    if simulator:
        return jsonify(simulator.latest_values)
    return jsonify({"error": "Simulator not running"}), 503

@app.route('/api/sensors/<sensor_type>', methods=['GET'])
def get_sensor(sensor_type):
    """Devuelve datos de un sensor específico"""
    if simulator and sensor_type in simulator.latest_values:
        # Devolver datos HTTP específicos para mantener consistencia con el protocolo
        http_latest_key = f'sensors:{sensor_type}:http:latest'
        http_data = simulator.redis_client.hgetall(http_latest_key)
        
        # Si no hay datos HTTP, usa los datos generales
        if not http_data and sensor_type in simulator.latest_values:
            return jsonify(simulator.latest_values[sensor_type])
            
        return jsonify(http_data)
    return jsonify({"error": "Sensor data not found"}), 404

@app.route('/api/history/<sensor_type>', methods=['GET'])
def get_sensor_history(sensor_type):
    """Obtiene historial de un sensor desde Redis"""
    if simulator:
        history_key = f'sensors:{sensor_type}:history'
        history_data = simulator.redis_client.lrange(history_key, 0, 9)  # Últimos 10 registros
        result = []
        for item in history_data:
            result.append(json.loads(item))
        return jsonify(result)
    return jsonify({"error": "Simulator not running"}), 503

@app.route('/api/v1/comparison/<sensor_type>', methods=['GET'])
def compare_protocols(sensor_type):
    """Compara datos entre protocolos MQTT y HTTP"""
    if simulator:
        # Obtener datos MQTT
        mqtt_stream_key = f'sensors:{sensor_type}:mqtt:stream'
        mqtt_stream = simulator.redis_client.xrevrange(mqtt_stream_key, count=50)
        mqtt_latest_key = f'sensors:{sensor_type}:mqtt:latest'
        mqtt_latest = simulator.redis_client.hgetall(mqtt_latest_key)
        
        # Obtener datos HTTP
        http_stream_key = f'sensors:{sensor_type}:http:stream'
        http_stream = simulator.redis_client.xrevrange(http_stream_key, count=50)
        http_latest_key = f'sensors:{sensor_type}:http:latest'
        http_latest = simulator.redis_client.hgetall(http_latest_key)
        
        # Calcular métricas
        mqtt_values = [float(item[1].get('value', 0)) for item in mqtt_stream if 'value' in item[1]]
        http_values = [float(item[1].get('value', 0)) for item in http_stream if 'value' in item[1]]
        
        # Preparar respuesta
        response = {
            'mqtt_count': len(mqtt_stream),
            'http_count': len(http_stream),
            'mqtt_latest': mqtt_latest,
            'http_latest': http_latest,
            'metrics': {
                'mqtt_avg': sum(mqtt_values) / len(mqtt_values) if mqtt_values else 0,
                'http_avg': sum(http_values) / len(http_values) if http_values else 0,
                'mqtt_min': min(mqtt_values) if mqtt_values else 0,
                'mqtt_max': max(mqtt_values) if mqtt_values else 0,
                'http_min': min(http_values) if http_values else 0,
                'http_max': max(http_values) if http_values else 0
            }
        }
        
        return jsonify(response)
    return jsonify({"error": "Simulator not running"}), 503

@app.route('/api/v1/protocols', methods=['GET'])
def get_protocols_summary():
    """Proporciona un resumen de los datos por protocolo"""
    if simulator:
        result = {}
        
        for sensor_type in simulator.sensors:
            mqtt_stream_key = f'sensors:{sensor_type}:mqtt:stream'
            mqtt_count = len(simulator.redis_client.xrevrange(mqtt_stream_key, count=1000))
            
            http_stream_key = f'sensors:{sensor_type}:http:stream'
            http_count = len(simulator.redis_client.xrevrange(http_stream_key, count=1000))
            
            # Total
            total_key = f'sensors:{sensor_type}:stream'
            total_count = len(simulator.redis_client.xrevrange(total_key, count=1000))
            
            result[sensor_type] = {
                'mqtt_count': mqtt_count,
                'http_count': http_count,
                'total_count': total_count,
                'mqtt_latest': simulator.redis_client.hgetall(f'sensors:{sensor_type}:mqtt:latest'),
                'http_latest': simulator.redis_client.hgetall(f'sensors:{sensor_type}:http:latest')
            }
        
        return jsonify(result)
    return jsonify({"error": "Simulator not running"}), 503

def start_flask():
    """Inicia el servidor Flask en un hilo separado"""
    app.run(host='0.0.0.0', port=5000, debug=False)


if __name__ == "__main__":
    simulator = IoTSensorSimulator()
    
    # Iniciar API HTTP en un hilo separado
    http_thread = threading.Thread(target=start_flask)
    http_thread.daemon = True
    http_thread.start()
    print(" - API HTTP iniciada en puerto 5000")
    
    # Iniciar simulación
    simulator.run_simulation(interval=7)  # Enviar datos cada n segundos