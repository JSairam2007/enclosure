// M3 actuator: '1' -> relay (pin 7) + LED (pin 13) ON, '0' -> OFF. 9600 baud.
// Check whether your relay module is active-LOW; if so, invert the digitalWrite on pin 7.
const int RELAY = 7, LED = 13;
void setup() {
  Serial.begin(9600);
  pinMode(RELAY, OUTPUT); pinMode(LED, OUTPUT);
}
void loop() {
  if (Serial.available()) {
    char c = Serial.read();
    if (c == '1' || c == '0') {
      bool on = (c == '1');
      digitalWrite(RELAY, on); digitalWrite(LED, on);
    }
  }
}
