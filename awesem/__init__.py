import platform
from loguru import logger

def is_machine_raspberry_pi() -> bool:
    """Checks if the current machine is a Raspberry Pi.

    Returns:
        bool: Returns true if machine is Pi.
    """
    return "arm" in platform.uname().machine

if not is_machine_raspberry_pi():
    logger.warning("Current architecture is not Raspberry Pi. Hardware specific imports will be mocked.")
