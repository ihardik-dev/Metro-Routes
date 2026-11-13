import csv
from pathlib import Path

from preview_stops import load_stops


def load_trip_stops(stop_times_path, trip_id):
    trip_stops = []
    with stop_times_path.open(encoding="utf-8-sig", newline="") as stop_times_file:
        for row in csv.DictReader(stop_times_file):
            if row["trip_id"] == trip_id:
                trip_stops.append(row)

    return sorted(trip_stops, key=lambda row: int(row["stop_sequence"]))


def time_to_seconds(time_text):
    hours, minutes, seconds = map(int, time_text.split(":"))
    return hours * 3600 + minutes * 60 + seconds


def main():
    project_root = Path(__file__).resolve().parent.parent
    feed_folder = project_root / "data" / "raw" / "gtfs"
    stops_path = feed_folder / "stops.txt"
    stop_times_path = feed_folder / "stop_times.txt"

    if not stops_path.is_file() or not stop_times_path.is_file():
        raise SystemExit("Put stops.txt and stop_times.txt in data/raw/gtfs.")

    trip_id = "0"
    trip_stops = load_trip_stops(stop_times_path, trip_id)
    if not trip_stops:
        raise SystemExit(f"Trip {trip_id} has no rows in stop_times.txt.")

    stops_by_id = load_stops(stops_path)
    print(f"Trip {trip_id} visits {len(trip_stops)} stops:")
    for position, row in enumerate(trip_stops, start=1):
        stop_id = row["stop_id"]
        stop_name = stops_by_id[stop_id]["stop_name"]
        print(f"{position}. {stop_name}")

    if len(trip_stops) >= 2:
        first_stop = trip_stops[0]
        second_stop = trip_stops[1]
        departure = time_to_seconds(first_stop["departure_time"])
        arrival = time_to_seconds(second_stop["arrival_time"])
        ride_seconds = arrival - departure

        from_name = stops_by_id[first_stop["stop_id"]]["stop_name"]
        to_name = stops_by_id[second_stop["stop_id"]]["stop_name"]
        print(f"{from_name} -> {to_name}: {ride_seconds} seconds")


if __name__ == "__main__":
    main()
