"""Tkinter overlay window that displays live ride metrics and rolling graphs."""

from __future__ import annotations

import json
import logging
import sys
import time
import tkinter as tk
from pathlib import Path
from typing import Any

from .config import LAYOUT, UNITS, OverlayConfig
from .metrics import RiderMetrics
from .settings import save_settings
from .tray import TrayIcon
from .watcher import FocusFileWatcher

logger = logging.getLogger(__name__)

ICON_PATH = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent)) / "assets" / "icon.ico"

ALERT_COLOR = "#ff3838"
DEFAULT_TEXT_COLOR = "#ffffff"

# Tabular-figure font for numbers that update every tick, so the digit width
# stays fixed and values don't jitter side to side as the digit count changes.
MONO_FONT = "Consolas"

BG_OUTER = "#0a0a0a"
BG_HEADER = "#15151f"
BG_CARD = "#16161f"
BORDER_DIM = "#242433"
TEXT_MUTED = "#83839a"
TEXT_DIM = "#9090a0"

CARD_RADIUS = 16
CARD_INSET = 5
CARD_HEIGHT = 134
GRAPH_RADIUS = 12

BASE_WINDOW_WIDTH = 480
BASE_WINDOW_HEIGHT = 890
DEFAULT_WINDOW_X = 100
DEFAULT_WINDOW_Y = 100

STALE_AFTER_SECONDS = 5.0
LIVE_COLOR = "#2ee6a8"
STALE_COLOR = "#83839a"
STALENESS_CHECK_MS = 1000


def _rounded_rect_points(x1: float, y1: float, x2: float, y2: float, radius: float) -> list[float]:
    radius = max(0.0, min(radius, (x2 - x1) / 2, (y2 - y1) / 2))
    return [
        x1 + radius, y1,
        x2 - radius, y1,
        x2, y1,
        x2, y1 + radius,
        x2, y2 - radius,
        x2, y2,
        x2 - radius, y2,
        x1 + radius, y2,
        x1, y2,
        x1, y2 - radius,
        x1, y1 + radius,
        x1, y1,
    ]


def _draw_rounded_rect(
    canvas: tk.Canvas, x1: float, y1: float, x2: float, y2: float, radius: float, **kwargs: Any
) -> int:
    return canvas.create_polygon(_rounded_rect_points(x1, y1, x2, y2, radius), smooth=True, **kwargs)


def _blend(fg_hex: str, bg_hex: str, factor: float) -> str:
    """Mix `fg_hex` toward `bg_hex`; factor=1 returns fg_hex, factor=0 returns bg_hex."""
    fg = tuple(int(fg_hex[i:i + 2], 16) for i in (1, 3, 5))
    bg = tuple(int(bg_hex[i:i + 2], 16) for i in (1, 3, 5))
    mixed = tuple(int(fg[i] * factor + bg[i] * (1 - factor)) for i in range(3))
    return f"#{mixed[0]:02x}{mixed[1]:02x}{mixed[2]:02x}"


