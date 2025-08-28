import tkinter as tk
import math
import time
import asyncio
from time import sleep

from bluetooth import BluetoothHandler, scan_devices
import threading

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Mouse Capture")
        self.root.geometry("400x500")

        # Bluetooth state
        self.ble_handler = None
        self.connected = False
        self.devices = []
        self.selected_device_var = tk.StringVar()
        self.selected_device_var.set("Waiting for Scan...")

        # Async loop
        self.bg_loop = None

        # Standard EMS intensities
        self.channel1_intensity = 100
        self.channel2_intensity = 100

        # Popup tracking
        self.loading_popup = None

        # Mouse tracking state
        self.mouse_down = False
        self.active_point = None
        self.active_point_start_time = None
        self.captured_points = []

        # Target points
        self.points = {
            "P1": (100, 50),
            "P2": (200, 50),
            "P3": (300, 50),
            "P4": (200, 150),
            "P5": (100, 250),
            "P6": (200, 250),
            "P7": (300, 250),
        }

        # Build the UI (after state setup)
        self._build_ui()

        # Create BLE message loop
        self.bg_loop = asyncio.new_event_loop()

        def _run():
            asyncio.set_event_loop(self.bg_loop)
            self.bg_loop.run_forever()

        threading.Thread(target=_run, daemon=True).start()

    def _build_ui(self):
        top_frame = tk.Frame(self.root)
        top_frame.pack(pady=5)

        tk.Button(top_frame, text="Scan", command=self.scan_devices).pack(side=tk.LEFT, padx=(0, 5))
        self.device_menu = tk.OptionMenu(top_frame, self.selected_device_var, "Waiting for Scan...")
        self.device_menu.pack(side=tk.LEFT, padx=5)
        tk.Button(top_frame, text="Connect", command=self.connect_ble).pack(side=tk.LEFT)

        self.canvas = tk.Canvas(self.root, bg="white", height=300)
        self.canvas.pack(fill=tk.X)

        self.confirm_button = tk.Button(self.root, text="Confirm Input", command=self.on_confirm)
        self.confirm_button.pack(pady=10)

        self.log_box = tk.Text(self.root, height=5, state="disabled")
        self.log_box.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # Draw points on canvas
        for x, y in self.points.values():
            self.canvas.create_oval(x - 5, y - 5, x + 5, y + 5, fill="gray")

        # Bind mouse events
        self.canvas.bind("<ButtonPress-1>", self.on_mouse_down)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)
        self.canvas.bind("<Motion>", self.on_mouse_move)

        self.log("UI initialized!")

    def on_mouse_down(self, event):
        self.mouse_down = True
        self.check_nearest_point(event.x, event.y)

    def on_mouse_up(self, event):
        self.mouse_down = False
        self.finalize_current_point()
        self.active_point = None
        self.active_point_start_time = None

    def on_mouse_move(self, event):
        if self.mouse_down:
            self.check_nearest_point(event.x, event.y)

    def check_nearest_point(self, x, y):
        min_dist = float('inf')
        closest_label = None

        for label, (px, py) in self.points.items():
            dist = math.hypot(x - px, y - py)
            if dist < min_dist:
                min_dist = dist
                closest_label = label

        if closest_label != self.active_point:
            self.finalize_current_point()
            self.active_point = closest_label
            self.active_point_start_time = time.time()
            self.log(f"Entered point: {closest_label}")

    def finalize_current_point(self):
        if self.active_point and self.active_point_start_time:
            duration = time.time() - self.active_point_start_time
            duration = max(0.1, round(duration, 1))
            self.captured_points.append((self.active_point, duration))
            self.log(f"Captured: {self.active_point} for {duration} seconds")

    def log(self, message):
        print(message)
        self.log_box.configure(state="normal")
        self.log_box.insert(tk.END, message + "\n")
        self.log_box.configure(state="disabled")
        self.log_box.see(tk.END)

    def connect_ble(self):
        def async_connect():
            self.log("Connecting to BLE...")
            selection = self.selected_device_var.get()
            if "(" not in selection:
                self.log("No device selected.")
                return

            address = selection.split("(")[-1].strip(")")
            if not address:
                self.log("Invalid device address.")
                return

            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                handler = BluetoothHandler(address)
                loop.run_until_complete(handler.connect(timeout=10.0))
                self.ble_handler = handler
                self.connected = True
                self.log(f"Connected to {address}")
                # Do calibration using console
                self.log("Please enter the channel intensities from the calibration phase in the terminal window.")
                self.channel1_intensity = int(input("Channel 1:"))
                self.channel2_intensity = int(input("Channel 2:"))
                self.log("Intensities set!")
                # self.channel1_intensity, self.channel2_intensity = calibrate(self.ble_handler)
            except Exception as e:
                self.connected = False
                self.log("Connection Failed: " + str(e))

        threading.Thread(target=async_connect, daemon=True).start()

    def scan_devices(self):
        def async_scan():
            self.selected_device_var.set("Scanning...")
            self.devices = []

            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                found = loop.run_until_complete(scan_devices(timeout=5.0))

                self.devices = found if found else [("No devices found", "")]
            except Exception as e:
                self.devices = [("Scan failed", "")]
                self.log("Scan error:" + str(e))

            self.update_device_menu()

        threading.Thread(target=async_scan, daemon=True).start()

    def update_device_menu(self):
        menu = self.device_menu["menu"]
        menu.delete(0, "end")

        for name, address in self.devices:
            label = f"{name} ({address})"
            menu.add_command(label=label, command=lambda v=label: self.selected_device_var.set(v))

        self.selected_device_var.set("Select device")

    def on_confirm(self):
        self.finalize_current_point()
        if not self.captured_points:
            self.log("No points captured.")
            return

        if not self.connected or not self.ble_handler:
            self.log("Not connected to BLE.")
            return

        points = self.captured_points[:]
        self.captured_points.clear()

        for point in points:
            match point[0]:
                case "P1" | "P2" | "P3":
                    channel = "C0"
                case "P5" | "P6" | "P7":
                    channel = "C1"
                case "P4":
                    duration = int(round(point[1] * 1000, 0))

                    message0 = "C0" + "I" + str(self.channel1_intensity) + "T" + str(duration) + "G"
                    message1 = "C1" + "I" + str(self.channel2_intensity) + "T" + str(duration) + "G"

                    self.send(message0)
                    self.send(message1)

                    sleep_time = (duration / 1000) - 0.5 if duration > 500 else 0
                    sleep(sleep_time)

                    continue

                case _:
                    self.log(f"Error for {point[0]}")
                    self.log("No appropriate points to send!")
                    return

            duration = int(round(point[1] * 1000, 0))

            message = channel + "I" + str(self.channel1_intensity) + "T" + str(duration) + "G" if channel == "C0" else channel + "I" + str(self.channel2_intensity) + "T" + str(duration) + "G"

            self.send(message)

            sleep_time = (duration / 1000) - 0.5 if duration > 500 else 0
            sleep(sleep_time)

            # "Fade Out" point for 500ms
            message = channel + "I" + str(self.channel1_intensity) + "T500" + "G" if channel == "C0" else channel + "I" + str(self.channel2_intensity) + "T500" + "G"
            self.send(message)

        self.captured_points = []

    def send(self, message):
        print("Sending: " + message)
        asyncio.run_coroutine_threadsafe(self.ble_handler.send(message), self.bg_loop)


