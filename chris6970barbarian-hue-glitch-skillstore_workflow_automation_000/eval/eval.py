import sys
import json
import pathlib
import re

def evaluate(workspace_dir: str):
    workspace = pathlib.Path(workspace_dir)
    checks = []
    total_score = 0.0

    KNOWN_SKILLS = {
        "homeassistant", "gog", "weather", "github", "himalaya",
        "obsidian", "sonoscli", "blucli", "eightctl", "ordercli",
        "blogwatcher", "gifgrep", "video-frames", "youtube-summarizer",
        "ga4", "gsc", "wacli", "browser", "healthcheck"
    }
    EXPECTED_SKILL_COUNT = 19  # 19 listed in table (skipping header; count from SKILL.md)
    # Let's count from SKILL.md exactly: homeassistant, gog, weather, github, himalaya,
    # obsidian, sonoscli, blucli, eightctl, ordercli, blogwatcher, gifgrep,
    # video-frames, youtube-summarizer, ga4, gsc, wacli, browser, healthcheck = 19
    # SKILL.md says "20 built-in" but the table has 19 rows. We accept 19 or 20.

    SCAFFOLD_FILES = {"SKILL.md", "README.md", "main.js", "config.json"}

    # ─── Check 1: catalog_audit.json exists ───────────────────────────────────
    catalog_files = list(workspace.rglob("catalog_audit.json"))
    if not catalog_files:
        checks.append({"name": "catalog_audit.json exists", "passed": False,
                        "detail": "File catalog_audit.json not found anywhere in workspace"})
        checks.append({"name": "catalog_audit.json has correct skills", "passed": False,
                        "detail": "Skipped: file missing"})
        checks.append({"name": "catalog_audit.json total_count field", "passed": False,
                        "detail": "Skipped: file missing"})
    else:
        catalog_path = catalog_files[0]
        checks.append({"name": "catalog_audit.json exists", "passed": True,
                        "detail": f"Found at {catalog_path}"})
        try:
            catalog_data = json.loads(catalog_path.read_text())
            skills_list = catalog_data.get("skills", [])
            skills_set = {s.lower().strip() for s in skills_list}

            # Check overlap with known skills
            overlap = skills_set & KNOWN_SKILLS
            missing = KNOWN_SKILLS - skills_set
            overlap_ratio = len(overlap) / len(KNOWN_SKILLS)

            skill_check_passed = overlap_ratio >= 0.85  # at least 85% correct
            checks.append({
                "name": "catalog_audit.json has correct skills",
                "passed": skill_check_passed,
                "detail": (f"Found {len(overlap)}/{len(KNOWN_SKILLS)} known skills. "
                           f"Missing: {sorted(missing) if missing else 'none'}")
            })

            # Check total_count field
            total_count = catalog_data.get("total_count")
            count_passed = isinstance(total_count, int) and 18 <= total_count <= 21
            checks.append({
                "name": "catalog_audit.json total_count field",
                "passed": count_passed,
                "detail": f"total_count = {total_count} (expected 18-21)"
            })

            if skill_check_passed:
                total_score += 25.0
            if count_passed:
                total_score += 10.0

        except Exception as e:
            checks.append({"name": "catalog_audit.json has correct skills", "passed": False,
                            "detail": f"Parse error: {e}"})
            checks.append({"name": "catalog_audit.json total_count field", "passed": False,
                            "detail": f"Parse error: {e}"})

    # ─── Check 2: search_report.json ─────────────────────────────────────────
    search_files = list(workspace.rglob("search_report.json"))
    if not search_files:
        checks.append({"name": "search_report.json exists", "passed": False,
                        "detail": "File search_report.json not found anywhere in workspace"})
        checks.append({"name": "search_report: 'zzzyyyxxx' yields no results", "passed": False,
                        "detail": "Skipped: file missing"})
        checks.append({"name": "search_report: 'youtube' yields results above threshold", "passed": False,
                        "detail": "Skipped: file missing"})
        checks.append({"name": "search_report: 'email' yields results above threshold", "passed": False,
                        "detail": "Skipped: file missing"})
        checks.append({"name": "search_report: all 4 queries present", "passed": False,
                        "detail": "Skipped: file missing"})
    else:
        search_path = search_files[0]
        checks.append({"name": "search_report.json exists", "passed": True,
                        "detail": f"Found at {search_path}"})
        try:
            search_data = json.loads(search_path.read_text())

            # Normalize: accept list or dict keyed by query
            if isinstance(search_data, list):
                entries = {e.get("query", "").lower().strip(): e for e in search_data}
            elif isinstance(search_data, dict):
                # might be {"results": [...]} or {"youtube": {...}, ...}
                if "results" in search_data:
                    entries = {e.get("query", "").lower().strip(): e for e in search_data["results"]}
                else:
                    entries = {k.lower().strip(): v for k, v in search_data.items()}
            else:
                entries = {}

            # Check all 4 queries are present (fuzzy key match)
            EXPECTED_QUERIES = {"youtube", "email", "zzzyyyxxx", "speaker music"}
            found_queries = set()
            for eq in EXPECTED_QUERIES:
                for key in entries:
                    if eq in key or key in eq:
                        found_queries.add(eq)
                        break
            all_queries_present = len(found_queries) >= 4
            checks.append({
                "name": "search_report: all 4 queries present",
                "passed": all_queries_present,
                "detail": f"Found queries: {sorted(found_queries)}, expected: {sorted(EXPECTED_QUERIES)}"
            })
            if all_queries_present:
                total_score += 5.0

            # "zzzyyyxxx" should yield no results (below 30% threshold)
            zzz_entry = None
            for key, val in entries.items():
                if "zzz" in key or "yyy" in key or "xxx" in key:
                    zzz_entry = val
                    break
            if zzz_entry is None:
                # Try direct key
                zzz_entry = entries.get("zzzyyyxxx", None)

            if zzz_entry is not None:
                zzz_results_found = zzz_entry.get("results_found", None)
                if zzz_results_found is None:
                    # Check top_skill
                    top = zzz_entry.get("top_skill", "MISSING")
                    zzz_no_results = top is None or str(top).lower() in ("null", "none", "")
                else:
                    zzz_no_results = zzz_results_found is False or zzz_results_found == 0
                checks.append({
                    "name": "search_report: 'zzzyyyxxx' yields no results",
                    "passed": zzz_no_results,
                    "detail": f"Entry: {zzz_entry}"
                })
                if zzz_no_results:
                    total_score += 10.0
            else:
                checks.append({
                    "name": "search_report: 'zzzyyyxxx' yields no results",
                    "passed": False,
                    "detail": "Could not locate zzzyyyxxx entry in search_report.json"
                })

            # "youtube" should yield results (youtube-summarizer >= 30%)
            yt_entry = None
            for key, val in entries.items():
                if "youtube" in key:
                    yt_entry = val
                    break
            if yt_entry is not None:
                yt_results = yt_entry.get("results_found", None)
                top_skill = str(yt_entry.get("top_skill", "") or "").lower()
                if yt_results is None:
                    yt_passed = top_skill and top_skill not in ("null", "none", "")
                else:
                    yt_passed = bool(yt_results)
                # top skill should mention youtube
                top_reasonable = "youtube" in top_skill or top_skill == ""
                checks.append({
                    "name": "search_report: 'youtube' yields results above threshold",
                    "passed": yt_passed,
                    "detail": f"results_found={yt_results}, top_skill={top_skill}"
                })
                if yt_passed:
                    total_score += 10.0
                # Check score is a percentage integer if present
                top_score = yt_entry.get("top_score", None)
                score_reasonable = top_score is None or (isinstance(top_score, (int, float)) and 0 < top_score <= 100)
                checks.append({
                    "name": "search_report: 'youtube' top_score is a percentage",
                    "passed": score_reasonable,
                    "detail": f"top_score={top_score}"
                })
                if score_reasonable and top_score is not None:
                    total_score += 5.0
            else:
                checks.append({
                    "name": "search_report: 'youtube' yields results above threshold",
                    "passed": False,
                    "detail": "Could not locate 'youtube' entry in search_report.json"
                })
                checks.append({
                    "name": "search_report: 'youtube' top_score is a percentage",
                    "passed": False,
                    "detail": "Skipped: entry missing"
                })

            # "email" should yield results (himalaya, gog, etc.)
            email_entry = None
            for key, val in entries.items():
                if "email" in key:
                    email_entry = val
                    break
            if email_entry is not None:
                email_results = email_entry.get("results_found", None)
                if email_results is None:
                    top = str(email_entry.get("top_skill", "") or "").lower()
                    email_passed = top and top not in ("null", "none", "")
                else:
                    email_passed = bool(email_results)
                checks.append({
                    "name": "search_report: 'email' yields results above threshold",
                    "passed": email_passed,
                    "detail": f"Entry: {email_entry}"
                })
                if email_passed:
                    total_score += 10.0
            else:
                checks.append({
                    "name": "search_report: 'email' yields results above threshold",
                    "passed": False,
                    "detail": "Could not locate 'email' entry in search_report.json"
                })

        except Exception as e:
            checks.append({"name": "search_report: 'zzzyyyxxx' yields no results", "passed": False,
                            "detail": f"Parse error: {e}"})
            checks.append({"name": "search_report: 'youtube' yields results above threshold", "passed": False,
                            "detail": f"Parse error: {e}"})
            checks.append({"name": "search_report: 'email' yields results above threshold", "passed": False,
                            "detail": f"Parse error: {e}"})
            checks.append({"name": "search_report: all 4 queries present", "passed": False,
                            "detail": f"Parse error: {e}"})

    # ─── Check 3: scaffold_summary.json ───────────────────────────────────────
    scaffold_files = list(workspace.rglob("scaffold_summary.json"))
    if not scaffold_files:
        checks.append({"name": "scaffold_summary.json exists", "passed": False,
                        "detail": "File scaffold_summary.json not found anywhere in workspace"})
        checks.append({"name": "scaffold_summary.json has skill_name=spotify-connect", "passed": False,
                        "detail": "Skipped: file missing"})
        checks.append({"name": "scaffold_summary.json has correct template files", "passed": False,
                        "detail": "Skipped: file missing"})
    else:
        scaffold_path = scaffold_files[0]
        checks.append({"name": "scaffold_summary.json exists", "passed": True,
                        "detail": f"Found at {scaffold_path}"})
        try:
            scaffold_data = json.loads(scaffold_path.read_text())

            skill_name = scaffold_data.get("skill_name", "")
            name_passed = "spotify" in skill_name.lower() and "connect" in skill_name.lower()
            checks.append({
                "name": "scaffold_summary.json has skill_name=spotify-connect",
                "passed": name_passed,
                "detail": f"skill_name = {skill_name!r}"
            })
            if name_passed:
                total_score += 5.0

            files_created = scaffold_data.get("files_created", [])
            files_set = {f.lower().strip() for f in files_created}

            # Must contain the 4 proprietary scaffold files from SKILL.md
            has_skill_md = any("skill.md" in f for f in files_set)
            has_readme = any("readme" in f for f in files_set)
            has_main_js = any("main.js" in f for f in files_set)
            has_config = any("config.json" in f or "config" in f for f in files_set)

            template_files_found = sum([has_skill_md, has_readme, has_main_js, has_config])
            template_passed = template_files_found >= 3  # at least 3 of 4

            checks.append({
                "name": "scaffold_summary.json has correct template files",
                "passed": template_passed,
                "detail": (f"files_created={files_created}, "
                           f"SKILL.md={has_skill_md}, README={has_readme}, "
                           f"main.js={has_main_js}, config.json={has_config}")
            })
            if template_passed:
                total_score += 15.0

        except Exception as e:
            checks.append({"name": "scaffold_summary.json has skill_name=spotify-connect", "passed": False,
                            "detail": f"Parse error: {e}"})
            checks.append({"name": "scaffold_summary.json has correct template files", "passed": False,
                            "detail": f"Parse error: {e}"})

    # ─── Check 4: spotify-connect skill directory actually created ────────────
    spotify_dir_candidates = list(pathlib.Path("/root/.openclaw").rglob("spotify-connect")) + \
                             list(workspace.rglob("spotify-connect"))
    spotify_dir_exists = any(p.is_dir() for p in spotify_dir_candidates)
    checks.append({
        "name": "spotify-connect skill directory actually created on disk",
        "passed": spotify_dir_exists,
        "detail": (f"Searched ~/.openclaw and workspace. "
                   f"Candidates: {[str(p) for p in spotify_dir_candidates[:5]]}")
    })
    if spotify_dir_exists:
        total_score += 15.0
        # Also verify it has the expected files
        for p in spotify_dir_candidates:
            if p.is_dir():
                actual_files = {f.name for f in p.iterdir() if f.is_file()}
                proprietary_overlap = actual_files & SCAFFOLD_FILES
                has_proprietary = len(proprietary_overlap) >= 2
                checks.append({
                    "name": "spotify-connect directory has proprietary scaffold files",
                    "passed": has_proprietary,
                    "detail": f"Files in dir: {sorted(actual_files)}, proprietary matches: {sorted(proprietary_overlap)}"
                })
                if has_proprietary:
                    total_score += 10.0
                break
    else:
        checks.append({
            "name": "spotify-connect directory has proprietary scaffold files",
            "passed": False,
            "detail": "Skipped: directory not found"
        })

    # Final pass/fail
    passed_checks = sum(1 for c in checks if c["passed"])
    total_checks = len(checks)
    final_passed = total_score >= 50.0

    return {
        "passed": final_passed,
        "score": round(min(total_score, 100.0) / 100.0, 3),
        "checks": checks
    }


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace_dir)
    print(json.dumps(result, indent=2))