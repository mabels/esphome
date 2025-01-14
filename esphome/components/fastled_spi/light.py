import esphome.codegen as cg
from esphome.components import fastled_bus
from esphome.components.fastled_bus import CONF_BUS
import esphome.config_validation as cv
from esphome import pins
from esphome.components import fastled_base, fastled_bus_spi
from esphome.const import (
    CONF_CHIPSET,
    CONF_CLOCK_PIN,
    CONF_DATA_PIN,
    CONF_DATA_RATE,
    CONF_NUM_LEDS,
)

AUTO_LOAD = ["fastled_base"]


def _validate(value):
    if CONF_BUS not in value:
        if not (
            CONF_CHIPSET in value
            and CONF_DATA_PIN in value
            and CONF_CLOCK_PIN in value
            and CONF_NUM_LEDS in value
        ):
            raise cv.Invalid(
                f"{CONF_CHIPSET},{CONF_DATA_PIN},{CONF_CLOCK_PIN},{CONF_NUM_LEDS} are required when {CONF_BUS} is not set"
            )
    return value


CONFIG_SCHEMA = cv.All(
    fastled_base.BASE_SCHEMA.extend(
        {
            cv.Optional(CONF_CHIPSET): cv.one_of(*fastled_bus_spi.CHIPSETS, upper=True),
            cv.Optional(CONF_DATA_PIN): pins.internal_gpio_output_pin_number,
            cv.Optional(CONF_CLOCK_PIN): pins.internal_gpio_output_pin_number,
            cv.Optional(CONF_DATA_RATE): cv.frequency,
            cv.Optional(CONF_BUS): cv.use_id(fastled_bus.FastLEDBus),
        }
    ),
    _validate,
    cv.require_framework_version(
        esp8266_arduino=cv.Version(2, 7, 4),
        esp32_arduino=cv.Version(99, 0, 0),
        max_version=True,
        extra_message="Please see note on documentation for FastLED",
    ),
)


async def to_code(config):
    var = await fastled_base.new_fastled_light(config)

    if CONF_BUS not in config:
        data_rate = None
        if CONF_DATA_RATE in config:
            data_rate_khz = int(config[CONF_DATA_RATE] / 1000)
            if data_rate_khz < 1000:
                data_rate = cg.RawExpression(f"DATA_RATE_KHZ({data_rate_khz})")
            else:
                data_rate_mhz = int(data_rate_khz / 1000)
                data_rate = cg.RawExpression(f"DATA_RATE_MHZ({data_rate_mhz})")

        template_args = cg.TemplateArguments(
            cg.RawExpression(config[CONF_CHIPSET]),
            fastled_bus.rgb_order(config),
            config[CONF_DATA_PIN],
            config[CONF_CLOCK_PIN],
            data_rate,
        )
        bus = cg.RawExpression(
            f"""[]() {{
    auto bus = new fastled_bus::FastLEDBus(3, {config[CONF_NUM_LEDS]});
    bus->set_controller(fastled_bus::CLEDControllerFactory::create{template_args}());
    return bus;
}}()"""
        )
    else:
        bus = await cg.get_variable(config[CONF_BUS])

    cg.add(var.set_bus(bus))
    # cg.add(var.add_leds(template_args, config[CONF_NUM_LEDS]))
