import os
import stat
import textwrap
from pathlib import Path

WORKSPACE = Path("/workspace")

# ── Skill scripts (simulate they already exist, as per instructions) ──────────
skill_scripts = WORKSPACE / "scripts"
skill_scripts.mkdir(parents=True, exist_ok=True)

# bootstrap_project.py — realistic implementation matching SKILL.md spec
bootstrap_src = textwrap.dedent('''\
    #!/usr/bin/env python3
    """Bootstrap script for agent-harness-engineering skill."""
    import argparse, os, sys, textwrap
    from pathlib import Path

    AGENT_DOCS = [
        "index.md", "architecture.md", "specs.md",
        "plans.md", "quality.md", "reliability.md", "security.md",
    ]

    AGENTS_MD_BLOCK = textwrap.dedent("""
        ## Agent Navigation

        | What you need | Where to look |
        |---|---|
        | Overview | [docs/agent/index.md](docs/agent/index.md) |
        | Architecture | [docs/agent/architecture.md](docs/agent/architecture.md) |
        | Specs | [docs/agent/specs.md](docs/agent/specs.md) |
        | Plans | [docs/agent/plans.md](docs/agent/plans.md) |
        | Quality gates | [docs/agent/quality.md](docs/agent/quality.md) |
        | Reliability | [docs/agent/reliability.md](docs/agent/reliability.md) |
        | Security | [docs/agent/security.md](docs/agent/security.md) |
        | Checks | Run `python3 scripts/agent_repo_check.py` |
    """).strip()

    FRONTMATTER_TMPL = """\
    ---
    owner: platform-team
    last_reviewed: 2025-01-01
    ---
    """

    INDEX_TMPL = """\
    ---
    owner: platform-team
    last_reviewed: 2025-01-01
    ---

    # Agent Doc Index

    - [architecture](architecture.md)
    - [specs](specs.md)
    - [plans](plans.md)
    - [quality](quality.md)
    - [reliability](reliability.md)
    - [security](security.md)
    """

    INDEX_GC_EXTRA = "- [garbage-collection](garbage-collection.md)\\n"

    GC_DOC = """\
    ---
    owner: platform-team
    last_reviewed: 2025-01-01
    ---

    # Garbage Collection Report

    This doc tracks candidates for cleanup: stale docs, oversized files,
    suspicious filenames (final-final, v2), TODO/FIXME clusters, and
    docs not linked from the index.
    """

    CHECK_SCRIPT = textwrap.dedent("""
        #!/usr/bin/env python3
        \"\"\"Mechanical repo check for agent harness.\"\"\"
        import sys
        from pathlib import Path

        REQUIRED_DOCS = [
            "docs/agent/index.md",
            "docs/agent/architecture.md",
            "docs/agent/specs.md",
            "docs/agent/plans.md",
            "docs/agent/quality.md",
            "docs/agent/reliability.md",
            "docs/agent/security.md",
        ]

        REQUIRED_FRONTMATTER = ["owner", "last_reviewed"]

        def check_frontmatter(path):
            text = path.read_text()
            if not text.startswith("---"):
                return False
            end = text.find("---", 3)
            if end == -1:
                return False
            block = text[3:end]
            return all(f in block for f in REQUIRED_FRONTMATTER)

        errors = []
        repo = Path(".")
        for doc in REQUIRED_DOCS:
            p = repo / doc
            if not p.exists():
                errors.append(f"MISSING: {doc}")
            elif not check_frontmatter(p):
                errors.append(f"BAD FRONTMATTER: {doc}")

        agents_md = repo / "AGENTS.md"
        if agents_md.exists():
            content = agents_md.read_text()
            if "docs/agent/index.md" not in content:
                errors.append("AGENTS.md does not link to docs/agent/index.md")

        if errors:
            for e in errors:
                print("ERROR:", e)
            sys.exit(1)
        else:
            print("OK: all checks passed")
    """).strip()

    def write_if_new_or_force(path: Path, content: str, force: bool, dry_run: bool):
        if path.exists() and not force:
            print(f"  skip (exists): {path}")
            return
        if dry_run:
            print(f"  [dry-run] would write: {path}")
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(textwrap.dedent(content))
        print(f"  wrote: {path}")

    def main():
        parser = argparse.ArgumentParser()
        parser.add_argument("--repo", required=True)
        parser.add_argument("--mode", choices=["overlay", "full"], default="overlay")
        parser.add_argument("--with-gc", action="store_true")
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--force", action="store_true")
        parser.add_argument("--no-claude-link", action="store_true")
        args = parser.parse_args()

        repo = Path(args.repo).resolve()
        force = args.force
        dry_run = args.dry_run
        print(f"Bootstrap mode={args.mode} repo={repo} with-gc={args.with_gc} dry-run={dry_run} force={force}")

        # docs/agent/ leaf docs
        agent_dir = repo / "docs" / "agent"
        for name in AGENT_DOCS:
            p = agent_dir / name
            if name == "index.md":
                content = INDEX_TMPL
                if args.with_gc:
                    # inject GC link into index
                    content = content.rstrip() + "\\n" + INDEX_GC_EXTRA
            else:
                content = FRONTMATTER_TMPL + "\\n# " + name.replace(".md","").capitalize() + "\\n"
            write_if_new_or_force(p, content, force, dry_run)

        # garbage-collection doc
        if args.with_gc:
            gc_doc = agent_dir / "garbage-collection.md"
            write_if_new_or_force(gc_doc, GC_DOC, force, dry_run)
            gc_script = repo / "scripts" / "agent_gc_report.py"
            write_if_new_or_force(gc_script, "#!/usr/bin/env python3\\n# GC report stub\\nprint(\\'GC: no issues found\\')\\n", force, dry_run)

        # agent_repo_check.py
        check_p = repo / "scripts" / "agent_repo_check.py"
        write_if_new_or_force(check_p, CHECK_SCRIPT, force, dry_run)

        # AGENTS.md — update or create
        agents_md = repo / "AGENTS.md"
        if agents_md.exists() and not force:
            existing = agents_md.read_text()
            if "## Agent Navigation" not in existing:
                if not dry_run:
                    agents_md.write_text(AGENTS_MD_BLOCK + "\\n\\n" + existing)
                    print(f"  prepended nav block to: {agents_md}")
                else:
                    print(f"  [dry-run] would prepend nav block to: {agents_md}")
            else:
                print(f"  skip AGENTS.md (nav block already present)")
        else:
            write_if_new_or_force(agents_md, AGENTS_MD_BLOCK + "\\n", force, dry_run)

        # CLAUDE.md symlink
        claude_md = repo / "CLAUDE.md"
        if not args.no_claude_link:
            if not claude_md.exists() or force:
                if not dry_run:
                    if claude_md.exists() or claude_md.is_symlink():
                        claude_md.unlink()
                    claude_md.symlink_to("AGENTS.md")
                    print(f"  symlink: CLAUDE.md -> AGENTS.md")
                else:
                    print(f"  [dry-run] would symlink: CLAUDE.md -> AGENTS.md")
            else:
                print(f"  skip CLAUDE.md (exists)")

        print("Done.")

    if __name__ == "__main__":
        main()
''')
(skill_scripts / "bootstrap_project.py").write_text(bootstrap_src)
os.chmod(skill_scripts / "bootstrap_project.py", 0o755)

