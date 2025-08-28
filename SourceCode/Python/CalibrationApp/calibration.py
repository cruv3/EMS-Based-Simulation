import threading

import asyncio

from bluetooth import BluetoothHandler

def start_background_loop():
    loop = asyncio.new_event_loop()
    def _run():
        asyncio.set_event_loop(loop)
        loop.run_forever()
    threading.Thread(target=_run, daemon=True).start()
    return loop

bg_loop = start_background_loop()

def cal_send(ble_handler, message):
    asyncio.run_coroutine_threadsafe(ble_handler.send(message), bg_loop)

def calibrate(ble_handler : BluetoothHandler):
    print("##### CALIBRATION #####")
    print("Please set the intensities for both channels to 0 on the EMS device.")
    start = input("Press Enter to start the calibration or enter 'Skip' to skip the calibration...")
    if start.lower().strip() == 'skip':
        print("Calibration skipped! \n Please continue in the App window!")
        return 100, 100

    channel1_intensity = 0
    channel2_intensity = 0

    for channel in [0, 1]:

        channel_intensity_set = False
        while not channel_intensity_set:
            print("Starting calibration for channel " + str(channel + 1) + ".")
            msg = "C" + str(channel) + "I100T30000G"
            cal_send(ble_handler, msg)
            print("Please slowly increase the intensity of channel " + str(channel + 1) + " until you can barely sense the EMS stimulation.")
            step1_complete = input("Enter 'Done' to continue. Otherwise, this step will restart.")
            if step1_complete.lower().strip() == "done":
                msg = "C" + str(channel) + "I100T1G"
                cal_send(ble_handler, msg)
                channel_intensity_set = True

        channel_finetuned = False
        while not channel_finetuned:
            print("Starting finetuning for channel " + str(channel + 1) + ".")
            print("In this step, we will set the intensity of the EMS stimulation more precisely using the toolkit.")
            print("The finetuning will start at the lowest level and increase the intensity by 5% each step.")
            print("If you can feel the stimulation at the current step, please enter 'Done'. Otherwise, continue to the next step by pressing Enter.")
            input("Press Enter to start...")

            intensity = 5
            while intensity <= 100:
                print("Starting finetuning for channel "+ str(channel + 1) +" with " + str(intensity) + "% strength.")
                msg = "C" + str(channel) + "I" + str(intensity) + "T30000G"
                cal_send(ble_handler, msg)
                print("Is the stimulation noticeable?")
                noticeable = input("Yes?: Type 'Done'. No?: Press Enter")
                if noticeable.lower().strip() == "done":
                    msg = "C" + str(channel) + "I100T1G"
                    cal_send(ble_handler, msg)
                    channel_finetuned = True
                    break

                if intensity >= 100:
                    msg = "C" + str(channel) + "I100T1G"
                    cal_send(ble_handler, msg)
                    print("Calibration failed. Please restart the calibration.")

                intensity += 5

        if not channel_intensity_set or not channel_finetuned:
            msg = "C" + str(channel) + "I100T1G"
            cal_send(ble_handler, msg)
            print("Error during calibration phase! Please restart the calibration.")
            break

        if channel == 0:
            channel1_intensity = intensity
        else:
            channel2_intensity = intensity

    print("Calibration complete!")
    print("Please set the following intesities when using the App: ")
    print("Channel 1:" + str(channel1_intensity))
    print("Channel 2:" + str(channel2_intensity))
