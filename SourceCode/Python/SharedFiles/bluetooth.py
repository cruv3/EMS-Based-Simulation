
from bleak import BleakScanner, BleakClient

async def scan_devices(timeout=5.0):
    """Scan for nearby BLE devices."""
    print("Scanning for BLE devices...")
    devices = await BleakScanner.discover(timeout=timeout)
    return [(d.name or "Unknown", d.address) for d in devices]


class BluetoothHandler:
    def __init__(self, address: str):
        self.address = address
        self.client = BleakClient(address)
        self.characteristic_uuid = None

    async def connect(self, timeout=10.0):
        print(f"Connecting to {self.address} with timeout {timeout}s...")
        try:
            await self.client.connect(timeout=timeout)
            if not self.client.is_connected:
                raise ConnectionError("Failed to connect to BLE device.")

            print("Connected. Discovering services...")
            # This populates self.client.services
            # await self.client.get_services()

            for service in self.client.services:
                print("Service found: " + service.uuid)
                if service.characteristics is not None:
                    # self.characteristic_uuid = service.characteristics[0].uuid
                    self.characteristic_uuid = "454d532d537465756572756e672d4348"
                    print("Characteristic found: " + self.characteristic_uuid)
                    # print(service.characteristics[0].properties)
                    return
                # for char in service.characteristics:
                #     self.characteristic_uuid = char.uuid
                #     print(char.properties)
                    # if "write" in char.properties or "write-without-response" in char.properties:
                    #     self.characteristic_uuid = char.uuid
                    #     print(f"Selected writable characteristic: {char.uuid}")
                    #     return

            raise ValueError("No writable characteristic found on device.")
        except Exception as e:
            raise e

    async def send(self, data: str):
        if not self.client.is_connected:
            raise ConnectionError("BLE device not connected.")
        if not self.characteristic_uuid:
            raise ValueError("No writable characteristic selected.")
        await self.client.write_gatt_char(self.characteristic_uuid, data.encode())
        print(f"Sent: {data}")

    async def disconnect(self):
        await self.client.disconnect()
        print("Disconnected from BLE device.")

