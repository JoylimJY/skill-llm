import sys
import json
import hashlib
from pathlib import Path

def main(workspace):
    workspace = Path(workspace)
    results = []
    total_score = 0.0

    def check(name, passed, detail, weight=1.0):
        results.append({"name": name, "passed": passed, "detail": detail})
        return weight if passed else 0.0

    # --- Find the output file ---
    candidates = list(workspace.rglob("catalog_records.json"))
    if not candidates:
        results.append({"name": "file_exists", "passed": False, "detail": "catalog_records.json not found anywhere in workspace."})
        print(json.dumps({"passed": False, "score": 0.0, "checks": results}))
        return

    output_file = candidates[0]
    total_score += check("file_exists", True, f"Found at {output_file}")

    # --- Parse JSON ---
    try:
        with open(output_file, "r") as f:
            data = json.load(f)
    except Exception as e:
        results.append({"name": "json_parseable", "passed": False, "detail": f"JSON parse error: {e}"})
        print(json.dumps({"passed": False, "score": 0.0, "checks": results}))
        return

    total_score += check("json_parseable", True, "Valid JSON.")

    # --- MANDATORY DISCLOSURE GATE ---
    # Per SKILL.md Section 2: disclosure must appear BEFORE asset-specific data.
    # In a JSON structure, we check for a top-level disclosure/disclaimer field
    # that appears before the assets array/object.
    
    # Check for disclosure at top level (not nested inside an asset)
    raw_text = open(output_file).read()
    
    # The disclosure must contain the key phrases from Section 2
    disclosure_phrases = [
        "does not provide legal advice",
        "does not",  # fallback
    ]
    
    # More precisely per SKILL.md Section 2:
    required_disclosure_fragments = [
        "legal advice",
        "ownership",
        "fair use",
        "responsible",
    ]
    
    disclosure_present = all(frag.lower() in raw_text.lower() for frag in required_disclosure_fragments)
    total_score += check(
        "mandatory_disclosure_gate",
        disclosure_present,
        "Disclosure text from Section 2 (legal advice / ownership / fair use / creator responsibility) must be present in the output." if not disclosure_present else "Disclosure gate text found.",
        weight=1.5
    )

    # Check that disclosure appears BEFORE asset records in the raw file
    # Find position of disclosure vs first asset ID
    first_asset_id_pos = min(
        (raw_text.find(aid) for aid in ["MBLX-2025-011", "VIS-2025-007", "MBLX-2025-013"] if raw_text.find(aid) != -1),
        default=-1
    )
    disclosure_pos = min(
        (raw_text.lower().find(frag) for frag in ["legal advice", "does not provide"] if raw_text.lower().find(frag) != -1),
        default=-1
    )
    
    if disclosure_pos != -1 and first_asset_id_pos != -1:
        disclosure_before_assets = disclosure_pos < first_asset_id_pos
    else:
        disclosure_before_assets = False
    
    total_score += check(
        "disclosure_before_assets",
        disclosure_before_assets,
        f"Disclosure at position {disclosure_pos}, first asset at position {first_asset_id_pos}. Must appear before assets." if not disclosure_before_assets else "Disclosure correctly precedes asset records.",
        weight=1.5
    )

    # --- Locate the three asset records ---
    # Accept either a list or a dict of assets
    asset_records = {}
    try:
        if isinstance(data, dict):
            # Could be {"disclosure": "...", "assets": [...]} or {"MBLX-2025-011": {...}, ...}
            if "assets" in data:
                assets_raw = data["assets"]
                if isinstance(assets_raw, list):
                    for rec in assets_raw:
                        for key in ["asset_identifier", "id", "asset_id", "identifier"]:
                            if key in rec:
                                asset_records[rec[key]] = rec
                                break
                        else:
                            # try to find asset ID value in the record
                            for v in rec.values():
                                if isinstance(v, str) and any(aid in v for aid in ["MBLX-2025-011", "VIS-2025-007", "MBLX-2025-013"]):
                                    asset_records[v] = rec
                                    break
                elif isinstance(assets_raw, dict):
                    asset_records = assets_raw
            else:
                # Direct dict keyed by asset ID or containing asset IDs
                for k, v in data.items():
                    if any(aid in k for aid in ["MBLX-2025-011", "VIS-2025-007", "MBLX-2025-013"]):
                        asset_records[k] = v
                    elif isinstance(v, dict):
                        for field_val in v.values():
                            if isinstance(field_val, str) and any(aid in field_val for aid in ["MBLX-2025-011", "VIS-2025-007", "MBLX-2025-013"]):
                                asset_records[field_val] = v
                                break
        elif isinstance(data, list):
            for rec in data:
                rec_str = json.dumps(rec)
                for aid in ["MBLX-2025-011", "VIS-2025-007", "MBLX-2025-013"]:
                    if aid in rec_str:
                        asset_records[aid] = rec
                        break
    except Exception as e:
        pass

    # Simpler fallback: search raw JSON for each asset
    def find_asset_record(asset_id):
        """Try to find a sub-dict in data that mentions this asset_id."""
        # already found above
        for k, v in asset_records.items():
            if asset_id in k or (isinstance(v, dict) and asset_id in json.dumps(v)):
                return v
        # deep search
        def search(obj, target):
            if isinstance(obj, dict):
                if any(target in str(vv) for vv in obj.values()):
                    return obj
                for vv in obj.values():
                    r = search(vv, target)
                    if r:
                        return r
            elif isinstance(obj, list):
                for item in obj:
                    r = search(item, target)
                    if r:
                        return r
            return None
        return search(data, asset_id)

    rec1 = find_asset_record("MBLX-2025-011")
    rec2 = find_asset_record("VIS-2025-007")
    rec3 = find_asset_record("MBLX-2025-013")

    all_three_present = all(r is not None for r in [rec1, rec2, rec3])
    total_score += check(
        "all_three_assets_present",
        all_three_present,
        "All three asset records (MBLX-2025-011, VIS-2025-007, MBLX-2025-013) must be present." if not all_three_present else "All three assets found.",
        weight=1.0
    )

    # ---- ASSET 1: MBLX-2025-011 checks ----
    rec1_str = json.dumps(rec1).lower() if rec1 else ""

    # Process Type: must be "Human-authored" (exact vocabulary from SKILL.md Section 4)
    human_authored_present = "human-authored" in rec1_str or "human authored" in rec1_str
    total_score += check(
        "asset1_process_type_human_authored",
        human_authored_present,
        "MBLX-2025-011 process type must be 'Human-authored' per SKILL.md vocabulary." if not human_authored_present else "Correct process type found.",
        weight=1.5
    )

    # License scope: North America, 2 years / Jan 2027
    license_ok_1 = ("north america" in rec1_str or "na" in rec1_str) and ("2027" in rec1_str or "2 year" in rec1_str or "two year" in rec1_str)
    total_score += check(
        "asset1_license_scope",
        license_ok_1,
        "MBLX-2025-011 must include North America territory and 2-year/Jan 2027 duration.",
        weight=1.0
    )

    # Credit string present
    credit_ok_1 = "jasper kline" in rec1_str
    total_score += check(
        "asset1_credit_string",
        credit_ok_1,
        "MBLX-2025-011 credit string must mention Jasper Kline.",
        weight=0.5
    )

    # Content hash from intake
    hash_ok_1 = "a3f8c2d1e4b09f76" in (rec1_str or "")
    total_score += check(
        "asset1_content_hash",
        hash_ok_1,
        "MBLX-2025-011 content hash (a3f8c2d1...) must be recorded.",
        weight=1.0
    )

    # ---- ASSET 2: VIS-2025-007 checks ----
    rec2_str = json.dumps(rec2).lower() if rec2 else ""

    # Process Type: must be "AI-assisted" (exact vocabulary)
    ai_assisted_present = "ai-assisted" in rec2_str or "ai assisted" in rec2_str
    total_score += check(
        "asset2_process_type_ai_assisted",
        ai_assisted_present,
        "VIS-2025-007 process type must be 'AI-assisted' per SKILL.md vocabulary." if not ai_assisted_present else "Correct process type found.",
        weight=1.5
    )

    # License: worldwide / perpetual
    license_ok_2 = ("worldwide" in rec2_str or "global" in rec2_str) and ("perpetual" in rec2_str or "no expiration" in rec2_str or "indefinite" in rec2_str)
    total_score += check(
        "asset2_license_scope",
        license_ok_2,
        "VIS-2025-007 must include worldwide territory and perpetual/no-expiration duration.",
        weight=1.0
    )

    # Platform notes: Instagram short form
    platform_notes_ok = "instagram" in rec2_str or "100 char" in rec2_str or "short form" in rec2_str
    total_score += check(
        "asset2_platform_notes",
        platform_notes_ok,
        "VIS-2025-007 must include platform notes for Instagram (short form attribution).",
        weight=1.0
    )

    # Content hash: must be computed SHA-256 of credit string
    # The cover memo says: compute SHA-256 of the asset's credit string as stand-in
    # Credit string: "Art Direction: Rhea Solano | AI-assisted textures via ArtiGen | MediaBlox 2025"
    credit_string_2 = "Art Direction: Rhea Solano | AI-assisted textures via ArtiGen | MediaBlox 2025"
    expected_hash_2 = hashlib.sha256(credit_string_2.encode()).hexdigest()
    hash_ok_2 = expected_hash_2 in (json.dumps(rec2) if rec2 else "")
    total_score += check(
        "asset2_content_hash_computed",
        hash_ok_2,
        f"VIS-2025-007 content hash must be SHA-256 of credit string = {expected_hash_2}. Got: {json.dumps(rec2)[:300] if rec2 else 'N/A'}",
        weight=2.0
    )

    # Version notes: v3.0 FINAL
    version_ok_2 = "v3" in rec2_str or "3.0" in rec2_str or "final" in rec2_str
    total_score += check(
        "asset2_version_notes",
        version_ok_2,
        "VIS-2025-007 must include version notes (v3.0 FINAL).",
        weight=0.5
    )

    # ---- ASSET 3: MBLX-2025-013 checks ----
    rec3_str = json.dumps(rec3).lower() if rec3 else ""

    # Process Type: must be "AI-generated" (exact vocabulary)
    ai_generated_present = "ai-generated" in rec3_str or "ai generated" in rec3_str
    total_score += check(
        "asset3_process_type_ai_generated",
        ai_generated_present,
        "MBLX-2025-013 process type must be 'AI-generated' per SKILL.md vocabulary." if not ai_generated_present else "Correct process type found.",
        weight=1.5
    )

    # License: internal use only
    license_ok_3 = "internal" in rec3_str
    total_score += check(
        "asset3_license_scope_internal",
        license_ok_3,
        "MBLX-2025-013 must specify internal use only.",
        weight=1.0
    )

    # Contributor context: HarmonizerAI + Jasper Kline as prompt author
    contributor_ok_3 = "harmonizerai" in rec3_str or "harmonizer" in rec3_str
    total_score += check(
        "asset3_contributor_context",
        contributor_ok_3,
        "MBLX-2025-013 must reference HarmonizerAI in contributor context.",
        weight=0.5
    )

    # Content hash from intake
    hash_ok_3 = "9b1d4e72f305a8c6" in (json.dumps(rec3) if rec3 else "")
    total_score += check(
        "asset3_content_hash",
        hash_ok_3,
        "MBLX-2025-013 content hash (9b1d4e72...) must be recorded.",
        weight=1.0
    )

    # ---- STRUCTURAL COMPLETENESS: All ABC sections present for all assets ----
    # Section 4 defines: Origin, Identity, Provenance, Licensing, Attribution, Integrity
    # Check for presence of all six conceptual sections across all records

    all_records_str = json.dumps(data).lower()

    # Origin: creation_timestamp or equivalent
    origin_ok = any(k in all_records_str for k in ["creation_timestamp", "timestamp", "finalized", "creation date", "date_finalized", "finalization"])
    total_score += check("abc_origin_fields", origin_ok, "ABC records must include Origin fields (creation timestamp).", weight=0.5)

    # Identity: author/creator reference
    identity_ok = any(k in all_records_str for k in ["primary_author", "author", "creator", "jasper kline", "rhea solano"])
    total_score += check("abc_identity_fields", identity_ok, "ABC records must include Identity fields.", weight=0.5)

    # Provenance: process_type
    provenance_ok = any(k in all_records_str for k in ["process_type", "process type", "provenance", "human-authored", "ai-assisted", "ai-generated"])
    total_score += check("abc_provenance_fields", provenance_ok, "ABC records must include Provenance fields (process type).", weight=0.5)

    # Licensing: license_scope or equivalent
    licensing_ok = any(k in all_records_str for k in ["license_scope", "license scope", "licensing", "territory", "duration"])
    total_score += check("abc_licensing_fields", licensing_ok, "ABC records must include Licensing fields.", weight=0.5)

    # Attribution: credit_string
    attribution_ok = any(k in all_records_str for k in ["credit_string", "credit string", "attribution", "credit"])
    total_score += check("abc_attribution_fields", attribution_ok, "ABC records must include Attribution (credit string).", weight=0.5)

    # Integrity: content_hash
    integrity_ok = any(k in all_records_str for k in ["content_hash", "content hash", "hash", "integrity"])
    total_score += check("abc_integrity_fields", integrity_ok, "ABC records must include Integrity (content hash).", weight=0.5)

    # --- Source References present ---
    source_ref_ok = any(k in all_records_str for k in ["lic-sync-na-2yr", "vlic-global-perp", "int-use-only-policy"])
    total_score += check(
        "source_references_present",
        source_ref_ok,
        "At least one license source reference (e.g., LIC-SYNC-NA-2YR) must be present.",
        weight=0.5
    )

    # --- Final scoring ---
    max_score = sum([
        1.0,  # file_exists
        1.0,  # json_parseable
        1.5,  # mandatory_disclosure_gate
        1.5,  # disclosure_before_assets
        1.0,  # all_three_assets_present
        1.5,  # asset1 process type
        1.0,  # asset1 license
        0.5,  # asset1 credit
        1.0,  # asset1 hash
        1.5,  # asset2 process type
        1.0,  # asset2 license
        1.0,  # asset2 platform notes
        2.0,  # asset2 computed hash
        0.5,  # asset2 version
        1.5,  # asset3 process type
        1.0,  # asset3 license
        0.5,  # asset3 contributor
        1.0,  # asset3 hash
        0.5 * 6,  # abc structural sections
        0.5,  # source refs
    ])

    normalized_score = round(min(total_score / max_score, 1.0), 4)
    passed = normalized_score >= 0.75

    print(json.dumps({
        "passed": passed,
        "score": normalized_score,
        "checks": results
    }, indent=2))

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    main(workspace)