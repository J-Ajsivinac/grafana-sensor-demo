import redis
import json
import time
import random
import math
from datetime import datetime

class IoTSensorSimulator:
    def __init__(self):
        self.redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
        
        # Configuración de sensores
        self.sensors = {
            'temperature': {'min': 15, 'max': 35, 'unit': '°C'},
            'humidity': {'min': 30, 'max': 90, 'unit': '%'},
            'light': {'min': 0, 'max': 1000, 'unit': 'lux'},
            'pressure': {'min': 980, 'max': 1030, 'unit': 'hPa'},
            'soil_moisture': {'min': 20, 'max': 80, 'unit': '%'},
            'battery_level': {'min': 50, 'max': 100, 'unit': '%'}
        }
        
        # Estados para simular patrones realistas
        self.base_values = {
            'temperature': 22,
            'humidity': 60,
            'light': 500,
            'pressure': 1013,
            'soil_moisture': 50,
            'battery_level': 85
        }
        
        print("Simulador de sensores IoT iniciado")
        print("Conectado a Redis en localhost:6379")

    def generate_realistic_value(self, sensor_type, timestamp):
        """Genera valores realistas que simulan patrones del mundo real"""
        base = self.base_values[sensor_type]
        config = self.sensors[sensor_type]
        
        # Simulamos ciclos diarios para algunos sensores
        hour = datetime.fromtimestamp(timestamp).hour
        
        if sensor_type == 'temperature':
            # Temperatura sigue un patrón diario
            daily_cycle = 5 * math.sin((hour - 6) * math.pi / 12)
            noise = random.uniform(-4, 17)
            value = base + daily_cycle + noise
            
        elif sensor_type == 'light':
            # Luminosidad alta durante el día, baja en la noche
            if 6 <= hour <= 18:
                value = base + random.uniform(-100, 200)
            else:
                value = random.uniform(0, 50)
                
        elif sensor_type == 'humidity':
            # Humedad inversamente relacionada con temperatura
            temp_effect = -0.5 * (self.base_values['temperature'] - 22)
            value = base + temp_effect + random.uniform(-5, 5)
            
        elif sensor_type == 'battery_level':
            # Batería se descarga lentamente
            self.base_values['battery_level'] -= random.uniform(0, 0.1)
            value = max(self.base_values['battery_level'], config['min'])
            
        else:
            # Otros sensores con variación aleatoria
            value = base + random.uniform(-5, 5)
        
        # Asegurar que esté dentro de los límites
        value = max(config['min'], min(config['max'], value))
        return round(value, 2)

    def send_sensor_data(self):
        """Envía datos de todos los sensores a Redis"""
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
                'device_id': 'raspberry_pi_001',
                'location': 'Aula_101'
            }
            
            # Guardar en Redis usando diferentes estructuras
            
            # 1. Stream para datos en tiempo real
            stream_key = f'sensors:{sensor_type}:stream'
            self.redis_client.xadd(stream_key, sensor_data)
            
            # 2. Hash para último valor
            hash_key = f'sensors:{sensor_type}:latest'
            self.redis_client.hset(hash_key, mapping=sensor_data)
            
            # 3. Lista con TTL para histórico reciente
            list_key = f'sensors:{sensor_type}:history'
            self.redis_client.lpush(list_key, json.dumps(sensor_data))
            self.redis_client.ltrim(list_key, 0, 999)  # Mantener últimos 1000
            
            # 4. Alertas si valores están fuera de rango
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
                self.redis_client.xadd('alerts:stream', alert_data)
                print(f"* ALERTA: {alert_data['message']}")

    def run_simulation(self, interval=2):
        """Ejecuta la simulación continuamente"""
        print(f"- Iniciando simulación (intervalo: {interval}s)")
        print("- Presiona Ctrl+C para detener")
        
        try:
            while True:
                self.send_sensor_data()
                
                # Mostrar último estado
                current_time = datetime.now().strftime('%H:%M:%S')
                temp = self.redis_client.hget('sensors:temperature:latest', 'value')
                humidity = self.redis_client.hget('sensors:humidity:latest', 'value')
                light = self.redis_client.hget('sensors:light:latest', 'value')
                
                print(f"[{current_time}] 🌡️ {temp}°C | 💧 {humidity}% | ☀️ {light}lux")
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n- Simulación detenida")

if __name__ == "__main__":
    simulator = IoTSensorSimulator()
    simulator.run_simulation(interval=7)