import logging
from configparser import ConfigParser
import selenium.common
from selenium import webdriver
from xdg import xdg_config_home
from time import sleep

from ebikesync import plugins

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
        logging.basicConfig(level=getattr(logging, config.get("ebikesync", "loglevel").upper(), logging.INFO))
    except FileNotFoundError:
        logging.exception(f"File {config_file} not found.")
        quit(-1)
    [plugins.load_plugin(plugin_name) for plugin_name in config.sections() if plugin_name.startswith("input.")]
    [plugins.load_plugin(plugin_name) for plugin_name in config.sections() if plugin_name.startswith("output.")]
    return config


def process_data(config: ConfigParser):
    try:
        selenium_driver = getattr(webdriver, config.get("ebikesync", "selenium_driver", fallback="Chrome"))()
    except selenium.common.exceptions.WebDriverException:
        logging.error(
            f"Error loading Selenium Driver {config['ebikesync']['selenium_driver']}. Please check your config.ini")
        return -2

    with selenium_driver:
        # process input
        try:
            for input_name, InputClass in plugins.input_plugins.items():
                kwargs = dict(config[input_name])
                input_plugin = InputClass(driver=selenium_driver, **kwargs)
                input_plugin.fetch_data()
                for output_name, OutputClass in plugins.output_plugins.items():
                    kwargs = dict(config[output_name])
                    output_plugin = OutputClass(driver=selenium_driver, **kwargs)
                    output_plugin.fetch_data()
                    output_plugin.submit_data(input_plugin)
        except selenium.common.TimeoutException:
            logging.exception("Error accessing a HTML element, check the code!")
            sleep(30)
            return (-4)
    return 0


def run():
    config = get_config()
    return_code: int = 0
    logging.basicConfig(level=logging.INFO)
    if XVFBWRAPPER_INSTALLED and config.getboolean("ebikesync", "xvfbwrapper", fallback=False):
        with Xvfb() as xvfb:
            return_code = process_data(config=config)
    else:
        return_code = process_data(config=config)
    quit(return_code)
