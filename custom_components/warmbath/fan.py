import logging
import asyncio
import threading
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
import homeassistant.components.mqtt as mqtt
from homeassistant.components.fan import (
    FanEntity,
    SPEED_OFF,
    SUPPORT_SET_SPEED,
    SUPPORT_PRESET_MODE,
    PLATFORM_SCHEMA,
    DOMAIN,
)
from homeassistant.const import (CONF_NAME, )

_LOGGER = logging.getLogger(__name__)

CONFIG_DEFAULT_SPEED = 'default'
CONFIG_TOPIC = 'command_topic'
CONFIG_PAYLOAD_CLOSE = 'payload_close'
CONFIG_PAYLOAD_HEAT = 'payload_heat'
CONFIG_PAYLOAD_VENTILATE = 'payload_ventilate'
CONFIG_PAYLOAD_COOL = 'payload_cool'
CONFIG_PAYLOAD_DRY = 'payload_dry'

DEFAULT_MODE = 'Heat'
PRESET_MODES = ['Heat', 'Ventilate', 'Cool', 'Dry']

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_NAME): cv.string,
    vol.Optional(CONFIG_DEFAULT_SPEED, default=DEFAULT_MODE): cv.string,
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
        WarmbathFan(name, mqtt_topic, payload, default_speed)
    ])


class WarmbathFan(FanEntity):
    def __init__(self, name, mqtt_topic, payload, default_speed):
        """Initialize the generic Xiaomi device."""
        self._name = name
        self._mqtt_topic = mqtt_topic
        self._payload = payload
        self._default_speed = default_speed
        self._speed = SPEED_OFF
        self._percentage = None
        self._speed_list = []
        self._preset_modes = PRESET_MODES
        self._preset_mode = None

    @property
    def supported_features(self):
        """Flag supported features."""
        return SUPPORT_PRESET_MODE

    @property
    def should_poll(self):
        """Poll the device."""
        return True

    @property
    def name(self):
        """Return the name of the device if any."""
        return self._name

    @property
    def percentage(self) -> int:
        """Return the current speed."""
        return self._percentage

    @property
    def speed_count(self) -> int:
        """Return the number of speeds the fan supports."""
        return len(PRESET_MODES)

    async def async_set_percentage(self, percentage: int) -> None:
        """Set the speed of the fan, as a percentage."""
        self._percentage = percentage
        self._preset_mode = None
        self.async_write_ha_state()

    @property
    def preset_mode(self) -> str:
        """Return the current preset mode, e.g., auto, smart, interval, favorite."""
        return self._preset_mode

    @property
    def preset_modes(self) -> list:
        """Return a list of available preset modes."""
        return self._preset_modes

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set new preset mode."""
        if preset_mode not in self.preset_modes and preset_mode != SPEED_OFF:
            return
        _LOGGER.debug("Setting the operation mode to: %s", preset_mode)
        self._preset_mode = preset_mode
        self._percentage = None
        self.send_ir(preset_mode)
        self.async_write_ha_state()

    async def async_turn_on(
            self,
            speed: str = None,
            percentage: int = None,
            preset_mode: str = None,
            **kwargs,
    ) -> None:
        """Turn on the entity."""
        if preset_mode is None:
            preset_mode = self._default_speed
            _LOGGER.debug("No speed provided, use: %s" % preset_mode)
        await self.async_set_preset_mode(preset_mode)

    async def async_turn_off(self, **kwargs) -> None:
        """Turn off the entity."""
        _LOGGER.debug("Turn off")
        await self.async_set_preset_mode(SPEED_OFF)

    timer = None

    def send_ir(self, preset_mode):
        payload = self._payload[preset_mode]
        mqtt.publish(self.hass, self._mqtt_topic, payload)
        """auto close in 15mins when turn on."""
        if preset_mode != SPEED_OFF:
            if self.timer is not None:
                if self.timer.is_alive():
                    self.timer.cancel()
            self.timer = threading.Timer(60*15, self.auto_turn_off)
            self.timer.start()

    def auto_turn_off(self) -> None:
        _LOGGER.debug("auto turn off warmbath in 15 mins")
        self.hass.states.set(self.entity_id, SPEED_OFF)
        self._preset_mode = SPEED_OFF
        self.async_schedule_update_ha_state()
