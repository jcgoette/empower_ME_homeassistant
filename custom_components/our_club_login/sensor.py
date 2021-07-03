"""Platform for ourclublogin.com sensor integration."""
import logging
import re
from datetime import datetime, timedelta, timezone

import homeassistant.helpers.config_validation as cv
import homeassistant.util.dt as dt_util
import requests
import voluptuous as vol
from homeassistant.const import CONF_ID, CONF_PASSWORD, CONF_USERNAME
from homeassistant.helpers.entity import Entity

from .const import ATTR_CHECK_IN_DATE, ATTR_DATETIME_FORMAT, ATTR_ICON, ATTR_URL, DOMAIN

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(minutes=15)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Setup ourclublogin.com sensors from a config entry created in the integrations UI."""
    config = hass.data[DOMAIN][config_entry.entry_id]

    club_id = config[CONF_ID]
    username = config[CONF_USERNAME]
    password = config[CONF_PASSWORD]

    our_club_login_data = OurClubLoginData(club_id, username, password)

    async_add_entities(
        [OurClubLoginSensor(our_club_login_data)], update_before_add=True
    )


class OurClubLoginSensor(Entity):
    """Representation of a ourclublogin.com Sensor."""

    def __init__(self, our_club_login_data):
        """Initialize the ourclublogin.com sensor."""
        self._state = None
        self._our_club_login_data = our_club_login_data
        self._data = self._our_club_login_data.data

    @property
    def name(self):
        """Return the name of the ourclublogin.com sensor."""
        return f'Last {self._data.get("ClubName")} Check In'

    @property
    def state(self):
        """Return the state of the ourclublogin.com sensor."""
        return self._data.get("CheckInDate")

    @property
    def icon(self):
        """Return the icon to use in ourclublogin.com frontend."""
        return ATTR_ICON

    def update(self):
        """Update data from ourclublogin.com for the sensor."""
        self._our_club_login_data.update()
        self._data = self._our_club_login_data.data


class OurClubLoginData:
    """Coordinate retrieving and updating data from ourclublogin.com."""

    def __init__(self, club_id, username, password):
        """Initialize the OurClubLoginData object."""
        self._club_id = club_id
        self._username = username
        self._password = password
        self._session = requests.Session()
        self.data = None

    # TODO: OOP this
    def our_club_login_query(self):
        """Query ourclublogin.com for data."""
        params = (("ReturnUrl", f"^%^{self._club_id}"),)

        response = self._session.get(f"{ATTR_URL}/Account/Login", params=params)

        if response.ok:
            _LOGGER.info("Connected to ourclublogin.com")
        else:
            _LOGGER.critical("Could not connect to ourclublogin.com")

        csrf_hidden_token = re.search(
            '"\_\_RequestVerificationToken".+?value\="(.+?)"', str(response.content)
        )
        if csrf_hidden_token:
            csrf_hidden_token = csrf_hidden_token[1]
            _LOGGER.info("Hidden CSRF token acquired")
        else:
            _LOGGER.critical("Could not acquire hidden CSRF token")

        data = {
            "__RequestVerificationToken": csrf_hidden_token,
            "Username": self._username,
            "Password": self._password,
        }

        response = self._session.post(f"{ATTR_URL}/Account/Login", data=data)

        if response.ok:
            _LOGGER.info("Authenticated with ourclublogin.com")
        else:
            _LOGGER.critical("Could not authenticate with ourclublogin.com")

        datetime_local_now = datetime.now().astimezone()
        datetime_local_new_year = datetime(datetime_local_now.year, 1, 1)

        datetime_utc_now = datetime_local_now.astimezone(timezone.utc)
        datetime_utc_new_year = datetime_local_new_year.astimezone(timezone.utc)

        data = {
            "startDate": datetime_utc_new_year.strftime(ATTR_DATETIME_FORMAT),
            "endDate": datetime_utc_now.strftime(ATTR_DATETIME_FORMAT),
        }

        response = self._session.post(
            f"{ATTR_URL}/Checkin/GetCustomerVisits", data=data
        )

        if response.ok:
            _LOGGER.info("Posted to GetCustomerVisits endpoint")
        else:
            _LOGGER.critical("Could not post to GetCustomerVisits endpoint")

        customer_visits = response.json()
        customer_visits.sort(key=lambda item: item[ATTR_CHECK_IN_DATE])  # ensure sorted
        last_customer_visit = customer_visits[-1:][0]

        # TODO: add other data points
        self.data = last_customer_visit

    def update(self):
        """Update data from ourclublogin.com via our_club_login_query."""
        return self.our_club_login_query()
