# """
# Creates a sensor that breaks out attribute of defined entities.
# """
import asyncio
import logging

import voluptuous as vol

from homeassistant.core import callback
from homeassistant.components.sensor import (
    ENTITY_ID_FORMAT,
    PLATFORM_SCHEMA,
    DEVICE_CLASSES_SCHEMA,
    STATE_CLASSES_SCHEMA,
    CONF_STATE_CLASS,
)
from homeassistant.const import (
    ATTR_FRIENDLY_NAME,
    CONF_UNIT_OF_MEASUREMENT,
    ATTR_ICON,
    CONF_ENTITIES,
    CONF_DEVICE_CLASS,
    EVENT_HOMEASSISTANT_START,
    STATE_UNKNOWN,
    STATE_UNAVAILABLE,
    CONF_VALUE_TEMPLATE,
)
from homeassistant.exceptions import TemplateError
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import async_generate_entity_id
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers import template as template_helper
from homeassistant.util import slugify


__version__ = '1.3.0'

_LOGGER = logging.getLogger(__name__)

CONF_ATTRIBUTE = "attribute"
CONF_TIME_FORMAT = "time_format"
CONF_ROUND_TO = "round_to"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(ATTR_ICON): cv.string,
    vol.Optional(ATTR_FRIENDLY_NAME): cv.string,
    vol.Optional(CONF_DEVICE_CLASS): DEVICE_CLASSES_SCHEMA,
    vol.Optional(CONF_UNIT_OF_MEASUREMENT): cv.string,
    vol.Optional(CONF_TIME_FORMAT): cv.string,
    vol.Optional(CONF_ROUND_TO): cv.positive_int,
    vol.Optional(CONF_VALUE_TEMPLATE): cv.string,
    vol.Optional(CONF_STATE_CLASS): STATE_CLASSES_SCHEMA,
    vol.Required(CONF_ATTRIBUTE): cv.string,
    vol.Required(CONF_ENTITIES): cv.entity_ids
})


async def async_setup_platform(
    hass,
    config,
    async_add_devices,
    discovery_info=None
):
    """Set up the attributes sensors."""
    _LOGGER.info("Starting attribute sensor")
    sensors = []

    for device in config[CONF_ENTITIES]:
        attr = config.get(CONF_ATTRIBUTE)
        time_format = str(config.get(CONF_TIME_FORMAT))

        if (attr == "last_triggered" or
                attr == "last_changed") and time_format:

            state_template = ("{{% if states('{0}') != '{3}' "
                              "and states('{0}') != '{4}' %}}\
                              {{{{ as_timestamp(state_attr('{0}', '{1}'))\
                              | int | timestamp_local()\
                              | timestamp_custom('{2}') }}}}\
                              {{% else %}} {3} {{% endif %}}").format(
                device, attr, time_format, STATE_UNKNOWN, STATE_UNAVAILABLE)
        else:
            round_to = config.get(CONF_ROUND_TO, None)
            additional_template = config.get(CONF_VALUE_TEMPLATE, "")

            state_template = "{{% if states('{0}') != '{2}' "
            state_template += "and states('{0}') != '{5}' %}}"

            if round_to is None:
                state_template += "{{{{ state_attr('{0}', '{1}') {4} }}}}"
            elif round_to > 0:
                state_template += "{{{{ (state_attr('{0}', '{1}') | float)"
                state_template += " | round({3}) {4} }}}}"
            else:
                state_template += "{{{{ state_attr('{0}', '{1}')"
                state_template += " | int {4} }}}}"

            state_template += "{{% else %}} {2} {{% endif %}}"
            state_template = state_template.format(
                device, attr, STATE_UNKNOWN, round_to, additional_template,
                STATE_UNAVAILABLE)

        _LOGGER.info("Adding attribute: %s of entity: %s", attr, device)
        _LOGGER.debug("Applying template: %s", state_template)

        state_template = template_helper.Template(state_template)
        state_template.hass = hass

        icon = str(config.get(ATTR_ICON))

        device_state = hass.states.get(device)

        if device_state is not None:
            device_friendly_name = device_state.attributes.get('friendly_name')
        else:
            device_friendly_name = device.split(".", 1)[1]

        friendly_name = config.get(ATTR_FRIENDLY_NAME, None)

        if device_state is not None:
            device_class = config.get(
                CONF_DEVICE_CLASS, device_state.attributes.get('device_class'))
        else:
            device_class = config.get(CONF_DEVICE_CLASS, None)

        state_class = config.get(CONF_STATE_CLASS, None)

        unit_of_measurement = config.get(CONF_UNIT_OF_MEASUREMENT)

        if icon.startswith('mdi:') or icon.startswith('hass:'):
            _LOGGER.debug("Applying user defined icon: '%s'", icon)
            new_icon = ("{{% if states('{0}') != '{2}' "
                        "and states('{0}') != '{3}' %}} {1} {{% else %}}\
                mdi:eye {{% endif %}}").format(device, icon, STATE_UNKNOWN,
                                               STATE_UNAVAILABLE)

            new_icon = template_helper.Template(new_icon)
            new_icon.hass = hass
        elif (device_class is None or device_class != "battery") \
                and attr == "battery" or attr == "battery_level":
            _LOGGER.debug("Applying battery icon template")

            new_icon = ("{{% if states('{0}') != '{2}' "
                        "and states('{0}') != '{3}' %}}\
                {{% set batt = states.{0}.attributes['{1}']|int %}}\
                {{% if batt == 'unknown' %}}\
                mdi:battery-unknown\
                {{% elif batt > 95 %}}\
                mdi:battery\
                {{% elif batt > 85 %}}\
                mdi:battery-90\
                {{% elif batt > 75 %}}\
                mdi:battery-80\
                {{% elif batt > 65 %}}\
                mdi:battery-70\
                {{% elif batt > 55 %}}\
                mdi:battery-60\
                {{% elif batt > 45 %}}\
                mdi:battery-50\
                {{% elif batt > 35 %}}\
                mdi:battery-40\
                {{% elif batt > 25 %}}\
                mdi:battery-30\
                {{% elif batt > 15 %}}\
                mdi:battery-20\
                {{% elif batt > 10 %}}\
                mdi:battery-10\
                {{% else %}}\
                mdi:battery-outline\
                {{% endif %}}\
            {{% else %}}\
            mdi:battery-unknown\
            {{% endif %}}").format(
                device, attr, STATE_UNKNOWN, STATE_UNAVAILABLE)
            new_icon = template_helper.Template(str(new_icon))
            new_icon.hass = hass
        else:
            _LOGGER.debug("No icon applied")
            new_icon = None

        sensors.append(
            AttributeSensor(
                hass,
                ("{0}_{1}").format(device.split(".", 1)[1], attr),
                friendly_name,
                device_friendly_name,
                device_class,
                state_class,
                unit_of_measurement,
                state_template,
                new_icon,
                device)
        )
    if not sensors:
        _LOGGER.error("No sensors added")
        return False

    async_add_devices(sensors)
    return True


