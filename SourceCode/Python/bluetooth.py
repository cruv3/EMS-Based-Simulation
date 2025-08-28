import asyncio
from typing import Optional, Tuple, List
from bleak import BleakScanner, BleakClient, BLEDevice


# ---------- Scan Utility ----------

async def scan_devices(timeout: float = 5.0) -> List[Tuple[str, str]]:
    """Scan for nearby BLE devices and return (name, address)."""
    print(f"Scanning for BLE devices ({timeout:.1f}s)...")
    devices = await BleakScanner.discover(timeout=timeout)
    return [(d.name or "Unknown", d.address) for d in devices]


# ---------- Bluetooth Handler ----------

class BluetoothHandler:
    """
    Verbindung per Name, Adresse ODER Service-UUID.
    - address:     (macOS: flüchtige CoreBluetooth-UUID) – nur verwenden, wenn frisch gescannt.
    - target_name: exakter Anzeigename aus dem Scan (empfohlen).
    - service_uuid: 128-Bit Service-UUID aus deinem Arduino-Sketch (empfohlen).
    """
    def __init__(
        self,
        address: Optional[str] = None,
        target_name: Optional[str] = None,
        service_uuid: Optional[str] = None,
        preferred_write_char: Optional[str] = None,
    ):
        if not any([address, target_name, service_uuid]):
            raise ValueError("Gib mindestens eines an: address, target_name oder service_uuid.")

        self.address = address
        self.target_name = target_name
        self.service_uuid = (service_uuid or "").lower()
        self.preferred_write_char = (preferred_write_char or "").lower()

        self.device: Optional[BLEDevice] = None
        self.client: Optional[BleakClient] = None
        self.characteristic_uuid: Optional[str] = None

    # ---- intern: Gerät finden (ohne harte UUID) ----
    async def _resolve_device(self, timeout: float = 8.0) -> BLEDevice:
        # Wenn Adresse vorgegeben ist, versuchen wir direkt, ansonsten scannen wir.
        if self.address:
            # Adresse in aktueller Umgebung via Scan bestätigen (sicherer)
            devices = await BleakScanner.discover(timeout=timeout)
            for d in devices:
                if d.address == self.address:
                    return d
            raise RuntimeError(f"Gerät mit Adresse {self.address} nicht im Scan gefunden.")

        # Per Name oder Service-UUID finden
        devices = await BleakScanner.discover(timeout=timeout)
        candidate: Optional[BLEDevice] = None

        # Zuerst per exaktem Namen
        if self.target_name:
            for d in devices:
                if (d.name or "").strip() == self.target_name:
                    candidate = d
                    break

        # Falls nicht gefunden und Service-UUID vorhanden: erneut scannen mit Filter
        if not candidate and self.service_uuid:
            # Hinweis: BleakScanner.find_device_by_filter wartet aktiv.
            candidate = await BleakScanner.find_device_by_filter(
                lambda d, ad: any(
                    (self.service_uuid in [(u or "").lower() for u in (ad.service_uuids or [])])
                ),
                timeout=timeout
            )

        if candidate:
            return candidate

        # Diagnoseausgabe
        print("Scan-Ergebnisse:")
        for d in devices:
            print(f"  - {d.name or 'Unknown'} | {d.address}")
        raise RuntimeError("Zielgerät nicht gefunden. Prüfe Name/Service-UUID, Werbung/Verbindung und Nähe.")

    # ---- intern: schreibbare Characteristic finden ----
    async def _find_writable_characteristic(self) -> str:
        assert self.client and self.client.is_connected
        services = self.client.services   # NEU: Services direkt vom Client nehmen

        # 1) Falls bevorzugte Characteristic-UUID vorgegeben → validieren
        if self.preferred_write_char:
            for s in services:
                for c in s.characteristics:
                    if c.uuid.lower() == self.preferred_write_char and (
                        "write" in c.properties or "write-without-response" in c.properties
                    ):
                        return c.uuid
            raise ValueError(
                f"Vorgegebene Characteristic {self.preferred_write_char} ist nicht (mehr) schreibbar."
            )

        # 2) Bevorzugt in angegebenem Service suchen
        if self.service_uuid:
            for s in services:
                if s.uuid.lower() == self.service_uuid:
                    for c in s.characteristics:
                        props = set(c.properties or [])
                        if "write" in props or "write-without-response" in props:
                            return c.uuid

        # 3) Global erste schreibbare Characteristic nehmen
        for s in services:
            for c in s.characteristics:
                props = set(c.properties or [])
                if "write" in props or "write-without-response" in props:
                    return c.uuid

        raise ValueError("Keine schreibbare Characteristic gefunden.")


    # ---- Public API ----

    async def connect(self, timeout: float = 10.0, scan_timeout: float = 8.0):
        print(f"Verbindungsaufbau... (timeout={timeout:.1f}s)")
        self.device = await self._resolve_device(timeout=scan_timeout)

        # BleakClient mit BLEDevice (robuster als mit flüchtiger address auf macOS)
        self.client = BleakClient(self.device)

        await self.client.connect(timeout=timeout)
        if not self.client.is_connected:
            raise ConnectionError("Failed to connect to BLE device.")

        print("Verbunden. Dienste werden abgefragt...")
        self.characteristic_uuid = await self._find_writable_characteristic()
        print(f"Schreibbare Characteristic: {self.characteristic_uuid}")

    async def send(self, data: bytes | str):
        if not self.client or not self.client.is_connected:
            raise ConnectionError("BLE device not connected.")
        if not self.characteristic_uuid:
            raise ValueError("No writable characteristic selected.")

        payload = data if isinstance(data, bytes) else data.encode()
        await self.client.write_gatt_char(self.characteristic_uuid, payload)
        print(f"Gesendet ({len(payload)} Bytes).")

    async def disconnect(self):
        if self.client:
            await self.client.disconnect()
            print("Disconnected from BLE device.")
