import threading
import random
import asyncio
from time import sleep

from bluetooth import BluetoothHandler

def start_background_loop():
    loop = asyncio.new_event_loop()
    def _run():
        asyncio.set_event_loop(loop)
        loop.run_forever()
    threading.Thread(target=_run, daemon=True).start()
    return loop

bg_loop = start_background_loop()

def ble_send(ble_handler, message):
    asyncio.run_coroutine_threadsafe(ble_handler.send(message), bg_loop)


def start_tests(ble_handler : BluetoothHandler, channel1_intensity=100, channel2_intensity=100):
    print("##### STUDY #####")
    print("Please set the correct intensities for both channels on the EMS device.")
    start = input("Press Enter to start the study...")

    test_single_points(ble_handler, channel1_intensity, channel2_intensity)
    test_flow_directions(ble_handler, channel1_intensity, channel2_intensity)

    print("##### END STUDY #####")


def test_single_points(ble_handler : BluetoothHandler, channel1_intensity, channel2_intensity):
    print("##### TEST: Check if users can distinguish all zones in random order (twice) #####")
    print("##### Take note of all test results! #####")

    order = [1,1,2,2,3,3] # Zone 1 = Channel 1; Zone 2 = Middle; Zone 3 = Channel 2
    random.shuffle(order)

    print("Selected order: " + str(order))
    start = input("Press Enter to start the zone tests...")

    turn_off_channels(ble_handler)

    for zone in order:
        successful = False
        while not successful:
            match zone:
                case 1:
                    print("Testing Channel 1")
                    ble_send(ble_handler, "C1I0T0G")
                    ble_send(ble_handler, "C0I" + str(channel1_intensity) +"T30000G")
                    sleep(5)
                    turn_off_channels(ble_handler)

                case 2:
                    print("Testing Middle")
                    ble_send(ble_handler, "C0I" + str(channel1_intensity) +"T30000G")
                    ble_send(ble_handler, "C1I" + str(channel2_intensity) +"T30000G")
                    sleep(5)
                    turn_off_channels(ble_handler)

                case 3:
                    print("Testing Channel 2")
                    ble_send(ble_handler, "C0I0T0G")
                    ble_send(ble_handler, "C1I" + str(channel2_intensity) +"T30000G")
                    sleep(5)
                    turn_off_channels(ble_handler)

            again = input("Press Enter to continue or type 'again' to rerun the current test...")
            if again != "again":
                successful = True

    print("All zone tests completed!")


def test_flow_directions(ble_handler: BluetoothHandler, channel1_intensity, channel2_intensity):
    print("##### TEST: Check if users can distinguish two types of flow in random order (twice) #####")
    print("##### Take note of all test results! #####")

    order = [1, 1, 2, 2]  # 1 --> From Channel 1 to Channel 2; 2 --> Reverse
    random.shuffle(order)

    print("Selected order: " + str(order))
    start = input("Press Enter to start the flow tests...")

    turn_off_channels(ble_handler)

    for flow in order:
        successful = False
        while not successful:
            match flow:
                case 1:
                    print("Testing Channel 1 to Channel 2")
                    ble_send(ble_handler, "C1I0T0G")
                    ble_send(ble_handler, "C0I" + str(channel1_intensity) + "T30000G")
                    sleep(3)
                    ble_send(ble_handler, "C1I" + str(channel2_intensity) + "T30000G")
                    sleep(3)
                    ble_send(ble_handler, "C0I0T0G")
                    sleep(3)
                    ble_send(ble_handler, "C1I0T0G")

                case 2:
                    print("Testing Channel 2 to Channel 1")
                    ble_send(ble_handler, "C0I0T0G")
                    ble_send(ble_handler, "C1I" + str(channel2_intensity) + "T30000G")
                    sleep(3)
                    ble_send(ble_handler, "C0I" + str(channel1_intensity) + "T30000G")
                    sleep(3)
                    ble_send(ble_handler, "C1I0T0G")
                    sleep(3)
                    ble_send(ble_handler, "C0I0T0G")


            again = input("Press Enter to continue or type 'again' to rerun the current test...")
            if again != "again":
                successful = True

    print("All flow tests completed!")

def turn_off_channels(ble_handler: BluetoothHandler):
    ble_send(ble_handler, "C0I0T0G")
    ble_send(ble_handler, "C1I0T0G")

