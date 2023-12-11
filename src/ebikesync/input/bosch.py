import logging
from ebikesync.seleniumpage import SeleniumPageWithLogin
from ebikesync import plugins


class EBikeConnect(plugins.InputPlugin, SeleniumPageWithLogin):
    """
    Bosch ebike-connect.com to grab the total total_distance and total altitude from your E-Bike
    """
    cookies = [
        {'name': 'do-consent',
         'value': '{%22consent%22:{%22convenience%22:false%2C%22analysis%22:false%2C%22marketing%22:false%2C%22custom%22:[]}%2C%22timeToLive%22:60%2C%22timestamp%22:1702329911490%2C%22version%22:4}',
         'path': '/', 'domain': 'www.ebike-connect.com', 'secure': True, 'httpOnly': False,
         'sameSite': 'Lax'}
    ]
    login_url: str = "https://www.ebike-connect.com/login?lang=de-at"
    fetch_url: str = "https://www.ebike-connect.com/dashboard"
    email_field_selector: str = "#login__email"
    password_field_selector: str = "#login__password"
    distance_selector: str = '#statistic-box-distance span.font-style-h2'
    altitude_selector: str = '#statistic-box-elevation span.font-style-h2'

    def fetch_data(self):
        """fetch all wanted bike data from the dashboard."""
        logging.debug(f"fetching data from {self.fetch_url}")
        distance = self._wait_for(self.distance_selector)
        altitude = self._wait_for(self.altitude_selector)
        self.total_distance = int(distance.text) or 0
        logging.info(f"[BOSCH] Distance: {self.total_distance} km")
        self.total_altitude = int(altitude.text) or 0
        logging.info(f"[BOSCH] Altitude: {self.total_altitude} m")


def register(plugin_name: str) -> None:
    plugins.register_input(plugin_name, EBikeConnect)
