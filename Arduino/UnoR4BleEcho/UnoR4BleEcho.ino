#include <ArduinoBLE.h>
#include <Servo.h>

// Mac sends one ASCII servo angle (0..180) over BLE.
const char *DEVICE_NAME = "UNO-R4-Servo";
const char *SERVICE_UUID = "19B10000-E8F2-537E-4F6C-D104768A1214";
const char *ANGLE_UUID   = "19B10001-E8F2-537E-4F6C-D104768A1214";
const int SERVO_PIN = 6;

BLEService servoService(SERVICE_UUID);
BLEStringCharacteristic angleCharacteristic(
    ANGLE_UUID, BLEWrite | BLERead, 8);
Servo steeringServo;
int currentAngle = 90;

void setup() {
  Serial.begin(115200);
  steeringServo.attach(SERVO_PIN);
  steeringServo.write(currentAngle);

  if (!BLE.begin()) {
    Serial.println("BLE initialization failed");
    while (true) delay(1000);
  }

  BLE.setLocalName(DEVICE_NAME);
  BLE.setDeviceName(DEVICE_NAME);
  BLE.setAdvertisedService(servoService);
  servoService.addCharacteristic(angleCharacteristic);
  BLE.addService(servoService);
  angleCharacteristic.writeValue("90");
  BLE.advertise();

  Serial.println("BLE servo ready; advertising UNO-R4-Servo");
}

void loop() {
  BLEDevice central = BLE.central();
  if (!central) return;

  Serial.print("Connected: ");
  Serial.println(central.address());

  while (central.connected()) {
    BLE.poll();
    if (angleCharacteristic.written()) {
      String value = angleCharacteristic.value();
      char *end = nullptr;
      long requestedAngle = strtol(value.c_str(), &end, 10);
      if (end != value.c_str() && *end == '\0') {
        currentAngle = constrain(requestedAngle, 0, 180);
        steeringServo.write(currentAngle);
      }
    }
  }

  Serial.println("Disconnected; servo holds its last angle");
}
