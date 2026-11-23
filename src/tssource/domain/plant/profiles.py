"""Versioned fixture data for plant sizing and the equipment point templates."""

from dataclasses import dataclass

from tssource.domain.plant.model import ScanClass
from tssource.domain.time.site_zone import SiteCode


@dataclass(frozen=True, slots=True)
class SiteProfile:
    """Declare the number of ten-point units to allocate to each of five areas."""

    site_code: SiteCode
    units_by_area: tuple[int, ...]


SITE_PROFILES = (
    SiteProfile(SiteCode.BRAZIL, (14, 14, 14, 14, 14)),
    SiteProfile(SiteCode.US_GULF_COAST, (9, 9, 9, 9, 9)),
    SiteProfile(SiteCode.BELGIUM, (7, 7, 7, 7, 7)),
    SiteProfile(SiteCode.CHINA, (7, 7, 7, 7, 7)),
    SiteProfile(SiteCode.INDIA, (4, 4, 4, 4, 4)),
)


@dataclass(frozen=True, slots=True)
class PointTemplate:
    """Describe a point before binding it to equipment and assigning an ID."""

    code: str
    measurement: str
    canonical_unit: str
    range_min: float
    range_max: float
    scan_class: ScanClass
    data_type: str = "float64"


@dataclass(frozen=True, slots=True)
class EquipmentTemplate:
    """Describe the point set and optional loop roles of an equipment class."""

    equipment_class: str
    prefix: str
    points: tuple[PointTemplate, ...]
    loop_roles: tuple[str, str, str] | None


_TEMPERATURE = PointTemplate("TI", "temperature", "degC", -40, 900, ScanClass.THIRTY_SECONDS)
_PRESSURE = PointTemplate("PI", "pressure", "kPa", 0, 10000, ScanClass.ONE_MINUTE)
_ALARM = PointTemplate("ALM", "alarm_active", "1", 0, 1, ScanClass.EXCEPTION, "bool")

_CONTROL_POINTS = (
    PointTemplate("OUT", "controller_output", "%", 0, 100, ScanClass.FIVE_SECONDS),
    PointTemplate("POS", "actuator_position", "%", 0, 100, ScanClass.TEN_SECONDS),
    _TEMPERATURE,
    _PRESSURE,
    PointTemplate("FI", "flow", "m3/h", 0, 500, ScanClass.FIVE_MINUTES),
    PointTemplate("EI", "specific_energy", "kWh/m3", 0, 100, ScanClass.FIFTEEN_MINUTES),
    PointTemplate("MODE", "control_mode", "1", 0, 2, ScanClass.EXCEPTION, "int32"),
    _ALARM,
    PointTemplate("SP", "setpoint_fraction", "%", 0, 100, ScanClass.THIRTY_SECONDS),
)


def _controlled(
    equipment_class: str, prefix: str, measurement: str, unit: str, maximum: float
) -> EquipmentTemplate:
    """Use the shared control layout and give each equipment type its own primary point."""
    primary = PointTemplate("PV", measurement, unit, 0, maximum, ScanClass.ONE_SECOND)
    return EquipmentTemplate(
        equipment_class, prefix, (primary, *_CONTROL_POINTS), ("PV", "OUT", "POS")
    )


EQUIPMENT_TEMPLATES = (
    _controlled("reactor", "R", "reaction_temperature", "degC", 450),
    _controlled("column", "C", "reflux_flow", "m3/h", 250),
    _controlled("heat_exchanger", "E", "outlet_temperature", "degC", 350),
    _controlled("pump", "P", "discharge_pressure", "kPa", 2500),
    _controlled("compressor", "K", "discharge_pressure", "kPa", 8000),
    _controlled("tank", "T", "liquid_level", "%", 100),
    _controlled("furnace", "F", "firebox_temperature", "degC", 900),
    _controlled("separator", "S", "interface_level", "%", 100),
    _controlled("valve_station", "V", "header_flow", "m3/h", 500),
    EquipmentTemplate(
        "analyser_house",
        "AH",
        (
            PointTemplate("PH", "sample_ph", "1", 0, 14, ScanClass.LAB),
            PointTemplate("H2O", "water_content", "mg/L", 0, 30000, ScanClass.LAB),
            PointTemplate("CL", "chloride_content", "mg/L", 0, 1500, ScanClass.LAB),
            PointTemplate("SOL", "solids_content", "mg/L", 0, 30000, ScanClass.LAB),
            PointTemplate("RHO", "sample_density", "kg/m3", 500, 2000, ScanClass.LAB),
            PointTemplate("AI", "conductivity", "uS/cm", 0, 10000, ScanClass.ONE_MINUTE),
            PointTemplate("QI", "turbidity", "NTU", 0, 1000, ScanClass.FIVE_MINUTES),
            _TEMPERATURE,
            _PRESSURE,
            _ALARM,
        ),
        None,
    ),
)