# ── Simulated fintech payment-processing repo ─────────────────────────────────
repo = WORKSPACE / "payflow-repo"
repo.mkdir(parents=True, exist_ok=True)

# Bloated AGENTS.md (what the agent must fix — too long, not a router)
bloated_agents_md = textwrap.dedent("""\
    # AGENTS.md — PayFlow Backend

    This file is the single source of truth for our coding agents.

    ## Architecture
    PayFlow uses a microservice architecture with three core services:
    - payment-gateway: handles Stripe/Adyen webhook ingestion
    - ledger-service: double-entry accounting engine (Postgres)
    - fraud-ml: real-time fraud scoring via feature store

    All services communicate over gRPC with mTLS. The API gateway is Kong.

    ## Tech stack
    - Python 3.11, FastAPI, SQLAlchemy 2.x
    - PostgreSQL 15, Redis 7
    - Kubernetes 1.29 on GKE
    - GitHub Actions for CI

    ## Quality Gates
    - All PRs must pass `pytest` with >85% coverage
    - mypy --strict on all service packages
    - ruff check with no errors
    - docker build must succeed
    - No secrets committed (detect-secrets baseline)

    ## Reliability
    - SLO: 99.9% uptime per service per month
    - All external calls have 3-retry exponential backoff
    - Circuit breaker on fraud-ml calls (fallback: allow with flag)
    - PagerDuty alerts on p95 > 500ms

    ## Security
    - mTLS between all internal services
    - Secrets in GCP Secret Manager only
    - OWASP dependency scan weekly
    - pen-test annually

    ## Deployment
    Run `make deploy` to push to staging. Production requires two approvals.

    ## Onboarding
    Clone the repo. Run `make dev` to start the local stack. See docs/onboarding.md.

    ## How to add a new endpoint
    1. Add route in `src/gateway/routes/`
    2. Write contract test
    3. Update OpenAPI spec
    4. Open PR

    ## How to add a DB migration
    Use alembic: `alembic revision --autogenerate -m "description"`
    Never run migrations in production manually.

    ## Troubleshooting
    If Redis is down, the idempotency layer falls back to Postgres. Check the REDIS_FALLBACK env var.

    ## Contact
    Platform team: #platform-eng on Slack
""")
(repo / "AGENTS.md").write_text(bloated_agents_md)

