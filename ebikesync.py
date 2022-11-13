import logging
import re
from configparser import ConfigParser
from logging import debug, info, warning, error

from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait
from xdg import xdg_config_home
from xvfbwrapper import Xvfb

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
    Bosch ebike-connect.com to grab the total distance and total altitude from your E-Bike
    """
    distance: int = 0
    altitude: int = 0
    login_url: str = "https://www.ebike-connect.com/login?state=%2Fdashboard"
    cookie_button_selector: str = "#cookieConsent-button"
    email_field_selector: str = "#login__email"
    password_field_selector: str = "#login__password"
    distance_selector: str = '#statistic-box-distance span.font-style-h2'
    altitude_selector: str = '#statistic-box-elevation span.font-style-h2'

    def get_data(self):
        debug(f"fetching data from {self.login_url}")
        distance = self._wait_for(self.distance_selector)
        altitude = self._wait_for(self.altitude_selector)
        self.distance = int(distance.text) or 0
        info(f"[BOSCH] Distance: {self.distance} km")
        self.altitude = int(altitude.text) or 0
        info(f"[BOSCH] Altitude: {self.altitude} m")


class RadeltAt(SeleniumPageWithLogin):
    """
    radelt.at Portal to fill in the total distance and total_altitude from the Bosch E-Bike Site.
    """
    additional_altitude: int = 0
    altitude_input_selector: str = 'input[name="altitude"]'
    date_input_selector: str = 'input[name="userdate"]'
    description_input_selector: str = 'input[name="description"]'
    distance: int = 0
    distance_input_selector: str = 'input[name="km_end"]'
    distance_selector: str = '#km span.amount'
    email_field_selector: str = "#email"
    form_url: str = "https://burgenland.radelt.at/dashboard/rides/create/245325"
    login_url: str = "https://burgenland.radelt.at/dashboard/login"
    password_field_selector: str = "#password"
    timeline_entries_selector: str = 'div.timeline__entry__col.timeline__entry__col--bike-text p'
    total_altitude: int = 0

    def get_data(self, total_altitude: int):
        """
        fetch the previous total total_altitude and subtract it from the current total.
        :return: the difference
        """
        debug(f"fetching data from {self.form_url}")
        altitude_pattern = re.compile(r"^Gesamthöhe: ([0-9 ]+)m$", re.IGNORECASE)
        previous_altitude = 0
        self.total_altitude = total_altitude

        self.driver.get(self.form_url)
        self.distance = int(self._wait_for(self.distance_selector).text.replace(".", "")) or 0
        info(f"[Radelt] Distance: {self.distance} km")

        # iterate over every timeline to find the highest total_altitude
        for element in self.driver.find_elements(By.CSS_SELECTOR, self.timeline_entries_selector):
            match = altitude_pattern.match(element.text)
            if match:
                previous_altitude = max(int(match.group(1)), previous_altitude)
        self.additional_altitude = total_altitude - previous_altitude

        info(f"[Radelt] Altitude {previous_altitude} m (additional {self.additional_altitude} m)")
        return self.additional_altitude

    def submit_data(self, distance: int, submit: bool = True):
        """
        Submit the total distance and the new additional total_altitude to radelt.at
        :param distance: total Distance 
        :param submit: submit the Form?
        :return: 
        """
        debug(f"submit data using {self.form_url}")
        self.driver.get(self.form_url)
        description = f"Gesamthöhe: {self.total_altitude} m"
        distance_field = self._fill(self.distance_input_selector, str(distance))

        if self.total_altitude:
            self._fill(self.description_input_selector, description)
            self._fill(self.altitude_input_selector, str(self.additional_altitude))

        if not distance > self.distance:
            warning("No changes in distance, won't submit the form...")
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
        debug(f'Loading Selenium Driver {config["default"]["selenium_driver"]} ...')
        SELENIUM_DRIVER = getattr(webdriver, config.get("default", "selenium_driver"))()
    except Exception as error_msg:
        error(f"Error loading config from {config_file}: {error_msg}")
        raise error_msg
    return config


if __name__ == "__main__":
    CONFIG: ConfigParser = ConfigParser()
    RETURN_CODE: int = 0
    logging.basicConfig(level=logging.INFO)
    with Xvfb() as xvfb:
        try:
            CONFIG = get_config()
            logging.basicConfig(level=getattr(logging, CONFIG["default"]["loglevel"].upper()))
        except Exception as error_message:
            error(str(error_message))
            quit(-1)
        assert isinstance(SELENIUM_DRIVER, WebDriver)
        try:
            ebike_connect = eBikeConnect(
                SELENIUM_DRIVER,
                CONFIG["bosch"]["username"],
                CONFIG["bosch"]["password"])
            ebike_connect.get_data()

            radelt_at = RadeltAt(
                SELENIUM_DRIVER,
                CONFIG["radelt"]["username"],
                CONFIG["radelt"]["password"]
            )
            radelt_at.get_data(total_altitude=ebike_connect.altitude)
            radelt_at.submit_data(
                distance=ebike_connect.distance,
                submit=CONFIG.getboolean("radelt", "submit")
            )
        except Exception as error_message:
            error(str(error_message))
            RETURN_CODE = -2
        finally:
            SELENIUM_DRIVER.quit()
    quit(RETURN_CODE)
