import sys
import json
import os
import re
from pathlib import Path

def load_json_file(path):
    with open(path, "r") as f:
        return json.load(f)

def evaluate(workspace):
    checks = []
    
    # ─── CHECK 1: Wiki document was created ───────────────────────────────────
    wiki_dir = Path(workspace) / "tools" / "wiki"
    wiki_files = list(wiki_dir.glob("wiki_*.json"))
    
    check1_passed = len(wiki_files) >= 1
    checks.append({
        "name": "wiki_document_created",
        "passed": check1_passed,
        "detail": f"Found {len(wiki_files)} wiki document(s) in {wiki_dir}" if check1_passed
                  else f"No wiki documents found in {wiki_dir}"
    })
    
    if not check1_passed:
        return {"passed": False, "score": 0.0, "checks": checks}
    
    # Load the most recently created wiki document
    wiki_files_sorted = sorted(wiki_files, key=lambda p: p.stat().st_mtime, reverse=True)
    try:
        wiki_doc = load_json_file(wiki_files_sorted[0])
        wiki_content = wiki_doc.get("content", "")
        wiki_title = wiki_doc.get("title", "")
        wiki_doc_id = wiki_doc.get("document_id", "")
    except Exception as e:
        checks.append({"name": "wiki_document_readable", "passed": False, "detail": str(e)})
        return {"passed": False, "score": 0.0, "checks": checks}
    
    # ─── CHECK 2: Submission was made ─────────────────────────────────────────
    submission_path = Path(workspace) / "tools" / "submission" / "submission.json"
    try:
        submission = load_json_file(submission_path)
        check2_passed = submission.get("status") == "submitted"
        checks.append({
            "name": "submission_filed",
            "passed": check2_passed,
            "detail": f"Submission status: {submission.get('status')}"
        })
    except Exception as e:
        checks.append({"name": "submission_filed", "passed": False, "detail": f"submission.json missing or unreadable: {e}"})
        check2_passed = False
    
    # ─── CHECK 3: submission references the wiki document ─────────────────────
    if check2_passed:
        attached = submission.get("attachement_files", "")
        # The attached value should contain the wiki doc id or a path containing it
        check3_passed = bool(wiki_doc_id and wiki_doc_id in str(attached))
        checks.append({
            "name": "submission_references_wiki_doc",
            "passed": check3_passed,
            "detail": f"attachement_files='{attached}', expected to reference wiki doc_id='{wiki_doc_id}'"
        })
    else:
        checks.append({
            "name": "submission_references_wiki_doc",
            "passed": False,
            "detail": "Cannot check wiki reference because submission was not filed."
        })
        check3_passed = False
    
    # ─── CHECK 4: Content mentions Porter's Five Forces ────────────────────────
    # For "should we enter this industry" problems, Porter's Five Forces has HIGHEST priority
    content_lower = wiki_content.lower()
    porters_patterns = [
        r"porter",
        r"five forces",
        r"5 forces",
        r"five.force",
    ]
    check4_passed = any(re.search(p, content_lower) for p in porters_patterns)
    checks.append({
        "name": "uses_porters_five_forces_framework",
        "passed": check4_passed,
        "detail": "Wiki content should reference Porter's Five Forces as the primary MECE framework for market entry decisions."
                  if not check4_passed else "Porter's Five Forces framework detected in content."
    })
    
    # ─── CHECK 5: Two-layer decomposition present ──────────────────────────────
    # Look for evidence of first-layer and second-layer sub-problems
    has_layer1 = bool(re.search(r"(first.layer|layer.1|first.level|1st.layer|一级|sub.problem)", content_lower) or
                      re.search(r"(supplier|buyer|competitive|substitut|new entrant)", content_lower))
    # Porter's Five Forces gives 5 first-layer items; second layer should further break them down
    has_layer2 = bool(re.search(r"(second.layer|layer.2|second.level|2nd.layer|二级|sub-sub)", content_lower) or
                      # If there's a mermaid diagram with nested nodes, that counts
                      re.search(r"(-->|---|\|\s)", wiki_content))
    
    check5_passed = has_layer1 and has_layer2
    checks.append({
        "name": "two_layer_decomposition_present",
        "passed": check5_passed,
        "detail": f"Layer1 indicators found: {has_layer1}, Layer2 indicators found: {has_layer2}. "
                  "Both layers of MECE decomposition must be documented."
    })
    
    # ─── CHECK 6: Mermaid diagram present ─────────────────────────────────────
    mermaid_pattern = re.search(r"```mermaid", wiki_content, re.IGNORECASE)
    check6_passed = bool(mermaid_pattern)
    checks.append({
        "name": "mermaid_diagram_present",
        "passed": check6_passed,
        "detail": "Wiki content must include a Mermaid syntax tree diagram of the decomposition."
                  if not check6_passed else "Mermaid diagram block found in content."
    })
    
    # ─── CHECK 7: Second-layer sub-problems ≤ 3 per branch ────────────────────
    # Parse mermaid block if present and count child nodes per parent
    check7_passed = False
    check7_detail = "Could not verify second-layer constraint (no valid Mermaid block found)."
    
    if check6_passed:
        try:
            mermaid_match = re.search(r"```mermaid(.*?)```", wiki_content, re.DOTALL | re.IGNORECASE)
            if mermaid_match:
                mermaid_content = mermaid_match.group(1)
                # Extract edges: NodeA --> NodeB or NodeA --- NodeB
                edges = re.findall(r'(\w[\w\s]*?)\s*(?:-->|---)\s*(\w[\w\s]*)', mermaid_content)
                
                if edges:
                    # Build adjacency: parent -> list of children
                    from collections import defaultdict
                    children = defaultdict(set)
                    for parent, child in edges:
                        parent = parent.strip().split('\n')[-1].strip()
                        child = child.strip().split('\n')[0].strip()
                        if parent and child:
                            children[parent].add(child)
                    
                    # Find all second-layer nodes (children of root's children)
                    # Root is typically the first node; first-layer nodes are its children
                    # Second-layer nodes are children of first-layer nodes
                    # Count children for each first-layer node
                    violations = []
                    all_parents = set(children.keys())
                    
                    # The first-layer nodes are children of the root
                    # Find root: nodes that appear as parent but not as child
                    all_children_flat = set()
                    for ch_set in children.values():
                        all_children_flat.update(ch_set)
                    
                    roots = all_parents - all_children_flat
                    if not roots:
                        # Try to use first parent as root
                        first_edge_parent = edges[0][0].strip() if edges else None
                        roots = {first_edge_parent} if first_edge_parent else set()
                    
                    first_layer_nodes = set()
                    for root in roots:
                        first_layer_nodes.update(children.get(root, set()))
                    
                    # Check second-layer count for each first-layer node
                    for fl_node in first_layer_nodes:
                        fl_key = None
                        for k in children:
                            if fl_node.lower() in k.lower() or k.lower() in fl_node.lower():
                                fl_key = k
                                break
                        if fl_key:
                            sl_count = len(children[fl_key])
                            if sl_count > 3:
                                violations.append(f"Node '{fl_key}' has {sl_count} second-layer children (max 3)")
                    
                    if violations:
                        check7_passed = False
                        check7_detail = f"Second-layer constraint violated: {'; '.join(violations)}"
                    else:
                        check7_passed = True
                        check7_detail = f"All second-layer branches have ≤3 sub-problems. First-layer nodes checked: {list(first_layer_nodes)}"
                else:
                    # Fallback: just check that mermaid has content
                    check7_passed = len(mermaid_content.strip()) > 20
                    check7_detail = "Mermaid block present but edge parsing yielded no structured edges; assuming valid."
        except Exception as ex:
            check7_passed = False
            check7_detail = f"Error parsing mermaid content: {ex}"
    
    checks.append({
        "name": "second_layer_at_most_3_sub_problems",
        "passed": check7_passed,
        "detail": check7_detail
    })
    
    # ─── CHECK 8: Document explains decomposition rationale ───────────────────
    rationale_patterns = [
        r"(decomposition|decompose|principle|rationale|approach|methodology|reason)",
        r"(mece|mutually exclusive|collectively exhaustive)",
        r"(five forces|porter|competitive)",
    ]
    rationale_hits = sum(1 for p in rationale_patterns if re.search(p, content_lower))
    check8_passed = rationale_hits >= 2
    checks.append({
        "name": "decomposition_rationale_explained",
        "passed": check8_passed,
        "detail": f"Rationale pattern hits: {rationale_hits}/3. Document should explain MECE principles and decomposition thought process."
    })
    
    # ─── SCORING ──────────────────────────────────────────────────────────────
    # Critical checks (must pass for overall pass)
    critical = [
        checks[0]["passed"],   # wiki created
        checks[1]["passed"],   # submission filed
        checks[2]["passed"],   # submission references wiki
        checks[3]["passed"],   # Porter's Five Forces used
        checks[4]["passed"],   # two layers
        checks[5]["passed"],   # mermaid diagram
        checks[6]["passed"],   # ≤3 second-layer sub-problems
    ]
    
    all_checks_results = [c["passed"] for c in checks]
    score = sum(all_checks_results) / len(all_checks_results)
    overall_passed = all(critical)
    
    return {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "setup", "passed": False, "detail": "No workspace path provided"}]}))
        sys.exit(1)
    
    workspace_path = sys.argv[1]
    result = evaluate(workspace_path)
    print(json.dumps(result, indent=2))