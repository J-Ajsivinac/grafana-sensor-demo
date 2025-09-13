import time
import random
import math
from datetime import datetime, timezone

class IoTSensorSimulator:
    def __init__(self):
        
        # Configuracionde sensores
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
        
        print(" -Simulador de sensores IoT iniciado")
        print(" - Conectado a Redis en localhost:6379")

    def generate_realistic_value(self, sensor_type, timestamp):
        """Genera valores realistas"""
        base = self.base_values[sensor_type]
        config = self.sensors[sensor_type]
        
        # Simulamos ciclos diarios para algunos sensores
        hour = datetime.fromtimestamp(timestamp).hour
        
        if sensor_type == 'temperature':
            # Temperatura sigue un patrn diario
            daily_cycle = 5 * math.sin((hour - 6) * math.pi / 12)
            noise = random.uniform(-2, 2)
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
                'device_id': 'device_001',
                'location': 'India_02'
            }
            
            print(f" * Enviado: {sensor_data}")

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
                print(f"🚨 ALERTA: {alert_data['message']}")

    def run_simulation(self, interval=2):
        """Ejecuta la simulación continuamente"""
        print(f"Iniciando simulación (intervalo: {interval}s)")
        print("Presiona Ctrl+C para detener")
        
        try:
            while True:
                self.send_sensor_data()
                
                # Mostrar último estado
                current_time = datetime.now().strftime('%H:%M:%S')
                
                print(f"[{current_time}]")
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\nSimulación detenida")

if __name__ == "__main__":
    simulator = IoTSensorSimulator()
    simulator.run_simulation()