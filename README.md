# HomeAssistant component: `attributes`
[![Validate](https://github.com/pilotak/homeassistant-attributes/workflows/Validate/badge.svg)](https://github.com/pilotak/homeassistant-attributes/actions)
[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/custom-components/hacs)

The `attributes` platform supports sensors which break out a specified `attribute` from other entities.

To enable the `attributes` sensor in your installation, add the following to your `configuration.yaml` file:

```yaml
# Example configuration.yaml entry
sensor:  
  - platform: attributes
    friendly_name: "Batteries"
    attribute: battery_level
    device_class: battery
    entities:
      - sensor.myslipo_1_0
      - sensor.myslipo_2_0
      - sensor.myslipo_3_0
      - sensor.myslipo_4_0
      
  - platform: attributes
    friendly_name: "Last changed"
    attribute: last_triggered
    icon: 'mdi:clock'
    time_format: '%e %B - %H:%M:%S'
    entities:
      - automation.temp_changed
```

Configuration variables:

- **entities** (*Required*): A list of entity IDs that you want to read attributes from.
- **attribute** (*Required*): Which attribute to extract from defined entity IDs.
- **friendly_name** (*Optional*): Name to use in the Frontend *(will be the same for all entities specified)*.
- **icon** (*Optional*): Icon to use in the Frontend.
- **device_class** (*Optional*): Defines the device_class, if not specified it will be the same as parent.
- **unit_of_measurement** (*Optional*): Defines the units of measurement of the sensor, if any.
- **round_to** (*Optional*): Round numbers to 'x' decimals, if zero it will become whole number. Skip this field if you extracting a string or you want to leave the value as it is.
- **value_template** (*Optional*): In case you need to do a math with the value ie. offset, bit gain, etc. *(will be the same for all entities specified)*.
- **time_format** (*Optional*): **`strftime`** type string to beautify time attribute output. Applicable only when attribute `last_changed` or `last_triggered` is selected. Cheatsheet for strftime formatting  [here](http://strftime.ninja/).

## Install via [HACS](https://github.com/custom-components/hacs)
You can find this integration in the community store.

## Install manually
You need to copy the `attributes` folder from this repo to the `custom_components` folder in the root of your configuration. The file tree should look like this:
```
└── ...
└── configuration.yaml
└── custom_components
    └── attributes
        └── __init__.py
        └── manifest.json
        └── sensor.py
```

>__Note__: if the `custom_components` directory does not exist, you need to create it.

## Examples
This example shows how to extract the `battery_level` attribute.

```yaml
sensor:
  - platform: attributes
    friendly_name: "Batteries"
    attribute: battery_level
    unit_of_measurement: "%"
    entities:
      - sensor.test1
      - sensor.test2
      - sensor.test3
```

>If an attribute is __`battery`__ or __`battery_level`__ and you don't specify __`icon`__ or __`device_class`__ is not `battery`, the following icon_template is applied (fullness). The result is that the battery icon becomes as full as the battery based on percentage.

```yaml
{% if batt == 'unknown' %}
    {% if batt > 95 %}
        mdi:battery
    {% elif batt > 85 %}
        mdi:battery-90
    {% elif batt > 75 %}
        mdi:battery-80
    {% elif batt > 65 %}
        mdi:battery-70
    {% elif batt > 55 %}
        mdi:battery-60
    {% elif batt > 45 %}
        mdi:battery-50
    {% elif batt > 35 %}
        mdi:battery-40
    {% elif batt > 25 %}
        mdi:battery-30
    {% elif batt > 15 %}
        mdi:battery-20
    {% elif batt > 10 %}
        mdi:battery-10
    {% else %}
        mdi:battery-outline
    {% endif %}
{% else %}
    mdi:battery-unknown
{% endif %}
```

This example shows how to extract the `last_triggered` attribute in human-readable format.

```yaml
sensor:
  - platform: attributes
    friendly_name: "Last changed"
    attribute: last_triggered
    icon: 'mdi:clock'
    time_format: '%e %B - %H:%M:%S'
    entities:
      - automation.dummy_changed
```
>If you select attribute __`last_changed`__ or __`last_triggered`__ and you specify time_format, your datetime will get translated to your local timezone and will be formatted like `strftime()` e.g., ***2017-08-08T13:14:21.651894+00:00*** gets translated into the specified strftime format with timezone applied. The result would be: ***8 August 15:14:21*** if your timezone is UTC+2
