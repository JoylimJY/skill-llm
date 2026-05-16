import json
import sys
import os
from pathlib import Path

def evaluate(workspace_dir):
    checks = []
    total_score = 0.0
    max_score = 0.0

    # Find the output file
    config_files = list(Path(workspace_dir).rglob("workspace_config.json"))
    
    if not config_files:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "file_exists", "passed": False, "detail": "workspace_config.json not found anywhere in workspace"}]
        }
    
    # Use the most recently modified one if multiple
    config_path = sorted(config_files, key=lambda p: p.stat().st_mtime, reverse=True)[0]
    
    checks.append({"name": "file_exists", "passed": True, "detail": f"Found at {config_path}"})
    total_score += 1.0
    max_score += 1.0

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
    except Exception as e:
        return {
            "passed": False,
            "score": total_score / (max_score + 10),
            "checks": checks + [{"name": "valid_json", "passed": False, "detail": f"Failed to parse JSON: {e}"}]
        }
    
    checks.append({"name": "valid_json", "passed": True, "detail": "File is valid JSON"})
    total_score += 1.0
    max_score += 1.0

    # =====================================================================
    # CHECK 1: Bitable fields - must include correct field types from bitable.md
    # Expected fields: 任务名称(文本), 负责人(人员), 状态(选项), 截止日期(日期), 进度(数字)
    # The proprietary trap: agent must use the EXACT Chinese field type names from the docs
    # =====================================================================
    max_score += 3.0
    try:
        fields = config.get("bitable_fields", [])
        if not isinstance(fields, list) or len(fields) < 4:
            checks.append({"name": "bitable_fields_count", "passed": False, 
                          "detail": f"Expected at least 4 bitable fields, got {len(fields) if isinstance(fields, list) else 'non-list'}"})
        else:
            checks.append({"name": "bitable_fields_count", "passed": True, 
                          "detail": f"Found {len(fields)} fields"})
            total_score += 0.5

        # Check for required field types from bitable.md
        # Valid types: 文本, 数字, 选项, 日期, 人员, 文件, 复选框, 电话, 邮箱, 网址, 关联, 公式, 自动编号
        valid_types = {"文本", "数字", "选项", "日期", "人员", "文件", "复选框", "电话", "邮箱", "网址", "关联", "公式", "自动编号", "创建时间", "创建人", "修改时间", "修改人", "查找引用"}
        
        field_types_found = set()
        for field in fields:
            if isinstance(field, dict):
                ft = field.get("type", "")
                if ft in valid_types:
                    field_types_found.add(ft)
        
        # Must have 人员 type for assignee field
        if "人员" in field_types_found:
            checks.append({"name": "bitable_field_type_人员", "passed": True, "detail": "Found 人员 field type for assignee"})
            total_score += 0.5
        else:
            checks.append({"name": "bitable_field_type_人员", "passed": False, "detail": f"Missing 人员 field type. Found types: {field_types_found}"})
        
        # Must have 选项 type for status field
        if "选项" in field_types_found:
            checks.append({"name": "bitable_field_type_选项", "passed": True, "detail": "Found 选项 field type for status"})
            total_score += 0.5
        else:
            checks.append({"name": "bitable_field_type_选项", "passed": False, "detail": f"Missing 选项 field type. Found types: {field_types_found}"})
        
        # Must have 日期 type for due date field
        if "日期" in field_types_found:
            checks.append({"name": "bitable_field_type_日期", "passed": True, "detail": "Found 日期 field type for due date"})
            total_score += 0.5
        else:
            checks.append({"name": "bitable_field_type_日期", "passed": False, "detail": f"Missing 日期 field type. Found types: {field_types_found}"})
        
        # Validate all used types are from the official list
        all_field_types = [f.get("type", "") for f in fields if isinstance(f, dict)]
        invalid_types = [t for t in all_field_types if t and t not in valid_types]
        if not invalid_types:
            checks.append({"name": "bitable_field_types_valid", "passed": True, "detail": "All field types are from official bitable.md list"})
            total_score += 0.5
        else:
            checks.append({"name": "bitable_field_types_valid", "passed": False, "detail": f"Invalid/non-standard field types used: {invalid_types}"})

    except Exception as e:
        checks.append({"name": "bitable_fields_check", "passed": False, "detail": f"Error checking bitable fields: {e}"})

    # =====================================================================
    # CHECK 2: Automation rules - must use exact trigger names from bitable.md/automation.md
    # Valid triggers: "记录创建时", "记录更新时", "记录满足条件时", "定时触发"
    # =====================================================================
    max_score += 3.0
    try:
        automations = config.get("automations", [])
        valid_triggers = {"记录创建时", "记录更新时", "记录满足条件时", "定时触发"}
        valid_actions = {"发送通知", "更新字段", "创建记录", "发送消息"}
        
        if not isinstance(automations, list) or len(automations) < 2:
            checks.append({"name": "automations_count", "passed": False, 
                          "detail": f"Expected at least 2 automation rules, got {len(automations) if isinstance(automations, list) else 'non-list'}"})
        else:
            checks.append({"name": "automations_count", "passed": True, 
                          "detail": f"Found {len(automations)} automation rules"})
            total_score += 0.5

        # Check for "记录创建时" trigger (notify assignee on task creation)
        triggers_found = []
        for a in automations:
            if isinstance(a, dict):
                t = a.get("trigger", "")
                triggers_found.append(t)
        
        if "记录创建时" in triggers_found:
            checks.append({"name": "automation_trigger_记录创建时", "passed": True, 
                          "detail": "Found '记录创建时' trigger for new task notification"})
            total_score += 0.75
        else:
            checks.append({"name": "automation_trigger_记录创建时", "passed": False, 
                          "detail": f"Missing '记录创建时' trigger. Found: {triggers_found}"})
        
        # Check for "记录满足条件时" OR "记录更新时" trigger (status change to completed)
        if "记录满足条件时" in triggers_found or "记录更新时" in triggers_found:
            checks.append({"name": "automation_trigger_status_change", "passed": True, 
                          "detail": "Found appropriate trigger for status change notification"})
            total_score += 0.75
        else:
            checks.append({"name": "automation_trigger_status_change", "passed": False, 
                          "detail": f"Missing trigger for status change. Found: {triggers_found}. Expected '记录满足条件时' or '记录更新时'"})
        
        # Validate all triggers are from official list
        invalid_triggers = [t for t in triggers_found if t and t not in valid_triggers]
        if not invalid_triggers:
            checks.append({"name": "automation_triggers_valid", "passed": True, 
                          "detail": "All automation triggers use official names from documentation"})
            total_score += 1.0
        else:
            checks.append({"name": "automation_triggers_valid", "passed": False, 
                          "detail": f"Non-standard trigger names found: {invalid_triggers}. Valid triggers: {valid_triggers}"})

    except Exception as e:
        checks.append({"name": "automations_check", "passed": False, "detail": f"Error checking automations: {e}"})

    # =====================================================================
    # CHECK 3: Webhook card message - must use correct JSON structure from automation.md
    # Specifically: msg_type = "interactive", card.elements[].tag = "div"
    # =====================================================================
    max_score += 3.0
    try:
        webhook_msg = config.get("webhook_card_message", None)
        
        if webhook_msg is None:
            checks.append({"name": "webhook_message_exists", "passed": False, 
                          "detail": "Missing 'webhook_card_message' key in config"})
        else:
            checks.append({"name": "webhook_message_exists", "passed": True, 
                          "detail": "webhook_card_message field present"})
            total_score += 0.5
            
            # Must have msg_type = "interactive" (from automation.md card message spec)
            msg_type = webhook_msg.get("msg_type", "")
            if msg_type == "interactive":
                checks.append({"name": "webhook_msg_type_interactive", "passed": True, 
                              "detail": "msg_type correctly set to 'interactive' for card message"})
                total_score += 1.0
            else:
                checks.append({"name": "webhook_msg_type_interactive", "passed": False, 
                              "detail": f"msg_type should be 'interactive' for card message, got: '{msg_type}'"})
            
            # Must have card.elements structure
            card = webhook_msg.get("card", {})
            elements = card.get("elements", []) if isinstance(card, dict) else []
            
            if isinstance(elements, list) and len(elements) > 0:
                checks.append({"name": "webhook_card_elements", "passed": True, 
                              "detail": f"card.elements present with {len(elements)} element(s)"})
                total_score += 0.75
                
                # Check that element uses tag: "div" (from automation.md)
                first_elem = elements[0] if elements else {}
                if isinstance(first_elem, dict) and first_elem.get("tag") == "div":
                    checks.append({"name": "webhook_card_element_tag_div", "passed": True, 
                                  "detail": "First card element uses tag 'div' as per automation.md spec"})
                    total_score += 0.75
                else:
                    checks.append({"name": "webhook_card_element_tag_div", "passed": False, 
                                  "detail": f"First card element should have tag 'div', got: {first_elem.get('tag', 'missing')}"})
            else:
                checks.append({"name": "webhook_card_elements", "passed": False, 
                              "detail": "card.elements is missing or empty in webhook_card_message"})

    except Exception as e:
        checks.append({"name": "webhook_message_check", "passed": False, "detail": f"Error checking webhook message: {e}"})

    # =====================================================================
    # CHECK 4: Permission assignments - must use EXACT permission level names from permissions.md
    # Official levels: "查看权限", "编辑权限", "完全权限", "管理权限", "所有者权限"
    # Dave Chen -> "查看权限" (view only)
    # Bob Li, Carol Wang -> "编辑权限" (can edit, but NOT invite collaborators)
    # Alice Zhang -> "完全权限" (can invite collaborators, manage comments, but NOT manage permissions)
    # Eve Liu -> "所有者权限" (highest, can transfer ownership)
    # =====================================================================
    max_score += 5.0
    try:
        permissions = config.get("permissions", {})
        
        if not isinstance(permissions, dict) or len(permissions) < 4:
            checks.append({"name": "permissions_structure", "passed": False, 
                          "detail": f"permissions must be a dict with at least 4 members, got: {type(permissions).__name__}"})
        else:
            checks.append({"name": "permissions_structure", "passed": True, 
                          "detail": f"Permissions dict present with {len(permissions)} entries"})
            total_score += 0.5

        valid_permission_levels = {"查看权限", "编辑权限", "完全权限", "管理权限", "所有者权限"}
        
        # Helper to find permission by name fragment
        def find_perm(permissions_dict, name_fragment):
            for key, val in permissions_dict.items():
                if name_fragment.lower() in key.lower():
                    return val
            return None

        # Dave Chen -> 查看权限 (view only, no editing per requirements)
        dave_perm = find_perm(permissions, "Dave")
        if dave_perm == "查看权限":
            checks.append({"name": "perm_dave_view", "passed": True, 
                          "detail": "Dave Chen correctly assigned '查看权限'"})
            total_score += 1.0
        else:
            checks.append({"name": "perm_dave_view", "passed": False, 
                          "detail": f"Dave Chen should have '查看权限' (view only), got: '{dave_perm}'"})
        
        # Bob Li -> 编辑权限 (can edit but NOT invite per permissions.md table: 邀请协作 requires 完全权限+)
        bob_perm = find_perm(permissions, "Bob")
        if bob_perm == "编辑权限":
            checks.append({"name": "perm_bob_edit", "passed": True, 
                          "detail": "Bob Li correctly assigned '编辑权限'"})
            total_score += 0.75
        else:
            checks.append({"name": "perm_bob_edit", "passed": False, 
                          "detail": f"Bob Li should have '编辑权限', got: '{bob_perm}'"})

        # Carol Wang -> 编辑权限
        carol_perm = find_perm(permissions, "Carol")
        if carol_perm == "编辑权限":
            checks.append({"name": "perm_carol_edit", "passed": True, 
                          "detail": "Carol Wang correctly assigned '编辑权限'"})
            total_score += 0.75
        else:
            checks.append({"name": "perm_carol_edit", "passed": False, 
                          "detail": f"Carol Wang should have '编辑权限', got: '{carol_perm}'"})

        # Alice Zhang -> 完全权限 (can invite collaborators, manage comments, but NOT manage permissions)
        # From permissions.md table: 邀请协作(✓) at 完全权限 level, but 管理权限(✗)
        alice_perm = find_perm(permissions, "Alice")
        if alice_perm == "完全权限":
            checks.append({"name": "perm_alice_full", "passed": True, 
                          "detail": "Alice Zhang correctly assigned '完全权限' (can invite, manage comments, but not manage permissions)"})
            total_score += 1.0
        elif alice_perm == "管理权限":
            checks.append({"name": "perm_alice_full", "passed": False, 
                          "detail": "Alice Zhang got '管理权限' but requirements say she CANNOT manage permissions — should be '完全权限'"})
        else:
            checks.append({"name": "perm_alice_full", "passed": False, 
                          "detail": f"Alice Zhang should have '完全权限', got: '{alice_perm}'"})

        # Eve Liu -> 所有者权限 (highest, can transfer ownership per permissions.md)
        eve_perm = find_perm(permissions, "Eve")
        if eve_perm == "所有者权限":
            checks.append({"name": "perm_eve_owner", "passed": True, 
                          "detail": "Eve Liu correctly assigned '所有者权限' (highest, can transfer ownership)"})
            total_score += 1.0
        elif eve_perm == "管理权限":
            checks.append({"name": "perm_eve_owner", "passed": False, 
                          "detail": "Eve Liu got '管理权限' but requirements specify 'including ownership transfer' — must be '所有者权限'"})
        else:
            checks.append({"name": "perm_eve_owner", "passed": False, 
                          "detail": f"Eve Liu should have '所有者权限', got: '{eve_perm}'"})
        
        # Check all permission values are from official list
        all_perms = list(permissions.values())
        invalid_perms = [p for p in all_perms if p and p not in valid_permission_levels]
        if not invalid_perms:
            checks.append({"name": "permissions_use_official_names", "passed": True, 
                          "detail": "All permission levels use official names from permissions.md"})
            total_score += 0.0  # bonus already counted above
        else:
            checks.append({"name": "permissions_use_official_names", "passed": False, 
                          "detail": f"Non-standard permission level names: {invalid_perms}. Valid: {valid_permission_levels}"})

    except Exception as e:
        checks.append({"name": "permissions_check", "passed": False, "detail": f"Error checking permissions: {e}"})

    # Final scoring
    final_score = total_score / max_score if max_score > 0 else 0.0
    final_score = min(1.0, final_score)
    passed = final_score >= 0.75

    return {
        "passed": passed,
        "score": round(final_score, 4),
        "checks": checks
    }


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))