#include <Arduino.h>
#include <ArduinoBLE.h>
#include <Wire.h>
#include <Trill.h>

// BLE Service und Characteristic definieren
const char* PEER_NAME   = "ModiEMS";
const char* SERVICE_UUID = "454D532D-5365-7276-6963-652D424C4531";
const char* CHAR_UUID    = "454D532D-5374-6575-6572-756E672D4348";

BLECharacteristic serverChar;
BLEDevice serverPeripheral;

Trill trill;

// --- Zonengrenzen (kannst du anpassen) ---
const int ZONE1_MIN = 1;
const int ZONE1_MAX = 1237;
const int ZONE2_MIN = ZONE1_MAX + 1;
const int ZONE2_MAX = 2474;
const int ZONE3_MIN = ZONE2_MAX + 1;
const int ZONE3_MAX = 3712;
// 0 = kein Finger / Fehler / außerhalb Bereich

bool scanI2C();
int getZone();
void sendZone(int zone);
void connectToBluetooth();
void sendMessageViaBluetooth(String output);

int lastZone = 255; // 255 = Initialwert

void setup() {
  pinMode(LED_BUILTIN, OUTPUT);

  delay(3000);
  Wire.begin();
  Serial.begin(9600);
  while (!Serial);
  
  Serial.println("\nI2C Scanner");
  while (!scanI2C()) delay(2000);
  Serial.println("I2C device erkannt. Initialisiere Bluetooth...");

  // BLE starten
  if (!BLE.begin()) {
    Serial.println("BLE konnte nicht gestartet werden!");
    while (1);
  }

  Serial.println("Starte Scan nach BLE-Server...");
  connectToBluetooth();

  if (trill.setup(Trill::TRILL_FLEX)) {
    Serial.println("Fehler: Trill Flex Initialisierung fehlgeschlagen!");
    while (1);
  }

  trill.setMode(Trill::CENTROID);
  delay(10);
  trill.setPrescaler(3);
  delay(10);
  trill.setNoiseThreshold(200);
  delay(10);
  trill.updateBaseline();
  Serial.println("Trill Flex bereit.");

  // Zonengrenzen einmal anzeigen
  Serial.print("Zone 1 = "); Serial.print(ZONE1_MIN); Serial.print(" - "); Serial.println(ZONE1_MAX);
  Serial.print("Zone 2 = "); Serial.print(ZONE2_MIN); Serial.print(" - "); Serial.println(ZONE2_MAX);
  Serial.print("Zone 3 = "); Serial.print(ZONE3_MIN); Serial.print(" - "); Serial.println(ZONE3_MAX);
}

void loop() {
  if (!serverPeripheral.connected()) {
    Serial.println("Verbindung verloren, versuche Neuverbindung...");
    digitalWrite(LED_BUILTIN, LOW);
    connectToBluetooth();
  }
  int currentZone = getZone();
  if (currentZone != lastZone) {
    sendZone(currentZone);
    lastZone = currentZone;
  }
  delay(30);
}

bool scanI2C() {
  byte error, address;
  for (address = 1; address < 127; address++) {
    Wire.beginTransmission(address);
    error = Wire.endTransmission();
    if (error == 0) {
      Serial.print("I2C device found at address 0x");
      if (address < 16) Serial.print("0");
      Serial.println(address, HEX);
      return true;
    }
  }
  Serial.println("No I2C devices found");
  return false;
}

int getZone() {
  trill.read();
  int numTouches = trill.getNumTouches();
  if (numTouches == 1) {
    int pos = trill.touchLocation(0);
    if (pos >= ZONE1_MIN && pos <= ZONE1_MAX) return 1;
    if (pos >= ZONE2_MIN && pos <= ZONE2_MAX) return 2;
    if (pos >= ZONE3_MIN && pos <= ZONE3_MAX) return 3;
    // Wenn ungültig/außerhalb: Zone 0
    return 0;
  }
  // Kein Finger oder mehr als einer: Zone 0
  return 0;
}

void sendZone(int zone) {
  String zoneStr = String(zone);
  Serial.print("Finger in Zone: ");
  Serial.println(zoneStr);

  if (serverPeripheral.connected() && serverChar) {
    switch (zone)
    {
    case 0:
      sendMessageViaBluetooth("C0I0T0G");
      sendMessageViaBluetooth("C1I0T0G");
      break;
    case 1:
      sendMessageViaBluetooth("C1I0T0G");
      sendMessageViaBluetooth("C0I100T30000G");
      break;
    case 2:
      sendMessageViaBluetooth("C0I100T30000G");
      sendMessageViaBluetooth("C1I100T30000G");
      break;
    case 3:
      sendMessageViaBluetooth("C0I0T0G");
      sendMessageViaBluetooth("C1I100T30000G");
      break;
    default:
      sendMessageViaBluetooth("C0I0T0G");
      sendMessageViaBluetooth("C1I0T0G");
      break;
    }
  }
}

void sendMessageViaBluetooth(String output){
  bool ok = serverChar.writeValue(output.c_str(), output.length());
  if (ok) {
    Serial.println("erfolgreich gesendet");
  } else {
    Serial.println("Fehler beim Senden!");
  }
}

void connectToBluetooth() {
  while (true) {
    // Vor einem neuen Versuch alle Ressourcen freigeben
    if (serverPeripheral) {
      serverPeripheral.disconnect();
      // Warten bis die Trennung abgeschlossen ist
      unsigned long startTime = millis();
      while (serverPeripheral.connected() && (millis() - startTime < 5000)) {
        delay(100);
      }
      if (serverPeripheral.connected()) {
        Serial.println("Warnung: Trennung dauerte zu lange!");
      }
      serverPeripheral = BLEDevice(); // Reset des Peripheral-Objekts
    }

    // Neuen Scan starten
    do
      {
        BLE.scanForUuid(SERVICE_UUID);
        serverPeripheral = BLE.available();
      } while (!serverPeripheral);
        BLE.stopScan();

    if (!serverPeripheral) {
      Serial.println("Device nicht gefunden, neuer Versuch...");
      delay(1000);
      continue;
    }

    Serial.print("Gefunden, verbinde zu: ");
    Serial.println(PEER_NAME);

    if (!serverPeripheral.connect()) {
      Serial.println("Verbindung fehlgeschlagen!");
      serverPeripheral = BLEDevice();
      delay(1000);
      continue;
    }

    Serial.println("Verbunden!");

    // Service discovery mit Timeout
    unsigned long serviceStart = millis();
    bool serviceFound = false;
    while (millis() - serviceStart < 3000) {
      if (serverPeripheral.discoverService(SERVICE_UUID)) {
        serviceFound = true;
        break;
      }
      delay(100);
    }

    if (!serviceFound) {
      Serial.println("Service nicht gefunden! Neuer Versuch...");
      serverPeripheral.disconnect();
      delay(1000);
      continue;
    }

    // Characteristic suchen
    serverChar = serverPeripheral.characteristic(CHAR_UUID);
    if (!serverChar) {
      Serial.println("Characteristic nicht gefunden! Neuer Versuch...");
      serverPeripheral.disconnect();
      delay(1000);
      continue;
    }

    if (!serverChar.canWrite()) {
      Serial.println("Characteristic kann nicht geschrieben werden! Neuer Versuch...");
      serverPeripheral.disconnect();
      delay(1000);
      continue;
    }

    Serial.println("Verbindung zu Server steht.");
    digitalWrite(LED_BUILTIN, HIGH);
    break;
  }
}