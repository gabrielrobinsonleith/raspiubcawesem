from loguru import logger

from awesem.drivers.digital_potentiometers import DigitalPotentiometers

class DetectorAmplifierControl(object):
    def __init__(self):
        self._digital_pots = DigitalPotentiometers()

    def set_detector_bias(self, value:float):
        logger.debug(f"Setting detector bias with {value} V")

        logger.warning("Not implemented")

    def set_output_gain(self, value:float):
        logger.debug(f"Setting output gain/brightness with {value} V")

        self._digital_pots.set_device1_amplitude(
            self._digital_pots.RDAC1,
            value
        )
