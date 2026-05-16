#!/usr/bin/env python3
"""
Generate the initial sandbox workspace.
Simulates a partially-started, messy project repo for a HealthTech SaaS.
The agent must produce a proper monorepo scaffold from scratch.
"""
import os
import random
import textwrap
from pathlib import Path

random.seed(42)

WORKSPACE = Path("/workspace")

# ─── Distractor files simulating a chaotic previous attempt ───────────────────

distractors = {
    "old_attempt/backend/app.py": textwrap.dedent("""\
        # DEPRECATED - do not use
        from flask import Flask
        app = Flask(__name__)
        @app.route('/')
        def index():
            return 'hello'
    """),
    "old_attempt/frontend/index.js": textwrap.dedent("""\
        // old flat structure, not TypeScript
        var x = 1
        console.log(x)
    """),
    "old_attempt/README.txt": "This is an old readme. Ignore.",
    "old_attempt/config/settings.py": textwrap.dedent("""\
        DB_HOST = 'localhost'
        DB_PASSWORD = 'supersecret123'   # BAD: secret in code
        DEBUG = True
    """),
    "old_attempt/config/docker-compose.yml": textwrap.dedent("""\
        version: '3'
        services:
          backend:
            image: python:latest   # BAD: unpinned
            user: root             # BAD: running as root
    """),
    "scratch/notes.txt": textwrap.dedent("""\
        Ideas:
        - Use FastAPI for backend
        - React + TypeScript for frontend
        - Postgres for DB
        - Redis cache
        - Monorepo? Yes probably
        - Need CI/CD
    """),
    "scratch/stack_options.md": textwrap.dedent("""\
        ## Considered stacks
        | Layer | Option A | Option B |
        |-------|----------|----------|
        | API   | Flask    | FastAPI  |
        | Front | Vue      | React+TS |
        | DB    | MySQL    | Postgres |
        Chose: FastAPI + React/TS + Postgres + Redis
    """),
    "scratch/security_thoughts.txt": textwrap.dedent("""\
        - Must avoid secrets in code (learned from old config)
        - Need rate limiting on API
        - HTTPS only
        - Helmet for Node side
    """),
    "team/contacts.txt": "Alice (backend), Bob (frontend), Carol (devops)\n",
    "team/onboarding_draft.md": textwrap.dedent("""\
        # Onboarding (DRAFT)
        - Set up local env
        - Ask Alice for access
        - Read ... (TBD)
    """),
    "specs/product_spec.md": textwrap.dedent("""\
        # ClarityHealth Analytics Platform

        ## Purpose
        Enable clinicians to analyse de-identified patient datasets
        and generate actionable insights via a web dashboard.

        ## Users
        - Clinicians (read dashboards)
        - Data scientists (upload & process datasets)
        - Admins (manage users, audit logs)

        ## Key Constraints
        - HIPAA-adjacent data handling
        - Must scale to 50k concurrent users
        - Low-latency API (< 200ms p99)
    """),
    "specs/adr_ideas.txt": textwrap.dedent("""\
        ADR candidates:
        1. Monorepo vs separate repos  -> monorepo (shared types)
        2. FastAPI vs Flask            -> FastAPI (async, typing)
        3. Postgres vs MySQL           -> Postgres (JSONB, extensions)
    """),
    "infra/terraform_stub.tf": textwrap.dedent("""\
        # placeholder
        provider \"aws\" {
          region = \"us-east-1\"
        }
    """),
}

for rel_path, content in distractors.items():
    full_path = WORKSPACE / rel_path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content)

# ─── Existing skill asset files (simulate the SKILL.md workspace) ─────────────
# The skill references these; they must exist so the agent can read them.

