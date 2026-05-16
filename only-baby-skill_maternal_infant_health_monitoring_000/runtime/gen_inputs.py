import json
import os
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

random.seed(42)

WORKSPACE = Path("/workspace")
WORKSPACE.mkdir(exist_ok=True)

# Create realistic directory structure with distractor files
dirs = [
    "family_records/medical",
    "family_records/insurance",
    "family_records/appointments",
    "baby_gear/inventory",
    "baby_gear/manuals",
    "hospital_bag/checklist",
    "birth_plan/drafts",
    "nutrition/recipes",
    "logs/archive",
    "photos/metadata",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# Distractor files
distractor_files = {
    "family_records/medical/allergy_notes.txt": "Mother: No known allergies.\nFather: Penicillin allergy noted 2019.",
    "family_records/insurance/policy_2024.json": json.dumps({"provider": "BlueCross", "policyNo": "BC-9921-X", "coverage": "maternity"}),
    "family_records/appointments/antenatal_schedule.csv": "date,type,location\n2024-09-01,scan,City Hospital\n2024-10-15,checkup,GP Surgery",
    "baby_gear/inventory/items.txt": "1x bassinet\n2x swaddle wraps\n1x breast pump\n3x onesies (0-3m)",
    "baby_gear/manuals/pump_manual.txt": "Model: MedPump Pro 3. Max speed: level 9. Cleaning: sterilise every 24h.",
    "hospital_bag/checklist/items.md": "- [ ] Nappy bag\n- [ ] Going home outfit\n- [ ] Phone charger\n- [ ] Snacks for partner",
    "birth_plan/drafts/birth_plan_v1.txt": "Prefer minimal interventions. Epidural if requested. Delayed cord clamping preferred.",
    "birth_plan/drafts/birth_plan_v2.txt": "Updated: water birth preferred. Partner present at all times. No students.",
    "nutrition/recipes/postpartum_smoothie.txt": "Ingredients: banana, oats, almond milk, flaxseed. Blend 1 min.",
    "logs/archive/old_weight_log.json": json.dumps([{"date": "2024-11-01", "weightKg": 3.2}, {"date": "2024-11-08", "weightKg": 3.35}]),
    "photos/metadata/photo_index.json": json.dumps({"count": 47, "lastUpdated": "2024-11-10", "tags": ["newborn", "hospital", "home"]}),
    "family_records/medical/blood_type.txt": "Mother: A+\nBaby: O+ (cord blood test)",
}
for fpath, content in distractor_files.items():
    (WORKSPACE / fpath).write_text(content)

# ─── CONTRACTIONS DATA ───────────────────────────────────────────────────────
# Scenario: Contractions are progressing toward 5-1-1 rule (every 5 min, lasting ~60s, for 1h)
# We design the last ~60 min of data to clearly trigger 5-1-1 so the agent must flag "Seek care"
# Base anchor: 2024-11-12T02:00:00Z
# We'll have 15 contractions total:
# - First 5: irregular/early (long intervals, short durations) → building pattern
# - Last 10: meeting 5-1-1 pattern (every 5 min, ~60s duration, over ~50 min window)

base = datetime(2024, 11, 12, 0, 0, 0, tzinfo=timezone.utc)

contractions = []
cid = 1

# Early irregular contractions (first 5)
irregular_starts = [
    base + timedelta(minutes=0),
    base + timedelta(minutes=18),
    base + timedelta(minutes=34),
    base + timedelta(minutes=48),
    base + timedelta(minutes=61),
]
irregular_durations = [35, 42, 38, 45, 50]  # seconds, short/irregular

for i in range(5):
    st = irregular_starts[i]
    dur = irregular_durations[i]
    et = st + timedelta(seconds=dur)
    contractions.append({
        "id": f"c{cid:03d}",
        "startTime": st.isoformat().replace("+00:00", "Z"),
        "endTime": et.isoformat().replace("+00:00", "Z"),
    })
    cid += 1

# 5-1-1 compliant last 10 contractions
# Start ~02:00, every 5 min, lasting ~60s
five_one_one_start = base + timedelta(hours=2, minutes=0)
for i in range(10):
    st = five_one_one_start + timedelta(minutes=i * 5)
    # slight variation: 58-63 seconds
    dur_seconds = 58 + (i % 3) * 2  # 58, 60, 62, 58, 60, 62, 58, 60, 62, 58
    et = st + timedelta(seconds=dur_seconds)
    contractions.append({
        "id": f"c{cid:03d}",
        "startTime": st.isoformat().replace("+00:00", "Z"),
        "endTime": et.isoformat().replace("+00:00", "Z"),
    })
    cid += 1

# Shuffle slightly (agent must sort)
random.shuffle(contractions)

contractions_path = WORKSPACE / "contractions_2024-11-12.json"
contractions_path.write_text(json.dumps(contractions, indent=2))

# ─── BABY LOGS DATA ──────────────────────────────────────────────────────────
# Baby born 2024-11-06T08:30:00Z → age at latest log ~6 days
# Latest log timestamp: 2024-11-12T04:00:00Z
# 24h window: 2024-11-11T04:00:00Z to 2024-11-12T04:00:00Z
# 48h window: 2024-11-10T04:00:00Z to 2024-11-12T04:00:00Z
# 
# Design: Baby is borderline — only 6 bottle feeds in last 24h (threshold ~8 for newborn),
# 4 wet diapers (threshold 6), 2 dirty (threshold 3-4).
# Also 1 breastfeeding session in last 24h (very short, 8 min).
# This should produce "Monitor" or "Concern" verdict for baby.

birthday = datetime(2024, 11, 6, 8, 30, 0, tzinfo=timezone.utc)
latest_ts = datetime(2024, 11, 12, 4, 0, 0, tzinfo=timezone.utc)
window_24h_start = latest_ts - timedelta(hours=24)

baby_log = []
log_id = 1

def mkts(dt):
    return dt.isoformat().replace("+00:00", "Z")

# ── FEEDING entries (bottle) in last 24h: 6 feeds (below threshold of 8)
feeding_times_24h = [
    window_24h_start + timedelta(hours=1, minutes=20),
    window_24h_start + timedelta(hours=4, minutes=10),
    window_24h_start + timedelta(hours=7, minutes=5),
    window_24h_start + timedelta(hours=10, minutes=45),
    window_24h_start + timedelta(hours=15, minutes=30),
    window_24h_start + timedelta(hours=20, minutes=0),
]
feeding_volumes_24h = [55, 60, 45, 65, 50, 55]  # mL — smallish but not zero

for i, (ft, vol) in enumerate(zip(feeding_times_24h, feeding_volumes_24h)):
    baby_log.append({
        "id": f"bl{log_id:04d}",
        "timestamp": mkts(ft),
        "type": "feeding",
        "feedingDetails": {"volumeML": vol}
    })
    log_id += 1

# ── FEEDING entries outside 24h (in 48h window): 4 more feeds
feeding_times_48h = [
    window_24h_start - timedelta(hours=5),
    window_24h_start - timedelta(hours=9),
    window_24h_start - timedelta(hours=14),
    window_24h_start - timedelta(hours=20),
]
feeding_volumes_48h = [58, 62, 50, 55]

for i, (ft, vol) in enumerate(zip(feeding_times_48h, feeding_volumes_48h)):
    baby_log.append({
        "id": f"bl{log_id:04d}",
        "timestamp": mkts(ft),
        "type": "feeding",
        "feedingDetails": {"volumeML": vol}
    })
    log_id += 1

# ── BREASTFEEDING entries in last 24h: 1 session (8 minutes = 480 seconds, very short)
bf_time = window_24h_start + timedelta(hours=12, minutes=30)
baby_log.append({
    "id": f"bl{log_id:04d}",
    "timestamp": mkts(bf_time),
    "type": "breastFeeding",
    "breastFeedingDetails": {"durationSeconds": 480}
})
log_id += 1

# ── BREASTFEEDING entries outside 24h: 2 sessions
for hr_offset in [28, 36]:
    bt = window_24h_start - timedelta(hours=hr_offset - 24)
    # Actually place these before 24h window start
    bt2 = window_24h_start - timedelta(hours=hr_offset - 20)
    baby_log.append({
        "id": f"bl{log_id:04d}",
        "timestamp": mkts(window_24h_start - timedelta(hours=4 + hr_offset - 24)),
        "type": "breastFeeding",
        "breastFeedingDetails": {"durationSeconds": 720 + hr_offset * 5}
    })
    log_id += 1

# ── DIAPER entries in last 24h: 4 wet, 2 dirty (below thresholds)
diaper_data_24h = [
    # (hours_after_start, hasPee, hasPoo)
    (2, True, False),
    (5, True, True),
    (8, True, False),
    (11, False, True),  # dirty only
    (16, True, False),
    (21, True, False),
]
for (h, pee, poo) in diaper_data_24h:
    dt = window_24h_start + timedelta(hours=h)
    baby_log.append({
        "id": f"bl{log_id:04d}",
        "timestamp": mkts(dt),
        "type": "diaper",
        "diaperDetails": {"hasPee": pee, "hasPoo": poo}
    })
    log_id += 1

# ── DIAPER entries outside 24h: 5 more (for 48h context)
diaper_data_48h = [
    (3, True, False),
    (7, True, True),
    (12, True, False),
    (17, False, True),
    (22, True, False),
]
for (h, pee, poo) in diaper_data_48h:
    dt = window_24h_start - timedelta(hours=24 - h)
    # These should be before 24h window
    dt2 = window_24h_start - timedelta(hours=h)
    baby_log.append({
        "id": f"bl{log_id:04d}",
        "timestamp": mkts(dt2),
        "type": "diaper",
        "diaperDetails": {"hasPee": pee, "hasPoo": poo}
    })
    log_id += 1

# Shuffle baby log (agent must sort/filter properly)
random.shuffle(baby_log)

baby_data = {
    "birthday": birthday.isoformat().replace("+00:00", "Z"),
    "babyLog": baby_log
}

baby_logs_path = WORKSPACE / "babyLogs_2024-11-12.json"
baby_logs_path.write_text(json.dumps(baby_data, indent=2))

# Place an additional red-herring JSON in logs/archive that looks similar but is old
old_contractions = [
    {"id": "c001", "startTime": "2024-10-01T10:00:00Z", "endTime": "2024-10-01T10:00:30Z"},
    {"id": "c002", "startTime": "2024-10-01T10:25:00Z", "endTime": "2024-10-01T10:25:28Z"},
]
(WORKSPACE / "logs/archive/contractions_2024-10-01.json").write_text(json.dumps(old_contractions, indent=2))

old_baby = {
    "birthday": "2024-10-28T09:00:00Z",
    "babyLog": [
        {"id": "bl0001", "timestamp": "2024-10-29T08:00:00Z", "type": "diaper",
         "diaperDetails": {"hasPee": True, "hasPoo": False}}
    ]
}
(WORKSPACE / "logs/archive/babyLogs_2024-10-01.json").write_text(json.dumps(old_baby, indent=2))

print("Workspace generated successfully.")
print(f"  contractions: {contractions_path}")
print(f"  baby logs:    {baby_logs_path}")
print(f"  Total baby log entries: {len(baby_log)}")