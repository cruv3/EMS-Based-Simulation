import asyncio

from StudyTests.tests import start_tests
from SharedFiles.bluetooth import BluetoothHandler

# Replace with Toolkit address
DEVICE_ADDRESS = "DFA6C7B9-4E47-88B8-0E82-3A420A1C3FDD"

CHANNEL1_INTENSITY = 100
CHANNEL2_INTENSITY = 100

async def main():
    handler = BluetoothHandler(DEVICE_ADDRESS)

    try:
        print(f"Connecting to {DEVICE_ADDRESS}...")
        await handler.connect(timeout=10.0)
        print(f"Connected. Writable characteristic: {handler.characteristic_uuid}")

        start_tests(handler, CHANNEL1_INTENSITY, CHANNEL2_INTENSITY)

    except Exception as e:
        print("Connection Failed: " + str(e))


if __name__ == "__main__":
    asyncio.run(main())
