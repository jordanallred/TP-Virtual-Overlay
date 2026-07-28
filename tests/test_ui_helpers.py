from cycling_overlay.ui import _blend, _rounded_rect_points


def test_blend_at_factor_one_returns_foreground():
    assert _blend("#ff0000", "#000000", 1.0) == "#ff0000"


def test_blend_at_factor_zero_returns_background():
    assert _blend("#ff0000", "#000000", 0.0) == "#000000"


def test_blend_midpoint():
    assert _blend("#ffffff", "#000000", 0.5) == "#7f7f7f"


def test_rounded_rect_points_is_twelve_xy_pairs():
    points = _rounded_rect_points(0, 0, 100, 50, 10)
    assert len(points) == 24


def test_rounded_rect_points_stay_within_bounds():
    points = _rounded_rect_points(0, 0, 100, 50, 10)
    xs, ys = points[0::2], points[1::2]
    assert min(xs) >= 0
    assert max(xs) <= 100
    assert min(ys) >= 0
    assert max(ys) <= 50


def test_rounded_rect_radius_is_clamped_for_oversized_radius():
    # A radius far bigger than the rect must not push points outside it.
    points = _rounded_rect_points(0, 0, 20, 20, 1000)
    xs, ys = points[0::2], points[1::2]
    assert min(xs) >= 0
    assert max(xs) <= 20
    assert min(ys) >= 0
    assert max(ys) <= 20


def test_rounded_rect_radius_never_negative():
    points = _rounded_rect_points(0, 0, 20, 20, -5)
    xs = points[0::2]
    assert min(xs) >= 0
    assert max(xs) <= 20
