#!/usr/bin/env python3
"""Generate a realistic, messy medical-device-docs workspace for the markdown lint task."""

import os
import random

random.seed(42)

BASE = "/workspace"

# ---------------------------------------------------------------------------
# Directory structure
# ---------------------------------------------------------------------------
dirs = [
    "docs/clinical",
    "docs/clinical/protocols",
    "docs/regulatory",
    "docs/regulatory/submissions",
    "docs/engineering",
    "docs/engineering/architecture",
    "docs/engineering/api",
    "docs/onboarding",
    "scripts",
    "src/core",
    "src/utils",
    "tests",
    ".github/workflows",
]
for d in dirs:
    os.makedirs(os.path.join(BASE, d), exist_ok=True)

# ---------------------------------------------------------------------------
# Helper: write file
# ---------------------------------------------------------------------------
def write(path, content):
    full = os.path.join(BASE, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w") as f:
        f.write(content)

# ---------------------------------------------------------------------------
# Distractor non-markdown files (should not be touched)
# ---------------------------------------------------------------------------
write("src/core/device_monitor.py", """\
class DeviceMonitor:
    def __init__(self):
        self.status = "idle"

    def poll(self):
        pass
""")

write("src/utils/logger.py", """\
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
""")

write("tests/test_monitor.py", """\
def test_status():
    assert True
""")

write(".github/workflows/ci.yml", """\
name: CI
on: [push]
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
""")

write("src/core/__init__.py", "")
write("src/utils/__init__.py", "")

write("requirements.txt", "pytest==7.4.0\nrequests==2.31.0\n")
write("setup.py", "from setuptools import setup\nsetup(name='meddevice')\n")

# ---------------------------------------------------------------------------
# The check-horizontal-rules.sh script (already exists per SKILL.md)
# ---------------------------------------------------------------------------
write("scripts/check-horizontal-rules.sh", r"""#!/usr/bin/env bash
# Check for horizontal rules outside YAML frontmatter
set -euo pipefail

errors=0
for file in "$@"; do
    in_frontmatter=0
    line_num=0
    first_line=1
    while IFS= read -r line || [[ -n "$line" ]]; do
        line_num=$((line_num + 1))
        if [[ $first_line -eq 1 ]]; then
            first_line=0
            if [[ "$line" =~ ^---[[:space:]]*$ ]]; then
                in_frontmatter=1
                continue
            fi
        fi
        if [[ $in_frontmatter -eq 1 ]]; then
            if [[ "$line" =~ ^---[[:space:]]*$ ]]; then
                in_frontmatter=0
            fi
            continue
        fi
        if [[ "$line" =~ ^[[:space:]]*[-*_][[:space:]]*[-*_][[:space:]]*[-*_][-*_\ ]*$ ]]; then
            echo "${file}:${line_num}: horizontal rule found"
            errors=$((errors + 1))
        fi
    done < "$file"
done

if [[ $errors -gt 0 ]]; then
    echo "Error: $errors horizontal rule(s) found outside frontmatter" >&2
    exit 1
fi
exit 0
""")

# ---------------------------------------------------------------------------
# MESSY MARKDOWN FILES
# ---------------------------------------------------------------------------

# 1. Clinical protocol with YAML frontmatter + HR separators + missing code lang
write("docs/clinical/protocols/infusion_protocol.md", """\
---
title: IV Infusion Protocol
version: 2.3.1
status: approved
---

# IV Infusion Protocol

This document outlines the standard procedure for intravenous infusion in ICU settings.

---

## Patient Preparation

Verify patient identity using two identifiers before initiating infusion.

1. Check allergy bracelet
2. Confirm order in EHR
3. Perform hand hygiene

---

## Equipment Setup

Gather the following equipment:

- IV pole
- Infusion pump (Model X200)
- Primary tubing set
- 0.9% NaCl solution

```
# Sample pump configuration
pump.set_rate(125)  # mL/hr
pump.set_volume(500)
pump.start()
```

---

## Monitoring Parameters

| Parameter | Frequency | Alert Threshold |
|-----------|-----------|-----------------|
| Flow rate | Every 30 min | ±10% deviation |
| Site condition | Every hour | Redness, swelling |

---

## Adverse Events

Report any adverse events immediately using the incident reporting system.

```
incident_report = {
    "type": "infusion_complication",
    "severity": "moderate"
}
submit_report(incident_report)
```
""")

# 2. Regulatory submission doc with HR + duplicate headings (siblings) + missing lang
write("docs/regulatory/submissions/510k_summary.md", """\
---
document_type: 510k_summary
submission_date: 2024-01-15
---

# 510(k) Premarket Notification Summary

## Device Description

The MedFlow X200 is a volumetric infusion pump designed for hospital use.

---

## Intended Use

Intended for the controlled delivery of fluids, medications, and nutrients.

### Indications

Adult and pediatric patients requiring parenteral therapy.

### Indications

Critically ill patients in ICU/CCU settings requiring continuous medication infusion.

---

## Technological Characteristics

The device incorporates the following key technologies:

```
SAFETY_CLASS = "IIb"
SOFTWARE_LEVEL = "SIL-2"
EMC_STANDARD = "IEC 60601-1-2"
```

---

## Performance Testing

All bench testing performed per FDA guidance document.

```
test_results = {
    "flow_accuracy": "±2%",
    "occlusion_pressure": "900 mmHg"
}
```

---

## Conclusion

The MedFlow X200 is substantially equivalent to predicate devices.
""")

# 3. Engineering architecture doc with HR + missing code lang
write("docs/engineering/architecture/system_overview.md", """\
# System Architecture Overview

This document describes the high-level architecture of the MedFlow control software.

---

## Component Diagram

The system consists of three primary layers:

1. **Hardware Abstraction Layer (HAL)**
2. **Clinical Logic Engine (CLE)**
3. **User Interface Layer (UIL)**

---

## Communication Protocol

All inter-component communication uses the internal message bus:

```
bus.publish("pump.command", {"action": "start", "rate": 100})
msg = bus.subscribe("pump.status")
```

---

## Safety Architecture

The safety monitor runs as a separate process with highest priority.

```
if safety_monitor.triggered():
    pump.emergency_stop()
    alarm.activate("OCCLUSION")
```

---

## Deployment

```
docker build -t medflow-control .
docker run --privileged medflow-control
```
""")

# 4. API docs with HR + missing code lang
write("docs/engineering/api/pump_api.md", """\
# Pump Control API Reference

## Overview

REST API for controlling the MedFlow X200 infusion pump.

---

## Authentication

All endpoints require Bearer token authentication.

```
Authorization: Bearer <token>
```

---

## Endpoints

### POST /pump/start

Start infusion with specified parameters.

```
POST /api/v1/pump/start
Content-Type: application/json

{
  "rate_ml_hr": 125,
  "volume_ml": 500,
  "patient_id": "P-10042"
}
```

---

### GET /pump/status

Retrieve current pump status.

```
GET /api/v1/pump/status
```

Response:

```
{
  "status": "running",
  "rate_ml_hr": 125,
  "volume_infused": 87.5
}
```

---

## Error Codes

| Code | Meaning |
|------|---------|
| 4001 | Occlusion detected |
| 4002 | Air-in-line detected |
| 4003 | Door open |
""")

# 5. Onboarding guide - HR + missing lang
write("docs/onboarding/developer_setup.md", """\
# Developer Onboarding Guide

Welcome to the MedFlow software team.

---

## Prerequisites

Install the following tools:

- Python 3.11+
- Docker 24+
- Node.js 20+

---

## Repository Setup

Clone the repository and install dependencies:

```
git clone https://github.com/example/medflow.git
cd medflow
pip install -r requirements.txt
```

---

## Running Tests

```
pytest tests/ -v
```

Expected output:

```
collected 42 items
PASSED tests/test_monitor.py::test_status
```

---

## Code Style

We follow PEP8 for Python. Use the pre-commit hooks.

---
""")

# 6. Clinical doc without frontmatter - HR should still be removed
write("docs/clinical/alarm_management.md", """\
# Alarm Management Policy

---

## Priority Levels

Alarms are classified into three priority levels per IEC 60601-1-8.

| Priority | Color | Sound |
|----------|-------|-------|
| High | Red | Continuous |
| Medium | Yellow | Pulsing |
| Low | Cyan | Single |

---

## Response Times

High priority alarms must be acknowledged within 30 seconds.

```
alarm_handler.set_timeout("HIGH", 30)
alarm_handler.set_timeout("MEDIUM", 120)
```

---

## Escalation

If unacknowledged, alarms escalate to the charge nurse station.

---
""")

# 7. A clean doc that should NOT be broken (no HR, no missing lang) - distractor
write("docs/regulatory/iso_13485_checklist.md", """\
# ISO 13485 Compliance Checklist

## Management Responsibility

- [ ] Quality policy documented
- [ ] Management review conducted quarterly

## Resource Management

- [ ] Training records maintained
- [ ] Infrastructure requirements defined

## Product Realization

- [ ] Risk management per ISO 14971
- [ ] Design controls documented

## Measurement and Improvement

- [ ] Internal audits scheduled
- [ ] CAPA process implemented
""")

# 8. Another distractor - engineering notes, no issues
write("docs/engineering/architecture/data_flow.md", """\
# Data Flow Architecture

## Sensor Input Pipeline

Raw sensor data flows through the following stages:

1. ADC sampling at 1 kHz
2. Digital filtering (low-pass, 50 Hz cutoff)
3. Threshold comparison
4. Event generation

## Persistence Layer

Infusion events are persisted to the local SQLite database for audit trail.

## Telemetry

De-identified telemetry is transmitted to the cloud analytics platform.
""")

print("Workspace generated successfully.")
print("Files created:")
for root, dirs_list, files in os.walk(BASE):
    dirs_list[:] = [d for d in dirs_list if d not in ['node_modules', '.git']]
    for f in files:
        print(f"  {os.path.join(root, f).replace(BASE + '/', '')}")