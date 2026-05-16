#!/usr/bin/env python3
"""
Generates the sandbox workspace for the Apple serial number inventory task.
"""
import os
import json
import random
import textwrap

random.seed(42)

BASE = "/workspace"

# ── directory skeleton ──────────────────────────────────────────────────────
dirs = [
    "scripts",
    "references",
    "data/incoming",
    "data/archive",
    "data/processed",
    "logs",
    "config",
    "tools/helpers",
    "reports/draft",
    "reports/final",
]
for d in dirs:
    os.makedirs(os.path.join(BASE, d), exist_ok=True)

# ── the decode_serial.py script (bundled decoder) ──────────────────────────
# Implements the serial decoding logic from references/serial-format.md
decode_script = textwrap.dedent(r'''
    #!/usr/bin/env python3
    """
    Apple Serial Number Decoder
    Decodes old-format (11-12 character) Apple serial numbers.
    Outputs JSON with manufacturing info and model codes.
    """
    import sys
    import json

    # ── Location codes (position 1-3, greedy match from longest) ──
    LOCATION_CODES = {
        "FC":  "Fountain Colorado, USA",
        "F":   "Fremont, California, USA",
        "XA":  "USA",
        "XB":  "USA",
        "QP":  "USA",
        "G8":  "USA",
        "RN":  "Mexico",
        "GQ":  "Foxconn, Brazil",
        "CK":  "Cork, Ireland",
        "VM":  "Foxconn, Pardubice, Czech Republic",
        "SG":  "Singapore",
        "E":   "Singapore",
        "MB":  "Malaysia",
        "PT":  "Korea",
        "CY":  "Korea",
        "EE":  "Taiwan",
        "QT":  "Taiwan",
        "UV":  "Taiwan",
        "FK":  "Foxconn, Zhengzhou, China",
        "F1":  "Foxconn, Zhengzhou, China",
        "F2":  "Foxconn, Zhengzhou, China",
        "F7":  "China",
        "1C":  "China",
        "4H":  "China",
        "WQ":  "China",
        "W8":  "Shanghai, China",
        "DL":  "Foxconn, China",
        "DM":  "Foxconn, China",
        "DN":  "Foxconn, Chengdu, China",
        "DX":  "Foxconn, Zhengzhou, China",
        "YM":  "Hon Hai/Foxconn, China",
        "7J":  "Hon Hai/Foxconn, China",
        "C02": "Tech Com/Quanta, China",
        "C07": "Tech Com/Quanta, China",
        "C17": "Tech Com/Quanta, China",
        "C0":  "Tech Com/Quanta, China",
        "C3":  "Foxconn, Shenzhen, China",
        "C6K": "Foxconn, Zhengzhou, China",
        "C6":  "Foxconn, Zhengzhou, China",
        "C7":  "Pentragon, Shanghai, China",
        "G0":  "Pegatron, Shanghai, China",
        "G6":  "Foxconn, Shenzhen, China",
        "J2":  "Pegatron, Shanghai, China",
        "H0":  "Foxconn, India",
        "HN":  "Foxconn, India",
        "RM":  "Refurbished/Remanufactured",
    }

    # ── Year codes (position 4) – vowels A,B,E,I,O,U skipped ──
    YEAR_CODES = {
        "C": ("2010", "H1"), "D": ("2010", "H2"),
        "F": ("2011", "H1"), "G": ("2011", "H2"),
        "H": ("2012", "H1"), "J": ("2012", "H2"),
        "K": ("2013", "H1"), "L": ("2013", "H2"),
        "M": ("2014", "H1"), "N": ("2014", "H2"),
        "P": ("2015", "H1"), "Q": ("2015", "H2"),
        "R": ("2016", "H1"), "S": ("2016", "H2"),
        "T": ("2017", "H1"), "V": ("2017", "H2"),
        "W": ("2018", "H1"), "X": ("2018", "H2"),
        "Y": ("2019", "H1"), "Z": ("2019", "H2"),
    }

    # ── Week codes (position 5) – skipped: A,B,E,I,O,S,U ──
    WEEK_CODES = {
        "1": 1,  "2": 2,  "3": 3,  "4": 4,  "5": 5,
        "6": 6,  "7": 7,  "8": 8,  "9": 9,
        "C": 10, "D": 11, "F": 12, "G": 13, "H": 14,
        "J": 15, "K": 16, "L": 17, "M": 18, "N": 19,
        "P": 20, "Q": 21, "R": 22, "T": 23, "V": 24,
        "W": 25, "X": 26, "Y": 27,
    }

    # ── Model code database (last 4 chars) ──
    MODEL_CODES = {
        "DKQ":  {"model_identifier": "MacBookPro10,1",
                 "device": "MacBook Pro 15\" Retina Mid-2012",
                 "processor": "i7 2.3-2.7GHz", "ram": "8-16GB",
                 "storage": "256-768GB SSD"},
        "DL4":  {"model_identifier": "MacBookPro9,1",
                 "device": "MacBook Pro 15\" Mid-2012",
                 "processor": "i7 2.3-2.7GHz", "ram": "4-8GB",
                 "storage": "500GB-1TB"},
        "HG7H": {"model_identifier": "iPhone9,1",
                 "device": "iPhone 7 4.7\"",
                 "processor": "A10 Fusion", "ram": "2GB",
                 "storage": "32/128/256GB"},
        "NG":   {"model_identifier": "iPhone9,2",
                 "device": "iPhone 7 Plus 5.5\"",
                 "processor": "A10 Fusion", "ram": "3GB",
                 "storage": "32/128/256GB"},
    }

    def decode_location(serial):
        """Try longest-match first for location prefix."""
        for length in (3, 2, 1):
            prefix = serial[:length].upper()
            if prefix in LOCATION_CODES:
                return prefix, LOCATION_CODES[prefix], length
        return serial[:2], "Unknown", 2

    def decode_model_code(last4):
        """Try to match last 4 chars against model database."""
        # Try full 4-char match first, then 3-char prefix
        if last4.upper() in MODEL_CODES:
            return MODEL_CODES[last4.upper()]
        if last4[:3].upper() in MODEL_CODES:
            return MODEL_CODES[last4[:3].upper()]
        # Try 2-char prefix
        if last4[:2].upper() in MODEL_CODES:
            return MODEL_CODES[last4[:2].upper()]
        return None

    def decode_serial(serial):
        serial = serial.strip().upper()
        length = len(serial)

        result = {
            "serial": serial,
            "format": None,
            "location": None,
            "location_code": None,
            "year": None,
            "half": None,
            "week_in_half": None,
            "actual_week": None,
            "model_code": None,
            "model_info": None,
            "requires_web_lookup": False,
            "notes": [],
        }

        # Detect format
        if length == 15 and serial.isdigit():
            result["format"] = "IMEI"
            result["notes"].append("This is an IMEI number, not a serial number.")
            return result

        if length == 10:
            result["format"] = "new_randomized_2021+"
            result["requires_web_lookup"] = True
            result["notes"].append(
                "New randomized format (2021+). Cannot be decoded locally. "
                "Use https://checkcoverage.apple.com/ for device identification."
            )
            return result

        if length not in (11, 12):
            result["format"] = "unknown"
            result["notes"].append(f"Unexpected serial length: {length}")
            return result

        result["format"] = "old_11_12_char"

        # Location
        loc_code, loc_name, loc_len = decode_location(serial)
        result["location_code"] = loc_code
        result["location"] = loc_name

        # Year (position after location)
        year_char = serial[loc_len]
        if year_char in YEAR_CODES:
            result["year"], result["half"] = YEAR_CODES[year_char]
        else:
            result["notes"].append(f"Unknown year code: {year_char}")

        # Week (position after year)
        week_char = serial[loc_len + 1]
        if week_char in WEEK_CODES:
            week_in_half = WEEK_CODES[week_char]
            result["week_in_half"] = week_in_half
            if result["half"] == "H2":
                result["actual_week"] = week_in_half + 26
            else:
                result["actual_week"] = week_in_half
        else:
            result["notes"].append(f"Unknown week code: {week_char}")

        # Model code: last 4 characters
        model_chars = serial[-4:]
        result["model_code"] = model_chars
        model_info = decode_model_code(model_chars)
        if model_info:
            result["model_info"] = model_info
        else:
            result["requires_web_lookup"] = True
            result["notes"].append(
                f"Model code '{model_chars}' not in local database. "
                "Web lookup recommended: "
                f"https://everymac.com/ultimate-mac-lookup/?search_keywords={serial}"
            )

        return result

    if __name__ == "__main__":
        if len(sys.argv) < 2:
            print(json.dumps({"error": "Usage: decode_serial.py <SERIAL>"}))
            sys.exit(1)
        result = decode_serial(sys.argv[1])
        print(json.dumps(result, indent=2))
''')

