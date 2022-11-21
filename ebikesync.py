import logging
import re
from configparser import ConfigParser
from logging import debug, info, warning, error, exception

from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait
from xdg import xdg_config_home

try:
    from xvfbwrapper import Xvfb

    XVFBWRAPPER = True
except ModuleNotFoundError:
    XVFBWRAPPER = False
    pass

HTML_FETCH_TIMEOUT: int = 5
SELENIUM_DRIVER = None


class SeleniumPageWithLogin:
    """ A simple class to access a webpage via Selenium that needs a login first."""
    cookie_button_selector: str = ""
    driver: WebDriver
    email_field_selector: str = ""
    login_url: str = ""
    password_field_selector: str = ""

    def __init__(self, driver: webdriver, username: str = "", password: str = "") -> None:
        """
        sets the selenium driver and get the URL and completes the login form.
        :param driver: the selenium driver to use
        :param username: username to login
        :param password: password to login
        """
        self.driver = driver
        self.login(username, password)

    def _fill(self, selector_string: str, value: str, selector_type: str = By.CSS_SELECTOR) -> WebElement:
        """
        Waits HTML_FETCH_TIMEOUT seconds for a Formfield to appear and fills it with the given value.
        :param selector_string: ID, Name, CSS Selector or XPATH to get specify the Formfield
        :param value: Value to fill in
        :param selector_type: Type of the Selector By.ID, By.XPATH, By.Name for example
        :return: The Selenium WebElement
        """
        html_element = self._wait_for(selector_string, selector_type)
        html_element.clear()
        html_element.send_keys(value)
        return html_element

    def _wait_for(self, selector_string: str, selector_type: str = By.CSS_SELECTOR) -> WebElement:
        """
        Waits for an HTML element to appear and return it
        :param selector_string: ID, name, CSS selector or XPATH to get specify the formfield
        :param selector_type: Type of the Selector By.ID, By.XPATH, By.Name for example
        :return: The Selenium WebElement
       """
        return WebDriverWait(self.driver, HTML_FETCH_TIMEOUT).until(
            expected_conditions.presence_of_element_located((selector_type, selector_string)))

    def login(self, username: str, password: str):
        """
        login to the Webpage and consent with cookies if necessary.

        :param username: username to login
        :param password: password to login
        :return: None
        """
        debug(f"logging in on {self.login_url}")
        self.driver.get(self.login_url)
        if self.cookie_button_selector:
            consent_button = self._wait_for(self.cookie_button_selector)
            consent_button.click()

        self._fill(self.email_field_selector, username)
        password_field = self._fill(self.password_field_selector, password)
        password_field.submit()


class eBikeConnect(SeleniumPageWithLogin):
    """
    Bosch ebike-connect.com to grab the total total_distance and total altitude from your E-Bike
    """
    total_distance: int = 0
    total_altitude: int = 0
    login_url: str = "https://www.ebike-connect.com/login?lang=de-at"
    fetch_url: str = "https://www.ebike-connect.com/dashboard"
    cookie_button_selector: str = "#cookieConsent-button"
    email_field_selector: str = "#login__email"
    password_field_selector: str = "#login__password"
    distance_selector: str = '#statistic-box-distance span.font-style-h2'
    altitude_selector: str = '#statistic-box-elevation span.font-style-h2'

    def fetch_data(self):
        debug(f"fetching data from {self.fetch_url}")
        distance = self._wait_for(self.distance_selector)
        altitude = self._wait_for(self.altitude_selector)
        self.total_distance = int(distance.text) or 0
        info(f"[BOSCH] Distance: {self.total_distance} km")
        self.total_altitude = int(altitude.text) or 0
        info(f"[BOSCH] Altitude: {self.total_altitude} m")


