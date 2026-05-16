import os
import json
import textwrap
from pathlib import Path

WORKSPACE = Path("/workspace")

# ── directory skeleton ──────────────────────────────────────────────────────
dirs = [
    "memory",
    "src",
    "tests",
    "logs",
    "docs",
    "infra/terraform",
    "infra/ansible",
    "scripts",
    "data/raw",
    "data/processed",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# ── distractor files (realistic noise) ──────────────────────────────────────
(WORKSPACE / "docs" / "architecture.md").write_text(textwrap.dedent("""\
    # Architecture Notes
    The payment-gateway service exposes REST endpoints on a configurable port.
    All configuration is read from config.ini at startup.
    Database credentials are injected via environment or config file.
"""))

(WORKSPACE / "docs" / "runbook.md").write_text(textwrap.dedent("""\
    # Runbook
    1. Deploy with `python src/service.py`
    2. Healthcheck: `curl http://localhost:<PORT>/health`
    3. Logs written to logs/service.log
"""))

(WORKSPACE / "infra/terraform" / "main.tf").write_text(textwrap.dedent("""\
    resource "aws_instance" "gateway" {
      ami           = "ami-0abcdef1234567890"
      instance_type = "t3.micro"
    }
"""))

(WORKSPACE / "infra/ansible" / "deploy.yml").write_text(textwrap.dedent("""\
    - hosts: all
      tasks:
        - name: start service
          command: python /opt/service/src/service.py
"""))

(WORKSPACE / "scripts" / "migrate_db.sh").write_text("#!/bin/bash\necho 'Running DB migrations...'\n")
(WORKSPACE / "scripts" / "seed_data.sh").write_text("#!/bin/bash\necho 'Seeding data...'\n")

(WORKSPACE / "logs" / ".gitkeep").write_text("")

(WORKSPACE / "data" / "raw" / "transactions_2024.csv").write_text(
    "id,amount,currency\n1,100.00,USD\n2,250.50,EUR\n3,75.00,GBP\n"
)

(WORKSPACE / "data" / "processed" / ".gitkeep").write_text("")

# ── BROKEN config.ini ────────────────────────────────────────────────────────
# Bugs:
#   1. port is "eighty" instead of integer 8080
#   2. db_url key is named "database_url" but service.py expects "db_url"
#   3. timeout is missing entirely (service.py expects it, default should be 30)
(WORKSPACE / "config.ini").write_text(textwrap.dedent("""\
    [server]
    host = 0.0.0.0
    port = eighty
    debug = false

    [database]
    database_url = postgres://user:pass@localhost:5432/payments
    pool_size = 5

    [cache]
    enabled = true
    ttl = 300
"""))

# ── BROKEN data/raw/service_rules.json ───────────────────────────────────────
# Bug: malformed JSON (trailing comma)
(WORKSPACE / "data" / "raw" / "service_rules.json").write_text(textwrap.dedent("""\
    {
        "max_retries": 3,
        "allowed_currencies": ["USD", "EUR", "GBP"],
        "rate_limit": 100,
    }
"""))

# ── src/service.py ────────────────────────────────────────────────────────────
# Reads config.ini and service_rules.json; exposes simple functions tested by tests/
(WORKSPACE / "src" / "service.py").write_text(textwrap.dedent("""\
    import configparser
    import json
    from pathlib import Path

    BASE = Path(__file__).parent.parent

    def load_config():
        cfg = configparser.ConfigParser()
        cfg.read(BASE / "config.ini")
        port = cfg.getint("server", "port")          # must be integer
        db_url = cfg.get("database", "db_url")       # key must be db_url
        timeout = cfg.getint("server", "timeout")    # must exist
        return {"port": port, "db_url": db_url, "timeout": timeout}

    def load_rules():
        rules_path = BASE / "data" / "raw" / "service_rules.json"
        with open(rules_path) as f:
            return json.load(f)

    def is_currency_allowed(currency: str) -> bool:
        rules = load_rules()
        return currency.upper() in rules["allowed_currencies"]
"""))

# ── tests/test_service.py ─────────────────────────────────────────────────────
(WORKSPACE / "tests" / "test_service.py").write_text(textwrap.dedent("""\
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

    from service import load_config, load_rules, is_currency_allowed

    def test_config_port_is_integer():
        cfg = load_config()
        assert isinstance(cfg["port"], int), f"port must be int, got {type(cfg['port'])}"
        assert cfg["port"] == 8080

    def test_config_db_url_present():
        cfg = load_config()
        assert cfg["db_url"].startswith("postgres://"), "db_url must be a postgres URI"

    def test_config_timeout_present():
        cfg = load_config()
        assert cfg["timeout"] == 30, f"Expected timeout=30, got {cfg['timeout']}"

    def test_rules_json_valid():
        rules = load_rules()
        assert isinstance(rules, dict)
        assert "allowed_currencies" in rules

    def test_currency_allowed():
        assert is_currency_allowed("USD") is True
        assert is_currency_allowed("JPY") is False
"""))

# ── memory/tasks.md — intentionally ABSENT (agent must create it) ─────────────
# (not created here)

print("Workspace generated successfully.")