import sys
import json
import re
from pathlib import Path

def evaluate(workspace: str):
    checks = []
    total_score = 0.0

    def add_check(name, passed, detail, weight=1.0):
        checks.append({"name": name, "passed": passed, "detail": detail})
        return weight if passed else 0.0

    # --- Locate report files ---
    ws = Path(workspace)

    def find_report(publisher_id):
        # Accept various naming conventions
        candidates = list(ws.rglob(f"*{publisher_id}*.txt")) + \
                     list(ws.rglob(f"*{publisher_id}*.md")) + \
                     list(ws.rglob(f"*{publisher_id}*.report"))
        # Also try underscore variants
        pid_underscore = publisher_id.replace("-", "_")
        candidates += list(ws.rglob(f"*{pid_underscore}*.txt")) + \
                      list(ws.rglob(f"*{pid_underscore}*.md"))
        return candidates[0] if candidates else None

    reports = {
        "devtoolz-inc": find_report("devtoolz-inc") or find_report("devtoolz_inc"),
        "anthroplc": find_report("anthroplc"),
        "ml-pipeline-co": find_report("ml-pipeline-co") or find_report("ml_pipeline_co"),
    }

    # ========================
    # PUBLISHER 1: devtoolz-inc — Expected: VERIFIED
    # ========================
    pub1_path = reports.get("devtoolz-inc")
    try:
        if pub1_path is None:
            raise FileNotFoundError("Report file not found")
        content1 = pub1_path.read_text(encoding="utf-8", errors="replace")

        # Check: File exists
        total_score += add_check(
            "devtoolz-inc: report file exists",
            True,
            f"Found at {pub1_path}"
        )

        # Check: Trust rating is VERIFIED
        has_verified = bool(re.search(r'\bVERIFIED\b', content1, re.IGNORECASE))
        # Must NOT be SUSPICIOUS, UNVERIFIED, PARTIAL as the final rating
        has_wrong_rating = bool(re.search(r'Trust rating[:\s]+(?:SUSPICIOUS|UNVERIFIED|PARTIAL)\b', content1, re.IGNORECASE))
        passed_rating = has_verified and not has_wrong_rating
        total_score += add_check(
            "devtoolz-inc: trust rating is VERIFIED",
            passed_rating,
            f"Content contains VERIFIED: {has_verified}, wrong rating present: {has_wrong_rating}"
        )

        # Check: Key rotation section present and shows normal pattern (no ANOMALY)
        has_key_section = bool(re.search(r'key.{0,20}rotation', content1, re.IGNORECASE))
        has_anomaly = bool(re.search(r'ANOMALY', content1, re.IGNORECASE))
        passed_keys = has_key_section and not has_anomaly
        total_score += add_check(
            "devtoolz-inc: key rotation section present, no anomaly flagged",
            passed_keys,
            f"Key rotation section found: {has_key_section}, anomaly flagged: {has_anomaly}"
        )

        # Check: Cross-platform presence is not flagged as THIN (publisher has multiple platforms)
        has_thin = bool(re.search(r'THIN', content1, re.IGNORECASE))
        total_score += add_check(
            "devtoolz-inc: cross-platform presence NOT flagged as THIN",
            not has_thin,
            f"THIN incorrectly flagged: {has_thin}"
        )

        # Check: Impersonation check is CLEAN
        has_clean = bool(re.search(r'CLEAN', content1, re.IGNORECASE))
        total_score += add_check(
            "devtoolz-inc: impersonation check shows CLEAN",
            has_clean,
            f"CLEAN found in report: {has_clean}"
        )

        # Check: All 5 dimensions are present
        dim1 = bool(re.search(r'(history|publication.{0,20}history|consistency)', content1, re.IGNORECASE))
        dim2 = bool(re.search(r'key.{0,20}rotation', content1, re.IGNORECASE))
        dim3 = bool(re.search(r'impersonation', content1, re.IGNORECASE))
        dim4 = bool(re.search(r'cross.{0,20}platform', content1, re.IGNORECASE))
        dim5 = bool(re.search(r'(credential|lifecycle|attestation)', content1, re.IGNORECASE))
        all_dims = all([dim1, dim2, dim3, dim4, dim5])
        total_score += add_check(
            "devtoolz-inc: all 5 identity dimensions present",
            all_dims,
            f"Dims present — history:{dim1}, key_rotation:{dim2}, impersonation:{dim3}, cross_platform:{dim4}, credentials:{dim5}"
        )

        # Check: Structured report format (emoji header or PUBLISHER IDENTITY REPORT phrase)
        has_header = bool(re.search(r'PUBLISHER IDENTITY REPORT|🪪', content1))
        total_score += add_check(
            "devtoolz-inc: structured report header present",
            has_header,
            f"Report header found: {has_header}"
        )

    except FileNotFoundError as e:
        total_score += add_check("devtoolz-inc: report file exists", False, str(e))
        for name in [
            "devtoolz-inc: trust rating is VERIFIED",
            "devtoolz-inc: key rotation section present, no anomaly flagged",
            "devtoolz-inc: cross-platform presence NOT flagged as THIN",
            "devtoolz-inc: impersonation check shows CLEAN",
            "devtoolz-inc: all 5 identity dimensions present",
            "devtoolz-inc: structured report header present",
        ]:
            checks.append({"name": name, "passed": False, "detail": "Report file missing"})
    except Exception as e:
        checks.append({"name": "devtoolz-inc: unexpected error", "passed": False, "detail": str(e)})

    # ========================
    # PUBLISHER 2: anthroplc — Expected: SUSPICIOUS (impersonation of 'anthropic')
    # ========================
    pub2_path = reports.get("anthroplc")
    try:
        if pub2_path is None:
            raise FileNotFoundError("Report file not found")
        content2 = pub2_path.read_text(encoding="utf-8", errors="replace")

        total_score += add_check(
            "anthroplc: report file exists",
            True,
            f"Found at {pub2_path}"
        )

        # Check: Trust rating is SUSPICIOUS
        has_suspicious = bool(re.search(r'Trust rating[:\s—\-]+\s*SUSPICIOUS\b', content2, re.IGNORECASE))
        # Also accept SUSPICIOUS anywhere prominently
        if not has_suspicious:
            has_suspicious = bool(re.search(r'\bSUSPICIOUS\b', content2, re.IGNORECASE))
        total_score += add_check(
            "anthroplc: trust rating is SUSPICIOUS",
            has_suspicious,
            f"SUSPICIOUS found in report: {has_suspicious}"
        )

        # Check: Impersonation detected (typo-squat or homoglyph of 'anthropic')
        has_impersonation_flag = bool(re.search(
            r'(impersonation.{0,60}(detected|found|warning|risk)|typo.{0,30}squat|homoglyph|confusable|anthropic)',
            content2, re.IGNORECASE
        ))
        total_score += add_check(
            "anthroplc: impersonation/typo-squat detected",
            has_impersonation_flag,
            f"Impersonation signal found: {has_impersonation_flag}"
        )

        # Check: Unicode homoglyph detection mentioned
        has_homoglyph = bool(re.search(r'(homoglyph|unicode|cyrillic|confusable|lookalike)', content2, re.IGNORECASE))
        # Also accept if they mention the specific character issue
        if not has_homoglyph:
            has_homoglyph = bool(re.search(r'(display.{0,20}name|visual.{0,20}similar)', content2, re.IGNORECASE))
        total_score += add_check(
            "anthroplc: Unicode homoglyph or display name anomaly detected",
            has_homoglyph,
            f"Homoglyph/Unicode signal found: {has_homoglyph}"
        )

        # Check: Cross-platform presence is THIN (only marketplace, no repo/community)
        has_thin2 = bool(re.search(r'THIN', content2, re.IGNORECASE))
        # Also accept: "single-platform" or "no linked repository" + "no forum"
        if not has_thin2:
            has_thin2 = bool(re.search(r'(single.{0,15}platform|no.{0,20}repository|no.{0,20}community)', content2, re.IGNORECASE))
        total_score += add_check(
            "anthroplc: cross-platform presence flagged as THIN or single-platform",
            has_thin2,
            f"Thin/single-platform signal found: {has_thin2}"
        )

        # Check: All 5 dimensions
        dim1 = bool(re.search(r'(history|publication.{0,20}history|consistency)', content2, re.IGNORECASE))
        dim2 = bool(re.search(r'key.{0,20}rotation', content2, re.IGNORECASE))
        dim3 = bool(re.search(r'impersonation', content2, re.IGNORECASE))
        dim4 = bool(re.search(r'cross.{0,20}platform', content2, re.IGNORECASE))
        dim5 = bool(re.search(r'(credential|lifecycle|attestation)', content2, re.IGNORECASE))
        all_dims2 = all([dim1, dim2, dim3, dim4, dim5])
        total_score += add_check(
            "anthroplc: all 5 identity dimensions present",
            all_dims2,
            f"Dims present — history:{dim1}, key_rotation:{dim2}, impersonation:{dim3}, cross_platform:{dim4}, credentials:{dim5}"
        )

        # Check: Structured report format
        has_header2 = bool(re.search(r'PUBLISHER IDENTITY REPORT|🪪', content2))
        total_score += add_check(
            "anthroplc: structured report header present",
            has_header2,
            f"Report header found: {has_header2}"
        )

        # Check: Recommended actions present
        has_actions = bool(re.search(r'(recommended.{0,20}action|action.{0,20}recommend)', content2, re.IGNORECASE))
        total_score += add_check(
            "anthroplc: recommended actions section present",
            has_actions,
            f"Recommended actions found: {has_actions}"
        )

    except FileNotFoundError as e:
        total_score += add_check("anthroplc: report file exists", False, str(e))
        for name in [
            "anthroplc: trust rating is SUSPICIOUS",
            "anthroplc: impersonation/typo-squat detected",
            "anthroplc: Unicode homoglyph or display name anomaly detected",
            "anthroplc: cross-platform presence flagged as THIN or single-platform",
            "anthroplc: all 5 identity dimensions present",
            "anthroplc: structured report header present",
            "anthroplc: recommended actions section present",
        ]:
            checks.append({"name": name, "passed": False, "detail": "Report file missing"})
    except Exception as e:
        checks.append({"name": "anthroplc: unexpected error", "passed": False, "detail": str(e)})

    # ========================
    # PUBLISHER 3: ml-pipeline-co — Expected: SUSPICIOUS (key rotation + topic shift)
    # ========================
    pub3_path = reports.get("ml-pipeline-co")
    try:
        if pub3_path is None:
            raise FileNotFoundError("Report file not found")
        content3 = pub3_path.read_text(encoding="utf-8", errors="replace")

        total_score += add_check(
            "ml-pipeline-co: report file exists",
            True,
            f"Found at {pub3_path}"
        )

        # Check: Trust rating is SUSPICIOUS
        has_suspicious3 = bool(re.search(r'\bSUSPICIOUS\b', content3, re.IGNORECASE))
        total_score += add_check(
            "ml-pipeline-co: trust rating is SUSPICIOUS",
            has_suspicious3,
            f"SUSPICIOUS found in report: {has_suspicious3}"
        )

        # Check: Key rotation anomaly detected (key changed right before controversial publish)
        has_key_anomaly = bool(re.search(r'ANOMALY', content3, re.IGNORECASE))
        if not has_key_anomaly:
            has_key_anomaly = bool(re.search(
                r'(suspicious.{0,40}key|key.{0,40}suspicious|rotation.{0,40}before|before.{0,40}publish|no.{0,20}announcement)',
                content3, re.IGNORECASE
            ))
        total_score += add_check(
            "ml-pipeline-co: key rotation anomaly detected",
            has_key_anomaly,
            f"Key rotation anomaly signal found: {has_key_anomaly}"
        )

        # Check: Topic/history shift detected (ML tools → crypto/finance)
        has_topic_shift = bool(re.search(
            r'(topic.{0,20}shift|sudden.{0,20}pivot|pivot|shift.{0,20}topic|history.{0,20}warning|inconsistent|expertise.{0,30}trajectory)',
            content3, re.IGNORECASE
        ))
        if not has_topic_shift:
            # Accept if they mention the category change
            has_topic_shift = bool(re.search(r'(crypto|wallet|finance).{0,80}(ml|machine.{0,10}learning|preprocessing)', content3, re.IGNORECASE))
            if not has_topic_shift:
                has_topic_shift = bool(re.search(r'(ml|machine.{0,10}learning|preprocessing).{0,80}(crypto|wallet|finance)', content3, re.IGNORECASE))
        total_score += add_check(
            "ml-pipeline-co: topic/publication history shift detected",
            has_topic_shift,
            f"Topic shift signal found: {has_topic_shift}"
        )

        # Check: Timing correlation between key rotation and new topic skills noted
        has_timing = bool(re.search(
            r'(coincide|timing|before.{0,30}publish|2025.04.1[56]|April.{0,10}2025|days? before)',
            content3, re.IGNORECASE
        ))
        total_score += add_check(
            "ml-pipeline-co: timing correlation between key rotation and topic shift noted",
            has_timing,
            f"Timing correlation signal found: {has_timing}"
        )

        # Check: Cross-platform presence THIN
        has_thin3 = bool(re.search(r'THIN', content3, re.IGNORECASE))
        if not has_thin3:
            has_thin3 = bool(re.search(r'(single.{0,15}platform|no.{0,20}repository|no.{0,20}community)', content3, re.IGNORECASE))
        total_score += add_check(
            "ml-pipeline-co: cross-platform presence flagged as THIN or single-platform",
            has_thin3,
            f"Thin/single-platform signal found: {has_thin3}"
        )

        # Check: All 5 dimensions
        dim1 = bool(re.search(r'(history|publication.{0,20}history|consistency)', content3, re.IGNORECASE))
        dim2 = bool(re.search(r'key.{0,20}rotation', content3, re.IGNORECASE))
        dim3 = bool(re.search(r'impersonation', content3, re.IGNORECASE))
        dim4 = bool(re.search(r'cross.{0,20}platform', content3, re.IGNORECASE))
        dim5 = bool(re.search(r'(credential|lifecycle|attestation)', content3, re.IGNORECASE))
        all_dims3 = all([dim1, dim2, dim3, dim4, dim5])
        total_score += add_check(
            "ml-pipeline-co: all 5 identity dimensions present",
            all_dims3,
            f"Dims present — history:{dim1}, key_rotation:{dim2}, impersonation:{dim3}, cross_platform:{dim4}, credentials:{dim5}"
        )

        # Check: Structured report format
        has_header3 = bool(re.search(r'PUBLISHER IDENTITY REPORT|🪪', content3))
        total_score += add_check(
            "ml-pipeline-co: structured report header present",
            has_header3,
            f"Report header found: {has_header3}"
        )

        # Check: Credential lifecycle issue (expired credential_expiry 2025-05-01)
        has_cred_issue = bool(re.search(
            r'(expired?|lifecycle.{0,30}gap|broken.{0,20}chain|credential.{0,30}expir)',
            content3, re.IGNORECASE
        ))
        total_score += add_check(
            "ml-pipeline-co: credential lifecycle gap or expiry detected",
            has_cred_issue,
            f"Credential expiry/lifecycle signal found: {has_cred_issue}"
        )

    except FileNotFoundError as e:
        total_score += add_check("ml-pipeline-co: report file exists", False, str(e))
        for name in [
            "ml-pipeline-co: trust rating is SUSPICIOUS",
            "ml-pipeline-co: key rotation anomaly detected",
            "ml-pipeline-co: topic/publication history shift detected",
            "ml-pipeline-co: timing correlation between key rotation and topic shift noted",
            "ml-pipeline-co: cross-platform presence flagged as THIN or single-platform",
            "ml-pipeline-co: all 5 identity dimensions present",
            "ml-pipeline-co: structured report header present",
            "ml-pipeline-co: credential lifecycle gap or expiry detected",
        ]:
            checks.append({"name": name, "passed": False, "detail": "Report file missing"})
    except Exception as e:
        checks.append({"name": "ml-pipeline-co: unexpected error", "passed": False, "detail": str(e)})

    # --- Final score ---
    total_checks = len(checks)
    passed_checks = sum(1 for c in checks if c["passed"])
    final_score = round(passed_checks / total_checks, 4) if total_checks > 0 else 0.0
    overall_passed = final_score >= 0.75

    return {
        "passed": overall_passed,
        "score": final_score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, indent=2))