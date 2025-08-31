import asyncio

from CalibrationApp.calibration import calibrate
from SharedFiles.bluetooth import BluetoothHandler

# Replace with Toolkit address
DEVICE_ADDRESS = "DFA6C7B9-4E47-88B8-0E82-3A420A1C3FDD"


async def main():
    handler = BluetoothHandler(DEVICE_ADDRESS)

    try:
        print(f"Connecting to {DEVICE_ADDRESS}...")
        await handler.connect(timeout=10.0)
        print(f"Connected. Writable characteristic: {handler.characteristic_uuid}")

        calibrate(handler)

    except Exception as e:
        print("Connection Failed: " + str(e))


if __name__ == "__main__":
    asyncio.run(main())
