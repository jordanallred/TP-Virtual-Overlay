"""Regenerates assets/icon.ico and assets/icon.png (a simple bicycle glyph on a
dark rounded-square background, matching the overlay's color scheme).

Run with: uv run python scripts/make_icon.py
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

BG = (21, 21, 31, 255)  # matches ui.BG_HEADER
ACCENT = (76, 201, 240, 255)  # matches ui.py's header accent / speed card color
FRAME = (255, 255, 255, 255)

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
SIZE = 512


def draw_icon() -> Image.Image:
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Rounded-square background.
    margin = 8
    draw.rounded_rectangle(
        (margin, margin, SIZE - margin, SIZE - margin), radius=110, fill=BG,
    )

    # Bicycle geometry (all coordinates in the 512x512 canvas).
    rear_axle = (150, 372)
    front_axle = (378, 372)
    bottom_bracket = (255, 372)
    seat = (196, 232)
    handlebar = (352, 200)

    wheel_r = 82
    stroke = 16

    for axle in (rear_axle, front_axle):
        x, y = axle
        draw.ellipse(
            (x - wheel_r, y - wheel_r, x + wheel_r, y + wheel_r),
            outline=ACCENT, width=stroke,
        )
        hub_r = 8
        draw.ellipse((x - hub_r, y - hub_r, x + hub_r, y + hub_r), fill=ACCENT)

    frame_lines = [
        (rear_axle, seat),
        (seat, bottom_bracket),
        (bottom_bracket, rear_axle),
        (bottom_bracket, front_axle),
        (bottom_bracket, handlebar),
        (seat, handlebar),
    ]
    for start, end in frame_lines:
        draw.line([start, end], fill=FRAME, width=14)

    # Seat post + saddle.
    draw.line([seat, (seat[0] - 18, seat[1] - 26)], fill=FRAME, width=14)
    saddle_center = (seat[0] - 30, seat[1] - 30)
    draw.rounded_rectangle(
        (saddle_center[0] - 26, saddle_center[1] - 8, saddle_center[0] + 26, saddle_center[1] + 8),
        radius=8, fill=FRAME,
    )

    # Handlebar grip.
    draw.line([(handlebar[0] - 8, handlebar[1] - 22), (handlebar[0] + 20, handlebar[1] + 6)],
              fill=FRAME, width=14)

    # Crank + pedal.
    draw.ellipse(
        (bottom_bracket[0] - 10, bottom_bracket[1] - 10, bottom_bracket[0] + 10, bottom_bracket[1] + 10),
        fill=FRAME,
    )
    draw.line(
        [bottom_bracket, (bottom_bracket[0] + 36, bottom_bracket[1] + 30)], fill=FRAME, width=12,
    )

    return img


def main() -> None:
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    icon = draw_icon()

    png_path = ASSETS_DIR / "icon.png"
    icon.save(png_path)

    ico_path = ASSETS_DIR / "icon.ico"
    icon.save(
        ico_path,
        sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
    )

    print(f"Wrote {png_path} and {ico_path}")


if __name__ == "__main__":
    main()
