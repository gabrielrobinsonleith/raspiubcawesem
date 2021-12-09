"""
A library to communicate with the LTC2305 2-channel, 12-bit ADC
through I2C interface.

Linear Technology Datasheet: https://www.analog.com/media/en/technical-documentation/data-sheets/23015fb.pdf
"""

import smbus
from aenum import Constant

from awesem import is_machine_raspberry_pi
from loguru import logger
#hello

class AnalogDigitalConverter:
    """Analog to digital converter based on the LTC2305
    """
    DEVICE_ADDRESS_GLOBAL = 0x6b    # for synchronization of multiple LTC2305
    DEVICE_ADDRESS = 0x1A           # HIGH HIGH AD1 AD0 pin states
    RESOLUTION_BITS = 12
    RESOLUTION_STEPS = 2**12        # 4096
    CH0 = 0
    CH1 = 1
    CH_1_READ = 0b10001000          # SINGLE-ENDED, ~SIGN BIT, X, X, UNIPOLAR, SLEEPMODE, X, X
    CH_0_READ = 0b11001000          # SINGLE-ENDED, ~SIGN BIT, X, X, UNIPOLAR, SLEEPMODE, X, X
    OFFSET = 4
    REFERENCE_VOLTAGE = 4.096           # Voltage is set by input of Vdd

    def __init__(self):
        if is_machine_raspberry_pi():
            self.i2c_bus = smbus.SMBus(1)
        else:
            logger.info("Mock: Initialized ADC")

    def read_voltage(self, channel):
        if(int(channel) == 0):
            adc_command = self.CH_0_READ
        elif(int(channel) == 1):
            adc_command = self.CH_1_READ
        else:
            raise ValueError("Invalid channel selection")

        if is_machine_raspberry_pi():
            try:
                adc_code = self.i2c_bus.read_word_data(self.DEVICE_ADDRESS, adc_command)
            except OSError:
                logger.exception(f"Could not read {self.DEVICE_ADDRESS} with command {adc_command}. Returning 0V.")
                return 0

            adc_code_12_bit = ((adc_code & 0x00FF) << 8) | ((adc_code &0xFF00) >> 8) # swap MSB and LSB
            adc_code_12_bit = adc_code_12_bit >> self.OFFSET                      # right shift 4 bits
            voltage = float(adc_code_12_bit * self.REFERENCE_VOLTAGE/self.RESOLUTION_STEPS)
        else:
            from random import random
            voltage = random()

        return voltage

if __name__ == "__main__":
    import time

    adc = AnalogDigitalConverter()

    while True:
        channel = input("Channel to read from: ")
        channel = int(channel)
        # removes last reading before starting system
        adc.read_voltage(channel)

        for x in range(5):
            print(adc.read_voltage(channel))
            time.sleep(1)



