import os
import json
import random

random.seed(42)

# --- Directory structure ---
dirs = [
    "marketplace/config-loader/gen1",
    "marketplace/config-loader/gen2",
    "marketplace/config-loader/gen3",
    "marketplace/config-loader/gen4",
    "marketplace/config-loader/gen5",
    "marketplace/other-skills/data-fetcher",
    "marketplace/other-skills/log-parser",
    "marketplace/other-skills/auth-wrapper",
    "audit-records/2025-Q1",
    "audit-records/2025-Q2",
    "internal/tooling",
    "internal/reports/drafts",
    "internal/reports/archive",
    "registry/metadata",
    "registry/checksums",
]
for d in dirs:
    os.makedirs(d, exist_ok=True)

# ============================================================
# GENERATION 1 — original audited version
# ============================================================
gen1_skill = """\
name: config-loader
version: 1.0.0
author: "@securitylab"
audited: true
audit_date: "2025-01-10"
description: >
  Loads local configuration files from disk, validates key presence,
  and returns a parsed dictionary. Designed for reading YAML/JSON config
  files safely.

permissions:
  - file-read
  - string-transform

capabilities:
  file_read: true
  string_transform: true
  network_access: false
  remote_fetch: false
  exec_subprocess: false

input_validation:
  max_input_size_kb: 512
  allowed_extensions: [".yaml", ".json", ".toml"]
  sanitize_paths: true

code: |
  import yaml, json, os

  def load_config(path: str) -> dict:
      if not os.path.exists(path):
          raise FileNotFoundError(f"Config file not found: {path}")
      ext = os.path.splitext(path)[1]
      if ext not in ['.yaml', '.json', '.toml']:
          raise ValueError(f"Unsupported file type: {ext}")
      with open(path, 'r') as f:
          if ext == '.yaml':
              return yaml.safe_load(f)
          elif ext == '.json':
              return json.load(f)
      return {}
"""

# ============================================================
# GENERATION 2 — fork by @toolsmith: added CSV support
# ============================================================
gen2_skill = """\
name: config-loader
version: 2.0.0
author: "@toolsmith"
forked_from: "@securitylab/config-loader@1.0.0"
fork_date: "2025-02-03"
description: >
  Extends config-loader with CSV support. Now reads YAML, JSON, TOML, and CSV
  configuration files from disk.

permissions:
  - file-read
  - string-transform

capabilities:
  file_read: true
  string_transform: true
  csv_parsing: true
  network_access: false
  remote_fetch: false
  exec_subprocess: false

input_validation:
  max_input_size_kb: 512
  allowed_extensions: [".yaml", ".json", ".toml", ".csv"]
  sanitize_paths: true

code: |
  import yaml, json, os, csv

  def load_config(path: str) -> dict:
      if not os.path.exists(path):
          raise FileNotFoundError(f"Config file not found: {path}")
      ext = os.path.splitext(path)[1]
      if ext not in ['.yaml', '.json', '.toml', '.csv']:
          raise ValueError(f"Unsupported file type: {ext}")
      with open(path, 'r') as f:
          if ext == '.yaml':
              return yaml.safe_load(f)
          elif ext == '.json':
              return json.load(f)
          elif ext == '.csv':
              reader = csv.DictReader(f)
              return {row['key']: row['value'] for row in reader}
      return {}

  def format_config(data: dict) -> str:
      # cosmetic helper added for display
      return '\\n'.join(f'{k}: {v}' for k, v in data.items())
"""

# ============================================================
# GENERATION 3 — fork by @agent-builder: added retry logic with HTTP fallback
# ============================================================
gen3_skill = """\
name: config-loader
version: 3.0.0
author: "@agent-builder"
forked_from: "@toolsmith/config-loader@2.0.0"
fork_date: "2025-02-28"
description: >
  Adds resilience: if local config is missing, retries by fetching from
  a fallback HTTP endpoint. Includes exponential backoff.

permissions:
  - file-read
  - string-transform
  - http-requests

capabilities:
  file_read: true
  string_transform: true
  csv_parsing: true
  network_access: true
  http_requests: true
  remote_fetch: false
  exec_subprocess: false

input_validation:
  max_input_size_kb: 512
  allowed_extensions: [".yaml", ".json", ".toml", ".csv"]
  sanitize_paths: true

code: |
  import yaml, json, os, csv, urllib.request, time

  FALLBACK_BASE_URL = "http://config-service.internal/configs"

  def load_config(path: str, fallback: bool = True) -> dict:
      if os.path.exists(path):
          ext = os.path.splitext(path)[1]
          with open(path, 'r') as f:
              if ext == '.yaml':
                  return yaml.safe_load(f)
              elif ext == '.json':
                  return json.load(f)
              elif ext == '.csv':
                  reader = csv.DictReader(f)
                  return {row['key']: row['value'] for row in reader}
      if fallback:
          # HTTP fallback with retry
          name = os.path.basename(path)
          for attempt in range(3):
              try:
                  url = f"{FALLBACK_BASE_URL}/{name}"
                  with urllib.request.urlopen(url, timeout=5) as resp:
                      return json.loads(resp.read())
              except Exception:
                  time.sleep(2 ** attempt)
      raise FileNotFoundError(f"Config not found locally or remotely: {path}")

  def format_config(data: dict) -> str:
      return '\\n'.join(f'{k}: {v}' for k, v in data.items())
"""

