import csv
from pathlib import Path
from statistics import median_low

from preview_stops import load_stops
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


def collect_segment_samples(trips):
    samples_by_segment = {}
    for trip_stops in trips.values():
        ordered_stops = sorted(trip_stops, key=lambda row: int(row["stop_sequence"]))
        graph = build_trip_graph(ordered_stops)
        for from_id, rides in graph.items():
            for to_id, seconds in rides:
                segment = (from_id, to_id)
                samples_by_segment.setdefault(segment, []).append(seconds)
    return samples_by_segment


def main():
    feed_folder = Path(__file__).resolve().parent.parent / "data" / "raw" / "gtfs"
    route_id = "0"
    trips = load_route_trips(feed_folder, route_id)
    samples_by_segment = collect_segment_samples(trips)
    if not samples_by_segment:
        raise SystemExit(f"No ride times found for route {route_id}.")

    stops_by_id = load_stops(feed_folder / "stops.txt")
    print(f"Route {route_id}: {len(samples_by_segment)} segments from {len(trips)} trips")
    for (from_id, to_id), samples in samples_by_segment.items():
        from_name = stops_by_id[from_id]["stop_name"]
        to_name = stops_by_id[to_id]["stop_name"]
        estimate = median_low(samples)
        print(f"{from_name} -> {to_name}: {estimate} seconds ({len(samples)} samples)")


if __name__ == "__main__":
    main()