with open(os.path.join(BASE, "scripts", "decode_serial.py"), "w") as f:
    f.write(decode_script.lstrip())

os.chmod(os.path.join(BASE, "scripts", "decode_serial.py"), 0o755)

# ── references ──────────────────────────────────────────────────────────────
serial_format_md = """# Apple Serial Number Formats

## Old Format (11-12 characters, pre-2021)

Applies to all Apple hardware: Macs, iPhones, iPads, iPods, Apple Watch, Apple TV.

Structure (12-char): `PPP Y W D III MMMM`

| Position | Length | Meaning |
|----------|--------|---------|
| 1-3 | 1-3 | Manufacturing location code |
| 4 | 1 | Year + half of manufacture |
| 5 | 1 | Week within the half-year |
| 6 | 1 | Day/production refinement |
| 7-8 | 2-3 | Unique device identifier |
| 9-12 | 4 | Model: chars 9-11 = model+color, char 12 = config/storage |

### Manufacturing Location Codes (position 1-3)

| Code | Location |
|------|----------|
| FC | Fountain Colorado, USA |
| F | Fremont, California, USA |
| XA, XB, QP, G8 | USA |
| RN | Mexico |
| GQ | Foxconn, Brazil |
| CK | Cork, Ireland |
| VM | Foxconn, Pardubice, Czech Republic |
| SG, E | Singapore |
| MB | Malaysia |
| PT, CY | Korea |
| EE, QT, UV | Taiwan |
| FK, F1, F2 | Foxconn, Zhengzhou, China |
| F7, 1C, 4H, WQ | China |
| W8 | Shanghai, China |
| DL, DM | Foxconn, China |
| DN | Foxconn, Chengdu, China |
| DX | Foxconn, Zhengzhou, China |
| YM, 7J | Hon Hai/Foxconn, China |
| C0, C02, C07, C17 | Tech Com/Quanta, China |
| C3 | Foxconn, Shenzhen, China |
| C6, C6K | Foxconn, Zhengzhou, China |
| C7 | Pentragon, Shanghai, China |
| G0 | Pegatron, Shanghai, China |
| G6 | Foxconn, Shenzhen, China |
| J2 | Pegatron, Shanghai, China |
| H0, HN | Foxconn, India |
| RM | Refurbished/Remanufactured |

### Year Codes (position 4)

Each letter represents one half-year. Letters A, B, E, I, O, U are skipped.

| Code | Period | Code | Period |
|------|--------|------|--------|
| C | 2010 H1 | D | 2010 H2 |
| F | 2011 H1 | G | 2011 H2 |
| H | 2012 H1 | J | 2012 H2 |
| K | 2013 H1 | L | 2013 H2 |
| M | 2014 H1 | N | 2014 H2 |
| P | 2015 H1 | Q | 2015 H2 |
| R | 2016 H1 | S | 2016 H2 |
| T | 2017 H1 | V | 2017 H2 |
| W | 2018 H1 | X | 2018 H2 |
| Y | 2019 H1 | Z | 2019 H2 |

### Week Codes (position 5)

Represents week within the half-year (1-27). For H2 devices, add 26 to get actual week of year.
Letters A, B, E, I, O, S, U are skipped.

| Code | Week | Code | Week | Code | Week |
|------|------|------|------|------|------|
| 1 | 1 | C | 10 | P | 20 |
| 2 | 2 | D | 11 | Q | 21 |
| 3 | 3 | F | 12 | R | 22 |
| 4 | 4 | G | 13 | T | 23 |
| 5 | 5 | H | 14 | V | 24 |
| 6 | 6 | J | 15 | W | 25 |
| 7 | 7 | K | 16 | X | 26 |
| 8 | 8 | L | 17 | Y | 27 |
| 9 | 9 | M | 18 | | |
| | | N | 19 | | |

### iPhone-Specific (last 4 characters)

For iPhones, the last 4 digits encode additional info:
- Characters 9-11: model + color
- Character 12: storage capacity

## New Format (randomized, 2021+)

Starting in 2021, Apple switched to randomized serial numbers (typically 10 characters). These have NO decodable structure — web lookup is the only option.

## Identifying the Format

- **11-12 characters, 4th char is a letter C-Z** → Old format (decodable)
- **10 characters** → New randomized format (2021+)
- **15 digits** → IMEI, not a serial number

## Useful Lookup URLs

- EveryMac (Macs): `https://everymac.com/ultimate-mac-lookup/?search_keywords=SERIAL`
- Apple Coverage: `https://checkcoverage.apple.com/`
- Beetstech: `https://beetstech.com/apple-device-lookup`
- IMEI.info: `https://www.imei.info/apple-sn-check/?sn=SERIAL`
"""

