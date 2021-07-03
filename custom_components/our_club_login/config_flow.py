import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_ID, CONF_PASSWORD, CONF_USERNAME

from .const import ATTR_TITLE, DOMAIN


# TODO: better validation of data
# TODO: translations
class OurClubLoginConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    async def async_step_user(self, user_input):
        if user_input is not None:
            return self.async_create_entry(title=ATTR_TITLE, data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ID): cv.string,
                    vol.Required(CONF_USERNAME): cv.string,
                    vol.Required(CONF_PASSWORD): cv.string,
                }
            ),
        )
