import os
import random

random.seed(42)

workspace = "/workspace"

# Create distractor directory structure
dirs = [
    "docs/legacy/v1",
    "docs/legacy/v2",
    "docs/current/api",
    "docs/current/guides",
    "docs/current/reference",
    "docs/archive/2021",
    "docs/archive/2022",
    "assets/images",
    "assets/diagrams",
    "build/output",
    "tools/scripts",
    "config/profiles",
]

for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files (non-markdown, irrelevant)
distractors = {
    "docs/current/api/openapi.yaml": "openapi: 3.0.0\ninfo:\n  title: API\n  version: 1.0.0\n",
    "docs/current/api/endpoints.json": '{"endpoints": ["/api/v1/devices", "/api/v1/patients"]}',
    "config/profiles/default.json": '{"theme": "light", "lang": "en"}',
    "config/profiles/strict.json": '{"lint": true, "strict": true}',
    "tools/scripts/deploy.sh": "#!/bin/bash\necho 'deploy'\n",
    "tools/scripts/validate.py": "# validation placeholder\nprint('ok')\n",
    "assets/images/placeholder.txt": "image assets go here",
    "assets/diagrams/arch.txt": "architecture diagram placeholder",
    "build/output/build.log": "Build completed at 2024-01-15 14:32:00\nAll checks passed.\n",
    "docs/archive/2021/index.txt": "archived content - do not edit",
    "docs/archive/2022/notes.txt": "see current docs for updated content",
    "docs/current/guides/style-notes.txt": "internal style notes - NOT markdown",
}

for path, content in distractors.items():
    with open(os.path.join(workspace, path), "w") as f:
        f.write(content)

# ============================================================
# MESSY MARKDOWN FILES to be processed
# These simulate real-world legacy documentation with many issues:
# - Mixed list markers
# - Inconsistent emphasis (mix of * and _)
# - Multiple consecutive blank lines
# - Trailing whitespace
# - Inconsistent heading styles
# - Missing blank lines around headings
# ============================================================

messy_docs = {}

# File 1: Device Overview - many formatting problems
messy_docs["docs/legacy/v1/device-overview.md"] = """\
# Device Overview   
Device overview for CardioTrack 3000.   

## Introduction   
The CardioTrack 3000 is a **cardiac monitoring** device.


It features *real-time analysis* and __remote connectivity__.


### Key Components
* Power supply module
- Data acquisition board
* Display unit
- Wireless transceiver

## Specifications   

|Parameter|Value|
|---------|-----|
|Sampling Rate|1000 Hz|
|Battery Life|72 hours|

## Safety Information

This device MUST be operated by *trained personnel* only.



__Warning:__ Do not expose to moisture.

### Contraindications
* Pacemaker users   
- Patients with metal implants   
* Individuals under 18 years   

## Software Interface
```python
device = CardioTrack()
device.start_monitoring()
```

For more details, see [User Manual](./user-manual.md).

"""

# File 2: Installation Guide - different mess
messy_docs["docs/legacy/v1/installation-guide.md"] = """\
Installation Guide
==================

Prerequisites
-------------

Before installing, ensure you have:
1. A compatible operating system
2. Administrator privileges
3. Network connectivity


### Step 1: Download
Download the installer from our __secure portal__.


Visit *https://cardiotrack.example.com/download* to get the latest version.

### Step 2: Verify Checksum
Run the following command:

    sha256sum cardiotrack-installer.exe

Compare with the provided checksum in the *release notes*.

### Step 3: Install
Execute the installer with __elevated privileges__:

```bash
sudo ./cardiotrack-installer.sh --accept-license
```


After installation, the service starts *automatically*.

#### Post-Install Checks
+ Verify service status
+ Check log files   
+ Run self-test   

## Troubleshooting   

Common issues:

* __Error 101__: Permission denied - Run as administrator   
* __Error 202__: Network timeout - Check firewall settings   
* *Error 303*: Missing dependency - Install prerequisites   


Contact *support@cardiotrack.example.com* for assistance.
"""

