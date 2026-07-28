import tkinter as tk

import pytest

from cycling_overlay.ui import _blend, _rounded_rect_points, _Slider, _Toggle


class _FakeEvent:
    def __init__(self, x: float, y: float = 0) -> None:
        self.x = x
        self.y = y


@pytest.fixture(scope="module")
def tk_root():
    # A single shared root for the whole module: repeatedly creating and
    # tearing down full Tk()/Tcl interpreters per-test is flaky (can fail with
    # "Tcl wasn't installed properly" under resource pressure). Individual
    # tests create their own throwaway Frame/Canvas children under this root.
    root = tk.Tk()
    yield root
    root.destroy()


@pytest.fixture
def tk_parent(tk_root):
    frame = tk.Frame(tk_root)
    yield frame
    frame.destroy()


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


def test_toggle_starts_at_given_value(tk_parent):
    toggle = _Toggle(tk_parent, value=True)
    assert toggle.value is True


def test_toggle_click_flips_value(tk_parent):
    toggle = _Toggle(tk_parent, value=False)
    toggle._on_click(_FakeEvent(5))
    assert toggle.value is True
    toggle._on_click(_FakeEvent(5))
    assert toggle.value is False


def test_slider_starts_at_given_value(tk_parent):
    slider = _Slider(tk_parent, minimum=0.2, maximum=1.0, value=0.7)
    assert slider.value == 0.7


def test_slider_clamps_initial_value_to_range(tk_parent):
    too_high = _Slider(tk_parent, minimum=0.2, maximum=1.0, value=5.0)
    assert too_high.value == 1.0
    too_low = _Slider(tk_parent, minimum=0.2, maximum=1.0, value=-5.0)
    assert too_low.value == 0.2


def test_slider_drag_maps_position_to_value(tk_parent):
    slider = _Slider(tk_parent, minimum=0.0, maximum=1.0, value=0.5)
    slider.canvas.update_idletasks()
    slider.canvas.config(width=200)
    slider.canvas.update_idletasks()

    x0, x1 = slider._track_bounds()

    slider._on_drag(_FakeEvent(x0))
    assert slider.value == pytest.approx(0.0, abs=1e-6)

    slider._on_drag(_FakeEvent(x1))
    assert slider.value == pytest.approx(1.0, abs=1e-6)

    midpoint = (x0 + x1) / 2
    slider._on_drag(_FakeEvent(midpoint))
    assert slider.value == pytest.approx(0.5, abs=0.02)


def test_slider_drag_clamps_outside_track_bounds(tk_parent):
    slider = _Slider(tk_parent, minimum=0.0, maximum=1.0, value=0.5)
    slider.canvas.update_idletasks()
    slider.canvas.config(width=200)
    slider.canvas.update_idletasks()

    slider._on_drag(_FakeEvent(-1000))
    assert slider.value == pytest.approx(0.0, abs=1e-6)

    slider._on_drag(_FakeEvent(10000))
    assert slider.value == pytest.approx(1.0, abs=1e-6)
