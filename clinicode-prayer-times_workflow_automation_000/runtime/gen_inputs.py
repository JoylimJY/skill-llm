import os
import json
import random

random.seed(42)

workspace = "/workspace"

# Create realistic deeply nested directory structure with distractors
dirs = [
    "tours/hajj_2025/group_a",
    "tours/hajj_2025/group_b",
    "tours/umrah_2025/packages",
    "tours/umrah_2025/schedules",
    "admin/visas",
    "admin/bookings",
    "admin/contacts",
    "resources/guides",
    "resources/maps",
    "logistics/flights",
    "logistics/hotels",
    "reports/monthly",
    "reports/archive",
]

for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files - realistic travel operations files
distractor_files = {
    "tours/hajj_2025/group_a/manifest.txt": """GROUP A - HAJJ 2025
Travelers: 45
Departure: 2025-06-01
Guide: Mohammed Al-Rashid
Contact: +44 7700 900123
""",
    "tours/hajj_2025/group_b/manifest.txt": """GROUP B - HAJJ 2025
Travelers: 38
Departure: 2025-06-03
Guide: Fatima Hassan
Contact: +44 7700 900456
""",
    "tours/umrah_2025/packages/premium.json": json.dumps({
        "package": "Premium Umrah 2025",
        "cities": ["Makkah", "Madinah"],
        "duration": 14,
        "price_gbp": 3500
    }, indent=2),
    "tours/umrah_2025/packages/standard.json": json.dumps({
        "package": "Standard Umrah 2025",
        "cities": ["Makkah", "Madinah"],
        "duration": 10,
        "price_gbp": 2200
    }, indent=2),
    "tours/umrah_2025/schedules/itinerary_v1.txt": """DAY 1: Arrival Jeddah - Transfer to Makkah
DAY 2-5: Makkah - Haram visits
DAY 6: Transfer to Madinah
DAY 7-9: Madinah - Masjid Nabawi
DAY 10: Return Jeddah - Departure
""",
    "admin/visas/requirements.txt": """VISA REQUIREMENTS 2025
- Valid passport (6 months minimum)
- Completed application form
- 2 passport photos
- Proof of vaccination
- Hotel bookings
""",
    "admin/bookings/hotels.csv": """city,hotel,stars,nights,cost_pp
Makkah,Swissotel Al Maqam,5,5,800
Madinah,Anwar Al Madinah,5,3,450
Dubai,Jumeirah Emirates Towers,5,2,350
""",
    "admin/contacts/emergency.txt": """EMERGENCY CONTACTS
UK Office: +44 20 7946 0321
Saudi Rep: +966 12 345 6789
UAE Rep: +971 4 321 9876
""",
    "resources/guides/pilgrims_handbook.txt": """PILGRIMS HANDBOOK 2025
Section 1: Arrival Procedures
Section 2: Hotel Check-in
Section 3: Transportation
Section 4: Prayer Schedule Management
Section 5: Health Guidelines
""",
    "logistics/flights/departures.csv": """flight,origin,destination,date,seats
EK001,London Heathrow,Dubai,2025-06-01,250
SV100,Dubai,Jeddah,2025-06-01,180
EK002,London Heathrow,Dubai,2025-06-03,250
""",
    "logistics/hotels/confirmations.txt": """HOTEL CONFIRMATIONS
Makkah - Swissotel: REF#SW2025-4421
Madinah - Anwar: REF#AN2025-8832
Dubai - Jumeirah: REF#JE2025-1156
""",
    "reports/monthly/june_summary.txt": """JUNE 2025 OPERATIONS SUMMARY
Total travelers: 83
Destinations: Makkah, Madinah, Dubai
Revenue: GBP 287,450
Status: Confirmed
""",
}

for filepath, content in distractor_files.items():
    full_path = os.path.join(workspace, filepath)
    with open(full_path, "w") as f:
        f.write(content)

