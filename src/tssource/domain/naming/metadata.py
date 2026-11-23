"""Provide fixture vocabulary and known alternate spellings for reported units."""

from tssource.domain.time.site_zone import SiteCode

_PORTUGUESE = {
    "reaction_temperature": "temperatura de reação",
    "reflux_flow": "vazão de refluxo",
    "outlet_temperature": "temperatura de saída",
    "discharge_pressure": "pressão de descarga",
    "liquid_level": "nível de líquido",
    "firebox_temperature": "temperatura da fornalha",
    "interface_level": "nível de interface",
    "header_flow": "vazão do coletor",
    "controller_output": "saída do controlador",
    "actuator_position": "posição do atuador",
    "temperature": "temperatura",
    "pressure": "pressão",
    "flow": "vazão",
    "specific_energy": "energia específica",
    "control_mode": "modo de controle",
    "alarm_active": "alarme ativo",
    "setpoint_fraction": "fração do ponto de ajuste",
    "sample_ph": "pH da amostra",
    "water_content": "teor de água",
    "chloride_content": "teor de cloreto",
    "solids_content": "teor de sólidos",
    "sample_density": "densidade da amostra",
    "conductivity": "condutividade",
    "turbidity": "turbidez",
}
_ALTERNATE_UNITS = {
    "%": "pct",
    "degC": "°C",
    "kPa": "kpa",
    "m3/h": "m³/h",
    "kWh/m3": "kWh/m³",
    "1": "dimensionless",
    "mg/L": "mg/l",
    "kg/m3": "kg/m³",
    "uS/cm": "µS/cm",
    "NTU": "ntu",
}


def describe(measurement: str, site: SiteCode) -> str:
    """Return synthetic vocabulary for Brazil in Portuguese and other sites in English."""
    if site is SiteCode.BRAZIL:
        label = _PORTUGUESE.get(measurement)
        return f"Medição de {label}" if label else ""
    return f"{measurement.replace('_', ' ').capitalize()} measurement"


def alternate_unit(canonical_unit: str) -> str:
    """Return a spelling variant with the same units, or empty if no variant is defined."""
    return _ALTERNATE_UNITS.get(canonical_unit, "")
