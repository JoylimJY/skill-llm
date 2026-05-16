#!/usr/bin/env python3
"""
Evaluation script for ontology-clawra task.
Checks that agent correctly populated the pharmacology knowledge base
using the ontology-clawra CLI with proper fields, confidence labels,
and multi-step workflow (create → reason → extract → validate).
"""
import sys
import json
import yaml
import traceback
from pathlib import Path

def load_yaml_safe(path):
    try:
        with open(path) as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        return {"__error__": str(e)}

def load_jsonl_safe(path):
    records = []
    try:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
    except Exception:
        pass
    return records

VALID_CONFIDENCE = {"CONFIRMED", "ASSUMED", "SPECULATIVE", "UNKNOWN"}

def run_checks(workspace_dir):
    workspace = Path(workspace_dir)
    mem = workspace / "memory" / "ontology-clawra"
    checks = []
    total_score = 0.0

    # ── CHECK 1: laws.yaml exists and has at least 2 laws ─────────────────────
    try:
        laws_path = mem / "laws.yaml"
        laws_data = load_yaml_safe(laws_path)
        laws = laws_data.get("laws", [])
        has_enough_laws = len(laws) >= 2
        checks.append({
            "name": "laws.yaml has at least 2 Law entries",
            "passed": has_enough_laws,
            "detail": f"Found {len(laws)} law(s): {[l.get('name') for l in laws]}"
        })
        if has_enough_laws:
            total_score += 0.10
    except Exception as e:
        checks.append({"name": "laws.yaml has at least 2 Law entries", "passed": False, "detail": str(e)})

    # ── CHECK 2: DigoxinAmiodaroneInteractionLaw exists with required fields ───
    try:
        laws_data = load_yaml_safe(mem / "laws.yaml")
        laws = laws_data.get("laws", [])
        digoxin_law = next(
            (l for l in laws if "digoxin" in l.get("name","").lower() or
             "digoxin" in l.get("statement","").lower()),
            None
        )
        has_digoxin_law = digoxin_law is not None
        if has_digoxin_law:
            required_fields = ["name", "domain", "statement", "source", "confidence"]
            missing = [f for f in required_fields if f not in digoxin_law]
            has_all_fields = len(missing) == 0
            valid_conf = digoxin_law.get("confidence") in VALID_CONFIDENCE
            passed = has_all_fields and valid_conf
            detail = (f"Found: {digoxin_law.get('name')}, missing fields: {missing}, "
                      f"confidence: {digoxin_law.get('confidence')} (valid={valid_conf})")
        else:
            passed = False
            detail = "No Law entry found containing 'digoxin' in name or statement"
        checks.append({
            "name": "DigoxinAmiodarone Law: required fields + valid confidence",
            "passed": passed,
            "detail": detail
        })
        if passed:
            total_score += 0.15
    except Exception as e:
        checks.append({"name": "DigoxinAmiodarone Law: required fields + valid confidence",
                       "passed": False, "detail": traceback.format_exc()})

    # ── CHECK 3: WarfarinNSAID Law exists with required fields ────────────────
    try:
        laws_data = load_yaml_safe(mem / "laws.yaml")
        laws = laws_data.get("laws", [])
        warfarin_law = next(
            (l for l in laws if "warfarin" in l.get("name","").lower() or
             "warfarin" in l.get("statement","").lower()),
            None
        )
        has_warfarin_law = warfarin_law is not None
        if has_warfarin_law:
            required_fields = ["name", "domain", "statement", "source", "confidence"]
            missing = [f for f in required_fields if f not in warfarin_law]
            valid_conf = warfarin_law.get("confidence") in VALID_CONFIDENCE
            passed = len(missing) == 0 and valid_conf
            detail = (f"Found: {warfarin_law.get('name')}, missing: {missing}, "
                      f"confidence: {warfarin_law.get('confidence')} (valid={valid_conf})")
        else:
            passed = False
            detail = "No Law entry found containing 'warfarin'"
        checks.append({
            "name": "WarfarinNSAID Law: required fields + valid confidence",
            "passed": passed,
            "detail": detail
        })
        if passed:
            total_score += 0.10
    except Exception as e:
        checks.append({"name": "WarfarinNSAID Law: required fields + valid confidence",
                       "passed": False, "detail": traceback.format_exc()})

    # ── CHECK 4: rules.yaml has at least 2 Rules ──────────────────────────────
    try:
        rules_path = mem / "rules.yaml"
        rules_data = load_yaml_safe(rules_path)
        rules = rules_data.get("rules", [])
        has_enough_rules = len(rules) >= 2
        checks.append({
            "name": "rules.yaml has at least 2 Rule entries",
            "passed": has_enough_rules,
            "detail": f"Found {len(rules)} rule(s): {[r.get('name') for r in rules]}"
        })
        if has_enough_rules:
            total_score += 0.10
    except Exception as e:
        checks.append({"name": "rules.yaml has at least 2 Rule entries", "passed": False, "detail": str(e)})

    # ── CHECK 5: Rules have required fields (condition, action, source, confidence)
    try:
        rules_data = load_yaml_safe(mem / "rules.yaml")
        rules = rules_data.get("rules", [])
        required_rule_fields = ["name", "condition", "action", "source", "confidence"]
        all_valid = True
        issues = []
        for r in rules:
            missing = [f for f in required_rule_fields if f not in r]
            if missing:
                all_valid = False
                issues.append(f"Rule '{r.get('name','?')}' missing: {missing}")
            conf = r.get("confidence")
            if conf not in VALID_CONFIDENCE:
                all_valid = False
                issues.append(f"Rule '{r.get('name','?')}' invalid confidence: '{conf}'")
        checks.append({
            "name": "All Rules have required fields and valid confidence",
            "passed": all_valid and len(rules) >= 2,
            "detail": "; ".join(issues) if issues else f"All {len(rules)} rules valid"
        })
        if all_valid and len(rules) >= 2:
            total_score += 0.10
    except Exception as e:
        checks.append({"name": "All Rules have required fields and valid confidence",
                       "passed": False, "detail": traceback.format_exc()})

    # ── CHECK 6: reasoning.jsonl has at least 1 record ────────────────────────
    try:
        reasoning_path = mem / "reasoning.jsonl"
        records = load_jsonl_safe(reasoning_path)
        has_records = len(records) >= 1
        checks.append({
            "name": "reasoning.jsonl has at least 1 reasoning record",
            "passed": has_records,
            "detail": f"Found {len(records)} reasoning record(s)"
        })
        if has_records:
            total_score += 0.05
    except Exception as e:
        checks.append({"name": "reasoning.jsonl has at least 1 reasoning record",
                       "passed": False, "detail": str(e)})

    # ── CHECK 7: Reasoning record contains required fields ────────────────────
    try:
        records = load_jsonl_safe(mem / "reasoning.jsonl")
        required_fields = ["query", "confidence", "based_on_rules", "timestamp"]
        digoxin_records = [r for r in records if
                           "digoxin" in r.get("query","").lower() or
                           "amiodarone" in r.get("query","").lower()]
        if digoxin_records:
            rec = digoxin_records[0]
            missing = [f for f in required_fields if f not in rec]
            valid_conf = rec.get("confidence") in VALID_CONFIDENCE
            passed = len(missing) == 0 and valid_conf
            detail = (f"Query: '{rec.get('query','?')}', missing: {missing}, "
                      f"confidence: {rec.get('confidence')} (valid={valid_conf}), "
                      f"based_on_rules: {rec.get('based_on_rules')}")
        else:
            passed = False
            detail = (f"No reasoning record found with 'digoxin' or 'amiodarone' in query. "
                      f"Available queries: {[r.get('query','?') for r in records]}")
        checks.append({
            "name": "Reasoning record for digoxin/amiodarone has required fields",
            "passed": passed,
            "detail": detail
        })
        if passed:
            total_score += 0.15
    except Exception as e:
        checks.append({"name": "Reasoning record for digoxin/amiodarone has required fields",
                       "passed": False, "detail": traceback.format_exc()})

    # ── CHECK 8: Reasoning record's based_on_rules references an actual law/rule
    try:
        records = load_jsonl_safe(mem / "reasoning.jsonl")
        laws_data = load_yaml_safe(mem / "laws.yaml").get("laws", [])
        rules_data = load_yaml_safe(mem / "rules.yaml").get("rules", [])
        known_names = {l.get("name") for l in laws_data} | {r.get("name") for r in rules_data}

        digoxin_records = [r for r in records if
                           "digoxin" in r.get("query","").lower() or
                           "amiodarone" in r.get("query","").lower()]
        if digoxin_records:
            rec = digoxin_records[0]
            bor = rec.get("based_on_rules", [])
            # Check if reasoning was done AFTER laws were registered
            # If based_on_rules is populated, it should match known names
            # If empty, it could be because laws weren't registered first (methodology violation)
            # We check: either (a) bor references known names, OR (b) laws exist now meaning
            # agent registered them and then reasoned (we accept this either way but prefer non-empty)
            if bor:
                referenced_known = any(b in known_names for b in bor)
                passed = referenced_known
                detail = f"based_on_rules: {bor}, known: {list(known_names)[:5]}, referenced_known={referenced_known}"
            else:
                # No based_on_rules: acceptable if laws are empty but penalized if laws exist
                if known_names:
                    passed = False
                    detail = f"based_on_rules is empty but laws/rules exist: {list(known_names)[:5]}. Should reference registered laws."
                else:
                    passed = False
                    detail = "based_on_rules is empty and no laws/rules registered"
        else:
            passed = False
            detail = "No digoxin/amiodarone reasoning record found"
        checks.append({
            "name": "Reasoning record's based_on_rules references registered Laws/Rules",
            "passed": passed,
            "detail": detail
        })
        if passed:
            total_score += 0.10
    except Exception as e:
        checks.append({"name": "Reasoning record's based_on_rules references registered Laws/Rules",
                       "passed": False, "detail": traceback.format_exc()})

    # ── CHECK 9: extraction_log.jsonl has at least 1 entry ───────────────────
    try:
        ext_log_path = mem / "extraction_log.jsonl"
        ext_records = load_jsonl_safe(ext_log_path)
        has_extraction = len(ext_records) >= 1
        total_extracted = sum(r.get("total_extracted", 0) for r in ext_records)
        checks.append({
            "name": "extraction_log.jsonl has at least 1 extraction record",
            "passed": has_extraction,
            "detail": f"Found {len(ext_records)} extraction log(s), total entities extracted: {total_extracted}"
        })
        if has_extraction:
            total_score += 0.05
    except Exception as e:
        checks.append({"name": "extraction_log.jsonl has at least 1 extraction record",
                       "passed": False, "detail": str(e)})

    # ── CHECK 10: Extracted entities reference EHR-001 clinical note content ──
    try:
        ext_log_path = mem / "extraction_log.jsonl"
        ext_records = load_jsonl_safe(ext_log_path)
        graph_records = load_jsonl_safe(mem / "graph.jsonl")

        # Look for extraction that came from EHR-001 note (bradycardia/digoxin/amiodarone content)
        ehr_keywords = ["bradycardia", "digoxin", "amiodarone", "physician", "patient", "ehr"]
        ehr_extraction = any(
            any(kw in r.get("source_text","").lower() for kw in ehr_keywords)
            for r in ext_records
        )
        # Also check if graph has anything added from extraction
        has_extracted_entities = len(graph_records) > 0

        passed = ehr_extraction or has_extracted_entities
        checks.append({
            "name": "Extraction used EHR-001 clinical note content",
            "passed": passed,
            "detail": (f"EHR keywords in extraction logs: {ehr_extraction}, "
                       f"graph entities: {len(graph_records)}, "
                       f"log sources: {[r.get('source_text','?')[:40] for r in ext_records]}")
        })
        if passed:
            total_score += 0.05
    except Exception as e:
        checks.append({"name": "Extraction used EHR-001 clinical note content",
                       "passed": False, "detail": traceback.format_exc()})

    # ── CHECK 11: All confidence labels across all files are valid ─────────────
    try:
        laws = load_yaml_safe(mem / "laws.yaml").get("laws", [])
        rules = load_yaml_safe(mem / "rules.yaml").get("rules", [])
        graph = load_jsonl_safe(mem / "graph.jsonl")
        reasoning = load_jsonl_safe(mem / "reasoning.jsonl")

        all_records = laws + rules + graph + reasoning
        invalid = []
        for r in all_records:
            conf = r.get("confidence")
            if conf is not None and conf not in VALID_CONFIDENCE:
                invalid.append(f"{r.get('name', r.get('query','?'))}: '{conf}'")

        total_with_conf = sum(1 for r in all_records if r.get("confidence") is not None)
        passed = len(invalid) == 0 and total_with_conf > 0
        checks.append({
            "name": "All confidence labels are valid (CONFIRMED/ASSUMED/SPECULATIVE/UNKNOWN)",
            "passed": passed,
            "detail": (f"Invalid: {invalid}" if invalid else
                       f"All {total_with_conf} confidence labels valid across laws/rules/graph/reasoning")
        })
        if passed:
            total_score += 0.05
    except Exception as e:
        checks.append({"name": "All confidence labels are valid",
                       "passed": False, "detail": traceback.format_exc()})

    # ── CHECK 12: Law entries have 'source' field (provenance requirement) ────
    try:
        laws = load_yaml_safe(mem / "laws.yaml").get("laws", [])
        rules = load_yaml_safe(mem / "rules.yaml").get("rules", [])
        missing_source = []
        for l in laws:
            if not l.get("source"):
                missing_source.append(f"Law:{l.get('name','?')}")
        for r in rules:
            if not r.get("source"):
                missing_source.append(f"Rule:{r.get('name','?')}")
        passed = len(missing_source) == 0 and (len(laws) + len(rules)) > 0
        checks.append({
            "name": "All Laws and Rules have 'source' provenance field",
            "passed": passed,
            "detail": (f"Missing source: {missing_source}" if missing_source else
                       f"All {len(laws)} laws and {len(rules)} rules have source field")
        })
        if passed:
            total_score += 0.05
    except Exception as e:
        checks.append({"name": "All Laws and Rules have 'source' provenance field",
                       "passed": False, "detail": traceback.format_exc()})

    # ── CHECK 13: Workflow order – laws/rules registered BEFORE reasoning ──────
    try:
        # Check that reasoning records reference the laws by name (implying create ran first)
        laws = load_yaml_safe(mem / "laws.yaml").get("laws", [])
        rules = load_yaml_safe(mem / "rules.yaml").get("rules", [])
        reasoning = load_jsonl_safe(mem / "reasoning.jsonl")

        law_rule_names = {l.get("name") for l in laws} | {r.get("name") for r in rules}
        reasoning_refs = set()
        for rec in reasoning:
            for ref in rec.get("based_on_rules", []):
                reasoning_refs.add(ref)

        overlap = reasoning_refs & law_rule_names
        # If reasoning refs include law/rule names, workflow was correct
        correct_order = len(overlap) > 0 if law_rule_names else False
        checks.append({
            "name": "Reasoning references registered laws/rules (correct workflow order)",
            "passed": correct_order,
            "detail": (f"Laws/Rules registered: {list(law_rule_names)[:5]}, "
                       f"Referenced in reasoning: {list(reasoning_refs)[:5]}, "
                       f"Overlap: {list(overlap)}")
        })
        if correct_order:
            total_score += 0.05
    except Exception as e:
        checks.append({"name": "Reasoning references registered laws/rules (correct workflow order)",
                       "passed": False, "detail": traceback.format_exc()})

    # Final score normalization
    total_score = min(total_score, 1.0)
    passed_count = sum(1 for c in checks if c["passed"])
    overall_passed = passed_count >= 8  # Must pass at least 8 of 13 checks

    return {
        "passed": overall_passed,
        "score": round(total_score, 3),
        "checks": checks
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [
            {"name": "argument_check", "passed": False, "detail": "No workspace dir provided"}
        ]}))
        sys.exit(1)

    result = run_checks(sys.argv[1])
    print(json.dumps(result, indent=2, ensure_ascii=False))