with open(os.path.join(BASE, "references", "serial-format.md"), "w") as f:
    f.write(serial_format_md)

model_codes_md = """# Apple Model Code Mappings

These are the last 3-4 characters of old-format Apple serial numbers, which encode specific models, configurations, colors, and storage capacities.

**Note:** Apple doesn't publish complete model code tables. These mappings are compiled from repair databases, forums, and observed patterns.

## MacBook Pro Model Codes

### 2012 MacBook Pro Models

| Code | Model Identifier | Device | Processor | RAM | Storage | Notes |
|------|------------------|--------|-----------|-----|---------|-------|
| DKQ* | MacBookPro10,1 | MacBook Pro 15" Retina Mid-2012 | i7 2.3-2.7GHz | 8-16GB | 256-768GB | First Retina MacBook Pro |
| DL4* | MacBookPro9,1 | MacBook Pro 15" Mid-2012 | i7 2.3-2.7GHz | 4-8GB | 500GB-1TB | Non-Retina |

### 2013 MacBook Pro Models

| Code | Model Identifier | Device | Processor | RAM | Storage | Notes |
|------|------------------|--------|-----------|-----|---------|-------|
| F* | MacBookPro10,1 | MacBook Pro 15" Retina Early 2013 | i7 2.4-2.8GHz | 8-16GB | 256-768GB SSD | |
| G* | MacBookPro10,2 | MacBook Pro 13" Retina Late 2012/Early 2013 | i5/i7 | 8-16GB | 128-768GB SSD | |

## iPhone Model Codes

### iPhone 7 (2016)

| Code | Model Identifier | Device | Storage | Color | Carrier | Notes |
|------|------------------|--------|---------|-------|---------|-------|
| HG7H | iPhone9,1 | iPhone 7 4.7" | 32/128/256GB | Various | GSM | A10 Fusion, 2GB RAM |
| MN* | iPhone9,3 | iPhone 7 4.7" | 32/128/256GB | Various | CDMA | A10 Fusion, 2GB RAM |

### iPhone 7 Plus (2016)

| Code | Model Identifier | Device | Storage | RAM | Notes |
|------|------------------|--------|---------|-----|-------|
| NG* | iPhone9,2 | iPhone 7 Plus 5.5" | 32/128/256GB | 3GB | Dual camera |
| NF* | iPhone9,4 | iPhone 7 Plus 5.5" | 32/128/256GB | 3GB | CDMA variant |

## iPad Model Codes

### iPad (2021+) - New Randomized Format

New 10-character serials (like K4PMWCGJT4) cannot be decoded. Use Apple Check Coverage or browser automation for identification.

## Common Patterns

### Last Character (Storage/Config)
- **1, 2, 3**: Often indicate storage tiers (32/128/256GB) or configuration variants
- **H, K, L**: Common in iPhone storage encoding
- **Q, R, S**: Common in Mac configuration encoding

### Color Encoding (iPhones)
Model codes often embed color information, but mappings vary by generation.

## Model Identifier Patterns

### Mac Format
- **MacBookPro{X},{Y}**: X = generation, Y = size/variant
  - MacBookPro10,1 = 15" Retina Mid 2012-Early 2013
  - MacBookPro10,2 = 13" Retina Late 2012-Early 2013

### iPhone Format  
- **iPhone{X},{Y}**: X = chip generation, Y = variant
  - iPhone9,1 = iPhone 7 (GSM)
  - iPhone9,3 = iPhone 7 (CDMA)

## Data Sources

1. **EveryMac.com** - Most comprehensive Mac database
2. **The Apple Wiki** - Community-maintained device specifications
3. **Apple Support Pages** - Official model identifier listings
4. **Repair Databases** - Real-world mappings from service providers

## Limitations

- **Incomplete**: Many model codes are undocumented
- **Regional Variants**: Same model may have different codes by region/carrier
- **New Format**: Post-2021 serials are randomized and cannot be decoded
- **Updates**: Apple occasionally reuses or changes code patterns
"""

