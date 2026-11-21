import csv
import re
from pathlib import Path

from backend.app.database import SessionLocal
from backend.app.models import Station , Line


PROJECT_ROOT = Path(__file__).resolve().parents[2]
STOPS_FILE = PROJECT_ROOT / "data" / "raw" / "gtfs" / "stops.txt"
TRIPS_FILE = PROJECT_ROOT / "data" / "raw" / "gtfs" / "trips.txt"
ROUTES_FILE = PROJECT_ROOT / "data" / "raw" / "gtfs" / "routes.txt"
STOP_TIMES_FILE = PROJECT_ROOT / "data" / "raw" / "gtfs" / "stop_times.txt"

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

if __name__ == "__main__":
    imported_count = import_stations()
    print(f"Imported or updated {imported_count} stations.")
    print(f"Imported or updated {import_lines()} lines.")
