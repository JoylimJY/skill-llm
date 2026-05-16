import os
import random
import textwrap

random.seed(42)

BASE = "/workspace"

# ── helpers ───────────────────────────────────────────────────────────────────
def write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(textwrap.dedent(content))

# ── Cargo workspace ───────────────────────────────────────────────────────────
write(f"{BASE}/Cargo.toml", """
    [workspace]
    members = [
        "crates/logistics-core",
        "crates/route-planner",
        "crates/tracking-utils",
    ]
    resolver = "2"
""")

# ── crates/logistics-core ──────────────────────────────────────────────────────
write(f"{BASE}/crates/logistics-core/Cargo.toml", """
    [package]
    name = "logistics-core"
    version = "0.1.0"
    edition = "2021"

    [dependencies]
""")

write(f"{BASE}/crates/logistics-core/src/lib.rs", """
    pub mod shipment;
    pub mod carrier;
""")

write(f"{BASE}/crates/logistics-core/src/shipment.rs", """
    /// Placeholder for shipment domain types.
    #[derive(Debug, Clone, PartialEq)]
    pub struct Shipment {
        pub id: String,
        pub origin: String,
        pub destination: String,
    }
""")

write(f"{BASE}/crates/logistics-core/src/carrier.rs", """
    /// Carrier codes recognised by the platform.
    #[derive(Debug, Clone, PartialEq)]
    pub enum Carrier {
        Dhl,
        Ups,
        FedEx,
        Unknown,
    }
""")

# Existing test examples in logistics-core — the agent MUST mirror this style
write(f"{BASE}/crates/logistics-core/src/carrier.rs", """\
/// Carrier codes recognised by the platform.
#[derive(Debug, Clone, PartialEq)]
pub enum Carrier {
    Dhl,
    Ups,
    FedEx,
    Unknown,
}

impl Carrier {
    pub fn from_prefix(prefix: &str) -> Self {
        match prefix {
            "DHL" => Carrier::Dhl,
            "UPS" => Carrier::Ups,
            "FDX" => Carrier::FedEx,
            _ => Carrier::Unknown,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn dhl_prefix_maps_to_dhl_carrier() {
        let c = Carrier::from_prefix("DHL");
        assert_eq!(c, Carrier::Dhl);
    }

    #[test]
    fn unknown_prefix_maps_to_unknown_carrier() {
        let c = Carrier::from_prefix("XYZ");
        assert_eq!(c, Carrier::Unknown);
    }
}
""")

# ── crates/route-planner ───────────────────────────────────────────────────────
write(f"{BASE}/crates/route-planner/Cargo.toml", """
    [package]
    name = "route-planner"
    version = "0.1.0"
    edition = "2021"

    [dependencies]
    logistics-core = { path = "../logistics-core" }
""")

write(f"{BASE}/crates/route-planner/src/lib.rs", """
    pub fn cheapest_route(origins: &[&str], destination: &str) -> Option<String> {
        origins.first().map(|o| format!("{} -> {}", o, destination))
    }

    #[cfg(test)]
    mod tests {
        use super::*;

        #[test]
        fn single_origin_returns_direct_route() {
            let r = cheapest_route(&["NYC"], "LAX");
            assert_eq!(r, Some("NYC -> LAX".to_string()));
        }

        #[test]
        fn empty_origins_returns_none() {
            let r = cheapest_route(&[], "LAX");
            assert_eq!(r, None);
        }
    }
""")

# ── crates/tracking-utils  ────────────────────────────────────────────────────
# This is the TARGET crate where the agent must work
write(f"{BASE}/crates/tracking-utils/Cargo.toml", """
    [package]
    name = "tracking-utils"
    version = "0.1.0"
    edition = "2021"

    [dependencies]
""")

# The module exists but is EMPTY — agent must add implementation
write(f"{BASE}/crates/tracking-utils/src/lib.rs", """\
pub mod tracking_id;
""")

write(f"{BASE}/crates/tracking-utils/src/tracking_id.rs", """\
// TODO: implement TrackingId parsing and validation
""")

# ── THE SPEC FILE the agent must process ──────────────────────────────────────
write(f"{BASE}/specs/tracking-id.spec.md", """\
# Tracking ID Specification

## Overview
A tracking ID is a string issued to each shipment. It must conform to a strict
format so downstream systems can parse carrier, region, and sequence number.

## Format
`<CARRIER:3>-<REGION:2>-<SEQ:6>`

- CARRIER: exactly 3 uppercase ASCII letters (e.g. DHL, UPS, FDX)
- REGION:  exactly 2 uppercase ASCII letters (e.g. EU, US, AP)
- SEQ:     exactly 6 ASCII digits (e.g. 000001)

Example valid ID: `DHL-EU-000042`

---

## Acceptance Criteria

### Given a well-formed tracking ID string
### When the ID is parsed
### Then a TrackingId value is returned with the correct carrier, region, and sequence fields

---

### Given a tracking ID with a carrier segment that is not exactly 3 uppercase letters
### When the ID is validated
### Then an error is returned indicating invalid carrier format

---

### Given a tracking ID where the sequence segment contains non-digit characters
### When the ID is validated
### Then an error is returned indicating invalid sequence format

---

### Given two tracking IDs that share the same carrier and region but differ only in sequence number
### When they are compared for equality
### Then they are not considered equal
""")

# ── Distractor files to test contextual awareness ────────────────────────────
distractors = {
    f"{BASE}/docs/architecture.md": "# Architecture\nSee the main README.\n",
    f"{BASE}/docs/api-reference.md": "# API Reference\nTODO\n",
    f"{BASE}/scripts/deploy.sh": "#!/bin/bash\necho 'deploy'\n",
    f"{BASE}/scripts/seed_db.py": "# seed script\nprint('seeding')\n",
    f"{BASE}/config/staging.toml": "[database]\nurl = 'postgres://localhost/staging'\n",
    f"{BASE}/config/production.toml": "[database]\nurl = 'postgres://prod-host/prod'\n",
    f"{BASE}/crates/logistics-core/README.md": "# logistics-core\nCore domain types.\n",
    f"{BASE}/crates/route-planner/README.md": "# route-planner\nRoute optimisation.\n",
    f"{BASE}/specs/carrier.spec.md": "# Carrier Spec\n## Acceptance Criteria\n### Given a prefix\n### When looked up\n### Then a carrier is returned\n",
    f"{BASE}/.github/workflows/ci.yml": "name: CI\non: push\njobs:\n  test:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v3\n",
    f"{BASE}/CHANGELOG.md": "# Changelog\n## Unreleased\n- nothing yet\n",
    f"{BASE}/crates/tracking-utils/README.md": "# tracking-utils\nTracking ID utilities — implementation pending.\n",
}

for path, content in distractors.items():
    write(path, content)

print("Workspace generated successfully.")