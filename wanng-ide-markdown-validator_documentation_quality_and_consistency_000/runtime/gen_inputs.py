import os
import random

random.seed(42)

workspace = "/workspace"

# Directory structure for a medical device documentation project
dirs = [
    "docs",
    "docs/specifications",
    "docs/specifications/hardware",
    "docs/specifications/software",
    "docs/test-protocols",
    "docs/test-protocols/unit",
    "docs/test-protocols/integration",
    "docs/compliance",
    "docs/compliance/iso13485",
    "docs/compliance/fda",
    "docs/release-notes",
    "docs/training",
    "assets",
    "assets/diagrams",
    "templates",
]

for d in dirs:
    os.makedirs(os.path.join(workspace, d), f"exist_ok=True".split("=")[1] == "True" or True)

# Helper to write file
def write(path, content):
    full = os.path.join(workspace, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w") as f:
        f.write(content)

# ── VALID files (no broken links, they exist) ──────────────────────────────

write("docs/compliance/iso13485/overview.md", """# ISO 13485 Overview

This document provides an overview of the ISO 13485 quality management system requirements.

## Sections

- Design controls
- Risk management
- Document control

See also: [FDA Requirements](../fda/fda-requirements.md)
""")

write("docs/compliance/fda/fda-requirements.md", """# FDA Requirements

Summary of applicable FDA 21 CFR Part 820 requirements.

## Design Controls

Refer to the [ISO overview](../iso13485/overview.md) for quality context.
""")

write("docs/test-protocols/unit/sensor-unit-test.md", """# Sensor Unit Test Protocol

## Objective

Validate the analog sensor reading pipeline.

## References

- [Integration tests](../integration/system-integration-test.md)
""")

write("docs/test-protocols/integration/system-integration-test.md", """# System Integration Test Protocol

Validates the end-to-end device workflow.

## Links

- [Unit tests](../unit/sensor-unit-test.md)
- [Release notes](../../release-notes/v2.1.0.md)
""")

write("docs/release-notes/v2.1.0.md", """# Release Notes v2.1.0

- Fixed calibration drift issue
- Improved Bluetooth connectivity

## See Also

- [Training materials](../training/operator-guide.md)
""")

write("docs/training/operator-guide.md", """# Operator Guide

Step-by-step guide for device operators.

## Sections

1. Setup
2. Operation
3. Maintenance

External ref (ignored): [FDA website](https://www.fda.gov)
Same-file anchor (ignored): [Jump to Sections](#sections)
""")

write("templates/doc-template.md", """# Document Template

Use this template for all new documentation.

## Metadata

- Author:
- Date:
- Version:
""")

# ── FILES WITH BROKEN LINKS ─────────────────────────────────────────────────

# Broken: references a hardware spec that doesn't exist yet
write("docs/specifications/software/software-requirements.md", """# Software Requirements Specification

Version: 3.1

## Overview

This document defines software requirements for the cardiac monitor firmware.

## Hardware Dependencies

Refer to the hardware specification: [Hardware Requirements](../hardware/hardware-requirements.md)

## Compliance

- [ISO 13485 Overview](../../compliance/iso13485/overview.md)
- [FDA Requirements](../../compliance/fda/fda-requirements.md)

## Test Coverage

- [Software Integration Test](../../test-protocols/integration/software-integration-test.md)

## External Resources (ignored by validator)

- [IEC 62304 Standard](https://www.iso.org/standard/38421.html)
""")

# Broken: references a risk doc that doesn't exist
write("docs/specifications/hardware/hardware-requirements.md", """# Hardware Requirements Specification

Version: 2.0

## Sensors

The device uses three analog sensors for vital sign monitoring.

## Risk Assessment

Risk analysis is documented in: [Risk Management File](../../compliance/iso13485/risk-management.md)

## Software Interface

See: [Software Requirements](../software/software-requirements.md)

## Test Protocol

[Hardware Verification Test](../../test-protocols/unit/hardware-verification-test.md)
""")

# Broken: references a non-existent calibration procedure and a missing checklist
write("docs/compliance/iso13485/design-controls.md", """# Design Controls

## Purpose

This document describes the design control process per ISO 13485 clause 7.3.

## Design Verification

All design verification activities must reference: [Verification Checklist](./verification-checklist.md)

## Calibration

Calibration procedure is defined in: [Calibration Procedure](../../test-protocols/unit/calibration-procedure.md)

## Related Documents

- [Overview](./overview.md)
- [FDA Requirements](../fda/fda-requirements.md)
- [Hardware Requirements](../../specifications/hardware/hardware-requirements.md)
""")

# Broken: references non-existent v3.0.0 release notes
write("docs/release-notes/v3.0.0-draft.md", """# Release Notes v3.0.0 (DRAFT)

## New Features

- Advanced arrhythmia detection
- Cloud sync module

## Breaking Changes

See upgrade guide: [v2.1.0 to v3.0.0 Migration](./migration-v2-to-v3.md)

## Previous Release

[v2.1.0 Release Notes](./v2.1.0.md)

## Training

Updated training: [Advanced Operator Guide](../training/advanced-operator-guide.md)
""")

# Distractor non-md files (should be ignored by validator)
write("assets/diagrams/architecture.png.placeholder", "binary content placeholder")
write("assets/diagrams/sensor-flow.svg.placeholder", "svg placeholder")
write("templates/style-guide.txt", "Use sentence case for headings.\nKeep lines under 100 chars.")
write("docs/compliance/.gitkeep", "")

print("Workspace generated successfully.")
print("Files with intentional broken links:")
print("  - docs/specifications/software/software-requirements.md")
print("  - docs/specifications/hardware/hardware-requirements.md")
print("  - docs/compliance/iso13485/design-controls.md")
print("  - docs/release-notes/v3.0.0-draft.md")