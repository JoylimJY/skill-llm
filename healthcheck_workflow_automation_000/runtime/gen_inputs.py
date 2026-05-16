import os
import json
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# Create a realistic, deeply nested directory structure with distractor files
dirs = [
    workspace / "projects" / "fitness-app" / "src" / "components",
    workspace / "projects" / "fitness-app" / "src" / "utils",
    workspace / "projects" / "fitness-app" / "tests",
    workspace / "projects" / "fitness-app" / "config",
    workspace / "personal" / "logs" / "2024",
    workspace / "personal" / "logs" / "2023",
    workspace / "personal" / "notes",
    workspace / "tools" / "scripts",
    workspace / "tools" / "backups",
    workspace / "data" / "raw",
    workspace / "data" / "processed",
]

for d in dirs:
    d.mkdir(parents=True, exist_ok=True)

# Distractor files - realistic but irrelevant
distractor_files = {
    workspace / "projects" / "fitness-app" / "src" / "components" / "WaterTracker.jsx": 
        "export default function WaterTracker() { return <div>Track water</div>; }",
    
    workspace / "projects" / "fitness-app" / "src" / "utils" / "dateHelper.js":
        "module.exports = { formatDate: (d) => new Date(d).toLocaleDateString() };",
    
    workspace / "projects" / "fitness-app" / "tests" / "water.test.js":
        "describe('water', () => { it('should track cups', () => { expect(true).toBe(true); }); });",
    
    workspace / "projects" / "fitness-app" / "config" / "app.config.json":
        json.dumps({"appName": "FitnessApp", "version": "2.1.0", "debug": False}),
    
    workspace / "personal" / "logs" / "2024" / "exercise_log.csv":
        "date,exercise,duration\n2024-01-15,running,30\n2024-01-16,cycling,45\n2024-01-17,yoga,60",
    
    workspace / "personal" / "logs" / "2023" / "weight_log.csv":
        "date,weight_kg\n2023-12-01,72.5\n2023-12-15,71.8\n2023-12-31,71.2",
    
    workspace / "personal" / "notes" / "goals_2024.txt":
        "1. Drink 8 cups of water daily\n2. Sleep 7-8 hours\n3. Exercise 3x per week",
    
    workspace / "tools" / "scripts" / "backup.sh":
        "#!/bin/bash\ntar -czf backup_$(date +%Y%m%d).tar.gz /workspace/data/",
    
    workspace / "tools" / "backups" / "health_backup_old.json":
        # This is a DISTRACTOR - wrong format, wrong location, should NOT be used
        json.dumps({"records": [{"type": "water", "amount": 5}], "version": "0.9"}),
    
    workspace / "data" / "raw" / "nutrition_data.json":
        json.dumps({"meals": [{"name": "lunch", "calories": 650}, {"name": "dinner", "calories": 800}]}),
    
    workspace / "data" / "processed" / "weekly_summary.json":
        json.dumps({"week": "2024-W03", "avg_water_cups": 6.5, "avg_sleep_hours": 7.2}),
    
    workspace / "projects" / "fitness-app" / "package.json":
        json.dumps({"name": "fitness-app", "version": "1.0.0", "dependencies": {"react": "^18.0.0"}}),
}

for filepath, content in distractor_files.items():
    filepath.write_text(content)

# Create the SKILL.md in workspace so the agent can reference it
skill_content = """---
name: healthcheck
description: Track water and sleep with JSON file storage
version: 1.0.2
tags: health, tracking
---

# Health Tracker

Simple tracking for water intake and sleep using JSON file.

## Data Format

File: `{baseDir}/health-data.json`

```json
{
  "water": [{"time": "ISO8601", "cups": 2}],
  "sleep": [{"time": "ISO8601", "action": "sleep|wake"}]
}
```

## Add Water Record

When user says "uống X cốc" or "uống nước X cốc":

```bash
node -e "const fs=require('fs');const f='{baseDir}/health-data.json';let d={water:[],sleep:[]};try{d=JSON.parse(fs.readFileSync(f))}catch(e){}d.water.push({time:new Date().toISOString(),cups:CUPS});fs.writeFileSync(f,JSON.stringify(d));console.log('Da ghi: '+CUPS+' coc')"
```

Replace `CUPS` with number from user input.

## Add Sleep Record

When user says "đi ngủ":

```bash
node -e "const fs=require('fs');const f='{baseDir}/health-data.json';let d={water:[],sleep:[]};try{d=JSON.parse(fs.readFileSync(f))}catch(e){}d.sleep.push({time:new Date().toISOString(),action:'sleep'});fs.writeFileSync(f,JSON.stringify(d));console.log('Da ghi: di ngu')"
```

## Add Wake Record

When user says "thức dậy" or "dậy rồi":

```bash
node -e "const fs=require('fs');const f='{baseDir}/health-data.json';let d={water:[],sleep:[]};try{d=JSON.parse(fs.readFileSync(f))}catch(e){}const last=d.sleep.filter(s=>s.action==='sleep').pop();d.sleep.push({time:new Date().toISOString(),action:'wake'});fs.writeFileSync(f,JSON.stringify(d));if(last){const h=((new Date()-new Date(last.time))/3600000).toFixed(1);console.log('Da ngu: '+h+' gio')}else{console.log('Da ghi: thuc day')}"
```

## View Stats

When user says "thống kê" or "xem thống kê":

```bash
node -e "const fs=require('fs');const f='{baseDir}/health-data.json';let d={water:[],sleep:[]};try{d=JSON.parse(fs.readFileSync(f))}catch(e){}console.log('Water:',d.water.length,'records');console.log('Sleep:',d.sleep.length,'records');const today=d.water.filter(w=>new Date(w.time).toDateString()===new Date().toDateString());console.log('Today:',today.reduce((s,w)=>s+w.cups,0),'cups')"
```

## Update Record

To update last water entry:

```bash
node -e "const fs=require('fs');const f='{baseDir}/health-data.json';let d=JSON.parse(fs.readFileSync(f));d.water[d.water.length-1].cups=NEW_CUPS;fs.writeFileSync(f,JSON.stringify(d));console.log('Updated')"
```

## Delete Record

To delete last water entry:

```bash
node -e "const fs=require('fs');const f='{baseDir}/health-data.json';let d=JSON.parse(fs.readFileSync(f));d.water.pop();fs.writeFileSync(f,JSON.stringify(d));console.log('Deleted')"
```

## Notes

- Uses Node.js built-in modules only
- File auto-created if missing
- All timestamps in ISO8601 format
"""

(workspace / "SKILL.md").write_text(skill_content)

# Create a task instruction file (the business prompt artifact, not a hint)
task_file = workspace / "daily_health_log_task.txt"
task_file.write_text(
    "Daily Health Logging Session\n"
    "============================\n"
    "User: remote_worker_alex\n"
    "Date: Today\n"
    "Session notes: Need to log morning hydration and last night's sleep.\n"
    "Corrections may be needed if entries are wrong.\n"
)

print("Workspace initialized successfully.")
print(f"Files created: {len(distractor_files)} distractor files + SKILL.md + task file")
print(f"Directory structure: {len(dirs)} directories")