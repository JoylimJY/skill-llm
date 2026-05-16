# Memory Governor 0.2.3-beta

This beta tightens the host-integration contract rather than adding new surface area.

## What Changed

- Added `fallback_paths` support to the manifest contract and host checker
- Added a migration guide for hosts that already have a messy or legacy memory setup
- Added explicit `reusable_lessons` examples for `single`, `directory`, and `pattern` style adapters

## Why

The main goal is to reduce drift between:

- the adapter a host prefers
- the local fallback a host can still rely on
- what the checker is actually able to validate

This makes the package easier to adopt without pretending every host starts from a clean slate.