with open(os.path.join(BASE, "references", "model-codes.md"), "w") as f:
    f.write(model_codes_md)

# ── SKILL.md ────────────────────────────────────────────────────────────────
skill_md = """---
name: apple-serial-lookup
description: Look up Apple device information from a serial number. Supports iPhones, iPads, Macs, Apple Watch, Apple TV, and iPods.
---

# Apple Serial Lookup

Identify any Apple device from its serial number by combining local decoding with web lookups.

## Workflow

### 1. Decode locally (old 11-12 char format)

Run the bundled decoder script:

```bash
python3 scripts/decode_serial.py <SERIAL>
```

This extracts manufacturing location/date, model codes, model identifier, and basic specs.

### 2. Web lookup for complete specs and unknown models

For full specifications or unknown model codes, perform web lookup:
- Primary: web_search for `"Apple serial number <SERIAL> specs"` or `"<SERIAL> site:everymac.com"`
- Fallback: web_fetch from `https://everymac.com/ultimate-mac-lookup/?search_keywords=<SERIAL>`

For new-format (post-2021) serials, web search won't help — direct the user to:
- **Apple Check Coverage:** `https://checkcoverage.apple.com/`

### 3. Present results

See references/serial-format.md and references/model-codes.md for encoding details.

The script outputs JSON for easy parsing.
"""

