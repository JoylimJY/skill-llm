import sys
import json
import math
from pathlib import Path

def evaluate(workspace_dir):
    workspace = Path(workspace_dir)
    checks = []
    total_score = 0.0

    MIMICRY_NS = "http://moltbook.org/mimicry/ontology#"
    BASE_NS = "http://moltbook.org/mimicry/"

    def add_check(name, passed, detail, weight=1.0):
        checks.append({"name": name, "passed": passed, "detail": detail})
        return weight if passed else 0.0

    # ── Find the two output files ────────────────────────────────────────────
    nova_files = list(workspace.rglob("novasynth_007*.ttl")) + list(workspace.rglob("*novasynth*007*.ttl")) + list(workspace.rglob("*nova*synth*7*.ttl"))
    wren_files = list(workspace.rglob("wrenmira_042*.ttl")) + list(workspace.rglob("*wrenmira*042*.ttl")) + list(workspace.rglob("*wren*mira*42*.ttl"))

    # More relaxed search
    if not nova_files:
        nova_files = [f for f in workspace.rglob("*.ttl") if "nova" in f.name.lower() or "synth" in f.name.lower()]
    if not wren_files:
        wren_files = [f for f in workspace.rglob("*.ttl") if "wren" in f.name.lower() or "mira" in f.name.lower()]

    nova_file = nova_files[0] if nova_files else None
    wren_file = wren_files[0] if wren_files else None

    # ── Validate each profile ────────────────────────────────────────────────
    try:
        from rdflib import Graph, Namespace, RDF
        from pyshacl import validate

        MIMICRY = Namespace(MIMICRY_NS)
        BASE = Namespace(BASE_NS)

        SHAPES_TTL = """
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix mimicry: <http://moltbook.org/mimicry/ontology#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

mimicry:AgentProfileShape
    a sh:NodeShape ;
    sh:targetClass mimicry:AgentProfile ;
    sh:property [ sh:path mimicry:agentId ; sh:datatype xsd:string ; sh:minCount 1 ; sh:maxCount 1 ] ;
    sh:property [ sh:path mimicry:agentName ; sh:datatype xsd:string ; sh:minCount 1 ; sh:maxCount 1 ] ;
    sh:property [ sh:path mimicry:platform ; sh:datatype xsd:string ; sh:minCount 1 ; sh:maxCount 1 ] ;
    sh:property [ sh:path mimicry:postCount ; sh:datatype xsd:integer ; sh:minCount 1 ; sh:maxCount 1 ] ;
    sh:property [ sh:path mimicry:daysSpan ; sh:datatype xsd:float ; sh:minCount 1 ; sh:maxCount 1 ] ;
    sh:property [ sh:path mimicry:hasCVScore ; sh:datatype xsd:float ; sh:minCount 1 ; sh:maxCount 1 ; sh:minInclusive 0.0 ; sh:maxInclusive 1.0 ] ;
    sh:property [ sh:path mimicry:hasMetaScore ; sh:datatype xsd:float ; sh:minCount 1 ; sh:maxCount 1 ; sh:minInclusive 0.0 ; sh:maxInclusive 1.0 ] ;
    sh:property [ sh:path mimicry:hasHumanContextScore ; sh:datatype xsd:float ; sh:minCount 1 ; sh:maxCount 1 ; sh:minInclusive 0.0 ; sh:maxInclusive 1.0 ] ;
    sh:property [ sh:path mimicry:hasAgentScore ; sh:datatype xsd:float ; sh:minCount 1 ; sh:maxCount 1 ; sh:minInclusive 0.0 ; sh:maxInclusive 1.0 ] ;
    sh:property [ sh:path mimicry:hasClassification ; sh:minCount 1 ; sh:maxCount 1 ] ;
    sh:property [ sh:path mimicry:hasConfidence ; sh:datatype xsd:float ; sh:minCount 1 ; sh:maxCount 1 ; sh:minInclusive 0.0 ; sh:maxInclusive 1.0 ] .
"""

        def parse_and_extract(ttl_path):
            g = Graph()
            g.parse(str(ttl_path), format="turtle")
            shapes_g = Graph()
            shapes_g.parse(data=SHAPES_TTL, format="turtle")
            conforms, _, results_text = validate(g, shacl_graph=shapes_g, abort_on_first=False)

            profile_node = None
            for s in g.subjects(RDF.type, MIMICRY.AgentProfile):
                profile_node = s
                break

            def get_val(pred):
                v = g.value(profile_node, MIMICRY[pred])
                return v.toPython() if v is not None else None

            def get_uri(pred):
                v = g.value(profile_node, MIMICRY[pred])
                return str(v) if v is not None else None

            return {
                "conforms": conforms,
                "results_text": results_text,
                "agentId": get_val("agentId"),
                "agentName": get_val("agentName"),
                "cv": get_val("hasCVScore"),
                "meta": get_val("hasMetaScore"),
                "human": get_val("hasHumanContextScore"),
                "score": get_val("hasAgentScore"),
                "classification_uri": get_uri("hasClassification"),
                "confidence": get_val("hasConfidence"),
                "postCount": get_val("postCount"),
                "daysSpan": get_val("daysSpan"),
            }

        # ─── NovaSynth_7 checks ──────────────────────────────────────────────
        if nova_file is None:
            total_score += add_check("nova_file_exists", False,
                "novasynth_007 TTL profile not found in workspace")
            total_score += add_check("nova_shacl_valid", False, "File not found")
            total_score += add_check("nova_correct_cv_score", False, "File not found")
            total_score += add_check("nova_correct_agent_score", False, "File not found")
            total_score += add_check("nova_cron_classification", False, "File not found")
            total_score += add_check("nova_correct_confidence", False, "File not found")
        else:
            total_score += add_check("nova_file_exists", True,
                f"Found at {nova_file.relative_to(workspace)}")
            try:
                nova = parse_and_extract(nova_file)

                total_score += add_check("nova_shacl_valid", nova["conforms"],
                    "SHACL validation passed" if nova["conforms"] else f"SHACL failed: {nova['results_text'][:200]}")

                # CV Score check
                cv_ok = nova["cv"] is not None and abs(nova["cv"] - 0.09) < 0.005
                total_score += add_check("nova_correct_cv_score", cv_ok,
                    f"CV={nova['cv']} (expected ~0.09)" if nova["cv"] is not None else "CV score missing")

                # Agent Score: 0.30*0.09 + 0.50*0.62 + 0.20*0.31 = 0.027+0.310+0.062 = 0.399
                expected_nova_score = round(0.30 * 0.09 + 0.50 * 0.62 + 0.20 * 0.31, 4)
                score_ok = nova["score"] is not None and abs(nova["score"] - expected_nova_score) < 0.015
                total_score += add_check("nova_correct_agent_score", score_ok,
                    f"Score={nova['score']} (expected ~{expected_nova_score})" if nova["score"] is not None else "Score missing")

                # Classification: CRON (CV < 0.12 override)
                class_uri = nova["classification_uri"] or ""
                is_cron = "Cron" in class_uri or "CRON" in class_uri or "cron" in class_uri
                total_score += add_check("nova_cron_classification", is_cron,
                    f"Classification URI: {class_uri} (must be Cron — CV=0.09 < 0.12 triggers override)")

                # Confidence: Minimal tier (post=8, days=5.5) → 0.80 - 0.10 = 0.70
                expected_nova_conf = 0.70
                conf_ok = nova["confidence"] is not None and abs(nova["confidence"] - expected_nova_conf) < 0.02
                total_score += add_check("nova_correct_confidence", conf_ok,
                    f"Confidence={nova['confidence']} (expected {expected_nova_conf}: base 0.80 - 0.10 Minimal penalty)")

            except Exception as e:
                for chk in ["nova_shacl_valid", "nova_correct_cv_score", "nova_correct_agent_score",
                            "nova_cron_classification", "nova_correct_confidence"]:
                    total_score += add_check(chk, False, f"Parse error: {e}")

        # ─── WrenMira_42 checks ──────────────────────────────────────────────
        if wren_file is None:
            total_score += add_check("wren_file_exists", False,
                "wrenmira_042 TTL profile not found in workspace")
            total_score += add_check("wren_shacl_valid", False, "File not found")
            total_score += add_check("wren_correct_cv_score", False, "File not found")
            total_score += add_check("wren_correct_agent_score", False, "File not found")
            total_score += add_check("wren_human_classification", False, "File not found")
            total_score += add_check("wren_correct_confidence", False, "File not found")
        else:
            total_score += add_check("wren_file_exists", True,
                f"Found at {wren_file.relative_to(workspace)}")
            try:
                wren = parse_and_extract(wren_file)

                total_score += add_check("wren_shacl_valid", wren["conforms"],
                    "SHACL validation passed" if wren["conforms"] else f"SHACL failed: {wren['results_text'][:200]}")

                # CV Score check
                cv_ok = wren["cv"] is not None and abs(wren["cv"] - 0.71) < 0.005
                total_score += add_check("wren_correct_cv_score", cv_ok,
                    f"CV={wren['cv']} (expected ~0.71)" if wren["cv"] is not None else "CV score missing")

                # Agent Score: 0.30*0.71 + 0.50*0.38 + 0.20*0.73 = 0.213+0.190+0.146 = 0.549
                expected_wren_score = round(0.30 * 0.71 + 0.50 * 0.38 + 0.20 * 0.73, 4)
                score_ok = wren["score"] is not None and abs(wren["score"] - expected_wren_score) < 0.015
                total_score += add_check("wren_correct_agent_score", score_ok,
                    f"Score={wren['score']} (expected ~{expected_wren_score})" if wren["score"] is not None else "Score missing")

                # Classification: HUMAN (0.35 ≤ 0.549 ≤ 0.55, CV=0.71>0.5, Human=0.73>0.6)
                class_uri = wren["classification_uri"] or ""
                is_human = "Human" in class_uri or "HUMAN" in class_uri or "human" in class_uri
                total_score += add_check("wren_human_classification", is_human,
                    f"Classification URI: {class_uri} (must be Human — score in [0.35,0.55], CV>0.5, Human>0.6)")

                # Confidence: Minimal tier (post=7, days=4.0) → 0.80 - 0.10 = 0.70
                expected_wren_conf = 0.70
                conf_ok = wren["confidence"] is not None and abs(wren["confidence"] - expected_wren_conf) < 0.02
                total_score += add_check("wren_correct_confidence", conf_ok,
                    f"Confidence={wren['confidence']} (expected {expected_wren_conf}: base 0.80 - 0.10 Minimal penalty)")

            except Exception as e:
                for chk in ["wren_shacl_valid", "wren_correct_cv_score", "wren_correct_agent_score",
                            "wren_human_classification", "wren_correct_confidence"]:
                    total_score += add_check(chk, False, f"Parse error: {e}")

        # ─── Bonus: correct ontology prefix usage ────────────────────────────
        bonus_checks = 0
        for ttl_f, label in [(nova_file, "nova"), (wren_file, "wren")]:
            if ttl_f is not None:
                try:
                    content = ttl_f.read_text()
                    uses_correct_ns = "http://moltbook.org/mimicry/ontology#" in content
                    bonus_checks += (1 if uses_correct_ns else 0)
                    total_score += add_check(f"{label}_correct_namespace", uses_correct_ns,
                        "Correct mimicry ontology namespace used" if uses_correct_ns else
                        "Wrong/missing mimicry namespace — agent likely used generic or wrong prefix")
                except Exception as e:
                    total_score += add_check(f"{label}_correct_namespace", False, f"Read error: {e}")

    except ImportError as e:
        for chk in ["rdflib_available"]:
            total_score += add_check(chk, False, f"Dependency error: {e}")

    # ── Final scoring ─────────────────────────────────────────────────────────
    num_checks = len(checks)
    passed_checks = sum(1 for c in checks if c["passed"])
    final_score = round(total_score / num_checks, 4) if num_checks > 0 else 0.0
    all_passed = all(c["passed"] for c in checks)

    return {
        "passed": all_passed,
        "score": final_score,
        "checks": checks
    }

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, indent=2))