"""
High Voltage Control
====================

Classes to control the UltraVolt model 40A12-N4-(standard) via switches and digital potentiometers.
"""
from loguru import logger

from awesem.drivers.analog_digital_converter import AnalogDigitalConverter
from awesem.drivers.relays import Relay, State, RelayControl, RELAY_PLATE_ADDRESS
from awesem.drivers.digital_potentiometers import DigitalPotentiometers

class HighVoltageControl:
    HV_READOUT_DIVIDER = 20e3   # readout voltage is 10,000x than output signal
    CURRENT_RESISTOR_1_OHM = 10700.0
    CURRENT_RESISTOR_2_OHM = 2500000000.0

    ADC_CHANNEL_ULTRAVOLT_VOLTAGE = 0
    ADC_CHANNEL_ULTRAVOLT_CURRENT = 1

    def __init__(self):
        self.sem_relays = RelayControl()
        self.adc = AnalogDigitalConverter()
        self.digital_pots = DigitalPotentiometers()

    def switch_enable_signal(self, state: bool):
        """Switch on/off a 5V enable signal
        """
        logger.debug(f"Setting enable signal: {state}")
        if state:
            self.sem_relays.on(Relay.ULTRAVOLT_ENABLE_SIGNAL)
        else:
            self.sem_relays.off(Relay.ULTRAVOLT_ENABLE_SIGNAL)

    def switch_ultravolt_power(self, state: bool):
        """Switch on/off 12V, 0.5A power
        """
        logger.debug(f"Setting ultravolt power: {state}")
        if state:
            self.sem_relays.on(Relay.ULTRAVOLT_POWER)
        else:
            self.sem_relays.off(Relay.ULTRAVOLT_POWER)

    def switch_ultravolt_output_signal(self, state: bool):
        """Switch on/off 0 to 5V high voltage output control signal
        """
        logger.debug(f"Setting ultravolt output signal: {state}")
        if state:
            self.sem_relays.on(Relay.ULTRAVOLT_HV_OUPUT_SIGNAL)
        else:
            self.sem_relays.off(Relay.ULTRAVOLT_HV_OUPUT_SIGNAL)

    def set_ultravolt_output_control_signal(self, voltage: float):
        """Set the output control signal to a given voltage.
        """
        logger.debug(f"Setting control signal with {voltage} V")

        self.digital_pots.set_device2_amplitude(
            self.digital_pots.RDAC3,
            voltage
        )

    def get_ultravolt_voltage(self, use_kilovolts=False) -> float:
        """Return ADC reading of output voltage

        Args:
            use_kilovolts (bool, optional): If true, returns the voltage in kilovolts
            instead of volts. Defaults to False.

        Returns:
            float: Ultravolt output voltage (in volts)
        """
        voltage = self.adc.read_voltage(self.ADC_CHANNEL_ULTRAVOLT_VOLTAGE) * self.HV_READOUT_DIVIDER

        if use_kilovolts:
            voltage = voltage / 1000

        return voltage

    def get_ultravolt_current(self, use_microamps=False) -> float:
        """Obtain ADC reading of load current and calculate the Ultravolt output current.

        Args:
            use_microamps (bool, optional): If true, returns the current in microamps
            instead of amps. Defaults to False.

        Returns:
            float: Ultravolt output load current (in amps)
        """

        set_voltage = self.get_ultravolt_voltage()
        current_voltage_readout = self.adc.read_voltage(self.ADC_CHANNEL_ULTRAVOLT_CURRENT)

        current = current_voltage_readout / self.CURRENT_RESISTOR_1_OHM - set_voltage / self.CURRENT_RESISTOR_2_OHM

        if use_microamps:
            current = current * 1e6

        return current

if __name__=="__main__":
    import time

    hv_control = HighVoltageControl()

    hv_control.switch_enable_signal(State.ON)
    time.sleep(1)
    hv_control.switch_ultravolt_power(State.ON)
    time.sleep(1)
    hv_control.switch_ultravolt_output_signal(State.ON)
    time.sleep(1)

    hv_control.switch_enable_signal(State.OFF)
    time.sleep(1)
    hv_control.switch_ultravolt_power(State.OFF)
    time.sleep(1)
    hv_control.switch_ultravolt_output_signal(State.OFF)
    time.sleep(1)

    print(f"Ultravolt voltage: {hv_control.get_ultravolt_voltage()}")
    print(f"Ultravolt current: {hv_control.get_ultravolt_current()}")
