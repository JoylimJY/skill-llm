import os
import json
import random

random.seed(42)

BASE = "/workspace"

# Directory structure — realistic wilderness school organization
dirs = [
    "wilderness_school/admin/enrollment",
    "wilderness_school/admin/waivers",
    "wilderness_school/courses/navigation_101/drafts",
    "wilderness_school/courses/navigation_101/resources",
    "wilderness_school/courses/navigation_101/assessments",
    "wilderness_school/courses/survival_basics/notes",
    "wilderness_school/courses/first_aid/materials",
    "wilderness_school/staff/instructor_notes",
    "wilderness_school/trips/2024_fall_oregon/planning",
    "wilderness_school/trips/2024_fall_oregon/gear_lists",
    "wilderness_school/archive/old_curricula",
    "wilderness_school/archive/photos_placeholder",
]
for d in dirs:
    os.makedirs(os.path.join(BASE, d), exist_ok=True)

# --- DISTRACTOR FILES ---

# Enrollment form placeholder
with open(os.path.join(BASE, "wilderness_school/admin/enrollment/form_template.txt"), "w") as f:
    f.write("Student enrollment form v3.2\nName: ___\nEmergency contact: ___\nMedical conditions: ___\n")

# Waiver placeholder
with open(os.path.join(BASE, "wilderness_school/admin/waivers/liability_waiver_2024.txt"), "w") as f:
    f.write("LIABILITY WAIVER\nParticipant acknowledges inherent risk in outdoor activities...\n[Signature block]\n")

# Gear list
with open(os.path.join(BASE, "wilderness_school/trips/2024_fall_oregon/gear_lists/ten_essentials.txt"), "w") as f:
    f.write("Ten Essentials:\n1. Navigation tools\n2. Sun protection\n3. Insulation\n4. Illumination\n5. First-aid supplies\n6. Fire\n7. Repair tools\n8. Nutrition\n9. Hydration\n10. Emergency shelter\n")

# Old curricula distractor
with open(os.path.join(BASE, "wilderness_school/archive/old_curricula/nav_curriculum_2019.txt"), "w") as f:
    f.write("2019 Navigation Curriculum (ARCHIVED - DO NOT USE)\nThis document is outdated. Declination values have changed.\nContact admin for current version.\n")

# Survival basics notes
with open(os.path.join(BASE, "wilderness_school/courses/survival_basics/notes/shelter_building.txt"), "w") as f:
    f.write("Shelter building notes:\n- Lean-to construction requires 6-8 branches minimum\n- Debris huts retain heat better in sub-freezing conditions\n- Always build shelter before dark\n")

# First aid materials
with open(os.path.join(BASE, "wilderness_school/courses/first_aid/materials/blister_care.txt"), "w") as f:
    f.write("Blister care protocol:\n1. Clean the area\n2. Do not pop blisters in the field if possible\n3. Use moleskin or second skin\n4. Monitor for infection\n")

# Staff instructor notes
with open(os.path.join(BASE, "wilderness_school/staff/instructor_notes/teaching_tips.txt"), "w") as f:
    f.write("Teaching tips for outdoor instructors:\n- Use Socratic method for problem-solving exercises\n- Always debrief after navigation exercises\n- Encourage students to verbalize their reasoning\n")

# Assessment placeholder
with open(os.path.join(BASE, "wilderness_school/courses/navigation_101/assessments/quiz_template.txt"), "w") as f:
    f.write("Navigation Quiz (Template)\nQ1: What does a tight cluster of contour lines indicate?\nQ2: What does 'red in the shed' mean?\nQ3: How do you use Polaris to find north?\n")

# Photos placeholder
with open(os.path.join(BASE, "wilderness_school/archive/photos_placeholder/README.placeholder"), "w") as f:
    f.write("Photo archive is stored on the NAS drive. Ask IT for access credentials.\n")

# Trip planning note
with open(os.path.join(BASE, "wilderness_school/trips/2024_fall_oregon/planning/trip_overview.txt"), "w") as f:
    f.write("Fall Oregon Backcountry Trip 2024\nLocation: Cascade Range, Oregon (approx. 44.5°N, 121.7°W)\nDuration: 3 days\nStudents: 12 undergraduates\nInstructor: To be confirmed\nObjective: Apply classroom navigation skills in real terrain.\n")

