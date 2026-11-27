from collections import defaultdict
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models import Line, RideConnection


@dataclass(frozen=True)
class RideEdge:
    end_station_id: str
    route_id: str
    physical_line: str
    duration_seconds: int


def load_ride_graph(session: Session) -> dict[str, list[RideEdge]]:
    route_to_line = {
        line.id: line.name.split("_", 1)[0]
        for line in session.scalars(select(Line))
    }

    graph = defaultdict(list)

    for ride in session.scalars(select(RideConnection)):
        graph[ride.start_station_id].append(
            RideEdge(
                end_station_id=ride.end_station_id,
                route_id=ride.line_id,
                physical_line=route_to_line[ride.line_id],
                duration_seconds=ride.duration_seconds,
            )
        )

    return dict(graph)
