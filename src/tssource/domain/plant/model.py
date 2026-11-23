"""Immutable plant values shared by the generator and its application use cases."""

from dataclasses import dataclass
from enum import StrEnum

from tssource.domain.time.site_zone import SiteCode


class ScanClass(StrEnum):
    """Sampling policies and their fixed intervals used for inventory sizing."""

    ONE_SECOND = "periodic_1s"
    FIVE_SECONDS = "periodic_5s"
    TEN_SECONDS = "periodic_10s"
    THIRTY_SECONDS = "periodic_30s"
    ONE_MINUTE = "periodic_60s"
    FIVE_MINUTES = "periodic_300s"
    FIFTEEN_MINUTES = "periodic_900s"
    LAB = "lab"
    EXCEPTION = "report_by_exception"

    @property
    def interval_seconds(self) -> int | None:
        """Return a scheduled interval only for a periodic policy."""
        if self.value.startswith("periodic_"):
            return int(self.value.removeprefix("periodic_").removesuffix("s"))
        return None


@dataclass(frozen=True, slots=True)
class Site:
    """Identify a fictional facility and its established time-core site code."""

    id: str
    code: SiteCode


@dataclass(frozen=True, slots=True)
class Area:
    """Group equipment and control loops within one site's namespace."""

    id: str
    site_id: str
    code: str


@dataclass(frozen=True, slots=True)
class Driver:
    """Identify a shared influence for equipment in one area."""

    id: str
    area_id: str
    kind: str


@dataclass(frozen=True, slots=True)
class Equipment:
    """Identify a unit and associate it with its area and shared driver."""

    id: str
    area_id: str
    driver_id: str
    equipment_class: str
    code: str


@dataclass(frozen=True, slots=True)
class Instrument:
    """Describe one equipment point, its engineering range and capture policy."""

    id: str
    equipment_id: str
    code: str
    measurement: str
    canonical_unit: str
    data_type: str
    range_min: float
    range_max: float
    scan_class: ScanClass

    @property
    def expected_interval_seconds(self) -> int | None:
        """Derive the interval from the policy so the two cannot disagree."""
        return self.scan_class.interval_seconds


@dataclass(frozen=True, slots=True)
class ControlLoop:
    """Connect the measurement, controller and actuator points in one area."""

    id: str
    area_id: str
    measurement_id: str
    controller_id: str
    final_element_id: str


@dataclass(frozen=True, slots=True)
class Stream:
    """Represent directed material flow between two pieces of equipment."""

    id: str
    area_id: str
    source_equipment_id: str
    target_equipment_id: str


@dataclass(frozen=True, slots=True)
class InventoryCount:
    """Count the instruments in one site and sampling policy."""

    site_code: SiteCode
    scan_class: ScanClass
    count: int


@dataclass(frozen=True, slots=True)
class Plant:
    """Hold the ordered topology, point definitions and reconciled inventory."""

    sites: tuple[Site, ...]
    areas: tuple[Area, ...]
    equipment: tuple[Equipment, ...]
    instruments: tuple[Instrument, ...]
    control_loops: tuple[ControlLoop, ...]
    streams: tuple[Stream, ...]
    drivers: tuple[Driver, ...]
    inventory: tuple[InventoryCount, ...]
