# Delhi Metro Journey Planner — final scope

This is a portfolio and learning project. Build one runnable milestone at a time. Explain important code and decisions in plain language so the developer can explain every file. Inspect existing work and preserve user edits. Do not commit or push. Suggest a commit message after each milestone for the user to run.

## Product

Build a public full-stack planner comparing Delhi Metro journeys and explaining why one is faster or has fewer transfers. Include a secondary Algorithm Lab showing searches in action.

- Search origin to destination with station autocomplete, line badges, swap, shareable URLs, and Try example.
- Show fastest and fewest-transfer journeys. Show one card if the same itinerary wins both, plus a third only for a meaningful trade-off.
- Show total estimated duration, ride time, transfer allowance, station count, transfer count, interchanges, lines, and leg-by-leg itinerary. Selecting a route updates itinerary and map together.
- Generate Why this route explanations from computed figures.
- Guests can search. Signed-in users have private recent history and named station-pair bookmarks. Reopening reruns against the current network.
- Use fixed graph estimates, excluding initial wait and walking to/from stations. No departure-time picker, live tracking, or timetable routing.
- No admin panel or RBAC. Enforce ownership of private history and saved journeys server-side.

## GTFS and network corrections

Use the feed from C:/projects/metro-routing/data/raw/gtfs for stops, route metadata, ordered trip stops, and shapes where available. Derive segment estimates offline from adjacent stop timings and document the aggregation method. Preserve direction. Document source, coverage, and license, checking the license before public release. Do not imply comprehensive current coverage.

Create a repeatable transactional import. Validate station and line references, ride edges, and transfer costs within one transaction. Failed imports roll back and preserve prior network data. Print a data-quality report with loaded and rejected counts and reasons. Keep corrections in explicit reviewable data files with sources. Use distinct internal line IDs because old short-name parsing conflates Green/Gray as G and Red/Rapid Metro as R.

1. Punjabi Bagh West (176) ↔ Punjabi Bagh (33) is a same-line Green ride, with zero transfers and zero allowance. Feed lists Punjabi Bagh West only on Pink and has a Green edge Shivaji Park (32) → Punjabi Bagh (33). Correct Green topology to Shivaji Park ↔ Punjabi Bagh West ↔ Punjabi Bagh using documented segment estimates. Punjabi Bagh West belongs to Green and Pink, and Green/Pink interchange is at Punjabi Bagh West. Test both directions as one Green ride segment and zero transfers.
2. Dhaula Kuan (156, Airport Express) ↔ Durgabai Deshmukh South Campus (181, Pink) is a bidirectional pedestrian interchange between separate stations, confirmed by DMRC.
3. Noida Sector 52 (234, Blue, feed name Noida Sec-52) ↔ Noida Sector 51 (500, Aqua) is a bidirectional pedestrian interchange between separate stations. Recheck the reported public opening date of 28 August 2026 and topology against NMRC sources.

The two pedestrian links each count as one transfer when changing trains and use their configurable allowance once. Use a 720-second (12-minute) project estimate for Dhaula Kuan ↔ Durgabai Deshmukh South Campus and a 300-second (5-minute) project estimate for Noida Sector 52 ↔ Noida Sector 51. Keep transfer durations configurable and test both directions.

Sources: https://delhimetrorail.com/line/LN5 ; https://delhimetrorail.com/pages/en/pressrelease_details/additional-interchange-station-at-punjabi-bagh-con ; https://backend.delhimetrorail.com/documents/20/DMRC-REPORT-2018-2019-English-Web.pdf ; https://www.nmrcnoida.com/uploads/press_releases/68dfa40c-0caf-4553-bbda-653982c9929c_Press%20Release.pdf

## Routing engine

Implement searches in pure Python without FastAPI/database/Redis imports. Use directed adjacency lists, priority queues, and (station, current_line) states. Ride edges add integer estimated seconds. Changing lines or using a pedestrian link adds one transfer and configurable duration. Initial boarding is free. Use deterministic tie-breaking and reconstruct ride/transfer legs. Count both endpoints in station counts and count an interchange within one station once.

- Dijkstra finds fastest route including transfer costs, ordered by total seconds then transfers.
- A* solves the same objective. Provide a cheap straight-line-distance heuristic divided by maximum speed observed in data, kept admissible. Also provide a prepared heuristic from reverse Dijkstra on a simplified station graph: collapse line states, allow free line changes within a station, keep cheapest parallel links, and preserve directed links between separate interchange stations. Benchmark both against Dijkstra including heuristic preparation time. ALT/landmarks optional.
- Fewest transfers uses lexicographic Dijkstra on (transfer_count, seconds), computed independently.
- Yen's K-shortest search returns a bounded batch of loopless candidates ordered by transfer-aware duration. Deduplicate paths and equivalent rider itineraries by ride segments/interchanges. Filter physical station loops after collapsing consecutive same-station line-change visits. Always include distinct fastest and fewest-transfer results.
- Return structured totals and comparison deltas consistently used by cards, explanations, and map.

