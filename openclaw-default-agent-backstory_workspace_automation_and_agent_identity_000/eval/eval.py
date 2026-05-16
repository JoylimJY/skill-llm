import sys
import os
import json
import re
from pathlib import Path

def read_file(path):
    try:
        return Path(path).read_text(encoding="utf-8")
    except Exception as e:
        return None

def evaluate(workspace):
    checks = []
    workspace = Path(workspace)

    # ------------------------------------------------------------------ #
    # HELPER
    # ------------------------------------------------------------------ #
    def check(name, passed, detail):
        checks.append({"name": name, "passed": bool(passed), "detail": str(detail)})
        return bool(passed)

    # ------------------------------------------------------------------ #
    # 1. All 7 core context files exist at workspace ROOT
    # ------------------------------------------------------------------ #
    core_files = ["AGENTS.md", "SOUL.md", "TOOLS.md", "IDENTITY.md",
                  "USER.md", "HEARTBEAT.md", "BOOTSTRAP.md"]
    all_core_exist = True
    for fname in core_files:
        fpath = workspace / fname
        exists = fpath.exists() and fpath.is_file()
        c = check(f"core_file_exists:{fname}", exists,
                  f"{'Found' if exists else 'MISSING'}: {fpath}")
        if not exists:
            all_core_exist = False

    # ------------------------------------------------------------------ #
    # 2. Core files must NOT be placeholders (non-trivial content)
    # ------------------------------------------------------------------ #
    placeholder_markers = [
        r"\(not set\)", r"TBD", r"TODO", r"\(rest TBD\)", r"Not started",
        r"\(list tools here\)", r"<!-- TODO"
    ]
    placeholder_re = re.compile("|".join(placeholder_markers), re.IGNORECASE)

    for fname in core_files:
        fpath = workspace / fname
        content = read_file(fpath)
        if content is None:
            check(f"non_placeholder:{fname}", False, "File missing, cannot check content.")
            continue
        # Must have meaningful length
        stripped = content.strip()
        long_enough = len(stripped) > 80
        no_placeholder = not placeholder_re.search(stripped)
        detail = (f"length={len(stripped)}, "
                  f"has_placeholder={not no_placeholder}")
        check(f"non_placeholder:{fname}", long_enough and no_placeholder, detail)

    # ------------------------------------------------------------------ #
    # 3. IDENTITY.md must contain all three required sections
    # ------------------------------------------------------------------ #
    identity_content = read_file(workspace / "IDENTITY.md") or ""
    has_backstory = bool(re.search(r"^#{1,3}\s+Backstory", identity_content, re.MULTILINE | re.IGNORECASE))
    has_guardrails = bool(re.search(r"^#{1,3}\s+Behavioral\s+Guardrails", identity_content, re.MULTILINE | re.IGNORECASE))
    has_growth = bool(re.search(r"^#{1,3}\s+Growth\s+Arc", identity_content, re.MULTILINE | re.IGNORECASE))
    check("identity_has_backstory_section", has_backstory,
          f"'## Backstory' section {'found' if has_backstory else 'MISSING'} in IDENTITY.md")
    check("identity_has_guardrails_section", has_guardrails,
          f"'## Behavioral Guardrails' section {'found' if has_guardrails else 'MISSING'} in IDENTITY.md")
    check("identity_has_growth_arc_section", has_growth,
          f"'## Growth Arc' section {'found' if has_growth else 'MISSING'} in IDENTITY.md")

    # ------------------------------------------------------------------ #
    # 4. IDENTITY.md reflects interview content (oncology / Tanaka / KRAS)
    # ------------------------------------------------------------------ #
    identity_lower = identity_content.lower()
    has_domain_content = (
        "oncol" in identity_lower or "kras" in identity_lower or
        "cancer" in identity_lower or "tanaka" in identity_lower or
        "bioinformatics" in identity_lower
    )
    check("identity_reflects_interview_domain", has_domain_content,
          f"IDENTITY.md should reference oncology/KRAS/Tanaka domain from interview answers. "
          f"Found relevant keywords: {has_domain_content}")

    # ------------------------------------------------------------------ #
    # 5. IDENTITY.md guardrails reflect actual constraints from interview
    # ------------------------------------------------------------------ #
    guardrails_keywords = ["fabricat", "citation", "clinical", "confidential", "sample id", "escalat"]
    guardrail_hits = sum(1 for kw in guardrails_keywords if kw in identity_lower)
    check("identity_guardrails_reflect_interview",
          guardrail_hits >= 2,
          f"Guardrails section should reflect interview Q4 constraints. "
          f"Found {guardrail_hits}/6 expected keywords in IDENTITY.md.")

    # ------------------------------------------------------------------ #
    # 6. MEMORY.md exists as standalone root file (NOT inside AGENTS.md)
    # ------------------------------------------------------------------ #
    memory_file = workspace / "MEMORY.md"
    memory_exists_as_root = memory_file.exists() and memory_file.is_file()
    check("MEMORY_md_exists_at_root", memory_exists_as_root,
          f"MEMORY.md {'found' if memory_exists_as_root else 'MISSING'} at workspace root.")

    # Check AGENTS.md does NOT contain MEMORY as its only/primary memory doc
    agents_content = read_file(workspace / "AGENTS.md") or ""
    # It's OK if AGENTS.md mentions memory, but MEMORY.md must be standalone
    # Fail if MEMORY.md is missing but AGENTS.md has a "## Memory" section claiming to be the memory file
    if not memory_exists_as_root:
        agents_has_memory_section = bool(re.search(r"^#{1,3}\s+Memory", agents_content, re.MULTILINE | re.IGNORECASE))
        check("memory_not_embedded_only_in_agents",
              not agents_has_memory_section,
              "MEMORY.md is missing AND AGENTS.md has a ## Memory section — this violates the standalone MEMORY.md rule.")
    else:
        check("memory_not_embedded_only_in_agents", True,
              "MEMORY.md exists as standalone file — constraint satisfied.")

    # ------------------------------------------------------------------ #
    # 7. memory/ directory exists at workspace root
    # ------------------------------------------------------------------ #
    memory_dir = workspace / "memory"
    memory_dir_exists = memory_dir.exists() and memory_dir.is_dir()
    check("memory_directory_exists", memory_dir_exists,
          f"memory/ directory {'found' if memory_dir_exists else 'MISSING'} at workspace root.")

    # ------------------------------------------------------------------ #
    # 8. BOOTSTRAP.md is SHORT (under 400 words) and has status + next steps
    # ------------------------------------------------------------------ #
    bootstrap_content = read_file(workspace / "BOOTSTRAP.md") or ""
    word_count = len(bootstrap_content.split())
    bootstrap_short = word_count < 400
    has_status = bool(re.search(r"status|complete|done|created|bootstrapped", bootstrap_content, re.IGNORECASE))
    has_next_steps = bool(re.search(r"next\s+step|todo|remaining|action", bootstrap_content, re.IGNORECASE))
    check("bootstrap_is_short",
          bootstrap_short,
          f"BOOTSTRAP.md has {word_count} words (must be < 400).")
    check("bootstrap_has_status",
          has_status,
          f"BOOTSTRAP.md should contain setup status. Found: {has_status}")
    check("bootstrap_has_next_steps",
          has_next_steps,
          f"BOOTSTRAP.md should contain next steps. Found: {has_next_steps}")

    # ------------------------------------------------------------------ #
    # 9. MEMORY.md reflects session/memory policy from interview (Q5)
    # ------------------------------------------------------------------ #
    memory_content = read_file(memory_file) or ""
    memory_lower = memory_content.lower()
    memory_policy_keywords = ["daily", "session", "project", "decision", "sample id"]
    mem_hits = sum(1 for kw in memory_policy_keywords if kw in memory_lower)
    check("memory_reflects_interview_policy",
          mem_hits >= 2,
          f"MEMORY.md should reflect Q5 session/memory policy. "
          f"Found {mem_hits}/5 expected keywords.")

    # ------------------------------------------------------------------ #
    # 10. TOOLS.md reflects actual tools from interview (Q2)
    # ------------------------------------------------------------------ #
    tools_content = read_file(workspace / "TOOLS.md") or ""
    tools_lower = tools_content.lower()
    tools_keywords = ["python", "jupyter", "deseq", "pandas", "slack", "notion", "s3"]
    tools_hits = sum(1 for kw in tools_keywords if kw in tools_lower)
    check("tools_reflects_interview_tools",
          tools_hits >= 3,
          f"TOOLS.md should list tools from interview Q2. "
          f"Found {tools_hits}/7 expected tool names.")

    # ------------------------------------------------------------------ #
    # 11. USER.md has meaningful content about Dr. Tanaka beyond stub
    # ------------------------------------------------------------------ #
    user_content = read_file(workspace / "USER.md") or ""
    user_lower = user_content.lower()
    # Must have more than just the name/role that was already in the stub
    user_enriched = (
        len(user_content.strip()) > 200 and
        ("principal investigator" in user_lower or "pi" in user_lower or "oncol" in user_lower) and
        not placeholder_re.search(user_content)
    )
    check("user_md_enriched_beyond_stub",
          user_enriched,
          f"USER.md should be enriched beyond the stub. "
          f"Length={len(user_content.strip())}, oncology_context={'oncol' in user_lower}")

    # ------------------------------------------------------------------ #
    # Scoring
    # ------------------------------------------------------------------ #
    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = round(passed_count / total, 4)
    all_passed = passed_count == total

    return {
        "passed": all_passed,
        "score": score,
        "checks": checks
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0,
                          "checks": [{"name": "args", "passed": False,
                                      "detail": "No workspace path provided."}]}))
        sys.exit(1)
    result = evaluate(sys.argv[1])
    print(json.dumps(result, indent=2))