# Existing docs structure (partial, no docs/agent/)
(repo / "docs").mkdir(exist_ok=True)
(repo / "docs" / "onboarding.md").write_text("# Onboarding\nSee the wiki.\n")
(repo / "docs" / "runbook.md").write_text("# Runbook\nOperational runbooks here.\n")
(repo / "docs" / "adr").mkdir(exist_ok=True)
(repo / "docs" / "adr" / "001-grpc-transport.md").write_text("# ADR 001: gRPC Transport\nDecision: use gRPC.\n")
(repo / "docs" / "adr" / "002-postgres-ledger.md").write_text("# ADR 002: Postgres for Ledger\n")

# Source tree (distractor files)
for svc in ["payment-gateway", "ledger-service", "fraud-ml"]:
    svc_dir = repo / "src" / svc
    svc_dir.mkdir(parents=True, exist_ok=True)
    (svc_dir / "main.py").write_text(f"# {svc} entry point\n")
    (svc_dir / "models.py").write_text(f"# {svc} models\n")
    (svc_dir / "routes.py").write_text(f"# {svc} routes\n")
    (svc_dir / "tests").mkdir(exist_ok=True)
    (svc_dir / "tests" / "test_basic.py").write_text(f"# {svc} tests\n")

# Stale distractor files (GC bait)
(repo / "src" / "fraud-ml" / "model-final-final.pkl").write_text("binary_stub")
(repo / "src" / "payment-gateway" / "routes_v2.py").write_text("# old version\n")

# CI config (GitHub Actions)
github_dir = repo / ".github" / "workflows"
github_dir.mkdir(parents=True, exist_ok=True)
(github_dir / "ci.yml").write_text(textwrap.dedent("""\
    name: CI
    on: [push, pull_request]
    jobs:
      test:
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@v4
          - name: Run tests
            run: |
              pip install -r requirements.txt
              pytest
          - name: Lint
            run: ruff check .
"""))

# Makefile
(repo / "Makefile").write_text(textwrap.dedent("""\
    .PHONY: dev test lint deploy check

    dev:
    \tdocker-compose up

    test:
    \tpytest

    lint:
    \truff check .

    check:
    \techo "TODO: add repo checks here"

    deploy:
    \tkubectl apply -f k8s/
"""))

# requirements stub
(repo / "requirements.txt").write_text("fastapi\nsqlalchemy\npsycopg2-binary\nredis\npytest\nruff\nmypy\n")

# k8s stubs
k8s_dir = repo / "k8s"
k8s_dir.mkdir(exist_ok=True)
(k8s_dir / "gateway-deploy.yaml").write_text("# k8s deployment stub\n")
(k8s_dir / "ledger-deploy.yaml").write_text("# k8s deployment stub\n")
(k8s_dir / "fraud-deploy.yaml").write_text("# k8s deployment stub\n")

# Existing scripts dir in repo (not the skill's scripts)
repo_scripts = repo / "scripts"
repo_scripts.mkdir(exist_ok=True)
(repo_scripts / "run_migrations.sh").write_text("#!/bin/bash\nalembic upgrade head\n")
(repo_scripts / "seed_data.py").write_text("# seed development data\n")

print("Workspace generated successfully.")
print(f"Repo at: {repo}")
print(f"Skill bootstrap script at: {skill_scripts / 'bootstrap_project.py'}")