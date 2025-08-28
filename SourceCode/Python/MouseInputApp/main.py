import tkinter as tk
from app import App
from SharedFiles.mqtt import MQTTReceiver
from SharedFiles.bluetooth import BluetoothHandler
import asyncio
from bleak import BleakScanner


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
