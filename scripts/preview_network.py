import csv
from pathlib import Path
from statistics import median_low

from preview_segment import collect_segment_samples


def load_trips_by_route(feed_folder):
    trips_by_route = {}
    stops_by_trip = {}
    with (feed_folder / "trips.txt").open(encoding="utf-8-sig", newline="") as file:
        for row in csv.DictReader(file):
            trip_id = row["trip_id"]
            trip_stops = []
            stops_by_trip[trip_id] = trip_stops
            route_trips = trips_by_route.setdefault(row["route_id"], {})
            route_trips[trip_id] = trip_stops

    with (feed_folder / "stop_times.txt").open(encoding="utf-8-sig", newline="") as file:
        for row in csv.DictReader(file):
            stops_by_trip[row["trip_id"]].append(row)
    return trips_by_route


def estimate_network(trips_by_route):
    estimates = {}
    for route_id, trips in trips_by_route.items():
        samples_by_segment = collect_segment_samples(trips)
        for (from_id, to_id), samples in samples_by_segment.items():
            estimates[(route_id, from_id, to_id)] = median_low(samples)
    return estimates


def main():
    feed_folder = Path(__file__).resolve().parent.parent / "data" / "raw" / "gtfs"
    trips_by_route = load_trips_by_route(feed_folder)
    estimates = estimate_network(trips_by_route)

    print(f"Loaded trips for {len(trips_by_route)} GTFS routes.")
    print(f"Estimated {len(estimates)} directed ride segments across those routes.")
    print(f"Route 0, Rithala -> Rohini West: {estimates[('0', '21', '20')]} seconds")


if __name__ == "__main__":
    main()