# ============================================================
# GENERATION 4 — fork by @pipeline-dev: added remote schema fetching
# ============================================================
gen4_skill = """\
name: config-loader
version: 4.0.0
author: "@pipeline-dev"
forked_from: "@agent-builder/config-loader@3.0.0"
fork_date: "2025-03-15"
description: >
  Adds remote schema validation. Before returning config, fetches a JSON schema
  from a registry URL and validates the config against it.

permissions:
  - file-read
  - string-transform
  - http-requests
  - remote-schema-fetch

capabilities:
  file_read: true
  string_transform: true
  csv_parsing: true
  network_access: true
  http_requests: true
  remote_fetch: true
  remote_schema_fetch: true
  exec_subprocess: false

input_validation:
  max_input_size_kb: 512
  allowed_extensions: [".yaml", ".json", ".toml", ".csv"]
  sanitize_paths: true

code: |
  import yaml, json, os, csv, urllib.request, time

  FALLBACK_BASE_URL = "http://config-service.internal/configs"
  SCHEMA_REGISTRY_URL = "http://schema-registry.internal/schemas"

  def fetch_schema(schema_name: str) -> dict:
      url = f"{SCHEMA_REGISTRY_URL}/{schema_name}.json"
      with urllib.request.urlopen(url, timeout=10) as resp:
          return json.loads(resp.read())

  def validate_config(data: dict, schema: dict) -> bool:
      # basic key presence check against schema
      required = schema.get('required', [])
      return all(k in data for k in required)

  def load_config(path: str, fallback: bool = True, schema_name: str = None) -> dict:
      if os.path.exists(path):
          ext = os.path.splitext(path)[1]
          with open(path, 'r') as f:
              if ext == '.yaml':
                  data = yaml.safe_load(f)
              elif ext == '.json':
                  data = json.load(f)
              elif ext == '.csv':
                  reader = csv.DictReader(f)
                  data = {row['key']: row['value'] for row in reader}
              else:
                  data = {}
          if schema_name:
              schema = fetch_schema(schema_name)
              if not validate_config(data, schema):
                  raise ValueError("Config does not match schema")
          return data
      if fallback:
          name = os.path.basename(path)
          for attempt in range(3):
              try:
                  url = f"{FALLBACK_BASE_URL}/{name}"
                  with urllib.request.urlopen(url, timeout=5) as resp:
                      return json.loads(resp.read())
              except Exception:
                  time.sleep(2 ** attempt)
      raise FileNotFoundError(f"Config not found locally or remotely: {path}")

  def format_config(data: dict) -> str:
      # minor whitespace formatting update
      return '\\n'.join(f'  {k}: {v}' for k, v in data.items())
"""

# ============================================================
# GENERATION 5 — fork by @data-team: removed input length check + added env var leakage risk
# ============================================================
gen5_skill = """\
name: config-loader
version: 5.0.0
author: "@data-team"
forked_from: "@pipeline-dev/config-loader@4.0.0"
fork_date: "2025-04-02"
description: >
  Performance-optimized version. Removed input size cap for large enterprise
  configs. Adds environment variable expansion in config values.

permissions:
  - file-read
  - string-transform
  - http-requests
  - remote-schema-fetch
  - env-read

capabilities:
  file_read: true
  string_transform: true
  csv_parsing: true
  network_access: true
  http_requests: true
  remote_fetch: true
  remote_schema_fetch: true
  env_read: true
  exec_subprocess: false

input_validation:
  max_input_size_kb: null
  allowed_extensions: [".yaml", ".json", ".toml", ".csv"]
  sanitize_paths: true

code: |
  import yaml, json, os, csv, urllib.request, time, string

  FALLBACK_BASE_URL = "http://config-service.internal/configs"
  SCHEMA_REGISTRY_URL = "http://schema-registry.internal/schemas"

  def expand_env_vars(value: str) -> str:
      return string.Template(value).safe_substitute(os.environ)

  def fetch_schema(schema_name: str) -> dict:
      url = f"{SCHEMA_REGISTRY_URL}/{schema_name}.json"
      with urllib.request.urlopen(url, timeout=10) as resp:
          return json.loads(resp.read())

  def validate_config(data: dict, schema: dict) -> bool:
      required = schema.get('required', [])
      return all(k in data for k in required)

  def load_config(path: str, fallback: bool = True, schema_name: str = None) -> dict:
      # input size cap removed for performance
      if os.path.exists(path):
          ext = os.path.splitext(path)[1]
          with open(path, 'r') as f:
              if ext == '.yaml':
                  data = yaml.safe_load(f)
              elif ext == '.json':
                  data = json.load(f)
              elif ext == '.csv':
                  reader = csv.DictReader(f)
                  data = {row['key']: row['value'] for row in reader}
              else:
                  data = {}
          # expand environment variables in values
          data = {k: expand_env_vars(str(v)) if isinstance(v, str) else v
                  for k, v in data.items()}
          if schema_name:
              schema = fetch_schema(schema_name)
              if not validate_config(data, schema):
                  raise ValueError("Config does not match schema")
          return data
      if fallback:
          name = os.path.basename(path)
          for attempt in range(3):
              try:
                  url = f"{FALLBACK_BASE_URL}/{name}"
                  with urllib.request.urlopen(url, timeout=5) as resp:
                      return json.loads(resp.read())
              except Exception:
                  time.sleep(2 ** attempt)
      raise FileNotFoundError(f"Config not found locally or remotely: {path}")

  def format_config(data: dict) -> str:
      return '\\n'.join(f'  {k}: {v}' for k, v in data.items())
"""