class AttributeSensor(RestoreEntity):
    """Representation of a Attribute Sensor."""

    def __init__(self, hass, device_id, friendly_name, device_friendly_name,
                 device_class, state_class, unit_of_measurement,
                 state_template, icon_template, entity_id):
        """Initialize the sensor."""
        self.hass = hass
        self.entity_id = async_generate_entity_id(ENTITY_ID_FORMAT, device_id,
                                                  hass=hass)
        self._name = friendly_name if friendly_name is not None \
            else device_friendly_name
        self._friendly_name = friendly_name
        self._unique_id = slugify(f"{entity_id}_{device_id}")
        self._attr_device_class = device_class
        self._attr_state_class = state_class
        self._unit_of_measurement = unit_of_measurement
        self._template = state_template
        self._state = None
        self._icon_template = icon_template
        self._icon = None
        self._entity = entity_id

    async def async_added_to_hass(self):
        """Register callbacks."""
        state = await self.async_get_last_state()
        if state:
            self._state = state.state

        @callback
        def template_sensor_state_listener(entity, old_state, new_state):
            """Handle device state changes."""
            self.hass.async_create_task(self.async_update_ha_state(True))

        @callback
        def template_sensor_startup(event):
            """Update on startup."""
            async_track_state_change_event(
                self.hass, self._entity, template_sensor_state_listener)

            self.hass.async_create_task(self.async_update_ha_state(True))

        self.hass.bus.async_listen_once(
            EVENT_HOMEASSISTANT_START, template_sensor_startup)

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def unique_id(self):
        """Return the unique ID of the sensor."""
        return self._unique_id

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def icon(self):
        """Return the icon to use in the frontend, if any."""
        return self._icon

    @property
    def unit_of_measurement(self):
        """Return the unit_of_measurement of the device."""
        return self._unit_of_measurement

    @property
    def should_poll(self):
        """No polling needed."""
        return False

    async def async_update(self):
        """Update the state from the template and the friendly name."""

        entity_state = self.hass.states.get(self._entity)
        if self._friendly_name is None and entity_state is not None:
            dev_friendly_name = entity_state.attributes.get('friendly_name')
            if dev_friendly_name is not None:
                self._name = dev_friendly_name

        try:
            self._state = self._template.async_render()
        except TemplateError as ex:
            if ex.args and (
                    ex.args[0].startswith(
                        "UndefinedError: 'None' has no attribute") or
                    ex.args[0].startswith(
                        "UndefinedError: 'mappingproxy object' has "
                        "no attribute")):
                # Common during HA startup - so just a warning
                _LOGGER.warning('Could not render attribute sensor for %s,'
                                ' the state is unknown.', self._entity)
                return
            self._state = None
            _LOGGER.error('Could not attribute sensor for %s: %s',
                          self._entity, ex)

        if self._icon_template is not None:
            try:
                self._icon = self._icon_template.async_render()
            except TemplateError as ex:
                if ex.args and (
                        ex.args[0].startswith(
                            "UndefinedError: 'None' has no attribute") or
                        ex.args[0].startswith(
                            "UndefinedError: 'mappingproxy object' has "
                            "no attribute")):
                    # Common during HA startup - so just a warning
                    _LOGGER.warning('Could not render icon template %s,'
                                    ' the state is unknown.', self._name)
                    return
                self._icon = super().icon
                _LOGGER.error('Could not render icon template %s: %s',
                              self._name, ex)
