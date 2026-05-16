#!/usr/bin/env python3
import os
import json
import random

random.seed(42)

workspace = "/workspace"

# --- Directory structure ---
dirs = [
    "scripts",
    "references",
    "contracts/2024/q1",
    "contracts/2024/q2",
    "contracts/archive",
    "artists/profiles",
    "artists/sessions",
    "accounting/invoices",
    "accounting/splits_history",
    "legal/templates",
    "legal/signed",
    "distribution/platforms",
    "distribution/reports",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# --- scripts/splitxch.sh (the actual script the agent must use) ---
splitxch_sh = r"""#!/usr/bin/env bash
# SplitXCH API wrapper
# Usage: bash scripts/splitxch.sh <payload_json_file>
set -euo pipefail

PAYLOAD_FILE="${1:?Usage: splitxch.sh <payload_json_file>}"

if [ ! -f "$PAYLOAD_FILE" ]; then
  echo "ERROR: Payload file not found: $PAYLOAD_FILE" >&2
  exit 1
fi

# Use mock server if SPLITXCH_API_URL is set, else default
API_URL="${SPLITXCH_API_URL:-https://splitxch.com/api/compute/fast}"

RESPONSE=$(curl -s -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -d @"$PAYLOAD_FILE")

echo "$RESPONSE"
"""
with open(os.path.join(workspace, "scripts/splitxch.sh"), "w") as f:
    f.write(splitxch_sh)

# --- references/api.md ---
api_md = """# SplitXCH API Reference

## POST https://splitxch.com/api/compute/fast

Create a split address from recipients. Returns the computed XCH address.

### Request
```json
{
  "recipients": [
    {
      "name": "Artist",
      "address": "xch1...",
      "points": 4925,
      "id": 1
    },
    {
      "name": "Manager",
      "address": "xch1...",
      "points": 4925,
      "id": 2
    }
  ]
}
```

### Key Rules
- **Basis points**: 10,000 = 100%. Platform fee is 150 bps (1.5%).
- Recipient points must sum to **9,850** (10,000 minus 150 fee).
- Up to **128 recipients** per split. For more, use cascading splits.
- All addresses must be valid XCH addresses (start with `xch1`).
- All addresses must be unique within a single split.
- Each recipient's points must be > 0.

### Response
```json
{
  "id": "66f21c17eb854b8fab7327280ac5eb21",
  "message": "Saved",
  "pctProgress": 100,
  "address": "xch1q3ge2z5g5fsk4ckkunmszwlhpcmgns7c5y5gwku86tdsa4wfhg6qszeuzg"
}
```

### Errors
HTTP 400 with `message` field describing the validation failure.

## Cascading Splits (Nested)

For >128 recipients or complex hierarchies, create splits-of-splits:
1. Create leaf splits first (bottom-up)
2. Use the returned split addresses as recipients in parent splits
3. Each level has its own 150 bps fee

## Basis Points Math

| Percentage | Basis Points (of 9850) |
|-----------|----------------------|
| 50%       | 4925                 |
| 25%       | 2462 or 2463         |
| 10%       | 985                  |
| 5%        | 492 or 493           |
| 1%        | 98 or 99             |

Formula: `points = round(percentage / 100 * 9850)`

When rounding causes the sum to not equal 9850, adjust the last recipient.
"""
with open(os.path.join(workspace, "references/api.md"), "w") as f:
    f.write(api_md)

# --- SKILL.md at workspace root ---
skill_md = """---
name: splitxch
description: Create SplitXCH royalty split addresses from plain language descriptions.
---

# SplitXCH Royalty Split Builder

Create complex XCH royalty distribution addresses from natural language descriptions.

## How It Works

SplitXCH creates special Chia blockchain addresses that automatically split incoming payments to multiple recipients based on configured percentages.

## Workflow

1. Parse the user's plain-language split description into recipients with percentages
2. Convert percentages to basis points (scale to 9850 total, API adds 150 bps / 1.5% fee)
3. For nested splits (splits-of-splits), build bottom-up: create leaf splits first, then use their addresses as recipients in parent splits
4. Call the SplitXCH API via `scripts/splitxch.sh` or direct curl
5. Return the generated split address and a summary

## Basis Points Conversion

- 10,000 bps = 100%. API fee = 150 bps (1.5%). Recipients get 9,850 bps total.
- Formula: `points = round(percentage / 100 * 9850)`
- Adjust last recipient so points sum to exactly 9850.

Example: "Split 60/40 between Alice and Bob"
- Alice: round(0.60 * 9850) = 5910
- Bob: 9850 - 5910 = 3940

## Building the API Payload

```json
{
  "recipients": [
    {"name": "Alice", "address": "xch1...", "points": 5910, "id": 1},
    {"name": "Bob", "address": "xch1...", "points": 3940, "id": 2}
  ]
}
```

Save to a temp file and run:
```bash
bash scripts/splitxch.sh /tmp/split-payload.json
```

## Nested Splits (>128 recipients or hierarchies)

When the user describes groups within groups:
1. Create each leaf-level split first via the API
2. Use the returned `address` as a recipient in the parent split
3. Each split level incurs its own 150 bps fee

## Validation Rules

- All addresses must start with `xch1` and be valid bech32m
- Max 128 recipients per split
- All addresses unique within a split
- Each recipient's points > 0
- Points must sum to exactly 9850

## Output Format

After creating a split, present:
1. **Split Address**: The generated `xch1...` address
2. **Summary Table**: Each recipient's name, address (truncated), and percentage
3. **Fee Note**: "SplitXCH takes a 1.5% platform fee per split level"

If nested, show the full tree structure.
"""
with open(os.path.join(workspace, "SKILL.md"), "w") as f:
    f.write(skill_md)

# --- deal_memo.txt: the business problem the agent must solve ---
deal_memo = """CONFIDENTIAL - Internal Deal Memo
Project: "Neon Cascade" Album Release
Date: 2024-11-15

ROYALTY DISTRIBUTION AGREEMENT

Parties and wallet addresses confirmed by legal (2024-11-14):

1. Lead Artist - "Zara Voss"
   Wallet: xch1zv8r9k2pmn4x5qjfl3wd6uthcn7ae2sg0yp8mvx3dlk5q9h6frt2scewj
   Share: 55% of all streaming and sync royalties

2. Studio Collective (sub-group, equal shares among three session musicians):
   - Drummer "Marcus Webb"
     Wallet: xch1mw4p7n3kqx9r2fl8vc5te6dy0hs1ujg2bz4an8xk7mp3q5l9efr0tgdvs
   - Bassist "Priya Okonkwo"  
     Wallet: xch1pk8l2q5wr7nx3yd4fs9cv0bh6mt1ej5au3rn2xg8lp4k7q9d0cfr1shmz
   - Keys "Dmitri Sousa"
     Wallet: xch1ds6m3p8kq2xr4nl9fw5vc7tb0hy1ej3au5rn4xg2lp8k0q7d6cfr9smvz
   Collective share: 30% of all streaming and sync royalties
   (each session musician gets exactly equal share within the collective)

3. Label Reserve - "Neon Records LLC"
   Wallet: xch1nr5k8q2pm7x4rfl9wd3vc6th0ys1uj8gb2az4xn7lp5q3m9d0efr6twsc
   Share: 15% of all streaming and sync royalties

PAYMENT METHOD:
All royalty payments from DSPs will be sent in XCH to a single on-chain address.
The finance team requires an automated distribution system - no manual transfers.
Total shares must equal 100%.

ACTION REQUIRED:
Generate the automated payment routing address and save full configuration 
details to royalty_split.json
"""
with open(os.path.join(workspace, "contracts/2024/q2/deal_memo.txt"), "w") as f:
    f.write(deal_memo)

# --- Distractor files ---

# Old split attempt with wrong math
old_split = {
    "note": "DRAFT - DO NOT USE - math is wrong",
    "recipients": [
        {"name": "Zara Voss", "points": 5500},
        {"name": "Studio Collective", "points": 3000},
        {"name": "Neon Records", "points": 1500}
    ],
    "total": 10000,
    "error": "This uses 10000 bps instead of 9850 - invalid"
}
with open(os.path.join(workspace, "accounting/splits_history/draft_neon_cascade_WRONG.json"), "w") as f:
    json.dump(old_split, f, indent=2)

# Another distractor: a completed split for a different project
other_split = {
    "project": "Phantom Waves EP",
    "split_address": "xch1phantom000000000000000000000000000000000000000000000000fake",
    "recipients": [
        {"name": "DJ Solaris", "points": 6895, "percentage": "70%"},
        {"name": "Producer Mx", "points": 2955, "percentage": "30%"}
    ]
}
with open(os.path.join(workspace, "accounting/splits_history/phantom_waves_ep_split.json"), "w") as f:
    json.dump(other_split, f, indent=2)

# Artist profiles (distractors)
profiles = [
    {"name": "Zara Voss", "genre": "Electronic", "label": "Neon Records", "joined": "2022-03"},
    {"name": "Marcus Webb", "instrument": "Drums", "sessions": 47},
    {"name": "Priya Okonkwo", "instrument": "Bass", "sessions": 31},
    {"name": "Dmitri Sousa", "instrument": "Keys", "sessions": 28},
]
for p in profiles:
    fname = p["name"].lower().replace(" ", "_") + ".json"
    with open(os.path.join(workspace, "artists/profiles", fname), "w") as f:
        json.dump(p, f, indent=2)

# Contract templates (distractors)
for i, name in enumerate(["standard_royalty_agreement.txt", "session_musician_contract.txt", "label_deal_template.txt"]):
    with open(os.path.join(workspace, "legal/templates", name), "w") as f:
        f.write(f"TEMPLATE v{i+1}.0\nThis agreement is entered into between [ARTIST] and [LABEL]...\n[PLACEHOLDER CONTENT]\n")

# Invoice files
for month in ["jan", "feb", "mar"]:
    with open(os.path.join(workspace, "accounting/invoices", f"2024_{month}_streaming.csv"), "w") as f:
        f.write("platform,streams,revenue_usd\nSpotify,124500,987.32\nApple Music,43200,432.10\nTidal,8900,120.55\n")

# Distribution platform configs (distractors)
platform_cfg = {"platforms": ["Spotify", "Apple Music", "Tidal", "Amazon Music"], "format": "XCH", "auto_convert": False}
with open(os.path.join(workspace, "distribution/platforms/active_platforms.json"), "w") as f:
    json.dump(platform_cfg, f, indent=2)

# A deliberately wrong basis points table as a distractor
wrong_bps_table = """INTERNAL NOTE (OUTDATED - DO NOT USE)
Old conversion table:
- 50% = 5000 bps
- 30% = 3000 bps
- 15% = 1500 bps
- Total always = 10000 bps

** This was before the platform fee change. Now we use 9850 total. **
"""
with open(os.path.join(workspace, "accounting/splits_history/OUTDATED_bps_table.txt"), "w") as f:
    f.write(wrong_bps_table)

# Session musician booking records
with open(os.path.join(workspace, "artists/sessions/neon_cascade_session_log.txt"), "w") as f:
    f.write("Session Log - Neon Cascade\n2024-09-10: Drums (Webb) - 6hrs\n2024-09-11: Bass (Okonkwo) - 5hrs\n2024-09-12: Keys (Sousa) - 5hrs\n")

print("Workspace generated successfully.")
print(f"Key file: contracts/2024/q2/deal_memo.txt")