## Backend and persistence

Use Python, FastAPI, Pydantic, PostgreSQL, SQLAlchemy, and Alembic in one API service. Store stations, lines, station-line memberships, directed rides, transfer edges/overrides, users, saved journeys, and search history. Use foreign keys, uniqueness and duration checks. Load active graph into memory for routing.

Use Google OpenID Connect. FastAPI verifies identity and ownership. Keep one history row per user and ordered station pair with last-searched time and search count. Users can filter, reopen, and clear history.

Use Redis cache-aside for public route comparisons keyed by ordered pair, routing options, graph revision, and TTL. Search works if Redis is unavailable. Update signed-in history on cache hits too. Never place private history in shared cache.

Add PostgreSQL pg_trgm autocomplete after basic search: exact and prefix first, then fuzzy, with aliases. Record an EXPLAIN ANALYZE before/after comparison for README.

Add /health and /ready endpoints, with readiness checking PostgreSQL and Redis. Use structured logging with request IDs and no private data. Keep secrets in environment variables, configure CORS, and generate TypeScript API types from FastAPI OpenAPI.

## Frontend and Algorithm Lab

Use React, strict TypeScript, Vite, and React Leaflet. Desktop has search/results beside map. Mobile shows results first with Itinerary and Map views. Station pickers work by keyboard and itinerary works without map.

Use Metro line colors, interchange markers, and dashed verified pedestrian links. Use GTFS shapes where available, label geometry schematic, and fit map to selected route.

Build typed API client with loading, no-route, and failure states. First use sample response, then connect real API. Add Recent Searches and Saved Journeys after public planner works.

Algorithm Lab has one curated journey, Dijkstra/A* switch, Step, Play, Reset. Backend emits bounded trace from actual search. Show frontier, expanded states, final path, and current line. Server-Sent Events are optional.

## Tests and quality

- Start with hand-solvable two-line fixture including faster extra-transfer route and a transfer-cost change that flips the winner.
- Use exhaustive simple-path enumeration as independent oracle and Hypothesis tests on random tiny graphs comparing Dijkstra/A*/oracle.
- Test algorithm agreement, fewest-transfer tie-breaks, Yen ordering/uniqueness, ties, unreachable and same-station searches, all three corrections, and import rollback.
- API tests with two users cover shared public cache and isolated private histories. Test Redis fallback.
- Playwright smoke test verifies route-card selection updates itinerary and map.
- From first commit use Ruff, mypy, ESLint, strict TypeScript, GitHub Actions CI for lint/types/tests with README badge, and Dependabot.
- Benchmark short, long, interchange-heavy queries with tracing disabled. Report measured median/p95 runtime, expanded states, duration, transfers, A* preparation, Yen work and usable alternatives.
- Use Locust for cold-cache, warm-cache, and Redis-unavailable load tests. Report measured results.

## Build order and checkpoints

1. Inspect repo, set up tooling/CI, fixtures, Dijkstra and fewest-transfer routing, oracle and Hypothesis tests.
2. Add both A* heuristics and Yen with correctness tests and reproducible benchmark.
3. Build GTFS import, PostgreSQL, FastAPI, and React to show one journey end to end. Validate all three corrections. Stop and confirm everything works before proceeding.
4. Add route comparison and Why this route, map, Google sign-in, history, bookmarks, Redis cache, basic Algorithm Lab, Docker Compose.
5. After step 4 add Prometheus metrics with aggregated data and no user info, Locust load tests, Redis counter rate limits (429 with Retry-After and local concurrency cap), then deployment, README, and 60–90 second demo. Free tier acceptable.

Skip Grafana, request coalescing, and Yen divergence view.

## Documentation and delivery

README includes architecture diagram, algorithms, data limitations/license, setup, benchmark instructions. Add short ADRs for (station,line) states, cache-aside, ownership authorization over RBAC, and separate fewest-transfer search. Document Punjabi Bagh as a data-quality story. Deliver Docker Compose, CI, deployment-ready app, deployed demo, and short recording.

## Current learning workflow decisions

The user is a first-time project builder and wants syntax and logic explained as code is added. No more preview-only milestones. Build meaningful runnable features, explain code and API routes, suggest appropriate milestone commits. The user performs commits and pushes.