skill_assets = {
    "assets/templates/README.md": textwrap.dedent("""\
        # Project:

        ## Overview

        Brief description of the project.

        ## Quick Start

        ### Node / TypeScript

        ```bash
        git clone ...
        npm install
        npm run dev
        ```

        ### Python

        ```bash
        git clone ...
        python3 -m venv .venv
        source .venv/bin/activate   # Windows: .venv\\Scripts\\activate
        pip install -e .
        pytest
        ```

        ## Architecture

        - **Frontend**: [React/Vue/Next.js]
        - **Backend**: [Node/Python/Go]
        - **Database**: [Postgres/MySQL/SQLite]
        - **Cache**: [Redis/Memcached]

        See [ARCHITECTURE.md](ARCHITECTURE.md) for components, data flow, and decisions.

        ## Development Standards

        - Use pre-commit hooks (e.g. `husky` for Node, `pre-commit` for Python).
        - Lint and format before pushing.
        - Unit tests required for new features.

        ## Contributors

        - [Your Name]
    """),
    "assets/templates/ARCHITECTURE.md": textwrap.dedent("""\
        # Architecture: {{project_name}}

        ## Overview
        High-level description of the system: purpose, main users, and key constraints.

        ## Components

        | Component | Responsibility | Tech |
        |-----------|----------------|------|
        | [Frontend/API/Worker] | [Brief responsibility] | [Stack] |

        ## Data Flow
        - Describe request/response paths.
        - Note async flows (queues, events) if any.

        ## Deployment
        - **Runtime**: [Docker / K8s / Serverless]
        - **Environments**: dev, staging, prod
        - **Secrets**: env vars / vault; never in repo.

        ## Decisions
        - **ADR-001**: [Title] – [One-line summary and link or short rationale.]

        ## Diagrams
        Use Mermaid in this doc or link to `docs/diagrams/`. Keep node IDs safe (no spaces, quoted labels).
    """),
    "assets/templates/.editorconfig": textwrap.dedent("""\
        root = true

        [*]
        charset = utf-8
        end_of_line = lf
        insert_final_newline = true
        trim_trailing_whitespace = true

        [*.py]
        indent_style = space
        indent_size = 4
        max_line_length = 88

        [*.{js,ts,json}]
        indent_style = space
        indent_size = 2

        [*.md]
        trim_trailing_whitespace = false
    """),
    "assets/templates/.pylintrc": textwrap.dedent("""\
        [MASTER]
        jobs=1

        [MESSAGES CONTROL]
        disable=C0114,C0115,C0116

        [FORMAT]
        max-line-length=88
        indent-string='    '

        [DESIGN]
        max-args=7
        max-attributes=10
    """),
    "assets/templates/.eslintrc.json": textwrap.dedent("""\
        {
          "root": true,
          "parser": "@typescript-eslint/parser",
          "plugins": ["@typescript-eslint", "prettier"],
          "extends": [
            "eslint:recommended",
            "plugin:@typescript-eslint/recommended",
            "plugin:prettier/recommended"
          ],
          "rules": {
            "@typescript-eslint/no-explicit-any": "error",
            "prettier/prettier": "error"
          },
          "env": {
            "node": true,
            "es2021": true
          }
        }
    """),
    "references/python-standards.md": textwrap.dedent("""\
        # Python Development Standards

        ## Code Style (PEP 8)
        - Use **snake_case** for variables, functions, and methods.
        - Use **PascalCase** for classes.
        - Use **UPPER_CASE** for constants.
        - Indent using **4 spaces**.
        - Maximum line length: **88 characters** (Black standard) or 79 (PEP 8 strict).

        ## Structure
        - Use `src/` for source code.
        - Use `tests/` for unit tests (pytest recommended).
        - Include `pyproject.toml` for modern packaging.
        - Use `if __name__ == "__main__":` for scripts.

        ## Tools
        - **Formatter**: `black` or `ruff`.
        - **Linter**: `pylint` or `ruff`.
        - **Type Checking**: `mypy` (strict mode).
    """),
    "references/js-ts-standards.md": textwrap.dedent("""\
        # JavaScript/TypeScript Development Standards

        ## Code Style
        - Use **camelCase** for variables, functions, and methods.
        - Use **PascalCase** for classes, components, and interfaces.
        - Use **UPPER_CASE** for constants.
        - Indent using **2 spaces**.
        - Always use **Semicolons**.

        ## TypeScript Rules
        - Avoid `any` - use explicit types or `unknown`.
        - Use `interface` over `type` for object shapes.
        - Enable `strict: true` in `tsconfig.json`.

        ## Tools
        - **Formatter**: `prettier`.
        - **Linter**: `eslint` (with TypeScript plugin).
        - **Package Manager**: `npm` (preferred) or `pnpm`.
    """),
    "references/scaffolding.md": textwrap.dedent("""\
        # Project Scaffolding

        Standard directory layouts for new projects. Prefer minimalism; add only what the project needs.

        ## Python (package or app)

        ```
        project/
        ├── src/
        │   └── <package_name>/
        │       ├── __init__.py
        │       └── ...
        ├── tests/
        │   ├── __init__.py
        │   └── test_*.py
        ├── docs/
        ├── pyproject.toml
        ├── README.md
        ├── .editorconfig
        ├── .gitignore
        └── .env.example
        ```

        - Use `src/` layout so the package is not imported from the repo root; install with `pip install -e .`.
        - Alternative: flat `app/` or `<package_name>/` at root for small scripts or single-module apps.
        - Config: `pyproject.toml` for tooling (Black, Ruff, mypy, pytest). Optional `.pylintrc` if using Pylint.

        ## JavaScript / TypeScript (Node or SPA)

        ```
        project/
        ├── src/
        │   ├── index.ts (or main entry)
        │   └── ...
        ├── public/          (if SPA)
        ├── tests/           (or __tests__/, spec/)
        ├── package.json
        ├── tsconfig.json
        ├── .eslintrc.json
        ├── .editorconfig
        ├── README.md
        ├── .gitignore
        └── .env.example
        ```

        - Use `src/` for application code; config at repo root.
        - Tests: `tests/` or colocated `__tests__/` / `*.spec.ts` depending on framework.
        - Add `vite.config.ts`, `next.config.js`, etc. at root as needed.

        ## Full-stack (monorepo or separate repos)

        - **Option A**: Two repos (frontend, backend); each follows the layout above.
        - **Option B**: Monorepo with `apps/frontend/`, `apps/backend/`, shared code in `packages/` (e.g. pnpm workspaces, Turborepo, Nx).
        - Prefer separate repos unless you need shared types or coordinated releases.

        ## Config files to add from templates

        - `.editorconfig` – shared indent, charset, line endings.
        - `.pylintrc` or Ruff in `pyproject.toml` – Python lint.
        - `.eslintrc.json` + Prettier – JS/TS lint and format.
        - `ARCHITECTURE.md` – overview, components, data flow, deployment, decisions.
    """),
    "references/security-checklist.md": textwrap.dedent("""\
        # Security Checklist (OWASP-Based)

        ## General
        - [ ] No secrets in code or git (use `.env`).
        - [ ] Dependencies are audited (`npm audit`, `pip-audit`).
        - [ ] Use HTTPS everywhere (no mixed content).

        ## Python (Flask/FastAPI)
        - [ ] Security headers set (e.g. FastAPI/Starlette middleware, or Flask-Talisman); secure cookie settings.
        - [ ] SQL injection prevention (ORM or parametrized queries only).
        - [ ] Rate limiting enabled (e.g. `Flask-Limiter`, `slowapi`).

        ## Node.js (Express)
        - [ ] Use `helmet` middleware.
        - [ ] Input validation (Joi/Zod) on all endpoints.
        - [ ] Sanitize HTML inputs (XSS prevention).

        ## Docker
        - [ ] Run as non-root user.
        - [ ] Pin base image versions (e.g. `python:3.11-slim`, not `latest`).
        - [ ] Minimal base images (Alpine/Distroless).
    """),
    "SKILL.md": textwrap.dedent("""\
        ---
        name: system-architect
        description: Acts as a Senior System Architect to design robust, scalable, and maintainable software architectures. Enforces industry standards (PEP 8 for Python, ESLint for JS/TS), modular design, and security best practices. Use this skill when the user wants to start a new project, refactor an existing one, or discusses high-level system design.
        ---

        # System Architect

        ## Usage
        - **Role**: You are a strict but helpful Technical Lead.
        - **Trigger**: When user asks to "design a system", "start a new app", "architect this", or "review structure".
        - **Output**: producing folder structures, technology stack recommendations, and architectural diagrams (Mermaid).

        ## Capabilities
        1.  **Project Scaffolding**: Create standard directory layouts.
        2.  **Tech Stack Selection**: Recommend tools based on requirements (e.g. Flask vs FastAPI, React vs Vue).
        3.  **Code Standards**: Provide `pylintrc`, `.eslintrc`, `.editorconfig` templates.
        4.  **Documentation**: Generate `README.md` and `ARCHITECTURE.md` templates.

        ## Rules
        - Always prioritize **Security** and **Scalability**.
        - Prefer **Minimalism** (YAGNI principle).
        - Use **Docker** for containerization by default.
        - Ensure all code examples follow strict linting rules.

        ## Reference Materials
        - [Python Standards](references/python-standards.md)
        - [JS/TS Standards](references/js-ts-standards.md)
        - [Security Checklist](references/security-checklist.md)
        - [Scaffolding](references/scaffolding.md) – standard directory layouts for Python and JS/TS.

        ## Assets (templates)
        - [README](assets/templates/README.md) – project overview, Node and Python quick-start.
        - [ARCHITECTURE](assets/templates/ARCHITECTURE.md) – components, data flow, deployment, decisions.
        - [.editorconfig](assets/templates/.editorconfig) – shared indent and line length.
        - [.pylintrc](assets/templates/.pylintrc) – Python lint (PEP 8–aligned).
        - [.eslintrc.json](assets/templates/.eslintrc.json) – JS/TS lint (TypeScript strict, Prettier).
    """),
}

for rel_path, content in skill_assets.items():
    full_path = WORKSPACE / rel_path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content)

print("Workspace generated successfully.")
print("\nDirectory structure:")
for p in sorted(WORKSPACE.rglob("*")):
    if p.is_file():
        print(f"  {p.relative_to(WORKSPACE)}")