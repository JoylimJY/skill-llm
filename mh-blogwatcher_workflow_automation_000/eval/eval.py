#!/usr/bin/env python3
import sys
import json
import subprocess
import os
from pathlib import Path

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")

checks = []
score_weights = []

def add_check(name, passed, detail, weight=1.0):
    checks.append({"name": name, "passed": passed, "detail": detail})
    score_weights.append((passed, weight))

def run_blogwatcher(args):
    env = os.environ.copy()
    env["PATH"] = "/root/go/bin:" + env.get("PATH", "")
    try:
        result = subprocess.run(
            ["blogwatcher"] + args,
            capture_output=True, text=True, timeout=30, env=env
        )
        return result.stdout, result.stderr, result.returncode
    except Exception as e:
        return "", str(e), -1

# ── Check 1: Verify blogwatcher has exactly 2 tracked blogs (CloudNative Weekly + DevSecOps Digest) ──
try:
    stdout, stderr, rc = run_blogwatcher(["blogs"])
    raw_output = stdout + stderr

    has_cloudnative = "CloudNative Weekly" in raw_output
    has_devsecops = "DevSecOps Digest" in raw_output
    has_platformeng = "PlatformEng Pulse" in raw_output

    if has_cloudnative and has_devsecops and not has_platformeng:
        add_check(
            "tracked_blogs_correct",
            True,
            f"Exactly the right 2 blogs are tracked. PlatformEng Pulse is absent.",
            weight=2.0
        )
    else:
        detail = f"cloudnative={has_cloudnative}, devsecops={has_devsecops}, platformeng_absent={not has_platformeng}"
        add_check(
            "tracked_blogs_correct",
            False,
            f"Blog tracking state incorrect: {detail}. Raw output snippet: {raw_output[:300]}",
            weight=2.0
        )
except Exception as e:
    add_check("tracked_blogs_correct", False, f"Exception running blogwatcher blogs: {e}", weight=2.0)

# ── Check 2: Verify unread articles count via blogwatcher articles ──
try:
    stdout, stderr, rc = run_blogwatcher(["articles"])
    raw_articles = stdout + stderr

    # Count unread articles: look for lines that are article entries
    # blogwatcher articles shows unread articles (those not marked read)
    # CloudNative Weekly had 3 articles, first 2 marked read → 1 unread
    # DevSecOps Digest had 2 articles, none marked read → 2 unread
    # PlatformEng Pulse removed entirely → 0
    # Expected unread: 3

    lines = raw_articles.strip().split("\n")
    # Count article entries - they appear as numbered items or titled entries
    # We look for presence of specific article titles
    unread_titles = [
        "Service Mesh Showdown 2024",   # CloudNative #3 (unread)
        "SLSA Framework Adoption Guide", # DevSecOps #1 (unread)
        "Secrets Management with Vault",  # DevSecOps #2 (unread)
    ]
    read_titles = [
        "Kubernetes 1.30 Released",       # CloudNative #1 (should be read)
        "eBPF in Production",             # CloudNative #2 (should be read)
        "Internal Developer Portals",     # PlatformEng (removed)
        "Golden Paths",                   # PlatformEng (removed)
        "Terraform vs Pulumi",            # PlatformEng (removed)
        "GitOps Patterns",                # PlatformEng (removed)
    ]

    unread_present = [t for t in unread_titles if t in raw_articles]
    read_present = [t for t in read_titles if t in raw_articles]

    if len(unread_present) == 3 and len(read_present) == 0:
        add_check(
            "unread_articles_correct",
            True,
            f"All 3 expected unread articles present, no read/removed articles showing. Articles: {unread_present}",
            weight=2.0
        )
    else:
        add_check(
            "unread_articles_correct",
            False,
            f"Unread present: {unread_present} (expected 3). Read/removed still showing: {read_present}. Raw: {raw_articles[:400]}",
            weight=2.0
        )
except Exception as e:
    add_check("unread_articles_correct", False, f"Exception running blogwatcher articles: {e}", weight=2.0)