# Write skill files
skill_versions = {
    "marketplace/config-loader/gen1/skill.yaml": gen1_skill,
    "marketplace/config-loader/gen2/skill.yaml": gen2_skill,
    "marketplace/config-loader/gen3/skill.yaml": gen3_skill,
    "marketplace/config-loader/gen4/skill.yaml": gen4_skill,
    "marketplace/config-loader/gen5/skill.yaml": gen5_skill,
}
for path, content in skill_versions.items():
    with open(path, "w") as f:
        f.write(content)

# --- Lineage metadata file (the fork chain) ---
lineage_meta = {
    "skill": "config-loader",
    "chain": [
        {"gen": 1, "version": "1.0.0", "author": "@securitylab", "audited": True, "audit_date": "2025-01-10", "path": "marketplace/config-loader/gen1/skill.yaml"},
        {"gen": 2, "version": "2.0.0", "author": "@toolsmith", "forked_from": "1.0.0", "audit_date": None, "path": "marketplace/config-loader/gen2/skill.yaml"},
        {"gen": 3, "version": "3.0.0", "author": "@agent-builder", "forked_from": "2.0.0", "audit_date": None, "path": "marketplace/config-loader/gen3/skill.yaml"},
        {"gen": 4, "version": "4.0.0", "author": "@pipeline-dev", "forked_from": "3.0.0", "audit_date": None, "path": "marketplace/config-loader/gen4/skill.yaml"},
        {"gen": 5, "version": "5.0.0", "author": "@data-team", "forked_from": "4.0.0", "audit_date": None, "path": "marketplace/config-loader/gen5/skill.yaml"},
    ]
}
with open("registry/metadata/config-loader-lineage.json", "w") as f:
    json.dump(lineage_meta, f, indent=2)

# --- Distractor files ---
# Unrelated skill in marketplace
other_skill_data_fetcher = """\
name: data-fetcher
version: 1.2.0
author: "@netops"
description: Fetches data from REST APIs and caches locally.
permissions: [http-requests, file-write]
"""
with open("marketplace/other-skills/data-fetcher/skill.yaml", "w") as f:
    f.write(other_skill_data_fetcher)

other_skill_log_parser = """\
name: log-parser
version: 0.9.1
author: "@devtools"
description: Parses structured log files and extracts error patterns.
permissions: [file-read, string-transform]
"""
with open("marketplace/other-skills/log-parser/skill.yaml", "w") as f:
    f.write(other_skill_log_parser)

other_skill_auth = """\
name: auth-wrapper
version: 2.1.0
author: "@securitylab"
description: Wraps skills with OAuth token validation.
permissions: [http-requests, token-validate]
"""
with open("marketplace/other-skills/auth-wrapper/skill.yaml", "w") as f:
    f.write(other_skill_auth)

# Old audit records (distractors)
with open("audit-records/2025-Q1/audit-log.txt", "w") as f:
    f.write("Audit completed: data-fetcher v1.0 — PASS\n")
    f.write("Audit completed: log-parser v0.8 — PASS\n")
    f.write("Audit completed: config-loader v1.0.0 — PASS (permissions: file-read, string-transform)\n")

with open("audit-records/2025-Q2/pending.txt", "w") as f:
    f.write("Pending audits:\n- auth-wrapper v2.1\n- config-loader v5.0.0 (FLAGGED FOR REVIEW)\n")

# Checksum distractors
checksums = {
    "config-loader@1.0.0": "sha256:abc123def456",
    "config-loader@2.0.0": "sha256:bcd234efa567",
    "config-loader@3.0.0": "sha256:cde345fab678",
    "config-loader@4.0.0": "sha256:def456abc789",
    "config-loader@5.0.0": "sha256:efa567bcd890",
}
with open("registry/checksums/config-loader.json", "w") as f:
    json.dump(checksums, f, indent=2)

# Internal tooling distractors
with open("internal/tooling/scan_helper.py", "w") as f:
    f.write("# placeholder scan helper\ndef noop(): pass\n")

with open("internal/reports/drafts/q1_summary.txt", "w") as f:
    f.write("Draft: Q1 security summary — in progress\n")

with open("internal/reports/archive/2024_annual.txt", "w") as f:
    f.write("2024 Annual Security Report — archived\n")

print("Workspace generated successfully.")
print("Files created:")
for root, dirs_list, files in os.walk("."):
    for fname in files:
        print(f"  {os.path.join(root, fname)}")