# Resources placeholder
with open(os.path.join(BASE, "wilderness_school/courses/navigation_101/resources/map_symbols_reference.txt"), "w") as f:
    f.write("Map Symbol Reference (General)\nBlue = water features\nGreen = vegetation\nBrown = contour lines and elevation\nBlack = human-made features\nRed/Pink = roads and boundaries\nSee USGS topo legend for full symbol list.\n")

# --- PRIMARY PROBLEM FILES (messy draft notes with deliberate errors) ---

# Draft 1: Route planning notes with WRONG Naismith's Rule calculation and WRONG scale conversion
draft_route = {
    "document_type": "route_planning_draft",
    "version": "0.3",
    "author": "J. Hartwell (intern)",
    "status": "NEEDS REVIEW",
    "trip": "Fall Oregon 2024 — Day 2 navigation segment",
    "route_data": {
        "map_scale": "1:24000",
        "map_scale_note": "On this scale, about 3 inches equals 1 mile. Use this for quick measurement.",
        "start_point_description": "Trailhead parking lot",
        "end_point_description": "Summit campsite",
        "horizontal_distance_miles": 4.5,
        "elevation_gain_feet": 2800,
        "estimated_time_calculation": {
            "method": "Naismith Rule",
            "base_time_hours": 1.8,
            "elevation_adjustment_note": "Add 15 minutes for every 1000 feet of elevation gain",
            "elevation_adjustment_minutes": 42,
            "total_estimated_time_hours": 2.5,
            "notes": "Calculation seems off, please double-check"
        },
        "pace_count_reference": {
            "description": "Count double-steps (every time left foot hits) per 100m",
            "typical_range_per_100m": "45-55 double-paces",
            "note": "Use this to measure distance while walking"
        }
    },
    "comments": [
        "Draft only — numbers need verification against instructor materials",
        "Naismith calc may be wrong, intern used 15 min/1000ft",
        "Scale conversion note seems off too"
    ]
}

with open(os.path.join(BASE, "wilderness_school/courses/navigation_101/drafts/route_planning_draft.json"), "w") as f:
    json.dump(draft_route, f, indent=2)

# Draft 2: Compass/declination briefing with WRONG declination (says west instead of east, and wrong value)
draft_compass = {
    "document_type": "compass_briefing_draft",
    "version": "0.2",
    "author": "P. Reyes (returning instructor)",
    "status": "NEEDS REVIEW",
    "location": {
        "region": "Oregon, USA",
        "general_coords": "44.5N, 121.7W",
        "hemisphere": "Northern"
    },
    "declination_info": {
        "value_degrees": 8,
        "direction": "west",
        "source": "Remembered from a trip years ago — needs verification",
        "application_note": "Subtract declination from compass bearing to get true bearing",
        "warning": "THIS MAY BE OUTDATED — please verify with current source"
    },
    "compass_technique_notes": {
        "red_in_shed": "Align the red needle with the orienting arrow",
        "bearing_taking_steps": [
            "Place compass edge along desired travel line on map",
            "Direction-of-travel arrow points toward destination",
            "Rotate bezel until orienting lines parallel to map north-south grid",
            "Read bearing at index line"
        ],
        "common_mistake": "Holding compass tilted — keep it level"
    },
    "comments": [
        "Declination for Oregon is uncertain — intern looked it up but got a different number",
        "Some sources say east, some say west — confused on this"
    ]
}

with open(os.path.join(BASE, "wilderness_school/courses/navigation_101/drafts/compass_briefing_draft.json"), "w") as f:
    json.dump(draft_compass, f, indent=2)

