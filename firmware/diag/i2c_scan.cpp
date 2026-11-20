// Diagnostic: find which GPIO pair the OLED (I2C 0x3C/0x3D) is on.
// Prints results repeatedly so they survive USB CDC re-enumeration.
#include <Arduino.h>
#include <Wire.h>

static const int pins[] = {0, 1, 2, 3, 4, 5, 6, 7, 8, 10};
static String report;

void setup() {
  Serial.begin(115200);
  for (int sda : pins) {
    for (int scl : pins) {
      if (sda == scl) continue;
      Wire.begin(sda, scl, 100000);
      for (uint8_t addr : {0x3C, 0x3D}) {
        Wire.beginTransmission(addr);
        if (Wire.endTransmission() == 0) {
          report += "FOUND sda=" + String(sda) + " scl=" + String(scl) +
                    " addr=0x" + String(addr, HEX) + "\n";
        }
      }
      Wire.end();
    }
  }
  if (report.isEmpty()) report = "NOTHING FOUND\n";
}

void loop() {
  Serial.print("SCAN:\n" + report);
  delay(1000);
}
