import os
import json
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)

# ── distractor directory structure ──────────────────────────────────────────
dirs = [
    "travel_agency/clients/vip",
    "travel_agency/clients/standard",
    "travel_agency/reports/2024/q1",
    "travel_agency/reports/2024/q2",
    "travel_agency/config",
    "travel_agency/scripts/legacy",
    "travel_agency/scripts/active",
    "travel_agency/data/raw",
    "travel_agency/data/processed",
    "travel_agency/integrations/booking",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# ── distractor files ─────────────────────────────────────────────────────────
distractor_files = {
    "travel_agency/clients/vip/client_007.json": json.dumps({
        "name": "Isabella Fontaine",
        "tier": "VIP",
        "preferred_language": "en",
        "past_trips": ["paris", "rome", "kyoto"]
    }, indent=2),

    "travel_agency/clients/standard/client_042.json": json.dumps({
        "name": "Marco Delgado",
        "tier": "standard",
        "preferred_language": "es",
        "past_trips": ["barcelona", "lisbon"]
    }, indent=2),

    "travel_agency/reports/2024/q1/summary.csv": (
        "city,tours_booked,revenue\n"
        "barcelona,120,0\n"
        "madrid,95,0\n"
        "seville,40,0\n"
    ),

    "travel_agency/reports/2024/q2/summary.csv": (
        "city,tours_booked,revenue\n"
        "san-sebastian,18,0\n"
        "bilbao,22,0\n"
        "valencia,55,0\n"
    ),

    "travel_agency/config/agency_settings.yaml": (
        "agency_name: Wanderlust Concierge\n"
        "default_currency: EUR\n"
        "tour_search_radius_km: 50\n"
        "max_results_per_query: 10\n"
        "timezone: Europe/Madrid\n"
    ),

    "travel_agency/scripts/legacy/old_tour_scraper.py": (
        "# DEPRECATED - do not use\n"
        "import requests\n"
        "def scrape_tours(city):\n"
        "    # old scraping logic removed\n"
        "    pass\n"
    ),

    "travel_agency/scripts/active/send_notification.py": (
        "import smtplib\n"
        "def send(to, subject, body):\n"
        "    # stub\n"
        "    pass\n"
    ),

    "travel_agency/data/raw/unprocessed_requests.txt": (
        "Client request 1: tours in San Sebastian, English, next weekend\n"
        "Client request 2: free walks in Barcelona, Spanish, June\n"
        "Client request 3: guided tour new york english july 10-12\n"
    ),

    "travel_agency/data/processed/past_tour_results.json": json.dumps([
        {"city": "barcelona", "language": "en", "tours_found": 8, "date": "2024-03-15"},
        {"city": "madrid", "language": "es", "tours_found": 12, "date": "2024-04-01"},
    ], indent=2),

    "travel_agency/integrations/booking/connector_config.json": json.dumps({
        "provider": "legacy_booking_api",
        "base_url": "http://old-provider.internal/api/v1",
        "timeout_seconds": 30,
        "retry_attempts": 3
    }, indent=2),

    "travel_agency/integrations/booking/field_mapping.json": json.dumps({
        "tour_id": "external_ref",
        "tour_title": "name",
        "meeting_location": "meetpoint_address",
        "guide": "guru.name"
    }, indent=2),
}

for rel_path, content in distractor_files.items():
    fpath = workspace / rel_path
    fpath.write_text(content)

# ── THE ACTUAL TASK INPUT ─────────────────────────────────────────────────────
# A messy client brief that requires the agent to:
# 1. Parse the city name (mixed case, full name) -> slug
# 2. Use explicit date range
# 3. Use language code
# 4. Call the mock MCP server
# 5. Filter, rank, and output correctly

client_brief = {
    "client_name": "Wanderlust Concierge Agency",
    "request_id": "REQ-2025-0847",
    "destination": "San Sebastian",
    "trip_window": {
        "from": "2025-08-10",
        "to": "2025-08-12"
    },
    "preferred_language": "English",
    "notes": (
        "Client wants free walking tours only. "
        "Please find all available options and produce a recommendations file. "
        "Exclude any fully booked sessions. "
        "Prefer English-language tours, then best-rated, then soonest."
    ),
    "output_file": "tour_recommendations.json"
}

(workspace / "travel_agency" / "data" / "raw" / "client_brief_REQ-2025-0847.json").write_text(
    json.dumps(client_brief, indent=2)
)

print("Workspace initialized.")
print("Client brief written to: travel_agency/data/raw/client_brief_REQ-2025-0847.json")