# Draft 3: Grid reference and star navigation with WRONG grid reference order AND wrong hemisphere star method
draft_nav_methods = {
    "document_type": "navigation_methods_draft",
    "version": "0.4",
    "author": "M. Chung (volunteer)",
    "status": "NEEDS REVIEW",
    "grid_reference_system": {
        "system_used": "UTM",
        "country": "USA",
        "reading_order": "Read northing (up) first, then easting (right) — northing then easting",
        "mnemonic": "Go up before you go across",
        "six_figure_steps": [
            "Read the northing (vertical) line below your point",
            "Estimate tenths up to your point",
            "Read the easting (horizontal) line to the left of your point",
            "Estimate tenths across to your point",
            "Combine: northing digits first, then easting digits"
        ],
        "note": "Volunteer was not sure about the order — please verify"
    },
    "star_navigation": {
        "applicable_hemisphere": "Northern",
        "primary_method": "Southern Cross method",
        "steps": [
            "Find the Southern Cross (Crux) — four bright stars",
            "Extend the long axis 4.5 times its length",
            "That point is roughly the South Celestial Pole",
            "Drop a line to the horizon — that direction is south"
        ],
        "polaris_note": "Polaris not visible from Oregon — use Southern Cross instead",
        "backup_method": "Use Big Dipper pointer stars to find Polaris"
    },
    "sun_navigation": {
        "shadow_stick_method": {
            "applicable": True,
            "steps": [
                "Place stick vertically in ground",
                "Mark shadow tip with rock",
                "Wait 15-20 minutes",
                "Mark new shadow tip",
                "Line between marks runs east-west (first mark east, second mark west)",
                "Stand with east on left, west on right — facing north"
            ]
        }
    },
    "comments": [
        "Grid reference order is uncertain — need someone to verify",
        "Star nav section may have Southern/Northern hemisphere mixed up",
        "Shadow stick east/west labels might be backwards too"
    ]
}

with open(os.path.join(BASE, "wilderness_school/courses/navigation_101/drafts/navigation_methods_draft.json"), "w") as f:
    json.dump(draft_nav_methods, f, indent=2)

# Draft 4: STOP protocol with some correct and some scrambled steps
draft_emergency = {
    "document_type": "emergency_protocol_draft",
    "version": "0.1",
    "author": "Committee draft",
    "status": "NEEDS REVIEW",
    "stop_protocol": {
        "acronym": "STOP",
        "S": {
            "word": "Search",
            "instruction": "Immediately search for landmarks you recognize. Keep moving until you find something familiar."
        },
        "T": {
            "word": "Think",
            "instruction": "When did you last know where you were? What have you done since? How long walking? What direction? Can you retrace?"
        },
        "O": {
            "word": "Observe",
            "instruction": "Look around. Landmarks? Hear a road, river, people? Higher ground for view? Check map if you have one."
        },
        "P": {
            "word": "Plan",
            "instruction": "Make a deliberate plan. Options: retrace steps, navigate from known position, stay put if people know your route, or move downhill as last resort."
        },
        "distress_signal": {
            "description": "Universal distress signal",
            "number_of_signals": 5,
            "examples": "five whistle blasts, five fires, five rock piles"
        },
        "downhill_rationale": "Downhill leads to water, water leads to trails, trails lead to people."
    },
    "comments": [
        "S definition is wrong — committee had debate about this",
        "Distress signal count may be wrong — some said 3, some said 5",
        "Need to verify against standard wilderness protocol"
    ]
}

with open(os.path.join(BASE, "wilderness_school/courses/navigation_101/drafts/emergency_protocol_draft.json"), "w") as f:
    json.dump(draft_emergency, f, indent=2)

# Master task brief (what the coordinator wants produced)
task_brief = """TASK BRIEF — Navigation Coordinator
Date: 2024-10-01
Prepared by: Director of Curriculum

We have four draft documents in the navigation_101/drafts/ folder that need to be
consolidated into a single, CORRECTED navigation briefing package for our Fall Oregon trip.

Multiple interns and volunteers contributed to these drafts and several contain factual errors.
All data must be verified against our primary skill reference materials and corrected.

OUTPUT REQUIRED: A single JSON file named "navigation_briefing.json"

The file must contain one top-level JSON object with the following sections:

1. "route_timing" — corrected route time estimate
2. "compass_setup" — corrected declination info for Oregon (US West Coast)
3. "grid_reference" — corrected UTM reading procedure
4. "star_navigation_north" — correct star navigation for NORTHERN hemisphere
5. "emergency_protocol" — correct STOP acronym and distress signal
6. "pace_count" — correct typical double-pace range per 100m
7. "map_scale_rule" — correct 1:24000 scale rule of thumb

Every section must contain a "corrected" boolean field indicating whether corrections were
needed, and the accurate data fields. See our skill reference documentation for correct values.
"""

with open(os.path.join(BASE, "wilderness_school/courses/navigation_101/TASK_BRIEF.txt"), "w") as f:
    f.write(task_brief)

print("Workspace generated successfully.")
print("Draft files with deliberate errors placed in: wilderness_school/courses/navigation_101/drafts/")
print("Task brief at: wilderness_school/courses/navigation_101/TASK_BRIEF.txt")