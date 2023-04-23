from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait
from logging import debug, info, warning, error, exception


class SeleniumPageWithLogin:
    """ A simple class to access a webpage via Selenium that needs a login first."""
    cookie_button_selector: str
    email_field_selector: str
    login_url: str
    password_field_selector: str
    html_fetch_timeout: int = 5

    def __init__(self, driver: WebDriver, username: str, password: str, html_fetch_timeout: int = 5) -> None:
        """
        sets the selenium driver and get the URL and completes the login form.
        :param driver: the selenium driver to use
        :param username: username to login
        :param password: password to login
        :param html_fetch_timeout: seconds to wait for an element to appear
        """
        self.driver = driver
        self.login(username, password)
        self.html_fetch_timeout = html_fetch_timeout

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
        return WebDriverWait(self.driver, self.html_fetch_timeout).until(
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
        if hasattr(self, "cookie_button_selector"):
            consent_button = self._wait_for(self.cookie_button_selector)
            consent_button.click()

        self._fill(self.email_field_selector, username)
        password_field = self._fill(self.password_field_selector, password)
        password_field.submit()