class RadeltAt(SeleniumPageWithLogin):
    """
    radelt.at Portal to fill in the total total_distance and total_altitude from the Bosch E-Bike Site.
    """
    additional_altitude: int = 0
    altitude_input_selector: str = 'input[name="altitude"]'
    date_input_selector: str = 'input[name="userdate"]'
    description_input_selector: str = 'input[name="description"]'
    total_distance: int = 0
    distance_input_selector: str = 'input[name="km_end"]'
    distance_selector: str = '#km span.amount'
    email_field_selector: str = "#email"
    fetch_url: str = "https://burgenland.radelt.at/dashboard/statistics"
    submit_url: str = "https://burgenland.radelt.at/dashboard/rides/create/245325"
    login_url: str = "https://burgenland.radelt.at/dashboard/login"
    password_field_selector: str = "#password"
    personal_stats_selector: str = "div[id^=pers] table:first-of-type tr"
    total_altitude: int = 0

    def fetch_data(self):
        """
        fetch the previous total distance and altitude calculate additional altitude.
        """
        debug(f"fetching data from {self.fetch_url}")
        altitude_pattern = re.compile(r"^Höhenmeter([0-9. ]+)m$", re.IGNORECASE)
        distance_pattern = re.compile(r"^gefahrene Kilometer([0-9. ]+)km$", re.IGNORECASE)

        self.driver.get(self.fetch_url)
        # iterate over every timeline to find the highest total_altitude
        for element in self.driver.find_elements(By.CSS_SELECTOR, self.personal_stats_selector):
            match_altitude = altitude_pattern.match(element.text)
            match_distance = distance_pattern.match(element.text)
            if match_altitude:
                debug(f"Altitude found {match_altitude.string}: {self.total_altitude}")
                self.total_altitude = max(int(match_altitude.group(1).replace(".", "")), self.total_altitude)
            elif match_distance:
                debug(f"Distance found {match_distance.string}: {self.total_distance}")
                self.total_distance = max(int(match_distance.group(1).replace(".", "")), self.total_distance)
        info(f"[Radelt] Distance: {self.total_distance} km")
        info(f"[Radelt] Altitude {self.total_altitude} m")

    def submit_data(self, total_distance: int, total_altitude: int = 0, submit: bool = True):
        """
        Submit the total total_distance and the new additional total_altitude to radelt.at
        :param total_distance: total Distance
        :param total_altitude:  new total altitude for the ebike
        :param submit: submit the Form?
        :return: 
        """
        debug(f"submit data using {self.submit_url}")
        self.driver.get(self.submit_url)
        distance_field = self._fill(self.distance_input_selector, str(total_distance))

        if total_altitude:
            self.additional_altitude = total_altitude - self.total_altitude
            info(f"[Radelt] Additional altitude {self.additional_altitude} m")
            self._fill(self.description_input_selector, f"Gesamthöhe: {self.total_altitude} m")
            self._fill(self.altitude_input_selector, str(self.additional_altitude))

        if total_distance <= self.total_distance:
            warning("No changes in total_distance, won't submit the form...")
        elif not submit:
            warning("Submit ist set to False, won't submit the form...")
        else:
            distance_field.submit()


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
        HTML_FETCH_TIMEOUT = config["default"]["html_fetch_timeout"]
        logging.basicConfig(level=getattr(logging, config.get("default", "loglevel").upper(), logging.INFO))
    except Exception:
        exception(f"Error loading config from {config_file}")
    return config


def run(config: ConfigParser) -> int:
    """

    :param config:
    :return:
    """
    try:
        selenium_driver = getattr(webdriver, config.get("default", "selenium_driver", fallback="Chrome"))()
    except Exception:
        exception("Error loading Selenium Driver!")
        return -2

    with selenium_driver:
        try:
            ebike_connect = eBikeConnect(
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
                submit=CONFIG.getboolean("radelt", "submit")
            )
        except Exception:
            exception("Error accessing radelt.at!")
            return -4
    return 0


if __name__ == "__main__":
    CONFIG: ConfigParser = ConfigParser()
    RETURN_CODE: int = 0
    logging.basicConfig(level=logging.INFO)
    try:
        CONFIG = get_config()
    except Exception as error_message:
        error(str(error_message))
        quit(-1)
    if XVFBWRAPPER and CONFIG.getboolean("default", "xvfbwrapper", fallback=False):
        with Xvfb() as xvfb:
            RETURN_CODE = run(config=CONFIG)
    else:
        RETURN_CODE = run(config=CONFIG)
    from time import sleep
    sleep(10)
    quit(RETURN_CODE)
