import sys
import os
import json
import yaml
from pathlib import Path

def evaluate(workspace: str):
    checks = []
    total_score = 0.0

    contacts_dir = Path(workspace) / "memory" / "contacts" / "contacts.d"

    # === CHECK 1: zero-producer.yaml exists with all required fields ===
    def check_contact(contact_id, expected_name_fragment, expected_open_id, expected_nickname, expected_chat_id, expected_account_id, check_label):
        yaml_path = contacts_dir / f"{contact_id}.yaml"
        if not yaml_path.exists():
            return False, f"File {contact_id}.yaml not found in contacts.d/"
        try:
            with open(yaml_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except Exception as e:
            return False, f"Failed to parse YAML: {e}"

        issues = []

        # contact_id field
        if data.get("contact_id") != contact_id:
            issues.append(f"contact_id should be '{contact_id}', got '{data.get('contact_id')}'")

        # name field exists and contains expected fragment
        name = data.get("name", "")
        if not name or expected_name_fragment not in name:
            issues.append(f"name field missing or doesn't contain '{expected_name_fragment}', got '{name}'")

        # channels.feishu required sub-fields
        channels = data.get("channels", {})
        feishu = channels.get("feishu", {})

        if not feishu:
            issues.append("channels.feishu block is missing")
        else:
            if feishu.get("open_id") != expected_open_id:
                issues.append(f"open_id should be '{expected_open_id}', got '{feishu.get('open_id')}'")
            if feishu.get("nickname") != expected_nickname:
                issues.append(f"nickname should be '{expected_nickname}', got '{feishu.get('nickname')}'")
            if feishu.get("chat_id") != expected_chat_id:
                issues.append(f"chat_id should be '{expected_chat_id}', got '{feishu.get('chat_id')}'")
            if feishu.get("account_id") != expected_account_id:
                issues.append(f"account_id should be '{expected_account_id}', got '{feishu.get('account_id')}'")

        if issues:
            return False, "; ".join(issues)
        return True, "All required fields present and correct"

    # Check zero-producer
    passed_1, detail_1 = check_contact(
        contact_id="zero-producer",
        expected_name_fragment="零",
        expected_open_id="ou_z3r0pr0duc3r9988",
        expected_nickname="零·节拍",
        expected_chat_id="oc_visualremix_main",
        expected_account_id="zero_feishu_acct",
        check_label="zero-producer"
    )
    checks.append({"name": "zero-producer.yaml: all required fields correct", "passed": passed_1, "detail": detail_1})
    if passed_1:
        total_score += 0.25

    # Check acheng-pixel
    passed_2, detail_2 = check_contact(
        contact_id="acheng-pixel",
        expected_name_fragment="橙",
        expected_open_id="ou_ACH3NGp1x3L2077",
        expected_nickname="阿橙🎨",
        expected_chat_id="oc_visualremix_main",
        expected_account_id="acheng_pixel_fs",
        check_label="acheng-pixel"
    )
    checks.append({"name": "acheng-pixel.yaml: all required fields correct", "passed": passed_2, "detail": detail_2})
    if passed_2:
        total_score += 0.25

    # Check songwei-ops
    passed_3, detail_3 = check_contact(
        contact_id="songwei-ops",
        expected_name_fragment="宋微",
        expected_open_id="ou_S0NGW31ops5566",
        expected_nickname="宋微运营",
        expected_chat_id="oc_ops_collab_007",
        expected_account_id="songwei_ops_acct",
        check_label="songwei-ops"
    )
    checks.append({"name": "songwei-ops.yaml: all required fields correct", "passed": passed_3, "detail": detail_3})
    if passed_3:
        total_score += 0.25

    # === CHECK 4: YAML structure integrity — no required field stored as wrong type ===
    def check_yaml_types(contact_id):
        yaml_path = contacts_dir / f"{contact_id}.yaml"
        if not yaml_path.exists():
            return False, f"{contact_id}.yaml missing"
        try:
            with open(yaml_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except Exception as e:
            return False, f"YAML parse error: {e}"
        feishu = data.get("channels", {}).get("feishu", {})
        for field in ["open_id", "nickname", "chat_id", "account_id"]:
            val = feishu.get(field)
            if val is not None and not isinstance(val, str):
                return False, f"Field {field} should be a string, got {type(val).__name__}"
        if not isinstance(data.get("name", ""), str):
            return False, "name should be a string"
        return True, "Types OK"

    type_results = []
    for cid in ["zero-producer", "acheng-pixel", "songwei-ops"]:
        ok, msg = check_yaml_types(cid)
        type_results.append((ok, f"{cid}: {msg}"))
    all_types_ok = all(r[0] for r in type_results)
    checks.append({
        "name": "All 3 contacts: YAML field types are strings",
        "passed": all_types_ok,
        "detail": "; ".join(r[1] for r in type_results)
    })
    # No additional score for this — it's a quality gate captured within the field checks above

    # === CHECK 5: acheng_lookup.txt exists and contains acheng-pixel's open_id ===
    lookup_files = list(Path(workspace).rglob("acheng_lookup.txt"))
    if not lookup_files:
        checks.append({
            "name": "acheng_lookup.txt: file exists",
            "passed": False,
            "detail": "acheng_lookup.txt not found anywhere in workspace"
        })
    else:
        lookup_path = lookup_files[0]
        try:
            content = lookup_path.read_text(encoding="utf-8")
        except Exception as e:
            content = ""
            checks.append({
                "name": "acheng_lookup.txt: file exists",
                "passed": False,
                "detail": f"Could not read file: {e}"
            })
        else:
            checks.append({
                "name": "acheng_lookup.txt: file exists",
                "passed": True,
                "detail": f"Found at {lookup_path}"
            })

        # Must contain acheng-pixel's open_id
        has_open_id = "ou_ACH3NGp1x3L2077" in content
        # Must contain account_id
        has_account_id = "acheng_pixel_fs" in content
        # Must contain nickname
        has_nickname = "阿橙" in content

        checks.append({
            "name": "acheng_lookup.txt: contains acheng-pixel's open_id",
            "passed": has_open_id,
            "detail": f"open_id 'ou_ACH3NGp1x3L2077' {'found' if has_open_id else 'NOT found'} in lookup output"
        })
        checks.append({
            "name": "acheng_lookup.txt: contains acheng-pixel's account_id",
            "passed": has_account_id,
            "detail": f"account_id 'acheng_pixel_fs' {'found' if has_account_id else 'NOT found'} in lookup output"
        })
        checks.append({
            "name": "acheng_lookup.txt: contains acheng-pixel's nickname",
            "passed": has_nickname,
            "detail": f"nickname '阿橙' {'found' if has_nickname else 'NOT found'} in lookup output"
        })

        if has_open_id and has_account_id and has_nickname:
            total_score += 0.25

    # === CHECK 6: Original mala.yaml still intact (no side effects) ===
    mala_path = contacts_dir / "mala.yaml"
    try:
        with open(mala_path, "r", encoding="utf-8") as f:
            mala_data = yaml.safe_load(f)
        mala_intact = (
            mala_data.get("contact_id") == "mala" and
            mala_data.get("channels", {}).get("feishu", {}).get("open_id") == "ou_abc123def456"
        )
        checks.append({
            "name": "Original mala.yaml not corrupted",
            "passed": mala_intact,
            "detail": "mala.yaml still has correct contact_id and open_id" if mala_intact else "mala.yaml was modified or corrupted"
        })
    except Exception as e:
        checks.append({
            "name": "Original mala.yaml not corrupted",
            "passed": False,
            "detail": f"Could not read mala.yaml: {e}"
        })

    passed_all = all(c["passed"] for c in checks)

    result = {
        "passed": passed_all,
        "score": round(min(total_score, 1.0), 4),
        "checks": checks
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    evaluate(workspace)