# Create the prayer_times.py script (the actual skill script)
# This is a realistic implementation matching the SKILL.md spec
prayer_times_script = r'''#!/usr/bin/env python3
"""
Prayer Times - Global Islamic Prayer Times Calculator
Version 1.0.0
Uses ISNA calculation method via Aladhan API
"""

import sys
import requests
from datetime import datetime

try:
    from thefuzz import process as fuzzy_process
    FUZZY_AVAILABLE = True
except ImportError:
    FUZZY_AVAILABLE = False

# Known cities for fuzzy matching
KNOWN_CITIES = [
    "Makkah", "Madinah", "Dubai", "Riyadh", "Jeddah", "Cairo", "Jerusalem",
    "Amman", "Doha", "Kuwait City", "Karachi", "Lahore", "Dhaka", "Jakarta",
    "Kuala Lumpur", "Singapore", "Mumbai", "Delhi", "Islamabad", "London",
    "Paris", "Berlin", "Amsterdam", "Brussels", "Rome", "Madrid", "Istanbul",
    "Birmingham", "Manchester", "Leicester", "Glasgow", "Bradford", "Leeds",
    "New York", "Toronto", "Chicago", "Los Angeles", "Houston", "Montreal",
    "Casablanca", "Tunis", "Nairobi", "Johannesburg", "Sydney", "Melbourne",
    "Perth", "Brisbane"
]

def get_auto_location():
    """Auto-detect location via IP"""
    try:
        resp = requests.get("https://ipapi.co/json/", timeout=5)
        data = resp.json()
        city = data.get("city", "London")
        country = data.get("country_name", "United Kingdom")
        lat = data.get("latitude", 51.5074)
        lon = data.get("longitude", -0.1278)
        return city, country, lat, lon
    except Exception:
        return "London", "United Kingdom", 51.5074, -0.1278

def geocode_city(city_name):
    """Geocode city using OpenStreetMap Nominatim with fuzzy matching"""
    # First try fuzzy match to fix typos
    resolved_city = city_name
    if FUZZY_AVAILABLE:
        match, score = fuzzy_process.extractOne(city_name, KNOWN_CITIES)
        if score >= 60:
            resolved_city = match

    # Geocode with Nominatim
    try:
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            "q": resolved_city,
            "format": "json",
            "limit": 1,
            "addressdetails": 1
        }
        headers = {"User-Agent": "PrayerTimesApp/1.0"}
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        results = resp.json()
        if results:
            result = results[0]
            lat = float(result["lat"])
            lon = float(result["lon"])
            address = result.get("address", {})
            country = address.get("country", "")
            display_city = resolved_city
            return display_city, country, lat, lon
    except Exception:
        pass

    return resolved_city, "", 51.5074, -0.1278

def get_prayer_times(lat, lon):
    """Fetch prayer times from Aladhan API using ISNA method (method=2)"""
    try:
        url = "https://api.aladhan.com/v1/timings"
        today = datetime.now()
        params = {
            "latitude": lat,
            "longitude": lon,
            "method": 2,  # ISNA method
            "date_or_timestamp": today.strftime("%d-%m-%Y")
        }
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()
        if data.get("code") == 200:
            timings = data["data"]["timings"]
            date_info = data["data"]["date"]["readable"]
            return timings, date_info
    except Exception:
        pass
    return None, None

def format_time_12h(time_24h):
    """Convert 24h time to 12h AM/PM format"""
    try:
        # Handle times with timezone offset like "05:12 (+03)"
        time_part = time_24h.split(" ")[0]
        dt = datetime.strptime(time_part, "%H:%M")
        return dt.strftime("%I:%M %p")
    except Exception:
        return time_24h

def display_prayer_times(city, country, timings, date_str):
    """Display prayer times in the standard format"""
    location_str = f"{city.upper()}, {country.upper()}" if country else city.upper()

    print("=" * 60)
    print(f"\U0001f54c PRAYER TIMES - {location_str}")
    print(f"\U0001f4c5 {date_str}")
    print("=" * 60)
    print()
    print(f"Fajr:    {format_time_12h(timings['Fajr'])}")
    print(f"Sunrise: {format_time_12h(timings['Sunrise'])}")
    print(f"Dhuhr:   {format_time_12h(timings['Dhuhr'])}")
    print(f"Asr:     {format_time_12h(timings['Asr'])}")
    print(f"Maghrib: {format_time_12h(timings['Maghrib'])}")
    print(f"Isha:    {format_time_12h(timings['Isha'])}")
    print()
    print("=" * 60)

def main():
    args = sys.argv[1:]

    # Check for specific prayer request: "Asr in Dubai"
    if len(args) >= 3 and args[1].lower() == "in":
        prayer_name = args[0]
        city_name = " ".join(args[2:])
        city, country, lat, lon = geocode_city(city_name)
        timings, date_str = get_prayer_times(lat, lon)
        if timings and prayer_name.capitalize() in timings:
            t = format_time_12h(timings[prayer_name.capitalize()])
            print(f"{prayer_name.capitalize()} in {city}, {country}: {t}")
        return

    if not args or args[0].lower() in ["today", "times"]:
        # Auto-detect
        city, country, lat, lon = get_auto_location()
    else:
        city_name = " ".join(args)
        city, country, lat, lon = geocode_city(city_name)

    timings, date_str = get_prayer_times(lat, lon)
    if timings:
        display_prayer_times(city, country, timings, date_str)
    else:
        print("Error: Could not fetch prayer times. Check internet connection.")

if __name__ == "__main__":
    main()
'''

with open(os.path.join(workspace, "prayer_times.py"), "w") as f:
    f.write(prayer_times_script)

# Create a traveler request document (the business context)
traveler_request = """URGENT REQUEST - Hajj/Umrah Operations Team
Date: Internal Memo

We have travelers departing soon for their pilgrimage tour covering:
1. The holy city commonly written as "Meca" by our non-Arabic speaking clients
2. Madinah (the Prophet's city)  
3. "Dubay" - the stopover city in UAE

Our team needs a consolidated prayer schedule file so guides can print and 
distribute to travelers. The schedule must be machine-readable for our 
booking system integration.

Please compile the complete daily prayer timetable for all three destinations
and save it as: prayer_schedule.json

The JSON file must contain all six prayer times (Fajr, Sunrise, Dhuhr, Asr, 
Maghrib, Isha) for each city, along with the resolved/correct city name and 
country, and the date the data was fetched.

Our booking system requires the times in 12-hour format as displayed.
"""

with open(os.path.join(workspace, "admin/bookings/traveler_request.txt"), "w") as f:
    f.write(traveler_request)

# Create a distractor prayer-times config that is NOT the right approach
distractor_config = """{
  "note": "Old manual prayer times - DO NOT USE - outdated",
  "Makkah": {
    "Fajr": "04:45 AM",
    "note": "These are WRONG - generated manually in 2023"
  }
}
"""
with open(os.path.join(workspace, "resources/guides/old_prayer_times.json"), "w") as f:
    f.write(distractor_config)

print("Workspace initialized successfully.")
print(f"Files created in: {workspace}")