with open(os.path.join(BASE, "SKILL.md"), "w") as f:
    f.write(skill_md)

# ── Primary task input: device inventory CSV ─────────────────────────────────
# Serial analysis:
# C02JH7GJDKQ1: C02(3-char)=Quanta China | J=2012H2 | H=week14 | 7=day | GJ=unique | DKQ1=model
#   actual_week = 14 + 26 = 40
# DNRTRXHG7H1F: DN(2-char)=FoxconnChengdu | R=2016H1 | T=week23 | R=day | XH=unique | G7H1=model
#   G7H1 -> not in DB -> requires web lookup
# Actually let's use: DNRTR1HG7H12 — wait, we want HG7H to be last 4.
# DN + R + T + R + 1H + HG7H = DN(2)+R(1)+T(1)+R(1)+1H(2)+HG7H(4) = 11 chars. Need 12.
# DN + R + T + R + X1H + HG7H = 2+1+1+1+3+4 = 12. Yes.
# DNRTRX1HG7H1 — wait: D-N-R-T-R-X-1-H-G-7-H-1 = 12. Last 4 = G7H1, not HG7H.
# For HG7H to be last 4: need serial[8:12] = HG7H
# DN(2)+R(1)+T(1)+R(1)+XY(2)+HG7H(4) = 11. Need one more char.
# DN(2)+R(1)+T(1)+R(1)+XYZ(3)+HG7H(4) = 12. 
# DNRTRXHG7H -> 10 chars. That's new format!
# Let me try: DNR = 3-char prefix? No, DN is 2-char.
# C02 prefix (3-char) for serial 2: C02 + R(2016H1) + T(week23) + H(day) + GU(unique,2) + HG7H(model) = 3+1+1+1+2+4=12
# C02RTHGUHG7H — C-0-2-R-T-H-G-U-H-G-7-H = 12 chars. 
# Decode: C02=Quanta, R=2016H1, T=week23(H1 so actual=23), H=day, GU=unique, HG7H=iPhone9,1
# That works!

