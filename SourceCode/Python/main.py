import asyncio

from tests import start_tests
from bluetooth import BluetoothHandler

# Replace with Toolkit address
# DFA6C7B9-4E47-88B8-0E82-3A420A1C3FDD
# 454D532D-5365-7276-6963-652D424C4531
DEVICE_ADDRESS = "DFA6C7B9-4E47-88B8-0E82-3A420A1C3FDD"
TARGET_NAME = "EMS99TD"

CHANNEL1_INTENSITY = 100
CHANNEL2_INTENSITY = 100

async def main():
    handler = BluetoothHandler(target_name=TARGET_NAME)

    try:
        print(f"Connecting to {DEVICE_ADDRESS}...")
        await handler.connect(timeout=10.0)
        print(f"Connected. Writable characteristic: {handler.characteristic_uuid}")

        start_tests(handler, CHANNEL1_INTENSITY, CHANNEL2_INTENSITY)

    except Exception as e:
        print("Connection Failed: " + str(e))


if __name__ == "__main__":
    asyncio.run(main())