class CyclingOverlay:
    def __init__(self, config: OverlayConfig) -> None:
        logger.info("Initializing CyclingOverlay")
        self.config = config
        self.min_cadence = config.min_cadence
        self.min_power = config.min_power
        self.imperial = config.imperial
        self.hide_units = config.hide_units
        self.metric_cards: dict[str, dict[str, Any]] = {}

        # Historical data for graphs (configurable window duration in seconds)
        self.hr_history: list[float] = []
        self.power_history: list[float] = []
        self.max_history_points = config.window_duration

        self._last_update_monotonic: float | None = None
        self._is_stale = False
        self._hidden = False

        self.root = tk.Tk()
        self.setup_window()
        self.create_widgets()

        self.watcher = FocusFileWatcher(config.focus_file, self.schedule_update)
        self.watcher.start()

        self.tray = TrayIcon(
            icon_path=ICON_PATH,
            on_show_hide=lambda icon, item: self.root.after(0, self.toggle_visibility),
            on_reset_position=lambda icon, item: self.root.after(0, self.reset_position),
            on_quit=lambda icon, item: self.root.after(0, self.close),
        )
        if ICON_PATH.exists():
            self.tray.start()
        else:
            logger.warning("Icon missing, skipping system tray: %s", ICON_PATH)

        # Variables for dragging
        self.start_x = 0
        self.start_y = 0

        # Force geometry to resolve before the first draw, otherwise the graph
        # canvases report a 1x1 size (unmapped placeholder) and draw nothing.
        self.root.update_idletasks()
        self.update_data()
        self._check_staleness()
        logger.info("CyclingOverlay initialization complete")

    def setup_window(self) -> None:
        self.root.title("Cycling Stats")

        # winfo_fpixels("1i") reflects the monitor's real DPI once the process
        # has declared DPI awareness (see __main__._set_dpi_awareness); scaling
        # our base pixel geometry by it keeps the window's physical on-screen
        # size consistent across monitors instead of shrinking on scaled ones.
        dpi_scale = self.root.winfo_fpixels("1i") / 96.0
        width = round(BASE_WINDOW_WIDTH * dpi_scale)
        height = round(BASE_WINDOW_HEIGHT * dpi_scale)
        x = self.config.window_x if self.config.window_x is not None else DEFAULT_WINDOW_X
        y = self.config.window_y if self.config.window_y is not None else DEFAULT_WINDOW_Y
        self.root.geometry(f"{width}x{height}+{x}+{y}")

        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", self.config.opacity)
        self.root.configure(bg="#000000")
        self.root.overrideredirect(True)

        if ICON_PATH.exists():
            try:
                self.root.iconbitmap(default=str(ICON_PATH))
            except tk.TclError:
                logger.warning("Could not set window icon from %s", ICON_PATH)

        self.root.bind("<Button-1>", self.start_drag)
        self.root.bind("<B1-Motion>", self.drag_window)
        self.root.bind("<ButtonRelease-1>", self.end_drag)

    def create_widgets(self) -> None:
        main_frame = tk.Frame(self.root, bg=BG_OUTER, relief="flat", bd=0)
        main_frame.pack(fill="both", expand=True, padx=8, pady=8)

        header_frame = tk.Frame(main_frame, bg=BG_HEADER, height=38)
        header_frame.pack(fill="x", pady=(0, 10))
        header_frame.pack_propagate(False)

        header_accent = tk.Frame(header_frame, bg="#4cc9f0", height=2)
        header_accent.pack(fill="x", side="bottom")

        title_label = tk.Label(
            header_frame, text="\U0001f6b4 CYCLING STATS",
            bg=BG_HEADER, fg="#ffffff", font=("Segoe UI", 11, "bold"),
        )
        title_label.pack(side="left", padx=12, pady=8)

        self.status_label = tk.Label(
            header_frame, text="● LIVE", bg=BG_HEADER, fg=LIVE_COLOR,
            font=("Segoe UI", 8, "bold"),
        )
        self.status_label.pack(side="left", padx=(0, 12), pady=8)

        units_text = "Imperial" if self.imperial else "Metric"
        self.units_button = tk.Button(
            header_frame, text=units_text, bg="#2c3e50", fg="white",
            command=self.toggle_units, font=("Segoe UI", 9, "bold"),
            width=8, height=1, bd=0, relief="flat",
            activebackground="#34495e", activeforeground="white",
        )
        self.units_button.pack(side="right", padx=4, pady=6)

        close_button = tk.Button(
            header_frame, text="✕", bg="#3a3a3a", fg="#aaaaaa",
            command=self.close, font=("Segoe UI", 10, "bold"),
            width=3, height=1, bd=0, relief="flat",
            activebackground="#ff4757", activeforeground="white",
        )
        close_button.pack(side="right", padx=8, pady=6)

        settings_button = tk.Button(
            header_frame, text="⚙", bg="#2c3e50", fg="white",
            command=self.open_settings_dialog, font=("Segoe UI", 10, "bold"),
            width=3, height=1, bd=0, relief="flat",
            activebackground="#34495e", activeforeground="white",
        )
        settings_button.pack(side="right", padx=4, pady=6)

        for widget in (header_frame, title_label):
            widget.bind("<Button-1>", self.start_drag)
            widget.bind("<B1-Motion>", self.drag_window)
            widget.bind("<ButtonRelease-1>", self.end_drag)

        stats_container = tk.Frame(main_frame, bg=BG_OUTER)
        stats_container.pack(fill="x", expand=False)
        self.create_dynamic_layout(stats_container)

        graphs_container = tk.Frame(main_frame, bg=BG_OUTER)
        graphs_container.pack(fill="both", expand=True, pady=(10, 0))
        self.create_graphs(graphs_container)

    def create_dynamic_layout(self, parent: tk.Frame) -> None:
        for row_config in LAYOUT:
            row = row_config.get("row", 0)
            metrics = row_config.get("metrics", [])

            parent.grid_rowconfigure(row, weight=1)

            for col, metric_config in enumerate(metrics):
                parent.grid_columnconfigure(col, weight=1)

                metric_type = metric_config["type"]
                title = metric_config.get("title", metric_type.upper())
                default_value = self.get_default_value_for_metric(metric_config)
                color = metric_config.get("color", DEFAULT_TEXT_COLOR)
                icon = metric_config.get("icon", "")

                card = self.create_metric_card(parent, title, default_value, color, icon, row, col)
                self.metric_cards[metric_type] = {"card": card, "config": metric_config}

    def get_default_value_for_metric(self, metric_config: dict[str, Any]) -> str:
        metric_type = metric_config["type"]
        default = metric_config.get("default_value", "--")

        if metric_type == "speed":
            return "-- MPH" if self.imperial else "-- KM/H"
        if metric_type == "distance":
            return "-- MI" if self.imperial else "-- KM"
        return default

    def create_metric_card(
        self, parent: tk.Frame, title: str, value: str, color: str, icon: str, row: int, col: int
    ) -> dict[str, Any]:
        card_canvas = tk.Canvas(
            parent, bg=BG_OUTER, highlightthickness=0, bd=0, width=200, height=CARD_HEIGHT,
        )
        card_canvas.grid(row=row, column=col, padx=6, pady=6, sticky="nsew")

        content = tk.Frame(card_canvas, bg=BG_CARD)

        accent_bar = tk.Frame(content, bg=color, height=3)
        accent_bar.pack(fill="x", side="top")

        header = tk.Frame(content, bg=BG_CARD)
        header.pack(fill="x", padx=12, pady=(9, 0))
        if icon:
            tk.Label(header, text=icon, bg=BG_CARD, fg=color, font=("Segoe UI", 10)).pack(side="left")
        title_label = tk.Label(header, text=title, bg=BG_CARD, fg=TEXT_MUTED,
                                font=("Segoe UI", 8, "bold"))
        title_label.pack(side="left", padx=(6 if icon else 0, 0))

        value_label = tk.Label(content, text=value, bg=BG_CARD, fg=color,
                                font=(MONO_FONT, 21, "bold"))
        value_label.pack(pady=(3, 1))

        avg_label = tk.Label(content, text="", bg=BG_CARD, fg=TEXT_DIM,
                              font=("Segoe UI", 10, "normal"))
        avg_label.pack(pady=(0, 9))

        window_id = card_canvas.create_window(CARD_INSET, CARD_INSET, window=content, anchor="nw")
        border_color = _blend(color, BG_CARD, 0.55)

        def _redraw(event: tk.Event, canvas: tk.Canvas = card_canvas) -> None:
            w, h = event.width, event.height
            canvas.delete("bg")
            rect_id = _draw_rounded_rect(
                canvas, 1, 1, w - 1, h - 1, CARD_RADIUS,
                fill=BG_CARD, outline=border_color, width=1, tags="bg",
            )
            canvas.tag_lower(rect_id)
            canvas.coords(window_id, CARD_INSET, CARD_INSET)
            canvas.itemconfig(window_id, width=w - 2 * CARD_INSET, height=h - 2 * CARD_INSET)

        card_canvas.bind("<Configure>", _redraw)

        return {
            "frame": content, "title": title_label, "value": value_label,
            "avg": avg_label, "color": color,
        }

    def create_graphs(self, parent: tk.Frame) -> None:
        power_frame = tk.Frame(parent, bg=BG_OUTER)
        power_frame.pack(fill="both", expand=True, padx=2, pady=(0, 6))

        self.power_canvas = tk.Canvas(power_frame, bg=BG_OUTER, height=110, highlightthickness=0, bd=0)
        self.power_canvas.pack(fill="both", expand=True)

        hr_frame = tk.Frame(parent, bg=BG_OUTER)
        hr_frame.pack(fill="both", expand=True, padx=2, pady=(0, 2))

        self.hr_canvas = tk.Canvas(hr_frame, bg=BG_OUTER, height=110, highlightthickness=0, bd=0)
        self.hr_canvas.pack(fill="both", expand=True)

    def draw_graph(self, canvas: tk.Canvas, data: list[float], color: str, label: str) -> None:
        try:
            canvas.delete("all")

            width = canvas.winfo_width()
            height = canvas.winfo_height()
            if width <= 1 or height <= 1:
                return

            border_color = _blend(color, BG_CARD, 0.5)
            _draw_rounded_rect(canvas, 1, 1, width - 1, height - 1, GRAPH_RADIUS,
                                fill=BG_CARD, outline=border_color, width=1)

            top_pad, bottom_pad, side_pad = 22, 18, 10
            plot_top = top_pad
            plot_bottom = height - bottom_pad
            plot_height = max(plot_bottom - plot_top, 1)
            plot_left = side_pad
            plot_right = width - side_pad

            canvas.create_text(12, 8, text=label, fill=TEXT_MUTED, font=("Segoe UI", 8, "bold"), anchor="nw")

            for fraction in (0.25, 0.5, 0.75):
                y = plot_top + plot_height * fraction
                canvas.create_line(plot_left, y, plot_right, y, fill=BORDER_DIM, dash=(2, 3))

            if not data:
                canvas.create_text(width // 2, (plot_top + plot_bottom) // 2, text="Waiting for data...",
                                    fill=TEXT_MUTED, font=("Segoe UI", 9), anchor="center")
                return

            max_value = max(data) or 1
            min_value = min(data)
            value_range = (max_value - min_value) or 1

            num_points = len(data)
            plot_width = max(plot_right - plot_left, 1)
            if num_points < self.max_history_points:
                x_step = plot_width / self.max_history_points
            else:
                x_step = plot_width / max(num_points - 1, 1)

            def to_xy(i: int, value: float) -> tuple[float, float]:
                x = plot_left + i * x_step
                y = plot_bottom - ((value - min_value) / value_range) * plot_height
                return x, y

            points = [to_xy(i, v) for i, v in enumerate(data)]

            if len(points) > 1:
                area = [(plot_left, plot_bottom), *points, (points[-1][0], plot_bottom)]
                flat_area = [coord for point in area for coord in point]
                canvas.create_polygon(flat_area, fill=_blend(color, BG_CARD, 0.22), outline="", smooth=True)

                flat_line = [coord for point in points for coord in point]
                canvas.create_line(flat_line, fill=color, width=2, smooth=True)

            last_x, last_y = points[-1]
            canvas.create_oval(last_x - 3, last_y - 3, last_x + 3, last_y + 3, fill=color, outline="")

            current_value = int(data[-1])
            badge_text = str(current_value)
            badge_w = 14 + 8 * len(badge_text)
            badge_x2 = plot_right
            badge_x1 = badge_x2 - badge_w
            _draw_rounded_rect(canvas, badge_x1, 4, badge_x2, 20, 7, fill=color, outline="")
            canvas.create_text((badge_x1 + badge_x2) / 2, 12, text=badge_text,
                                fill=BG_CARD, font=(MONO_FONT, 9, "bold"), anchor="center")

            canvas.create_text(plot_left, height - 5, text=f"min {int(min_value)} / max {int(max_value)}",
                                fill=TEXT_MUTED, font=("Segoe UI", 7), anchor="sw")

            window_minutes = self.max_history_points // 60
            if window_minutes > 0:
                window_text = f"last {window_minutes}:00"
            else:
                window_text = f"last {self.max_history_points}s"
            canvas.create_text(plot_right, height - 5, text=window_text,
                                fill=TEXT_MUTED, font=("Segoe UI", 7), anchor="se")
        except tk.TclError:
            logger.exception("Error drawing graph")

    def start_drag(self, event: tk.Event) -> None:
        self.start_x = event.x_root - self.root.winfo_x()
        self.start_y = event.y_root - self.root.winfo_y()

    def drag_window(self, event: tk.Event) -> None:
        x = event.x_root - self.start_x
        y = event.y_root - self.start_y
        self.root.geometry(f"+{x}+{y}")

    def end_drag(self, _event: tk.Event) -> None:
        save_settings({"window_x": self.root.winfo_x(), "window_y": self.root.winfo_y()})

    def schedule_update(self) -> None:
        """Schedule a UI update on the main thread (called from the watcher thread)."""
        self.root.after(0, self.update_data)

    def _check_staleness(self) -> None:
        """Flip the header's LIVE/NO DATA indicator based on how long it's been
        since the last successful read.

        Runs on its own timer independent of file-change events: if TPVirtual
        stops writing entirely (closed, crashed, ride ended), no watcher event
        ever fires again, so nothing else would ever notice the data went stale.
        """
        if self._last_update_monotonic is None:
            is_stale = True
        else:
            is_stale = (time.monotonic() - self._last_update_monotonic) > STALE_AFTER_SECONDS

        if is_stale != self._is_stale:
            self._is_stale = is_stale
            if is_stale:
                self.status_label.config(text="● NO DATA", fg=STALE_COLOR)
            else:
                self.status_label.config(text="● LIVE", fg=LIVE_COLOR)

        self.root.after(STALENESS_CHECK_MS, self._check_staleness)

    def update_data(self) -> None:
        focus_file = self.config.focus_file
        try:
            if not focus_file.exists():
                logger.warning("focus.json file does not exist: %s", focus_file)
                return

            with open(focus_file, encoding="utf-8-sig") as f:
                data = json.load(f)

            if not data or not isinstance(data, list):
                logger.warning("No valid data found in focus.json")
                return

            metrics = RiderMetrics.from_raw(data[0])
            self.update_display(metrics)
            logger.debug("Display updated with new data")
        except json.JSONDecodeError:
            logger.exception("Failed to parse focus.json")
        except OSError:
            logger.exception("Failed to read focus.json")

    def update_display(self, metrics: RiderMetrics) -> None:
        self._last_update_monotonic = time.monotonic()

        self.power_history.append(metrics.power)
        self.hr_history.append(metrics.heartrate)
        if len(self.power_history) > self.max_history_points:
            self.power_history.pop(0)
        if len(self.hr_history) > self.max_history_points:
            self.hr_history.pop(0)

        power_below_min = (
            self.min_power and metrics.power > 0 and metrics.power < self.min_power
        )
        cadence_below_min = (
            self.min_cadence and metrics.cadence > 0 and metrics.cadence < self.min_cadence
        )
        power_color = ALERT_COLOR if power_below_min else None
        cadence_color = ALERT_COLOR if cadence_below_min else None

        self.update_metric_value("power", metrics.power, metrics.norm_power, power_color)
        self.update_metric_value("heartrate", metrics.heartrate, metrics.avg_heartrate)
        self.update_metric_value("cadence", metrics.cadence, metrics.avg_cadence, cadence_color)

        if self.imperial:
            self.update_metric_value("speed", metrics.speed_mph, metrics.avg_speed_mph)
            self.update_metric_value("distance", metrics.distance_miles, None)
        else:
            self.update_metric_value("speed", metrics.speed_kmh, metrics.avg_speed_kmh)
            self.update_metric_value("distance", metrics.distance_km, None)

        self.update_metric_value("time", metrics.formatted_time, None)
        self.update_metric_value("tss", metrics.tss, None)
        self.update_metric_value("calories", metrics.calories, None)

        self.draw_graph(self.power_canvas, self.power_history, "#ffb020", "POWER")
        self.draw_graph(self.hr_canvas, self.hr_history, "#ff4d6d", "HEART RATE")

    def update_metric_value(
        self, metric_type: str, value: Any, avg_value: float | None = None, color: str | None = None
    ) -> None:
        card_info = self.metric_cards.get(metric_type)
        if card_info is None:
            return

        config = card_info["config"]
        formatted_value = self.format_metric_value(metric_type, value)

        avg_text = ""
        show_avg = avg_value is not None and config.get("show_average", False)
        if show_avg and metric_type in ("power", "heartrate", "cadence", "speed"):
            formatted_avg = f"{avg_value:.1f}" if metric_type == "speed" else str(int(avg_value))
            unit = "" if self.hide_units else self.get_unit_for_metric(metric_type)
            label = config.get("avg_label") if metric_type == "power" else None
            if label:
                avg_text = f"{label}: {formatted_avg}{' ' + unit if unit else ''}"
            else:
                avg_text = f"{formatted_avg}{' ' + unit if unit else ''}"

        accent_color = color or card_info["card"]["color"]
        self.update_card(card_info["card"], formatted_value, avg_text, accent_color)

    def format_metric_value(self, metric_type: str, value: Any) -> str:
        if metric_type == "time":
            return str(value)

        unit = "" if self.hide_units else self.get_unit_for_metric(metric_type)

        if metric_type in ("speed", "distance") and isinstance(value, (int, float)):
            precision = 1 if metric_type == "speed" else 2
            formatted = f"{value:.{precision}f}"
        else:
            formatted = str(value)

        return f"{formatted}{' ' + unit if unit else ''}"

    def get_unit_for_metric(self, metric_type: str) -> str:
        if metric_type == "speed":
            return "MPH" if self.imperial else "KM/H"
        if metric_type == "distance":
            return "MI" if self.imperial else "KM"
        return UNITS.get(metric_type, "")

    def update_card(self, card: dict[str, Any], value: str, avg_text: str, color: str) -> None:
        card["value"].config(text=value, fg=color)
        card["avg"].config(text=avg_text)

    def toggle_units(self) -> None:
        self.imperial = not self.imperial
        units_text = "Imperial" if self.imperial else "Metric"
        self.units_button.config(text=units_text)
        logger.info("Units toggled to: %s", units_text)
        save_settings({"imperial": self.imperial})
        self.update_data()

    def open_settings_dialog(self) -> None:
        dialog = tk.Toplevel(self.root)
        dialog.title("Settings")
        dialog.configure(bg=BG_OUTER)
        dialog.resizable(False, False)
        dialog.attributes("-topmost", True)
        dialog.transient(self.root)
        dialog.geometry(f"+{self.root.winfo_x() + 40}+{self.root.winfo_y() + 40}")

        entry_kwargs = {
            "bg": BG_CARD, "fg": "#ffffff", "insertbackground": "#ffffff",
            "relief": "flat", "font": ("Segoe UI", 10),
        }

        def add_label(text: str, top_pad: int = 10) -> None:
            tk.Label(dialog, text=text, bg=BG_OUTER, fg=TEXT_MUTED,
                      font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=16, pady=(top_pad, 0))

        add_label("MIN CADENCE THRESHOLD (RPM, BLANK = OFF)", top_pad=14)
        cadence_var = tk.StringVar(value=str(self.min_cadence) if self.min_cadence else "")
        tk.Entry(dialog, textvariable=cadence_var, **entry_kwargs).pack(fill="x", padx=16, pady=(2, 0))

        add_label("MIN POWER THRESHOLD (W, BLANK = OFF)")
        power_var = tk.StringVar(value=str(self.min_power) if self.min_power else "")
        tk.Entry(dialog, textvariable=power_var, **entry_kwargs).pack(fill="x", padx=16, pady=(2, 0))

        add_label("GRAPH WINDOW (SECONDS)")
        duration_var = tk.StringVar(value=str(self.max_history_points))
        tk.Entry(dialog, textvariable=duration_var, **entry_kwargs).pack(fill="x", padx=16, pady=(2, 0))

        add_label("OPACITY")
        opacity_var = tk.DoubleVar(value=float(self.root.attributes("-alpha")))
        tk.Scale(
            dialog, from_=0.2, to=1.0, resolution=0.05, orient="horizontal", variable=opacity_var,
            bg=BG_OUTER, fg="#ffffff", troughcolor=BG_CARD, highlightthickness=0, bd=0,
            font=("Segoe UI", 8),
        ).pack(fill="x", padx=12, pady=(2, 0))

        hide_units_var = tk.BooleanVar(value=self.hide_units)
        tk.Checkbutton(
            dialog, text="Hide unit labels", variable=hide_units_var, bg=BG_OUTER, fg="#ffffff",
            selectcolor=BG_CARD, activebackground=BG_OUTER, activeforeground="#ffffff",
            font=("Segoe UI", 9),
        ).pack(anchor="w", padx=16, pady=(14, 0))

        error_label = tk.Label(dialog, text="", bg=BG_OUTER, fg=ALERT_COLOR, font=("Segoe UI", 8))
        error_label.pack(anchor="w", padx=16, pady=(6, 0))

        def on_save() -> None:
            try:
                min_cadence = int(cadence_var.get()) if cadence_var.get().strip() else None
                min_power = int(power_var.get()) if power_var.get().strip() else None
                window_duration = int(duration_var.get())
                if window_duration <= 0:
                    raise ValueError("window_duration must be positive")
            except ValueError:
                error_label.config(text="Thresholds and window must be whole numbers (blank = off).")
                return

            self.min_cadence = min_cadence
            self.min_power = min_power
            self.hide_units = hide_units_var.get()

            opacity = round(opacity_var.get(), 2)
            self.root.attributes("-alpha", opacity)

            if window_duration != self.max_history_points:
                self.max_history_points = window_duration
                self.power_history = self.power_history[-window_duration:]
                self.hr_history = self.hr_history[-window_duration:]

            save_settings({
                "min_cadence": self.min_cadence,
                "min_power": self.min_power,
                "hide_units": self.hide_units,
                "window_duration": self.max_history_points,
                "opacity": opacity,
            })
            logger.info(
                "Settings updated: min_cadence=%s min_power=%s hide_units=%s window_duration=%s opacity=%s",
                self.min_cadence, self.min_power, self.hide_units, self.max_history_points, opacity,
            )
            self.update_data()
            dialog.destroy()

        button_row = tk.Frame(dialog, bg=BG_OUTER)
        button_row.pack(fill="x", padx=16, pady=16)
        tk.Button(
            button_row, text="Cancel", command=dialog.destroy, bg="#2c3e50", fg="#ffffff",
            bd=0, relief="flat", font=("Segoe UI", 9, "bold"), padx=10,
        ).pack(side="right", padx=(8, 0))
        tk.Button(
            button_row, text="Save", command=on_save, bg="#2ee6a8", fg="#0a0a0a",
            bd=0, relief="flat", font=("Segoe UI", 9, "bold"), padx=10,
        ).pack(side="right")

        dialog.grab_set()

    def toggle_visibility(self) -> None:
        if self._hidden:
            self.root.deiconify()
            self.root.attributes("-topmost", True)
            self._hidden = False
            logger.info("Overlay shown from tray")
        else:
            self.root.withdraw()
            self._hidden = True
            logger.info("Overlay hidden to tray")

    def reset_position(self) -> None:
        self.root.geometry(f"+{DEFAULT_WINDOW_X}+{DEFAULT_WINDOW_Y}")
        save_settings({"window_x": DEFAULT_WINDOW_X, "window_y": DEFAULT_WINDOW_Y})
        logger.info("Overlay position reset to default")
        if self._hidden:
            self.toggle_visibility()

    def close(self) -> None:
        self.tray.stop()
        self.root.quit()

    def run(self) -> None:
        logger.info("Starting overlay application")
        try:
            self.root.mainloop()
        finally:
            logger.info("Shutting down")
            self.watcher.stop()
