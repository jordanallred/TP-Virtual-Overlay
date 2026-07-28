from cycling_overlay.metrics import RiderMetrics


def test_from_raw_defaults_missing_keys():
    m = RiderMetrics.from_raw({})
    assert m.power == 0
    assert m.heartrate == 0
    assert m.cadence == 0
    assert m.time_s == 0
    assert m.tss == 0
    assert m.calories == 0


def test_formatted_time_zero():
    m = RiderMetrics.from_raw({"time": 0})
    assert m.formatted_time == "00:00:00"


def test_formatted_time_hours_minutes_seconds():
    m = RiderMetrics.from_raw({"time": 3725})  # 1h 2m 5s
    assert m.formatted_time == "01:02:05"


def test_distance_conversions():
    m = RiderMetrics.from_raw({"distance": 1000})
    assert m.distance_km == 1.0
    assert abs(m.distance_miles - 0.621371) < 1e-6


def test_avg_speed_zero_when_no_elapsed_time():
    m = RiderMetrics.from_raw({"time": 0, "distance": 500})
    assert m.avg_speed_kmh == 0.0
    assert m.avg_speed_mph == 0.0


def test_speed_uses_instantaneous_reading_when_positive():
    m = RiderMetrics.from_raw({"speed": 10000, "distance": 1000, "time": 100})
    assert m.speed_kmh == 10000 * 0.0036
    assert m.speed_mph == 10000 * 0.00224


def test_speed_falls_back_to_average_when_instantaneous_is_zero():
    # TPVirtual reports speed=0 while coasting/stopped; the overlay should show
    # the ride average instead of a misleading "0 km/h".
    m = RiderMetrics.from_raw({"speed": 0, "distance": 1000, "time": 3600})
    assert m.speed_kmh == m.avg_speed_kmh
    assert m.speed_kmh != 0.0


def test_speed_falls_back_to_average_when_instantaneous_is_negative():
    m = RiderMetrics.from_raw({"speed": -5, "distance": 1000, "time": 3600})
    assert m.speed_kmh == m.avg_speed_kmh
