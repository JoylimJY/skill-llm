import json
import os
import re
from pathlib import Path

workspace = Path(__file__).resolve().parent
if len(os.sys.argv) > 1:
    workspace = Path(os.sys.argv[1])

checks = []

def add_check(name, passed, detail):
    checks.append({"name": name, "passed": bool(passed), "detail": str(detail)})

try:
    triage_path = workspace / "cache" / "gmail-triage-labels.json"
    if not triage_path.exists():
        add_check("labels file exists", False, f"Missing file: {triage_path}")
        labels = None
    else:
        try:
            labels = json.loads(triage_path.read_text(encoding="utf-8"))
            add_check("labels file exists", True, f"Loaded {len(labels) if isinstance(labels, list) else 'non-list'} entries")
        except Exception as e:
            labels = None
            add_check("labels file parse", False, f"Could not parse JSON: {e}")

    if isinstance(labels, list):
        by_id = {}
        for item in labels:
            if isinstance(item, dict) and item.get("id"):
                by_id[str(item.get("id"))] = item

        expected = {
            "m-001": ("school", True),
            "m-002": ("school", True),
            "m-003": ("receipt", False),
            "m-004": ("admin", False),
            "m-005": ("clubs", True),
            "m-006": ("mayo", True),
            "m-007": ("read later", False),
            "m-008": ("school", True),
        }

        label_ok = True
        reply_ok = True
        missing = []
        for mid, (want_label, want_reply) in expected.items():
            item = by_id.get(mid)
            if not item:
                label_ok = False
                reply_ok = False
                missing.append(mid)
                continue
            labels_field = item.get("labels")
            label_field = item.get("label")
            text = " ".join([str(x) for x in (labels_field if isinstance(labels_field, list) else [label_field]) if x is not None])
            norm = re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()
            want_norm = re.sub(r"[^a-z0-9]+", " ", want_label.lower()).strip()
            if want_norm not in norm:
                label_ok = False
            needs_reply = item.get("needsReply")
            action = str(item.get("action") or "").lower()
            inferred = bool(needs_reply) or action == "reply"
            if inferred != want_reply:
                reply_ok = False
        add_check("expected messages present", len(missing) == 0, f"Missing ids: {missing}" if missing else "All expected ids found")
        add_check("labels are correct", label_ok, "Labels match expected categories with fuzzy normalization")
        add_check("reply flags are correct", reply_ok, "needsReply/action fields match expected reply requirements")

    drafts_path = workspace / "cache" / "gmail-drafts.md"
    if drafts_path.exists():
        try:
            txt = drafts_path.read_text(encoding="utf-8")
            ok = all(term.lower() in txt.lower() for term in ["ap calc", "science fair", "fbla", "mayo", "nhs"])
            add_check("draft queue mentions key items", ok, "Draft queue includes the main reply-worthy items" if ok else "Missing one or more expected draft topics")
        except Exception as e:
            add_check("draft queue mentions key items", False, f"Could not read drafts: {e}")
    else:
        add_check("draft queue mentions key items", False, f"Missing file: {drafts_path}")

    triage_md = workspace / "cache" / "gmail-triage.md"
    if triage_md.exists():
        try:
            txt = triage_md.read_text(encoding="utf-8")
            ok = "triage" in txt.lower() and any(k in txt.lower() for k in ["8 messages", "reviewed"])
            add_check("triage digest exists", ok, "Triage digest has summary text" if ok else "Digest content did not look right")
        except Exception as e:
            add_check("triage digest exists", False, f"Could not read triage digest: {e}")
    else:
        add_check("triage digest exists", False, f"Missing file: {triage_md}")

except Exception as e:
    add_check("top-level evaluator safety", False, f"Unexpected evaluator error: {e}")

passed = all(c["passed"] for c in checks) if checks else False
score = (sum(1 for c in checks if c["passed"]) / len(checks)) if checks else 0.0
print(json.dumps({"passed": passed, "score": score, "checks": checks}, ensure_ascii=False))