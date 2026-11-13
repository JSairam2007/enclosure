// M4: stream MPU6050 raw data over serial as "ax,ay,az,gx,gy,gz" (g and deg/s), 115200 baud.
// Wiring (Uno/Nano): VCC->5V, GND->GND, SDA->A4, SCL->A5. No extra library needed.
#include <Wire.h>
const int MPU = 0x68;
int16_t rd() { return (int16_t)(Wire.read() << 8 | Wire.read()); }
void setup() {
  Serial.begin(115200);
  Wire.begin();
  Wire.beginTransmission(MPU); Wire.write(0x6B); Wire.write(0); Wire.endTransmission(true);  // wake up
}
void loop() {
  Wire.beginTransmission(MPU); Wire.write(0x3B); Wire.endTransmission(false);
  Wire.requestFrom(MPU, 14, true);
  int16_t ax = rd(), ay = rd(), az = rd();
  rd();  // temperature, unused
  int16_t gx = rd(), gy = rd(), gz = rd();
  Serial.print(ax / 16384.0, 4); Serial.print(',');
  Serial.print(ay / 16384.0, 4); Serial.print(',');
  Serial.print(az / 16384.0, 4); Serial.print(',');
  Serial.print(gx / 131.0, 3);   Serial.print(',');
  Serial.print(gy / 131.0, 3);   Serial.print(',');
  Serial.println(gz / 131.0, 3);
  delay(10);  // ~100 Hz nominal; the real rate is measured from timestamps by the Python side
}