inventory_csv = """asset_tag,serial_number,condition,received_date,notes
ASSET-001,C02JH7GJDKQ1,Good,2024-01-15,Battery replaced
ASSET-002,C02RTHGUHG7H,Fair,2024-01-16,Screen cracked
ASSET-003,K4PMWCGJT4,Excellent,2024-01-17,Factory reset done
"""

with open(os.path.join(BASE, "data/incoming", "device_inventory.csv"), "w") as f:
    f.write(inventory_csv)

# ── Distractor files ─────────────────────────────────────────────────────────
distractors = {
    "config/settings.json": json.dumps({
        "org": "DepotTech Repairs Inc.",
        "region": "US-West",
        "db_version": "3.1.2",
        "auto_export": True,
    }, indent=2),

    "config/warranty_tiers.json": json.dumps({
        "AppleCare+": 36,
        "Standard": 12,
        "Expired": 0,
    }, indent=2),

    "logs/import_2024-01-10.log": (
        "[INFO] Imported 47 assets from spreadsheet\n"
        "[WARN] 3 serials failed validation (IMEI detected)\n"
        "[INFO] Export complete: depot_batch_jan10.csv\n"
    ),

    "logs/import_2024-01-14.log": (
        "[INFO] Imported 12 assets\n"
        "[ERROR] Serial 358901234567890 is an IMEI - skipped\n"
        "[INFO] Completed with 1 error\n"
    ),

    "data/archive/batch_dec2023.csv": (
        "asset_tag,serial_number,status\n"
        "OLD-201,C07KF3NYDL43,Sold\n"
        "OLD-202,YMKG3XXHG7H1,Sold\n"
        "OLD-203,C02MXACJDKQ3,Refurb\n"
    ),

    "data/processed/batch_jan05_report.json": json.dumps({
        "processed": 8,
        "identified": 7,
        "requires_web_lookup": 1,
        "timestamp": "2024-01-05T14:32:00Z",
    }, indent=2),

    "tools/helpers/validate_csv.py": (
        "#!/usr/bin/env python3\n"
        "# Validates CSV structure for depot imports\n"
        "import csv, sys\n"
        "def validate(path):\n"
        "    with open(path) as f:\n"
        "        reader = csv.DictReader(f)\n"
        "        return list(reader)\n"
        "if __name__ == '__main__':\n"
        "    rows = validate(sys.argv[1])\n"
        "    print(f'Valid: {len(rows)} rows')\n"
    ),

    "tools/helpers/export_report.py": (
        "#!/usr/bin/env python3\n"
        "# Exports report in various formats\n"
        "import json, csv, sys\n"
        "def to_csv(data, outpath):\n"
        "    pass\n"
        "def to_json(data, outpath):\n"
        "    with open(outpath, 'w') as f:\n"
        "        json.dump(data, f, indent=2)\n"
    ),

    "reports/draft/template_report.json": json.dumps({
        "_comment": "Template - do not use directly",
        "asset_tag": "",
        "serial": "",
        "device": "",
        "manufactured": "",
        "model_identifier": "",
        "requires_web_lookup": False,
    }, indent=2),

    "data/archive/imei_flagged.txt": (
        "# IMEIs submitted by mistake (NOT serial numbers)\n"
        "358901234567890\n"
        "354765098123456\n"
        "# These are 15-digit IMEI numbers\n"
    ),

    "references/warranty_lookup_notes.txt": (
        "For warranty status:\n"
        "- Old format serials: check EveryMac first\n"
        "- New format serials: must use checkcoverage.apple.com\n"
        "- IMEI: use imei.info instead\n"
    ),
}

for rel_path, content in distractors.items():
    full_path = os.path.join(BASE, rel_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w") as f:
        f.write(content)

print("Workspace generated successfully.")
print(f"Files created in {BASE}:")
for root, dirs, files in os.walk(BASE):
    level = root.replace(BASE, "").count(os.sep)
    indent = "  " * level
    print(f"{indent}{os.path.basename(root)}/")
    subindent = "  " * (level + 1)
    for file in files:
        print(f"{subindent}{file}")