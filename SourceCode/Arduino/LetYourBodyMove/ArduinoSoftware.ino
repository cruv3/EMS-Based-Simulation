/**
 * ArduinoSoftware_Arduino_IDE
 *
 *  Copyright 2016 by Tim Duente <tim.duente@hci.uni-hannover.de>
 *  Copyright 2016 by Max Pfeiffer <max.pfeiffer@hci.uni-hannover.de>
 *
 *  Licensed under "The MIT License (MIT) - military use of this product is forbidden - V 0.2".
 *  Some rights reserved. See LICENSE.
 *
 * @license "The MIT License (MIT) - military use of this product is forbidden - V 0.2"
 * <https://bitbucket.org/MaxPfeiffer/letyourbodymove/wiki/Home/License>
 */

/**
 * Minor Revisions to this file by Pedro Lopes <plopesresearch@gmail.com>, all credit remains with the original authors (see above).
 */

// Necessary files (AltSoftSerial.h, AD5252.h, Rn4020BTLe.h, EMSSystem.h, EMSChannel.h) and dependencies (Wire.h, Arduino.h)
#include "ArduinoSoftware.h"
#include "AltSoftSerial.h"
#include "Wire.h"
#include "AD5252.h"
#include "Rn4020BTLe.h"
#include "EMSSystem.h"
#include "EMSChannel.h"
#include "Debug.h"

//the string below is how your EMS module will show up for other BLE devices
#define EMS_BLUETOOTH_ID "ModiEMS"

//setup for accepting commands also via USB (accepts USB commands if ACCEPT_USB_COMMANDS is 1)
#define ACCEPT_USB_COMMANDS 0

//setup the Bluetooth module. This is necessary if the toolkit is programmed the first time or if Bluetooth parameter are changed
#define SETUP_BLUETOOTH 0

//Initialization of control objects
AltSoftSerial softSerial;
AD5252 digitalPot(0);
Rn4020BTLe bluetoothModule(2, &softSerial);
EMSChannel emsChannel1(5, 4, A2, &digitalPot, 1);
EMSChannel emsChannel2(6, 7, A3, &digitalPot, 3);
EMSSystem emsSystem(2);

String command = "";

void setup() {
	Serial.begin(115200);

	softSerial.setTimeout(100);
	debug_println(F("\nSETUP:"));

	if (SETUP_BLUETOOTH) {
		//Reset and initialize the Bluetooth module
		debug_println(F("\tBT: RESETTING"));
		bluetoothModule.reset();
		debug_println(F("\tBT: RESET DONE"));
		debug_println(F("\tBT: INITIALIZING"));
		bluetoothModule.init(EMS_BLUETOOTH_ID);
	} else {
		//Or only start the communication if the Bluetoothmodule is setup correctly.
		bluetoothModule.start_communication();
	}

	debug_println(F("\tBT: INITIALIZED"));

	//Add the EMS channels and start the control
	debug_println(F("\tEMS: INITIALIZING CHANNELS"));
	emsSystem.addChannelToSystem(&emsChannel1);
	emsSystem.addChannelToSystem(&emsChannel2);
	EMSSystem::start();
	debug_println(F("\tEMS: INITIALIZED"));
	debug_println(F("\tEMS: STARTED"));
	debug_println(F("SETUP DONE (LED 13 WILL BE ON)"));

	emsSystem.shutDown();

	command.reserve(21);

	pinMode(13, OUTPUT);
	digitalWrite(13, HIGH);
}

String hexCommandString;
const String BTLE_DISCONNECT = "Connection End";

void loop() {

	
	if (softSerial.available() > 0) {
		String notification = softSerial.readStringUntil('\n');
		notification.trim();
		debug_println(F("\tBT: received message: "));
		debug_println(notification);

		//Data messages from the RN4020 start with WN and look like the following WN,001C,1ABD3467. First 8 character are not relevant. But for offering more services the second parameter is the service ID
		if (notification.length() >= 2 && notification.charAt(0) == 'W'
				&& notification.charAt(1) == 'V') {

			for (uint8_t i = 8; i < notification.length() - 1; i = i + 2) {
				int nextChar = convertTwoHexCharsToOneByte(notification, i);
				if (nextChar == -1) {
					debug_println(F("Failed to convert"));
				} else {
					command = command + (char) nextChar;
				}
			}

			debug_println(F("\tEMS_CMD: Converted command: "));
			debug_println(command);

			emsSystem.doCommand(&command);

			command = "";
		} else if (notification.equals(BTLE_DISCONNECT)) {
			debug_println(F("\tBT: Disconnected"));
			emsSystem.shutDown();
		}

	}

	//Checks whether a signal has to be stoped
	if (emsSystem.check() > 0) {

	}

	//Communicate to the EMS-module over USB
	if (ACCEPT_USB_COMMANDS) {
		if (Serial.available() > 0) {

			/* Uncomment the lines below, if you like to send command via USB to the Toolkit
			 * String command = Serial.readStringUntil('\n');
			 * emsSystem.doCommand(&command);
			 */

			char c = Serial.read();
			debug_Toolkit(c);

		}
	}

}

//Convert-functions for HEX-Strings "4D"->"M"
int convertTwoHexCharsToOneByte(String &s, uint8_t index) {
	int byteOne = convertHexCharToByte(s.charAt(index));
	int byteTwo = convertHexCharToByte(s.charAt(index + 1));
	if (byteOne != -1 && byteTwo != -1)
		return (byteOne << 4) + byteTwo;
	else {
		return -1;
	}
}

int convertHexCharToByte(char hexChar) {
	if (hexChar >= 'A' && hexChar <= 'F') {
		return hexChar - 'A' + 10;
	} else if (hexChar >= '0' && hexChar <= '9') {
		return hexChar - '0';
	} else {
		return -1;
	}
}

//For testing
void debug_Toolkit(char c) {
	if (c == '1') {
		if (emsChannel1.isActivated()) {
			emsChannel1.deactivate();
			debug_println(F("\tEMS: Channel 1 inactive"));
		} else {
			emsChannel1.activate();
			debug_println(F("\tEMS: Channel 1 active"));
		}
	} else if (c == '2') {
		if (emsChannel2.isActivated()) {
			emsChannel2.deactivate();
			debug_println(F("\tEMS: Channel 2 inactive"));
		} else {
			emsChannel2.activate();
			debug_println(F("\tEMS: Channel 2 active"));
		}
	} else if (c == 'q') {
		digitalPot.setPosition(1, digitalPot.getPosition(1) + 1);
		debug_println(
				String(F("\tEMS: Intensity Channel 1: "))
						+ String(digitalPot.getPosition(1)));
	} else if (c == 'w') {
		digitalPot.setPosition(1, digitalPot.getPosition(1) - 1);
		debug_println(
				String(F("\tEMS: Intensity Channel 1: "))
						+ String(digitalPot.getPosition(1)));
	} else if (c == 'e') {
		//Note that this is channel 3 on Digipot but EMS channel 2
		digitalPot.setPosition(3, digitalPot.getPosition(3) + 1);
		debug_println(
				String(F("\tEMS: Intensity Channel 2: "))
						+ String(digitalPot.getPosition(3)));
	} else if (c == 'r') {
		//Note that this is channel 3 on Digipot but EMS channel 2
		digitalPot.setPosition(3, digitalPot.getPosition(3) - 1);
		debug_println(
				String(F("\tEMS: Intensity Channel 2: "))
						+ String(digitalPot.getPosition(3)));
	}
}
