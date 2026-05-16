#!/usr/bin/env python3
"""Evaluation script for the DataOps skill audit task."""
import sys
import json
from pathlib import Path

def find_report(workspace: Path) -> Path | None:
    candidates = list(workspace.rglob("vetting_report.json"))
    if candidates:
        return candidates[0]
    return None

def find_markdown(workspace: Path) -> Path | None:
    candidates = list(workspace.rglob("*.md")) + list(workspace.rglob("*.markdown"))
    # Filter out docs/CHANGELOG.md which is a distractor
    candidates = [c for c in candidates if "CHANGELOG" not in c.name and "changelog" not in c.name.lower()]
    for c in candidates:
        try:
            content = c.read_text()
            if "DataOps" in content and "|" in content and "Score" in content:
                return c
        except Exception:
            continue
    return None

def main():
    workspace = Path(sys.argv[1])
    checks = []
    total_score = 0.0

    # ── CHECK 1: vetting_report.json exists ──────────────────────────────────
    report_path = find_report(workspace)
    if report_path:
        checks.append({"name": "vetting_report.json exists", "passed": True, "detail": f"Found at {report_path}"})
        total_score += 10
    else:
        checks.append({"name": "vetting_report.json exists", "passed": False, "detail": "Could not find vetting_report.json anywhere in workspace."})

    # ── CHECK 2: Report is valid JSON ────────────────────────────────────────
    report = None
    if report_path:
        try:
            report = json.loads(report_path.read_text())
            checks.append({"name": "vetting_report.json is valid JSON", "passed": True, "detail": "Parsed successfully."})
            total_score += 5
        except Exception as e:
            checks.append({"name": "vetting_report.json is valid JSON", "passed": False, "detail": f"JSON parse error: {e}"})

    # ── CHECK 3: Search was restricted to DataOps category with min-score 60 ─
    # Skills in DataOps with score >= 60:
    # data-pipeline-runner (91), sql-query-optimizer (78), etl-transformer (65),
    # stream-aggregator (82), data-quality-checker (71)
    # Excluded by score: sketchy-data-exporter (23), raw-scraper (41)
    EXPECTED_SLUGS = {
        "data-pipeline-runner",
        "sql-query-optimizer",
        "etl-transformer",
        "stream-aggregator",
        "data-quality-checker",
    }
    EXCLUDED_SLUGS = {"sketchy-data-exporter", "raw-scraper"}  # score < 60
    NON_DATAOPS = {"k8s-deployer", "ci-monitor", "gpt-assistant", "llm-router", "web-scraper", "db-migrator"}

    if report is not None:
        try:
            # The report should contain an iterable of vetted skills
            # We accept: top-level "skills" key OR "vetted_skills" OR "results" OR list
            skills_list = None
            if isinstance(report, list):
                skills_list = report
            elif isinstance(report, dict):
                for key in ("skills", "vetted_skills", "results", "findings", "audited_skills"):
                    if key in report:
                        val = report[key]
                        if isinstance(val, list):
                            skills_list = val
                            break

            if skills_list is None:
                checks.append({"name": "Report contains skill entries", "passed": False, "detail": "Could not find a list of skill results in report. Expected key: 'skills', 'results', 'vetted_skills', or top-level list."})
            else:
                checks.append({"name": "Report contains skill entries", "passed": True, "detail": f"Found {len(skills_list)} skill entries."})
                total_score += 5

                # Extract slugs from the list entries
                found_slugs = set()
                for entry in skills_list:
                    if isinstance(entry, dict):
                        slug = entry.get("slug") or entry.get("name") or entry.get("skill")
                        if slug:
                            found_slugs.add(slug)
                    elif isinstance(entry, str):
                        found_slugs.add(entry)

                # All 5 DataOps/score>=60 skills should be present
                missing = EXPECTED_SLUGS - found_slugs
                if not missing:
                    checks.append({"name": "All DataOps min-score-60 skills included", "passed": True, "detail": f"All 5 expected skills found: {sorted(EXPECTED_SLUGS)}"})
                    total_score += 20
                else:
                    checks.append({"name": "All DataOps min-score-60 skills included", "passed": False, "detail": f"Missing skills: {sorted(missing)}. Found: {sorted(found_slugs)}"})

                # Low-score DataOps skills should NOT be in the main vetted list
                bad_included = EXCLUDED_SLUGS & found_slugs
                if not bad_included:
                    checks.append({"name": "Low-credibility skills excluded (score < 60)", "passed": True, "detail": "sketchy-data-exporter and raw-scraper correctly excluded."})
                    total_score += 10
                else:
                    checks.append({"name": "Low-credibility skills excluded (score < 60)", "passed": False, "detail": f"Skills with score < 60 should not be in vetted list: {bad_included}"})

                # Non-DataOps skills should NOT appear
                wrong_category = NON_DATAOPS & found_slugs
                if not wrong_category:
                    checks.append({"name": "Non-DataOps skills excluded", "passed": True, "detail": "No non-DataOps skills in report."})
                    total_score += 10
                else:
                    checks.append({"name": "Non-DataOps skills excluded", "passed": False, "detail": f"Non-DataOps skills incorrectly included: {wrong_category}"})

        except Exception as e:
            checks.append({"name": "Report contains skill entries", "passed": False, "detail": f"Exception parsing report structure: {e}"})

    # ── CHECK 4: Vet results captured — pass/fail per skill ──────────────────
    if report is not None and skills_list is not None:
        try:
            # data-quality-checker should be marked as failed
            dqc_entry = None
            for entry in skills_list:
                if isinstance(entry, dict):
                    slug = entry.get("slug") or entry.get("name") or entry.get("skill")
                    if slug == "data-quality-checker":
                        dqc_entry = entry
                        break

            if dqc_entry:
                # Should be marked failed/unsafe
                status_val = str(dqc_entry.get("passed", dqc_entry.get("status", dqc_entry.get("result", "")))).lower()
                is_failed = status_val in ("false", "fail", "failed", "unsafe", "0", "no")
                if is_failed:
                    checks.append({"name": "data-quality-checker correctly marked as FAILED", "passed": True, "detail": "data-quality-checker vet result correctly shows failure."})
                    total_score += 15
                else:
                    checks.append({"name": "data-quality-checker correctly marked as FAILED", "passed": False, "detail": f"Expected data-quality-checker to be marked as failed/unsafe. Got status: '{status_val}'. Vet reveals eval_exec, obfuscation, hidden_instructions."})
            else:
                checks.append({"name": "data-quality-checker correctly marked as FAILED", "passed": False, "detail": "data-quality-checker not found in report entries."})

            # data-pipeline-runner should be marked as passed
            dpr_entry = None
            for entry in skills_list:
                if isinstance(entry, dict):
                    slug = entry.get("slug") or entry.get("name") or entry.get("skill")
                    if slug == "data-pipeline-runner":
                        dpr_entry = entry
                        break

            if dpr_entry:
                status_val = str(dpr_entry.get("passed", dpr_entry.get("status", dpr_entry.get("result", "")))).lower()
                is_passed = status_val in ("true", "pass", "passed", "safe", "1", "yes")
                if is_passed:
                    checks.append({"name": "data-pipeline-runner correctly marked as PASSED", "passed": True, "detail": "data-pipeline-runner vet result correctly shows pass."})
                    total_score += 10
                else:
                    checks.append({"name": "data-pipeline-runner correctly marked as PASSED", "passed": False, "detail": f"Expected data-pipeline-runner to be marked as passed/safe. Got: '{status_val}'"})
            else:
                checks.append({"name": "data-pipeline-runner correctly marked as PASSED", "passed": False, "detail": "data-pipeline-runner not found in report."})

        except Exception as e:
            checks.append({"name": "Vet pass/fail status check", "passed": False, "detail": f"Exception: {e}"})

    # ── CHECK 5: Markdown table export for DataOps category ──────────────────
    md_path = find_markdown(workspace)
    if md_path:
        try:
            content = md_path.read_text()
            has_table = "|" in content and "---" in content
            has_dataops = "DataOps" in content
            has_slugs = "data-pipeline-runner" in content and "stream-aggregator" in content
            has_score_col = "Score" in content or "score" in content
            has_tier_col = "Tier" in content or "tier" in content

            all_good = has_table and has_dataops and has_slugs and has_score_col
            if all_good:
                checks.append({"name": "Markdown catalog export for DataOps exists and correct", "passed": True, "detail": f"Found at {md_path}. Contains table with DataOps slugs and score column."})
                total_score += 15
            else:
                detail_parts = []
                if not has_table: detail_parts.append("no markdown table (|---|)")
                if not has_dataops: detail_parts.append("no 'DataOps' text")
                if not has_slugs: detail_parts.append("missing expected slugs")
                if not has_score_col: detail_parts.append("no Score column")
                checks.append({"name": "Markdown catalog export for DataOps exists and correct", "passed": False, "detail": "Markdown file found but issues: " + "; ".join(detail_parts)})
        except Exception as e:
            checks.append({"name": "Markdown catalog export for DataOps exists and correct", "passed": False, "detail": f"Exception reading markdown file: {e}"})
    else:
        checks.append({"name": "Markdown catalog export for DataOps exists and correct", "passed": False, "detail": "No markdown catalog export file found in workspace."})

    # ── CHECK 6: Report references credibility tiers ─────────────────────────
    if report_path and report is not None:
        try:
            report_text = report_path.read_text().lower()
            tier_words = ["trusted", "good", "unvetted", "caution"]
            found_tiers = [t for t in tier_words if t in report_text]
            if len(found_tiers) >= 2:
                checks.append({"name": "Report uses credibility tier terminology", "passed": True, "detail": f"Found tiers: {found_tiers}"})
                total_score += 5
            else:
                checks.append({"name": "Report uses credibility tier terminology", "passed": False, "detail": f"Report should reference credibility tiers (Trusted/Good/Unvetted/Caution). Found: {found_tiers}"})
        except Exception as e:
            checks.append({"name": "Report uses credibility tier terminology", "passed": False, "detail": f"Exception: {e}"})

    # ── Normalize score ───────────────────────────────────────────────────────
    max_score = 100.0
    normalized = min(total_score / max_score, 1.0)
    passed = normalized >= 0.65

    result = {
        "passed": passed,
        "score": round(normalized, 3),
        "checks": checks,
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()