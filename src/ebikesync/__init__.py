import logging
from configparser import ConfigParser
from logging import exception

from selenium import webdriver
from xdg import xdg_config_home

from ebikesync.input.ebike_connect import EBikeConnect
from ebikesync.output.radelt import RadeltAt

try:
    from xvfbwrapper import Xvfb

    XVFBWRAPPER_INSTALLED = True
except ModuleNotFoundError:
    XVFBWRAPPER_INSTALLED = False

HTML_FETCH_TIMEOUT: int = 5
SELENIUM_DRIVER = None


def get_config() -> ConfigParser:
    """
    Loads the config from the config.ini in $XDG_CONFIG_DIR/ebikesync.
    :return: A ConfigParser Object with the current settings
    """
    global HTML_FETCH_TIMEOUT, SELENIUM_DRIVER
    config = ConfigParser()
    config_file = xdg_config_home() / "ebikesync" / "config.ini"
    try:
        config.read(config_file)
        logging.basicConfig(level=getattr(logging, config.get("default", "loglevel").upper(), logging.INFO))
    except FileNotFoundError:
        exception(f"File {config_file} not found.")
        quit(-1)
    return config


def process_data(config: ConfigParser):
    try:
        selenium_driver = getattr(webdriver, config.get("default", "selenium_driver", fallback="Chrome"))()
    except Exception:
        exception("Error loading Selenium Driver!")
        return -2

    with selenium_driver:
        try:
            ebike_connect = EBikeConnect(
                selenium_driver,
                config["bosch"]["username"],
                config["bosch"]["password"])
            ebike_connect.fetch_data()
            pass
        except Exception:
            exception("Error accessing ebike-connect.com!")
            return -3
        try:
            radelt_at = RadeltAt(
                selenium_driver,
                config["radelt"]["username"],
                config["radelt"]["password"]
            )
            radelt_at.fetch_data()
            radelt_at.submit_data(
                total_distance=ebike_connect.total_distance,
                total_altitude=ebike_connect.total_altitude,
                submit=config.getboolean("radelt", "submit")
            )
        except Exception:
            exception("Error accessing radelt.at!")
            return -4
    return 0


def run():
    config = get_config()
    return_code: int = 0
    logging.basicConfig(level=logging.INFO)
    if XVFBWRAPPER_INSTALLED and config.getboolean("default", "xvfbwrapper", fallback=False):
        with Xvfb() as xvfb:
            return_code = process_data(config=config)
    else:
        return_code = process_data(config=config)
    quit(return_code)
