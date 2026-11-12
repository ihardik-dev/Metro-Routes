# Delhi Metro GTFS data

 The feed identifies Delhi Metro Rail
Corporation in `agency.txt`. Its calendar ends on 31 December 2025, so we use
it as a historical snapshot for route estimates.

On a fresh checkout, run these commands from the repository root in PowerShell:


The local feed contains seven files. The main tables are `stops.txt` (262 rows),
`routes.txt` (36 rows), `trips.txt` (5,438 rows), and `stop_times.txt` (128,434
rows). The other files describe the agency, service calendar, and route shapes.
