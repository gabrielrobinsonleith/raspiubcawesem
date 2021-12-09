import os
import configparser

from loguru import logger

ROOT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(ROOT_DIRECTORY, "config.ini")

config = configparser.ConfigParser()
config.optionxform = str   # keep camelcase when saving to file
config.read(CONFIG_FILE)

WEBAPP_FILE_DIRECTORY = os.path.expanduser(config["WebApp"]["FileDirectory"])
LOG_DIRECTORY = os.path.join(WEBAPP_FILE_DIRECTORY, "logs")
LOG_FILE_PATH = os.path.join(LOG_DIRECTORY, "awesem-webapp.log")

if not os.path.exists(WEBAPP_FILE_DIRECTORY):
    os.makedirs(WEBAPP_FILE_DIRECTORY)

if not os.path.exists(LOG_DIRECTORY):
    os.makedirs(LOG_DIRECTORY)

def save_config():
    """Saves all current values tof ile
    """
    with open(CONFIG_FILE, 'w') as configfile:
        config.write(configfile)

    logger.info(f"Saved to {CONFIG_FILE}")
