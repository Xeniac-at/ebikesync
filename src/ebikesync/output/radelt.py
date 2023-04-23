import re
from ebikesync.seleniumpage import SeleniumPageWithLogin, By
from logging import debug, info, warning, error, exception


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
