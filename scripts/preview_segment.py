import csv
from pathlib import Path
from statistics import median_low

from preview_trip import build_trip_graph


def load_route_trips(feed_folder, route_id):
    with (feed_folder / "trips.txt").open(encoding="utf-8-sig", newline="") as file:
        trips = {}
        for row in csv.DictReader(file):
            if row["route_id"] == route_id:
                trips[row["trip_id"]] = []

    with (feed_folder / "stop_times.txt").open(encoding="utf-8-sig", newline="") as file:
        for row in csv.DictReader(file):
            trip_id = row["trip_id"]
            if trip_id in trips:
                trips[trip_id].append(row)
    return trips


def segment_samples(trips, from_id, to_id):
    samples = []
    for trip_stops in trips.values():
        ordered_stops = sorted(trip_stops, key=lambda row: int(row["stop_sequence"]))
        graph = build_trip_graph(ordered_stops)
        for destination, seconds in graph.get(from_id, []):
            if destination == to_id:
                samples.append(seconds)
    return samples


def main():
    feed_folder = Path(__file__).resolve().parent.parent / "data" / "raw" / "gtfs"
    trips = load_route_trips(feed_folder, route_id="0")
    samples = segment_samples(trips, from_id="21", to_id="20")
    if not samples:
        raise SystemExit("No ride times found for this segment.")

    estimate = median_low(samples)
    print(f"Rithala -> Rohini West: {len(samples)} scheduled samples")
    print(f"Samples in seconds: {samples}")
    print(f"Estimated ride time: {estimate} seconds")


if __name__ == "__main__":
    main()
