"""
Laser Control
====================

A class to control the laser
"""
from awesem.drivers.relays import Relay, State, RelayControl, RELAY_PLATE_ADDRESS

from loguru import logger

class LaserControl:
    def __init__(self):
        self.sem_relays = RelayControl()

    def power(self, state: bool):
        """Switch on/off a 5V, 0.38A power supply to the laser
        """
        logger.debug(f"Setting power: {state}")
        if state:
            self.sem_relays.on(Relay.LASER_POWER)
        else:
            self.sem_relays.off(Relay.LASER_POWER)

if __name__=="__main__":
    import time

    laser = LaserControl()
    laser.power(State.ON)
    time.sleep(1)
    laser.power(State.OFF)
