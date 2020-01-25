import logging
import asyncio
import threading
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
import homeassistant.components.mqtt as mqtt
from homeassistant.components.fan import (FanEntity, PLATFORM_SCHEMA, DOMAIN, SUPPORT_SET_SPEED, )
from homeassistant.const import (STATE_ON, STATE_OFF, CONF_NAME, )

_LOGGER = logging.getLogger(__name__)

CONFIG_DEFAULT_SPEED = 'default'
CONFIG_TOPIC = 'command_topic'
CONFIG_PAYLOAD_CLOSE = 'payload_close'
CONFIG_PAYLOAD_HEAT = 'payload_heat'
CONFIG_PAYLOAD_VENTILATE = 'payload_ventilate'
CONFIG_PAYLOAD_COOL = 'payload_cool'
CONFIG_PAYLOAD_DRY = 'payload_dry'

DEFAULT_SPEED = 'Heat'
SPEED_LIST = ['Heat', 'Ventilate', 'Cool', 'Dry']

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_NAME): cv.string,
    vol.Optional(CONFIG_DEFAULT_SPEED, default=DEFAULT_SPEED): cv.string,
    vol.Required(CONFIG_TOPIC): cv.string,
    vol.Required(CONFIG_PAYLOAD_CLOSE): cv.string,
    vol.Required(CONFIG_PAYLOAD_HEAT): cv.string,
    vol.Required(CONFIG_PAYLOAD_VENTILATE): cv.string,
    vol.Required(CONFIG_PAYLOAD_COOL): cv.string,
    vol.Required(CONFIG_PAYLOAD_DRY): cv.string,
})


def setup_platform(hass, config, add_devices_callback, discovery_info=None):

    name = config.get(CONF_NAME)
    mqtt_topic = config.get(CONFIG_TOPIC)
    default_speed = config.get(CONFIG_DEFAULT_SPEED)
    payload = {}
    payload['off'] = config.get(CONFIG_PAYLOAD_CLOSE)
    payload['Heat'] = config.get(CONFIG_PAYLOAD_HEAT)
    payload['Ventilate'] = config.get(CONFIG_PAYLOAD_VENTILATE)
    payload['Cool'] = config.get(CONFIG_PAYLOAD_COOL)
    payload['Dry'] = config.get(CONFIG_PAYLOAD_DRY)

    add_devices_callback([
        WarmbathFan(name, mqtt_topic, payload, default_speed, SPEED_LIST)
    ])


class WarmbathFan(FanEntity):
    def __init__(self, name, mqtt_topic, payload, default_speed, speed_list):
        """Initialize the generic Xiaomi device."""
        self._name = name
        self._mqtt_topic = mqtt_topic
        self._payload = payload
        self._speed = STATE_OFF
        self._default_speed = default_speed
        self._speed_list = speed_list

    @property
    def supported_features(self):
        """Flag supported features."""
        return SUPPORT_SET_SPEED

    @property
    def name(self):
        """Return the name of the device if any."""
        return self._name

    @property
    def speed(self):
        """Flag supported features."""
        return self._speed

    @property
    def speed_list(self) -> list:
        """Get the list of available speeds."""
        return self._speed_list

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
        yield from self.async_set_speed(STATE_OFF)

    @asyncio.coroutine
    def async_set_speed(self, speed: str) -> None:
        """Set the speed of the fan."""
        if self.supported_features & SUPPORT_SET_SPEED == 0:
            return
        _LOGGER.debug("Set speed: %s" % speed)
        self._speed = speed
        yield from self.async_send_ir()
        self.async_schedule_update_ha_state()

    timer = None

    @asyncio.coroutine
    def async_send_ir(self):
        payload =  self._payload[self._speed]
        mqtt.publish(self.hass, self._mqtt_topic, payload)
        """auto close in 15mins when turn on."""
        if self._speed != STATE_OFF:
            if self.timer is not None:
                if self.timer.is_alive():
                    self.timer.cancel()
            self.timer = threading.Timer(60*15, self.auto_turn_off)
            self.timer.start()

    def auto_turn_off(self) -> None:
        _LOGGER.debug("auto turn off warmbath in 15 mins")
        self.hass.states.set(self.entity_id, STATE_OFF)
        self._speed = STATE_OFF
        self.async_schedule_update_ha_state()
