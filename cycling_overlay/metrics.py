"""Parsing and unit conversion for a single rider data sample from focus.json."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

MM_S_TO_KMH = 0.0036
MM_S_TO_MPH = 0.00224
METERS_TO_KM = 0.001
METERS_TO_MILES = 0.000621371


@dataclass(frozen=True)
class RiderMetrics:
    power: float
    norm_power: float
    heartrate: float
    avg_heartrate: float
    cadence: float
    avg_cadence: float
    speed_mm_s: float
    distance_m: float
    time_s: int
    tss: float
    calories: float

    @classmethod
    def from_raw(cls, raw: dict[str, Any]) -> RiderMetrics:
        return cls(
            power=raw.get("power", 0),
            norm_power=raw.get("nrmPower", 0),
            heartrate=raw.get("heartrate", 0),
            avg_heartrate=raw.get("avgHeartrate", 0),
            cadence=raw.get("cadence", 0),
            avg_cadence=raw.get("avgCadence", 0),
            speed_mm_s=raw.get("speed", 0),
            distance_m=raw.get("distance", 0),
            time_s=raw.get("time", 0),
            tss=raw.get("tss", 0),
            calories=raw.get("calories", 0),
        )

    @property
    def formatted_time(self) -> str:
        hours, remainder = divmod(int(self.time_s), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    @property
    def distance_km(self) -> float:
        return self.distance_m * METERS_TO_KM

    @property
    def distance_miles(self) -> float:
        return self.distance_m * METERS_TO_MILES

    @property
    def avg_speed_kmh(self) -> float:
        if self.time_s <= 0:
            return 0.0
        return self.distance_km / (self.time_s / 3600)

    @property
    def avg_speed_mph(self) -> float:
        if self.time_s <= 0:
            return 0.0
        return self.distance_miles / (self.time_s / 3600)

    @property
    def speed_kmh(self) -> float:
        return self.speed_mm_s * MM_S_TO_KMH if self.speed_mm_s > 0 else self.avg_speed_kmh

    @property
    def speed_mph(self) -> float:
        return self.speed_mm_s * MM_S_TO_MPH if self.speed_mm_s > 0 else self.avg_speed_mph
