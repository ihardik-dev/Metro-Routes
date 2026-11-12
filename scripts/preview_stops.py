import csv
from itertools import islice
from pathlib import Path


def load_stops(stops_path):
    stops_by_id = {}
    with stops_path.open(encoding="utf-8-sig", newline="") as stops_file:
        for stop in csv.DictReader(stops_file):
            stop_id = stop["stop_id"]
            stops_by_id[stop_id] = stop
    return stops_by_id


def main():
    project_root = Path(__file__).resolve().parent.parent
    stops_path = project_root / "data" / "raw" / "gtfs" / "stops.txt"

    if not stops_path.is_file():
        raise SystemExit("Missing data/raw/gtfs/stops.txt. Copy the GTFS feed into data/raw/gtfs.")

    stops_by_id = load_stops(stops_path)
    for stop in islice(stops_by_id.values(), 5):
        print(f"{stop['stop_id']}: {stop['stop_name']}")
    print(f"Loaded {len(stops_by_id)} stops.")

    example_stop = stops_by_id.get("176")
    if example_stop is not None:
        print(f"Lookup 176: {example_stop['stop_name']}")


if __name__ == "__main__":
    main()
