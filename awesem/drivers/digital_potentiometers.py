"""
Digital Potentiometer Control
=============================

Author: Chuan Du
Date: 11/13/2019

Description:
------------
A library to communicate with the AD5263 Quad 256-Position I2C
Nonvolatile Memory Digital Potentiometers. The methods are for
the control of the 50kOhm package.

Analog Devices datasheet: https://www.analog.com/media/en/technical-documentation/data-sheets/AD5253_5254.pdf
"""
import smbus2

from awesem import is_machine_raspberry_pi
from loguru import logger

class DigitalPotentiometers:
    """
    A class to communicate with the AD5263 Quad 256-Position I2C
    Nonvolatile Memory Digital Potentiometers. The methods are for
    the control of the 50kOhm package. This device creates a voltage
    divider at wiper-to-B and wiper-to-A proportional to the input
    voltage from terminal A and terminal B.
    """
    RESISTANCE_OHMS = 50000.0
    NUM_CHANNELS = 4
    RESOLUTION = 8
    CHANNEL_OFFSET = 5 # number of positions to shift DAC channel address in i2c commands
    NUM_POSITIONS = 2**RESOLUTION
    MAX_ANALOG_WRITE = 2**RESOLUTION-1
    MIN_ANALOG_WRITE = 0
    DEVICE_ADDRESS_1 = 0x2C
    DEVICE_ADDRESS_2 = 0x2F
    AMPLITUDE_INPUT_VOLTS = 3.3

    # Resistive digital-to-analog converters
    RDAC1 = 0
    RDAC2 = 1
    RDAC3 = 2
    RDAC4 = 3

    def __init__(self):
        if is_machine_raspberry_pi():
            self.i2c_bus = smbus.SMBus(1)
        else:
            logger.info("Mock: Initialized")

    def set_device1_amplitude(self, rdac_addr:int, amplitude_out: float):
        self._set_amplitude(self.DEVICE_ADDRESS_1, rdac_addr, amplitude_out)

    def set_device2_amplitude(self, rdac_addr:int, amplitude_out: float):
        self._set_amplitude(self.DEVICE_ADDRESS_2, rdac_addr, amplitude_out)

    def _set_amplitude(self, device_addr:int, rdac_addr:int, amplitude_out: float):
        """Given the amplitude of a wave, set the voltage divider to obtain the desired output amplitude.

        Args:
            device_addr (int): Address of AD5263 pacakge
            rdac_addr (int): Address of specifc RDAC on the AD5263 package range [0,3]
            amplitude_in (float): Amplitude of input waveform
            amplitude_out (float): Amplitude configured by user
        """
        if is_machine_raspberry_pi():
            formatted_rdac_addr = self._format_device_addr(rdac_addr)
            databyte = self._calculate_databyte(self.AMPLITUDE_INPUT_VOLTS, amplitude_out)

            try:
                self.i2c_bus.write_i2c_block_data(device_addr, formatted_rdac_addr, [databyte])
            except OSError:
                logger.exception(f"Error writing {amplitude_out} to device {device_addr}, rdac_addr {rdac_addr}")

        else:
            logger.info(f"Mock: Device {device_addr}, RDAC {rdac_addr}, Amplitude {amplitude_out}")

    def _format_device_addr(self,device_addr_decimal:int) -> int:
        """Formats the device RDAC address to write to register through i2c.
        be written through i2c.

        Arguments:
            device_addr_decimal {int} -- RDAC addresses range from 0 - 3

        Returns:
            int -- decimal value to write to AD5263 register
        """
        if device_addr_decimal < 0 or device_addr_decimal > 3:
            raise ValueError("RDAC address %d outof range [%d..%d]" % (device_addr_decimal, 0, 3))

        return device_addr_decimal << self.CHANNEL_OFFSET

    def _calculate_databyte(self, amplitude_in: float, amplitude_out: float) -> int:
        """Calculate databyte to transmit for required voltage division

        Args:
            amplitude_in (float): Amplitude of input waveform
            amplitude_out (float): Amplitude configured by user

        Returns:
            int: Databyte value ranging from 0 to 255
        """
        if amplitude_out > amplitude_in:
            raise ValueError("Output amplitude %.2f is greater than input amplitude %.2f" % (amplitude_out, amplitude_in))

        data = amplitude_out/amplitude_in * self.NUM_POSITIONS - 1

        if data < 0.0:
            data = 0.0

        return round(data)

if __name__ == "__main__":
    import time

    voltage_div = DigitalPotentiometers()

    print("AD5263 Digital Potentiometer Control")
    print("====================================")
    print("Device 1")
    amplitude1 = input("DAC 1 (V): ")
    voltage_div.set_device1_amplitude(voltage_div.RDAC1, float(amplitude1))
    time.sleep(0.5)

    amplitude1 = input("DAC 2 (V): ")
    voltage_div.set_device1_amplitude(voltage_div.RDAC2, float(amplitude1))
    time.sleep(0.5)

    amplitude1 = input("DAC 3 (V): ")
    voltage_div.set_device1_amplitude(voltage_div.RDAC3, float(amplitude1))
    time.sleep(0.5)

    amplitude1 = input("DAC 4 (V): ")
    voltage_div.set_device1_amplitude(voltage_div.RDAC4, float(amplitude1))
    time.sleep(0.5)

    print("Device 2")
    amplitude1 = input("DAC 1 (V): ")
    voltage_div.set_device2_amplitude(voltage_div.RDAC1, float(amplitude1))
    time.sleep(0.5)

    amplitude1 = input("DAC 2 (V): ")
    voltage_div.set_device2_amplitude(voltage_div.RDAC2, float(amplitude1))
    time.sleep(0.5)


