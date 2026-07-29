"""Generates synthetic focus.json data for testing the overlay without TPVirtual running."""

from __future__ import annotations

import argparse
import json
import random
import time
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from .config import DEFAULT_FOCUS_FILE


def generate_random_data() -> Iterator[list[dict[str, Any]]]:
    """Yield successive rider data samples, matching the TPVirtual focus.json format."""
    elapsed_seconds = 0
    distance = 0.0

    total_power = 0
    total_hr = 0
    total_cadence = 0
    data_points = 0

    while True:
        elapsed_seconds += 1

        power = random.randint(80, 250)
        heartrate = random.randint(120, 180)
        cadence = random.randint(70, 100)
        speed = random.randint(20000, 35000)  # mm/s (20-35 km/h)
        slope = round(random.uniform(-8.0, 8.0), 1)
        draft = random.randint(0, 60)

        distance += speed / 1000  # mm/s -> m/s, times 1 second

        data_points += 1
        total_power += power
        total_hr += heartrate
        total_cadence += cadence

        avg_power = total_power // data_points
        avg_heartrate = total_hr // data_points
        avg_cadence = total_cadence // data_points

        data = [{
            "power": power,
            "heartrate": heartrate,
            "cadence": cadence,
            "speed": speed,
            "distance": int(distance),
            "time": elapsed_seconds,
            "avgPower": avg_power,
            "nrmPower": avg_power,
            "avgHeartrate": avg_heartrate,
            "avgCadence": avg_cadence,
            "tss": round(elapsed_seconds * avg_power / 3600 / 2.5),
            "calories": round(elapsed_seconds * avg_power * 3.6 / 4184),
            "slope": slope,
            "draft": draft,
        }]

        yield data


def write_to_file(output_path: Path, interval: float) -> None:
    print(f"Writing test data to: {output_path}")
    print(f"Update interval: {interval} second(s)")
    print("Press Ctrl+C to stop\n")

    try:
        for data in generate_random_data():
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

            rider = data[0]
            print(
                f"Time: {rider['time']:04d}s | Power: {rider['power']:3d}W | "
                f"HR: {rider['heartrate']:3d}bpm | Cadence: {rider['cadence']:3d}rpm | "
                f"Speed: {rider['speed'] / 1000:.1f}km/h | Distance: {rider['distance'] / 1000:.2f}km"
            )
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\n\nStopped generating test data")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate random cycling data for testing")
    parser.add_argument(
        "--output", type=Path, default=DEFAULT_FOCUS_FILE,
        help=f"Output file path (default: {DEFAULT_FOCUS_FILE})",
    )
    parser.add_argument(
        "--interval", type=float, default=1.0, help="Update interval in seconds (default: 1.0)",
    )
    args = parser.parse_args()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    write_to_file(args.output, args.interval)


if __name__ == "__main__":
    main()
