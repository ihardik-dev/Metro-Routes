TRANSFER_ROUTE = "TRANSFER"

DEFAULT_TRANSFER_SECONDS = 7 * 60
DHAULA_KUAN_TRANSFER_SECONDS = 12 * 60

# station_a, station_b, line_a, line_b, duration_seconds
TRANSFERS = [
    (156, 181, "AIRPORT_EXPRESS", "PINK", DHAULA_KUAN_TRANSFER_SECONDS),
    (234, 500, "BLUE", "AQUA", DEFAULT_TRANSFER_SECONDS),
]

# from_station, to_station, line, duration_seconds
GREEN_RIDES = [
    (32, 176, "GREEN", 90),
    (176, 33, "GREEN", 60),
    (33, 176, "GREEN", 60),
    (176, 32, "GREEN", 90),
]

def add_transfers(graph):
    for station_a, station_b, line_a, line_b, duration in TRANSFERS:
        graph.setdefault(station_a, {})
        graph.setdefault(station_b, {})

        graph[station_a][station_b] = {
            f"{TRANSFER_ROUTE}:{line_b}": duration
        }
        graph[station_b][station_a] = {
            f"{TRANSFER_ROUTE}:{line_a}": duration
        }

    return graph


def add_green_rides(graph):
    for from_station, to_station, line, duration in GREEN_RIDES:
        graph.setdefault(from_station, {})
        graph.setdefault(to_station, {})
        graph[from_station].setdefault(to_station, {})[line] = duration

    return graph
