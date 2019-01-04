import logging
import asyncio
import voluptuous as vol
import homeassistant.loader as loader
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.event import track_state_change
from homeassistant.components.fan import (FanEntity, PLATFORM_SCHEMA,
                                          SUPPORT_SET_SPEED, DOMAIN, )
from homeassistant.const import (STATE_OFF, CONF_NAME, CONF_HOST, CONF_MAC, CONF_TIMEOUT, CONF_CUSTOMIZE)

_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = ['mqtt']

CONFIG_TOPIC = 'command_topic'
CONFIG_PAYLOAD_CLOSE = 'payload_close'
CONFIG_PAYLOAD_HEAT = 'payload_heat'
CONFIG_PAYLOAD_VENTILATE = 'payload_ventilate'
CONFIG_PAYLOAD_COOL = 'payload_cool'
CONFIG_PAYLOAD_DRY = 'payload_dry'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_NAME): cv.string,
    vol.Required(CONFIG_TOPIC): cv.string,
    vol.Required(CONFIG_PAYLOAD_CLOSE): cv.string,
    vol.Required(CONFIG_PAYLOAD_HEAT): cv.string,
    vol.Required(CONFIG_PAYLOAD_VENTILATE): cv.string,
    vol.Required(CONFIG_PAYLOAD_COOL): cv.string,
    vol.Required(CONFIG_PAYLOAD_DRY): cv.string,
})


def setup_platform(hass, config, add_devices_callback, discovery_info=None):
    name = config.get(CONF_NAME)

#    hass.states.set('fan.warmbath', 'close')

    mqtt = loader.get_component(hass, 'mqtt')

    def state_changed(entity_id, old_state, new_state):

        if old_state is None or new_state is None:
            return
        _LOGGER.error('entity_id %s', entity_id)
        _LOGGER.error('old_state %s', old_state)
        _LOGGER.error('new_state %s', new_state)
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

    track_state_change(hass, ['fan.warmbath'], state_changed)

    add_devices_callback([
        WarmbathFan(hass, 'warmbath')
    ])


class WarmbathFan(FanEntity):
    def __init__(self, hass, name):
        """Initialize the generic Xiaomi device."""
        self._name = name
        self._speed = 'ventilate'
        self._default_speed = 'ventilate'

    @property
    def name(self):
        """Return the name of the device if any."""
        return self._name

    @property
    def supported_features(self):
        """Flag supported features."""
        return SUPPORT_SET_SPEED

    @property
    def speed_list(self) -> list:
        """Get the list of available speeds."""
        return ['heat', 'ventilate', 'cool', 'dry']

    @asyncio.coroutine
    def async_turn_on(self, speed: str=None) -> None:
        """Turn on the entity."""
        _LOGGER.debug("Turn on with speed: %s" % speed)
        if speed is None:
            speed = self._default_speed
            _LOGGER.debug("No speed provided, use: %s" % speed)
        yield from self.async_set_speed(speed)

    @asyncio.coroutine
    def async_turn_off(self) -> None:
        """Turn off the entity."""
        _LOGGER.debug("Turn off")
        #self.oscillate(False)
        yield from self.async_set_speed(STATE_OFF)

    @asyncio.coroutine
    def async_set_speed(self, speed: str) -> None:
        """Set the speed of the fan."""
        _LOGGER.debug("Set speed: %s" % speed)
        self._speed = speed
        yield from self.async_send_ir_after_delay()
        self.async_schedule_update_ha_state()

    @asyncio.coroutine
    def async_send_ir_after_delay(self):
        _LOGGER.error("speed %s", self._speed)


