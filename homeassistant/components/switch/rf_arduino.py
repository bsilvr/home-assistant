"""
Allows to configure a switch using a 433MHz module via an Arduino custom
firmware.

"""
import logging

import voluptuous as vol

from homeassistant.components.switch import (SwitchDevice, PLATFORM_SCHEMA)
from homeassistant.const import (CONF_DEVICE, CONF_SWITCHES, CONF_NAME)
import homeassistant.helpers.config_validation as cv

# The domain of your component. Should be equal to the name of your component.
DOMAIN = "rf_arduino"

# List of component names (string) your component depends upon.
DEPENDENCIES = []

REQUIREMENTS = ['RF433==0.1.6']

_LOGGER = logging.getLogger(__name__)

CONF_ADDRESS = "address"
CONF_HOME_EASY = "home_easy"

HOME_EASY_SWITCH_SCHEMA = vol.Schema({
    vol.Optional(CONF_NAME): cv.string,
    vol.Required(CONF_ADDRESS): cv.string,
    vol.Required(CONF_DEVICE): cv.string,
})

HOME_EASY_SCHEMA = vol.Schema({cv.string: HOME_EASY_SWITCH_SCHEMA})

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_DEVICE): cv.string,
    vol.Required(CONF_SWITCHES): vol.Schema({CONF_HOME_EASY: HOME_EASY_SCHEMA})
})


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup our skeleton component."""
    from RF433.driver.arduino import Arduino433

    Arduino433.list_devices()

    device = config.get(CONF_DEVICE)
    switches = config.get(CONF_SWITCHES)
    rfdevice = None
    try:
        rfdevice = Arduino433(device)
    except:
        _LOGGER.error("The device provided in the configuration is busy or \
                        does not exist")
        return

    devices = []
    for protocol, protocol_switches in switches.items():
        for dev_name, properties in protocol_switches.items():
            devices.append(
                ArduinoRFSwitch(
                    hass,
                    properties.get(CONF_NAME, dev_name),
                    protocol,
                    properties.get(CONF_ADDRESS),
                    properties.get(CONF_DEVICE),
                    rfdevice
                )
            )
    if devices:
        rfdevice.open()

    _LOGGER.info("The component rf_arduino has started")
    add_devices(devices)


class ArduinoRFSwitch(SwitchDevice):
    """Representation of an Arduino RF switch."""

    def __init__(self, hass, name, protocol, address, device, rfdevice):
        """Initialize the switch."""
        self._hass = hass
        self._name = name
        self._state = False
        self._rfdevice = rfdevice

        if protocol == CONF_HOME_EASY:
            from RF433.protocols.home_easy import HomeEasy
            self._protocol = HomeEasy(address, device)

    @property
    def should_poll(self):
        """No polling needed."""
        return False

    @property
    def name(self):
        """Return the name of the switch."""
        return self._name

    @property
    def is_on(self):
        """Return true if device is on."""
        return self._state

    def turn_on(self):
        """Turn the switch on."""
        self._state = True
        self._protocol.set_onoff(self._state)
        self._protocol.generate_bit_code()
        self._rfdevice.send(self._protocol.get_transmit_data())
        self.update_ha_state()

    def turn_off(self):
        """Turn the switch off."""
        self._state = False
        self._protocol.set_onoff(self._state)
        self._protocol.generate_bit_code()
        self._rfdevice.send(self._protocol.get_transmit_data())
        self.update_ha_state()
