import logging
import voluptuous as vol
import homeassistant.loader as loader
from homeassistant.helpers.event import track_state_change
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

DOMAIN = 'warmbath'
DEPENDENCIES = ['mqtt']

CONFIG_TOPIC = 'command_topic'
CONFIG_PAYLOAD_CLOSE = 'payload_close'
CONFIG_PAYLOAD_HEAT = 'payload_heat'
CONFIG_PAYLOAD_VENTILATE = 'payload_ventilate'
CONFIG_PAYLOAD_COOL = 'payload_cool'
CONFIG_PAYLOAD_DRY = 'payload_dry'

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONFIG_TOPIC): cv.string,
        vol.Required(CONFIG_PAYLOAD_CLOSE): cv.string,
        vol.Required(CONFIG_PAYLOAD_HEAT): cv.string,
        vol.Required(CONFIG_PAYLOAD_VENTILATE): cv.string,
        vol.Required(CONFIG_PAYLOAD_COOL): cv.string,
        vol.Required(CONFIG_PAYLOAD_DRY): cv.string,
    })
}, extra=vol.ALLOW_EXTRA)

def setup(hass, config):
    hass.states.set('warmbath.panasonic', 'close')

    mqtt = loader.get_component(hass, 'mqtt')

    def state_changed(entity_id, old_state, new_state):

        if old_state is None or new_state is None:
            return
        if old_state.state != new_state.state:
            payload = ''
            if new_state.state == 'close':
                payload = config[DOMAIN][CONFIG_PAYLOAD_CLOSE]
            if new_state.state == 'heat':
                payload = config[DOMAIN][CONFIG_PAYLOAD_HEAT]
            if new_state.state == 'ventilate':
                payload = config[DOMAIN][CONFIG_PAYLOAD_VENTILATE]
            if new_state.state == 'cool':
                payload = config[DOMAIN][CONFIG_PAYLOAD_COOL]
            if new_state.state == 'dry':
                payload = config[DOMAIN][CONFIG_PAYLOAD_DRY]
            mqtt.publish(hass, config[DOMAIN][CONFIG_TOPIC], payload)

    track_state_change(hass, ['warmbath.panasonic'], state_changed)

    return True

@property
def device_state_attributes(self):
    """Return device specific state attributes."""
    return self._attributes