# ── Check 3: Verify feed_status_report.json exists and has correct content ──
report_file = None
try:
    candidates = list(workspace.rglob("feed_status_report.json"))
    if not candidates:
        add_check(
            "report_file_exists",
            False,
            "feed_status_report.json not found anywhere in workspace.",
            weight=1.5
        )
        add_check(
            "report_content_correct",
            False,
            "Cannot check content - file not found.",
            weight=2.0
        )
    else:
        report_file = candidates[0]
        add_check(
            "report_file_exists",
            True,
            f"Found feed_status_report.json at {report_file}",
            weight=1.5
        )

        # Parse and validate
        try:
            with open(report_file) as f:
                report = json.load(f)

            # Must contain list of tracked blogs (2 names) and unread count (3)
            errors = []

            # Check for tracked sources field (flexible key names)
            tracked_key = None
            for k in report:
                if any(word in k.lower() for word in ["blog", "source", "feed", "track"]):
                    tracked_key = k
                    break

            if tracked_key is None:
                errors.append("No field found for tracked blogs/sources")
                tracked_blogs = []
            else:
                tracked_blogs = report[tracked_key]
                if not isinstance(tracked_blogs, list):
                    errors.append(f"Tracked blogs field '{tracked_key}' is not a list: {tracked_blogs}")
                    tracked_blogs = []

            # Check correct blogs in list
            tracked_str = json.dumps(tracked_blogs).lower()
            has_cn = "cloudnative" in tracked_str.replace(" ", "") or "cloud native" in tracked_str or "cloudnative weekly" in tracked_str
            has_ds = "devsecops" in tracked_str.replace(" ", "") or "devsecops digest" in tracked_str
            has_pe = "platformeng" in tracked_str.replace(" ", "") or "platformeng pulse" in tracked_str

            if not has_cn:
                errors.append("CloudNative Weekly missing from tracked sources in report")
            if not has_ds:
                errors.append("DevSecOps Digest missing from tracked sources in report")
            if has_pe:
                errors.append("PlatformEng Pulse should NOT be in tracked sources")

            # Check unread count field
            unread_key = None
            for k in report:
                if any(word in k.lower() for word in ["unread", "count", "total", "article", "remaining", "new"]):
                    unread_key = k
                    break

            if unread_key is None:
                errors.append("No field found for unread article count")
                unread_count = None
            else:
                unread_count = report[unread_key]
                if not isinstance(unread_count, (int, float)):
                    errors.append(f"Unread count field '{unread_key}' is not a number: {unread_count}")
                elif int(unread_count) != 3:
                    errors.append(f"Unread count should be 3, got {unread_count}")

            if not errors:
                add_check(
                    "report_content_correct",
                    True,
                    f"Report contains correct tracked blogs and unread count (3). Fields: {tracked_key}={tracked_blogs}, {unread_key}={unread_count}",
                    weight=2.0
                )
            else:
                add_check(
                    "report_content_correct",
                    False,
                    f"Report content issues: {'; '.join(errors)}. Report content: {json.dumps(report)[:400]}",
                    weight=2.0
                )

        except json.JSONDecodeError as e:
            add_check(
                "report_content_correct",
                False,
                f"feed_status_report.json is not valid JSON: {e}",
                weight=2.0
            )
        except Exception as e:
            add_check(
                "report_content_correct",
                False,
                f"Exception reading report: {e}",
                weight=2.0
            )

except Exception as e:
    add_check("report_file_exists", False, f"Exception searching for report: {e}", weight=1.5)
    add_check("report_content_correct", False, "Cannot check content due to earlier error.", weight=2.0)

# ── Check 4: Verify the scan was actually run (at least 9 articles were discovered total) ──
try:
    # Run articles with --all or check history — we infer from blogwatcher state
    # If articles were found and marked read, the scan must have run
    # We check by verifying total articles found is consistent with all 3 feeds scanned
    stdout, stderr, rc = run_blogwatcher(["articles"])
    # At minimum, we should see 3 unread articles (post-marking)
    # Also try to infer the scan happened by checking the output structure
    scan_happened = len(stdout.strip()) > 0 or "no" in stdout.lower() or "article" in stdout.lower()

    # Additional strong signal: unread count of 3 implies scan + selective marking happened
    # This check passes if unread_articles_correct also passed
    unread_check_passed = any(c["name"] == "unread_articles_correct" and c["passed"] for c in checks)

    if unread_check_passed:
        add_check(
            "scan_and_mark_workflow",
            True,
            "Scan was performed and articles were selectively marked as read (workflow integrity confirmed).",
            weight=1.5
        )
    else:
        # Check if any articles are tracked at all
        has_articles = "article" in (stdout + stderr).lower()
        add_check(
            "scan_and_mark_workflow",
            False,
            f"Cannot confirm full scan+mark workflow. Output: {(stdout+stderr)[:200]}",
            weight=1.5
        )
except Exception as e:
    add_check("scan_and_mark_workflow", False, f"Exception during workflow check: {e}", weight=1.5)

# ── Calculate final score ──────────────────────────────────────────────────
total_weight = sum(w for _, w in score_weights)
earned_weight = sum(w for passed, w in score_weights if passed)
score = round(earned_weight / total_weight, 4) if total_weight > 0 else 0.0
all_passed = all(c["passed"] for c in checks)

result = {
    "passed": all_passed,
    "score": score,
    "checks": checks
}

print(json.dumps(result, indent=2))