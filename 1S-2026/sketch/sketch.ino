
#include <DHT.h>

// ── Pines HC-SR04 ─────────────────────────
#define TRIG_PIN    9
#define ECHO_PIN    10

// ── Pines Sensor MQ ───────────────────────
#define MQ_AOUT     A0
#define MQ_DOUT     2

// ── Pin Potenciómetro ─────────────────────
#define POT_PIN     A1

// ── Pines DHT22 ───────────────────────────
#define DHT_PIN     4
#define DHT_TYPE    DHT22

DHT dht(DHT_PIN, DHT_TYPE);

// ─────────────────────────────────────────
void setup() {
  Serial.begin(9600);

  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  pinMode(MQ_DOUT, INPUT);

  dht.begin();
}

// ── Función: HC-SR04 → distancia en cm ───
float leerDistancia() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);

  long duracion = pulseIn(ECHO_PIN, HIGH);
  float distancia = duracion * 0.034 / 2.0;
  return distancia;
}

// ─────────────────────────────────────────
void loop() {

  // ── HC-SR04 ──────────────────────────────
  float distancia = leerDistancia();
  Serial.print("HC_SR04:distancia=");
  Serial.println(distancia, 1);

  // ── Sensor MQ ────────────────────────────
  int  mq_raw    = analogRead(MQ_AOUT);
  bool mq_alarma = digitalRead(MQ_DOUT) == HIGH;
  Serial.print("MQ_GAS:raw=");
  Serial.print(mq_raw);
  Serial.print(",alarma=");
  Serial.println(mq_alarma ? "1" : "0");

  // ── Potenciómetro ─────────────────────────
  int   pot_raw  = analogRead(POT_PIN);
  float pot_volt = pot_raw * (5.0 / 1023.0);
  Serial.print("POT:raw=");
  Serial.print(pot_raw);
  Serial.print(",voltaje=");
  Serial.println(pot_volt, 2);

  // ── DHT22 ────────────────────────────────
  float humedad     = dht.readHumidity();
  float temperatura = dht.readTemperature();

  if (!isnan(humedad) && !isnan(temperatura)) {
    Serial.print("DHT22:temperatura=");
    Serial.print(temperatura, 1);
    Serial.print(",humedad=");
    Serial.println(humedad, 1);
  } else {
    Serial.println("DHT22:error=1");
  }

  delay(10000);
}
