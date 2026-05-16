import os
import random

random.seed(42)

# --- Create workspace directory structure ---
workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# Create distractor directories / files to simulate a real messy environment
dirs = [
    "raw_exports/garmin",
    "raw_exports/apple_health",
    "raw_exports/strava",
    "chat_logs",
    "race_results",
    "nutrition/logs",
    "nutrition/plans",
    "gear",
    "old_notes",
    "tmp",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# --- Distractor files ---
distractor_files = {
    "raw_exports/garmin/README.txt": "Garmin Connect export. See garmin.com for format docs.",
    "raw_exports/garmin/sleep_2023.csv": "date,deep_sleep_min,light_sleep_min,rem_min\n2023-11-01,90,180,60\n2023-11-02,40,200,55\n",
    "raw_exports/apple_health/export_info.xml": "<ExportDate value='2024-01-15'/><Me HKCharacteristicTypeIdentifierBiologicalSex='HKBiologicalSexMale'/>",
    "raw_exports/apple_health/workout_summary.json": '{"workouts": 312, "total_hours": 410.5, "sport_types": ["running","cycling","swimming"]}',
    "raw_exports/strava/athlete_profile.json": '{"id": 9923841, "firstname": "Marcus", "lastname": "Holt", "city": "Boulder", "state": "CO", "country": "US", "sex": "M", "premium": true, "created_at": "2017-03-14"}',
    "raw_exports/strava/kudos_received.txt": "2024-01-10: Great ride Marcus!\n2024-03-22: Beast mode!\n2024-10-06: Ironman finisher!!\n",
    "nutrition/logs/macros_oct.csv": "date,calories,protein_g,carbs_g,fat_g\n2024-10-01,3200,180,390,75\n2024-10-02,2800,160,340,65\n",
    "nutrition/plans/race_week_protocol.txt": "Carb load starting 3 days before. Cut fiber 48h before. 500mg sodium/hour on bike.\n",
    "gear/bike_specs.txt": "Trek Speed Concept SLR 9. Shimano Dura-Ace Di2. Reynolds 65mm carbon wheels. Weight: 7.2kg\n",
    "gear/shoe_log.txt": "Hoka Clifton 9 - 487 miles (replace soon)\nOn Running Cloudflow 4 - 122 miles\n",
    "old_notes/2023_goals.txt": "Sub 10h Ironman. Run 5:30 marathon. FTP >300w.\n",
    "tmp/sync_errors.log": "2024-11-01 ERROR: Apple Health sync timeout\n2024-11-02 WARN: Strava rate limit\n",
    "race_results/placeholder.txt": "See race_results_2024.txt for full data.",
}

for rel_path, content in distractor_files.items():
    full_path = os.path.join(workspace, rel_path)
    with open(full_path, "w") as f:
        f.write(content)

# --- CORE INPUT FILES the agent must process ---

# 1. Garmin wearable data export (messy CSV-like format)
garmin_data = """\
GARMIN CONNECT EXPORT - Marcus Holt - Generated 2024-11-15
==========================================================
ACTIVITY LOG (last 90 days)
Date,Activity,Duration_min,HR_avg,Notes
2024-08-19,Swim,45,138,masters swim session
2024-08-21,Bike,180,148,long ride Sunshine Canyon
2024-08-22,Run,65,152,tempo run felt strong
2024-08-24,Swim,40,135,easy recovery
2024-08-26,Bike,210,155,Boulder Ironman simulation ride
2024-09-02,Run,90,158,20km long run AM
2024-09-04,Bike,150,145,
2024-09-09,Run,55,161,intervals track
2024-09-14,Swim,50,140,open water practice
2024-09-16,Bike,300,150,race sim 8h total training day
2024-09-21,Run,75,154,
2024-09-25,Rest,0,0,rest day
2024-09-27,Bike,90,143,easy spin recovery
2024-10-05,Race,660,159,IRONMAN World Championship Kona
2024-10-12,Rest,0,0,post-race week
2024-10-13,Rest,0,0,
2024-10-14,Walk,30,98,easy walk still sore
2024-11-01,Swim,45,136,back to training
2024-11-04,Bike,120,147,
2024-11-06,Run,50,150,
2024-11-08,Swim,40,133,

SLEEP DATA (last 30 days)
Date,Total_Sleep_h,Deep_Sleep_h,Notes
2024-10-15,9.2,2.1,
2024-10-16,8.8,1.9,
2024-10-17,4.1,0.8,team dinner lots of wine
2024-10-18,7.2,1.4,felt groggy morning workout poor
2024-10-19,8.1,1.8,
2024-10-20,7.9,1.7,
2024-10-21,4.8,0.9,alcohol night out poor workout next day
2024-10-22,6.8,1.3,
2024-10-28,5.1,0.7,late flight sleep disrupted
2024-10-29,6.5,1.2,workout felt flat travel fatigue
2024-11-01,8.5,2.0,
2024-11-02,8.3,1.9,
2024-11-03,7.8,1.7,

HRV DATA
Date,HRV_ms,Readiness,Recommendation
2024-11-01,68,87,Train
2024-11-02,71,91,Train Hard
2024-11-03,52,64,Easy Only
2024-11-04,49,58,Rest or Easy
2024-11-08,65,82,Train
"""

with open(os.path.join(workspace, "raw_exports/garmin/export_full_2024.txt"), "w") as f:
    f.write(garmin_data)

# 2. Conversation/chat log
chat_log = """\
=== FITNESS CHAT LOG - Marcus ===

[2024-09-10 07:12] Marcus: heading out for morning run, coffee kicking in nicely
[2024-09-10 07:15] Coach: nice, tempo pace today
[2024-09-10 08:45] Marcus: smashed it. Coffee before workouts is a game changer for me, feels like +20% intensity every time

[2024-09-16 21:30] Marcus: 8 hour training day done. legs are dead but in a good way
[2024-09-17 08:00] Coach: how you feeling?
[2024-09-17 08:03] Marcus: surprisingly ok. needed 9h sleep though

[2024-09-25 06:50] Marcus: taking today off, too tired to push, HRV crashed
[2024-09-25 07:02] Coach: smart call
[2024-09-25 07:05] Marcus: yeah when im too tired i know its not worth it, rather skip and come back strong

[2024-10-05 16:42] Marcus: FINISHED KONA. 9:47:32. sub 10 was the dream
[2024-10-05 16:50] Coach: INCREDIBLE! That's a massive PR!
[2024-10-05 17:00] Marcus: first kona finish too. best day of my life

[2024-10-17 19:30] Marcus: had too much wine at dinner last night, workout this morning was terrible
[2024-10-18 09:15] Coach: how bad?
[2024-10-18 09:17] Marcus: couldn't hit any power targets, called it after 30min. alcohol the night before just destroys my next day

[2024-10-21 22:00] Marcus: another night out, couple drinks. already dreading tomorrow's run
[2024-10-22 09:30] Marcus: yep, run was garbage as expected

[2024-10-28 15:00] Marcus: knee is a bit sore after the travel, nothing serious but keeping an eye on it
[2024-10-29 07:00] Marcus: knee still a bit tweaky, easy spin only

[2024-11-03 07:00] Marcus: HRV low again, gonna do easy swim only today instead of the planned run
[2024-11-03 09:00] Marcus: done. smart call i think. hate rest days but i know i need them
[2024-11-03 09:05] Coach: you're experienced enough to make those calls, no lectures from me :)
[2024-11-03 09:07] Marcus: exactly, just give me the data and ill decide. weekly summary is all i need, not daily check-ins

[2024-11-08 17:00] Marcus: new FTP test today - 318 watts!!
[2024-11-08 17:10] Coach: massive! what was previous?
[2024-11-08 17:11] Marcus: was 298 last April. huge jump. also hit a new swim CSS of 1:24/100m last week
"""

with open(os.path.join(workspace, "chat_logs/marcus_coach_2024.txt"), "w") as f:
    f.write(chat_log)

# 3. Race results file
race_results = """\
ATHLETE: Marcus Holt
AGE GROUP: M35-39

RACE HISTORY 2024
-----------------
Event: IRONMAN 70.3 Oceanside
Date: 2024-04-06
Result: 4:21:15
AG Place: 8/142
Notes: Windy on bike, strong run

Event: Boulder Triathlon Olympic
Date: 2024-06-15
Result: 2:04:33
AG Place: 3/87
Notes: Top 3 AG, first podium of year

Event: IRONMAN World Championship (Kona)
Date: 2024-10-05
Result: 9:47:32
AG Place: 22/310
Notes: Qualified 2025. First Kona finish. Sub-10 goal achieved.

PREVIOUS BESTS (All-time PRs)
------------------------------
Ironman Full: 9:47:32 (set 2024-10-05) *NEW PR*
Ironman 70.3: 4:08:44 (set 2022-09-18)
Olympic Tri: 2:01:19 (set 2021-07-04)
Marathon standalone: 2:58:07 (set 2023-04-16)
FTP (cycling): 318w (set 2024-11-08) *NEW PR*
Swim CSS: 1:24/100m (set 2024-11-01) *NEW PR*
"""

with open(os.path.join(workspace, "race_results/race_results_2024.txt"), "w") as f:
    f.write(race_results)

# 4. Strava activities summary (extra source)
strava_data = """\
STRAVA DATA EXPORT - Marcus Holt
Activity Count: 247 in 2024
Primary Sports: Triathlon (swim/bike/run)
Connected Apps: Garmin Connect (auto-sync), Training Peaks, Wahoo ELEMNT
Segment CRs: 4 (Boulder area climbs)
Followers: 312 | Following: 89
Weekly Training Load: typically 12-18h peak, 8-12h base
Training blocks: Mon/Wed swim AM, Tue/Thu/Sat bike, Wed/Fri/Sun run, structured periodization
"""

with open(os.path.join(workspace, "raw_exports/strava/activities_summary_2024.txt"), "w") as f:
    f.write(strava_data)

print("Workspace generated successfully.")
print(f"Files created in: {workspace}")