# File 3: API Reference - nested lists, code issues
messy_docs["docs/legacy/v2/api-reference.md"] = """\
# API Reference   

## Endpoints

### GET /api/v1/status

Returns the device status.

**Request Headers:**
- Content-Type: application/json   
- Authorization: Bearer {token}   

**Response:**

```json
{
  "status": "active",
  "uptime": 3600
}
```

**Status Codes:**
* 200: Success   
- 401: Unauthorized   
+ 500: Internal error   

### POST /api/v1/readings

Submit a new reading.


**Request Body:**
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "bpm": 72,
  "spo2": 98
}
```

The system processes readings *asynchronously*.


Results are returned via *webhook* or __polling__.

## Authentication

All endpoints require __Bearer token__ authentication.

Tokens expire after *24 hours* and must be refreshed.


### Token Refresh
Call the __refresh endpoint__ with your *current token*:

```bash
curl -X POST https://api.cardiotrack.com/auth/refresh \\
  -H 'Authorization: Bearer OLD_TOKEN'
```


__Note:__ Store tokens *securely* in your application.
"""

# File 4: Calibration Procedure - setext headings, plus markers, extra blanks
messy_docs["docs/legacy/v2/calibration-procedure.md"] = """\
Calibration Procedure
=====================

Overview
--------

This document describes the *monthly calibration* procedure for CardioTrack devices.



Prerequisites
-------------

+ Calibrated reference device   
+ Calibration kit (Part #CK-3000)   
+ Qualified biomedical engineer   


Procedure
---------

### Phase 1: Initial Checks

Before calibration:

1. Power cycle the device   
2. Allow 15-minute warm-up   
3. Connect reference device   

### Phase 2: Signal Calibration

Configure *baseline parameters*:

```python
calibrator.set_baseline(
    bpm_ref=60,
    spo2_ref=98,
    temp_ref=36.5
)
```


Run the __calibration sequence__:

+ Step A: Zero-point calibration   
- Step B: Span calibration   
+ Step C: Linearity check   

### Phase 3: Verification

After calibration, verify using *test signals*:



__Acceptance criteria:__
* BPM accuracy: ±2 BPM   
- SpO2 accuracy: ±2%   
* Temperature: ±0.1°C   


Record results in the __calibration log__.

Completion
----------

After successful calibration:

1. Update the *calibration certificate*   
2. Affix the __calibration sticker__   
3. Update the *device registry*   

"""

# File 5: Release Notes - straightforward but has issues
messy_docs["docs/current/reference/release-notes.md"] = """\
# Release Notes   


## Version 3.2.1 (2024-01-15)

### Bug Fixes
- Fixed *memory leak* in data acquisition module   
- Resolved __timezone handling__ in timestamp processing   
- Corrected *off-by-one error* in buffer management   

### Improvements   
* Enhanced __encryption__ for data transmission   
+ Improved *battery life* optimization   
* Updated __firmware__ signing process   


## Version 3.2.0 (2023-12-01)

### New Features
- Real-time *ECG analysis* using machine learning   
- __Bluetooth 5.0__ connectivity support   
- *Cloud synchronization* with configurable intervals   


### Breaking Changes


__API v1__ endpoints are now *deprecated*.

Migrate to __API v2__ before *March 2024*.

#### Migration Guide
1. Update authentication to use *OAuth 2.0*   
2. Replace __legacy endpoints__ with new *REST paths*   
3. Update *webhook URLs* to new domain   

## Known Issues   

- *Issue #4521*: Intermittent __disconnect__ on Android 14   
- __Issue #4498__: *Slow startup* on low-memory devices   
"""

for path, content in messy_docs.items():
    full_path = os.path.join(workspace, path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w") as f:
        f.write(content)

print("Workspace initialized successfully.")
print(f"Created {len(messy_docs)} messy markdown files to process.")
print(f"Created {len(distractors)} distractor files.")