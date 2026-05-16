# Memory Governor 0.2.4-beta

This beta fixes Python compatibility for the packaged scripts.

## What Changed

- `check-memory-host.py` now falls back to `tomli` when `tomllib` is unavailable
- `validate-memory-frontmatter.py` now falls back to `tomli` when `tomllib` is unavailable
- installation docs now state the Python compatibility rule explicitly

## Why

The previous package shape assumed Python 3.11+.

This update keeps the package usable on Python 3.9 / 3.10 hosts without changing the manifest or schema contract.
