import csv
import re
from collections import defaultdict
from pathlib import Path
from statistics import median

from sqlalchemy.dialects.postgresql import insert

from backend.app.database import SessionLocal
from backend.app.models import Line, RideConnection, Station, StationLine, TransferEdge
from transfers import TRANSFERS


PROJECT_ROOT = Path(__file__).resolve().parents[2]
STOPS_FILE = PROJECT_ROOT / "data" / "raw" / "gtfs" / "stops.txt"
TRIPS_FILE = PROJECT_ROOT / "data" / "raw" / "gtfs" / "trips.txt"
ROUTES_FILE = PROJECT_ROOT / "data" / "raw" / "gtfs" / "routes.txt"
STOP_TIMES_FILE = PROJECT_ROOT / "data" / "raw" / "gtfs" / "stop_times.txt"


def parse_gtfs_time(time_text: str) -> int:
    hours, minutes, seconds = map(int, time_text.split(":"))
    return hours * 3600 + minutes * 60 + seconds


def import_stations() -> int:
    with STOPS_FILE.open(newline="", encoding="utf-8") as stops_file:
        stops_reader = csv.DictReader(stops_file)
        stations = [
            Station(
                id=row["stop_id"],
                name=row["stop_name"],
                latitude=float(row["stop_lat"]),
                longitude=float(row["stop_lon"]),
            )
            for row in stops_reader
        ]

    with SessionLocal() as session:
        for station in stations:
            session.merge(station)
        session.commit()

    return len(stations)

def import_lines() -> int:
    with ROUTES_FILE.open(newline="", encoding="utf-8") as routes_file:
        routes_reader = csv.DictReader(routes_file)
        lines = []

        for row in routes_reader:
            color_match = re.match(r"^([^_]+)", row["route_long_name"])
            if color_match is None:
                raise ValueError(
                    f"Route name has no color prefix: {row['route_long_name']}"
                )

            # another method is: row["route_long_name"].split("_", 1)[0]
            lines.append(
                Line(
                    id=row["route_id"],
                    name=row["route_long_name"],
                    color=color_match.group(1),
                )
            )

    with SessionLocal() as session:
        for line in lines:
            session.merge(line)
        session.commit()

    return len(lines)


def import_station_lines() -> int:
    route_id_by_trip_id = {}

    with TRIPS_FILE.open(newline="", encoding="utf-8") as trips_file:
        trips_reader = csv.DictReader(trips_file)
        for trip in trips_reader:
            route_id_by_trip_id[trip["trip_id"]] = trip["route_id"]

    station_line_pairs = set()

    with STOP_TIMES_FILE.open(newline="", encoding="utf-8") as stop_times_file:
        stop_times_reader = csv.DictReader(stop_times_file)
        for stop_time in stop_times_reader:
            route_id = route_id_by_trip_id[stop_time["trip_id"]]
            station_line_pairs.add((stop_time["stop_id"], route_id))

    with SessionLocal() as session:
        for station_id, line_id in station_line_pairs:
            session.merge(StationLine(station_id=station_id, line_id=line_id))
        session.commit()

    return len(station_line_pairs)


def import_ride_connections() -> int:
    """Import directed adjacent-stop rides using median GTFS travel times."""
    route_id_by_trip_id = {}

    with TRIPS_FILE.open(newline="", encoding="utf-8") as trips_file:
        trips_reader = csv.DictReader(trips_file)
        for trip in trips_reader:
            route_id_by_trip_id[trip["trip_id"]] = trip["route_id"]

    stop_times_by_trip_id = defaultdict(list)

    with STOP_TIMES_FILE.open(newline="", encoding="utf-8") as stop_times_file:
        stop_times_reader = csv.DictReader(stop_times_file)
        for stop_time in stop_times_reader:
            stop_times_by_trip_id[stop_time["trip_id"]].append(stop_time)

    durations_by_connection = defaultdict(list)

    for trip_id, trip_stop_times in stop_times_by_trip_id.items():
        ordered_stop_times = sorted(
            trip_stop_times,
            key=lambda stop_time: int(stop_time["stop_sequence"]),
        )
        route_id = route_id_by_trip_id[trip_id]

        for current_stop, next_stop in zip(
            ordered_stop_times, ordered_stop_times[1:]
        ):
            duration_seconds = parse_gtfs_time(
                next_stop["arrival_time"]
            ) - parse_gtfs_time(current_stop["departure_time"])

            if duration_seconds <= 0:
                raise ValueError(
                    f"Non-positive ride duration in trip {trip_id}: "
                    f"{current_stop['stop_id']} to {next_stop['stop_id']}"
                )

            connection_key = (
                current_stop["stop_id"],
                next_stop["stop_id"],
                route_id,
            )
            durations_by_connection[connection_key].append(duration_seconds)

    ride_connections = [
        {
            "start_station_id": start_station_id,
            "end_station_id": end_station_id,
            "line_id": line_id,
            "duration_seconds": round(median(durations)),
        }
        for (start_station_id, end_station_id, line_id), durations
        in durations_by_connection.items()
    ]

    with SessionLocal() as session:
        statement = insert(RideConnection).values(ride_connections)
        statement = statement.on_conflict_do_update(
            constraint="uq_ride_connection_direction_line",
            set_={"duration_seconds": statement.excluded.duration_seconds},
        )
        session.execute(statement)
        session.commit()

    return len(durations_by_connection)


def import_transfer_edges() -> int:
    transfer_edges = []

    for station_a, station_b, _line_a, _line_b, duration_seconds in TRANSFERS:
        for start_station_id, end_station_id in (
            (station_a, station_b),
            (station_b, station_a),
        ):
            transfer_edges.append(
                TransferEdge(
                    start_station_id=str(start_station_id),
                    end_station_id=str(end_station_id),
                    duration_seconds=duration_seconds,
                    source="project_estimate",
                )
            )

    with SessionLocal() as session:
        for transfer_edge in transfer_edges:
            session.merge(transfer_edge)
        session.commit()

    return len(transfer_edges)


if __name__ == "__main__":
    imported_count = import_stations()
    print(f"Imported or updated {imported_count} stations.")
    print(f"Imported or updated {import_lines()} lines.")
    print(f"Imported or updated {import_station_lines()} station-line memberships.")
    print(f"Imported or updated {import_ride_connections()} ride connections.")
    print(f"Imported or updated {import_transfer_edges()} transfer edges.")
