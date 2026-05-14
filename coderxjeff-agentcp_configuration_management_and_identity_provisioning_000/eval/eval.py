import json
import sys
import os
import yaml
import re
from pathlib import Path

def load_json(path):
    with open(path, 'r') as f:
        return json.load(f)

def run_eval(workspace):
    HOME = os.path.expanduser("~")
    checks = []
    
    # --- Known fixed values from gen_inputs_script ---
    EXISTING_UUID = "a3f9c2d1-8b4e-4a7f-9c3d-2e1b5f0a6c4e"
    BROKEN_UUID = "d7e4b1a2-3c9f-4e8d-b2a1-7f6c0e5d9b3a"
    DEVICE_ID = "33ca5434ab12ef78901234567890abcd"
    OPENCLAW_JSON = f"{HOME}/.openclaw/openclaw.json"
    DEVICE_FILE = f"{HOME}/.openclaw/identities/{DEVICE_ID}.json"

    # ==========================================
    # CHECK GROUP 1: openclaw.json correctness
    # ==========================================

    try:
        cfg = load_json(OPENCLAW_JSON)
    except Exception as e:
        checks.append({"name": "openclaw.json is valid JSON", "passed": False, "detail": f"Could not read/parse openclaw.json: {e}"})
        result = {"passed": False, "score": 0.0, "checks": checks}
        print(json.dumps(result))
        return

    checks.append({"name": "openclaw.json is valid JSON", "passed": True, "detail": "File parsed successfully."})

    # CHECK 1.1: agents.list must contain "data-bot"
    try:
        agent_ids = [a.get("id") for a in cfg.get("agents", {}).get("list", [])]
        has_data_bot = "data-bot" in agent_ids
        checks.append({
            "name": "agents.list[] contains 'data-bot' entry",
            "passed": has_data_bot,
            "detail": f"agents.list ids found: {agent_ids}"
        })
    except Exception as e:
        checks.append({"name": "agents.list[] contains 'data-bot' entry", "passed": False, "detail": str(e)})

    # CHECK 1.2: agents.list must contain "research-bot" (the NEW identity)
    try:
        has_research_bot = "research-bot" in agent_ids
        checks.append({
            "name": "agents.list[] contains 'research-bot' entry (new identity)",
            "passed": has_research_bot,
            "detail": f"agents.list ids found: {agent_ids}"
        })
    except Exception as e:
        checks.append({"name": "agents.list[] contains 'research-bot' entry (new identity)", "passed": False, "detail": str(e)})

    # CHECK 1.3: channels.acp.identities must still contain BROKEN_UUID with agentId=data-bot
    try:
        identities = cfg.get("channels", {}).get("acp", {}).get("identities", {})
        broken_entry = identities.get(BROKEN_UUID)
        broken_ok = broken_entry is not None and broken_entry.get("agentId") == "data-bot"
        checks.append({
            "name": f"channels.acp.identities still contains data-bot entry (UUID {BROKEN_UUID[:8]}...)",
            "passed": broken_ok,
            "detail": f"Entry found: {broken_entry}"
        })
    except Exception as e:
        checks.append({"name": "channels.acp.identities data-bot entry preserved", "passed": False, "detail": str(e)})

    # CHECK 1.4: channels.acp.identities must contain a NEW entry for research-bot
    try:
        research_bot_entries = [
            (uid, entry) for uid, entry in identities.items()
            if entry.get("agentId") == "research-bot"
        ]
        has_research_identity = len(research_bot_entries) == 1
        research_bot_uuid = research_bot_entries[0][0] if research_bot_entries else None
        research_bot_entry = research_bot_entries[0][1] if research_bot_entries else None
        checks.append({
            "name": "channels.acp.identities contains new 'research-bot' identity entry",
            "passed": has_research_identity,
            "detail": f"Found {len(research_bot_entries)} research-bot entries. UUID: {research_bot_uuid}"
        })
    except Exception as e:
        research_bot_uuid = None
        research_bot_entry = None
        checks.append({"name": "channels.acp.identities research-bot entry", "passed": False, "detail": str(e)})

    # CHECK 1.5: research-bot identity must have agentMdPath following the correct pattern
    try:
        if research_bot_entry:
            amd_path = research_bot_entry.get("agentMdPath", "")
            # Must follow ~/.acp-storage/AIDs/research-bot.agentcp.io/public/agent.md
            path_ok = "research-bot.agentcp.io" in amd_path and "agent.md" in amd_path
            checks.append({
                "name": "research-bot agentMdPath follows correct pattern",
                "passed": path_ok,
                "detail": f"agentMdPath: {amd_path}"
            })
        else:
            checks.append({"name": "research-bot agentMdPath follows correct pattern", "passed": False, "detail": "No research-bot entry found."})
    except Exception as e:
        checks.append({"name": "research-bot agentMdPath follows correct pattern", "passed": False, "detail": str(e)})

    # CHECK 1.6: strict mode enabled
    try:
        binding_mode = cfg.get("channels", {}).get("acp", {}).get("agentAidBindingMode", "strict")
        strict_ok = binding_mode == "strict"
        checks.append({
            "name": "agentAidBindingMode is 'strict'",
            "passed": strict_ok,
            "detail": f"agentAidBindingMode: {binding_mode}"
        })
    except Exception as e:
        checks.append({"name": "agentAidBindingMode is 'strict'", "passed": False, "detail": str(e)})

    # CHECK 1.7: bindings[] must have entry for BROKEN_UUID/data-bot (THE PROPRIETARY TRAP - fix the missing binding)
    try:
        bindings = cfg.get("bindings", [])
        data_bot_binding = [
            b for b in bindings
            if b.get("agentId") == "data-bot"
            and b.get("match", {}).get("channel") == "acp"
            and b.get("match", {}).get("accountId") == BROKEN_UUID
        ]
        has_data_bot_binding = len(data_bot_binding) == 1
        checks.append({
            "name": f"bindings[] contains correct 1:1 entry for data-bot <-> {BROKEN_UUID[:8]}... (strict mode fix)",
            "passed": has_data_bot_binding,
            "detail": f"Found matching bindings: {data_bot_binding}"
        })
    except Exception as e:
        checks.append({"name": "bindings[] data-bot binding", "passed": False, "detail": str(e)})

    # CHECK 1.8: bindings[] must have entry for research-bot (new identity) - 1:1 strict requirement
    try:
        if research_bot_uuid:
            research_bindings = [
                b for b in bindings
                if b.get("agentId") == "research-bot"
                and b.get("match", {}).get("channel") == "acp"
                and b.get("match", {}).get("accountId") == research_bot_uuid
            ]
            has_research_binding = len(research_bindings) == 1
            checks.append({
                "name": "bindings[] contains correct 1:1 entry for research-bot (strict mode)",
                "passed": has_research_binding,
                "detail": f"research-bot UUID: {research_bot_uuid}, matching bindings: {research_bindings}"
            })
        else:
            checks.append({
                "name": "bindings[] contains correct 1:1 entry for research-bot (strict mode)",
                "passed": False,
                "detail": "Cannot check: research-bot UUID not found in identities."
            })
    except Exception as e:
        checks.append({"name": "bindings[] research-bot binding", "passed": False, "detail": str(e)})

    # CHECK 1.9: existing assistant-bot binding still intact
    try:
        assistant_bindings = [
            b for b in bindings
            if b.get("agentId") == "assistant-bot"
            and b.get("match", {}).get("channel") == "acp"
            and b.get("match", {}).get("accountId") == EXISTING_UUID
        ]
        has_assistant_binding = len(assistant_bindings) == 1
        checks.append({
            "name": "bindings[] existing assistant-bot entry preserved",
            "passed": has_assistant_binding,
            "detail": f"Matching bindings: {assistant_bindings}"
        })
    except Exception as e:
        checks.append({"name": "bindings[] assistant-bot entry preserved", "passed": False, "detail": str(e)})

    # CHECK 1.10: No duplicate bindings (strict 1:1)
    try:
        all_agent_ids_in_bindings = [b.get("agentId") for b in bindings if b.get("match", {}).get("channel") == "acp"]
        no_duplicates = len(all_agent_ids_in_bindings) == len(set(all_agent_ids_in_bindings))
        all_account_ids_in_bindings = [b.get("match", {}).get("accountId") for b in bindings if b.get("match", {}).get("channel") == "acp"]
        no_dup_accounts = len(all_account_ids_in_bindings) == len(set(all_account_ids_in_bindings))
        checks.append({
            "name": "No duplicate agent or account IDs in bindings (1:1 strict)",
            "passed": no_duplicates and no_dup_accounts,
            "detail": f"agentIds: {all_agent_ids_in_bindings}, accountIds: {all_account_ids_in_bindings}"
        })
    except Exception as e:
        checks.append({"name": "No duplicate bindings", "passed": False, "detail": str(e)})

    # ==========================================
    # CHECK GROUP 2: Device identity file
    # ==========================================

    try:
        dev_cfg = load_json(DEVICE_FILE)
    except Exception as e:
        checks.append({"name": "Device identity file is valid JSON", "passed": False, "detail": str(e)})
        dev_cfg = None

    if dev_cfg is not None:
        checks.append({"name": "Device identity file is valid JSON", "passed": True, "detail": "Parsed successfully."})

        # CHECK 2.1: data-bot identity entry added to device file
        try:
            dev_identities = dev_cfg.get("identities", [])
            dev_ids = [i.get("id") for i in dev_identities]
            has_broken_in_device = BROKEN_UUID in dev_ids
            checks.append({
                "name": f"Device identity file contains entry for data-bot (UUID {BROKEN_UUID[:8]}...)",
                "passed": has_broken_in_device,
                "detail": f"IDs in device file: {dev_ids}"
            })
        except Exception as e:
            checks.append({"name": "Device identity file data-bot entry", "passed": False, "detail": str(e)})

        # CHECK 2.2: data-bot entry has channels: ["acp"]
        try:
            dev_identities = dev_cfg.get("identities", [])
            data_bot_dev = next((i for i in dev_identities if i.get("id") == BROKEN_UUID), None)
            if data_bot_dev:
                channels_ok = data_bot_dev.get("channels") == ["acp"]
                checks.append({
                    "name": "data-bot device entry has channels: ['acp']",
                    "passed": channels_ok,
                    "detail": f"channels: {data_bot_dev.get('channels')}"
                })
            else:
                checks.append({"name": "data-bot device entry has channels: ['acp']", "passed": False, "detail": "Entry not found."})
        except Exception as e:
            checks.append({"name": "data-bot device entry channels field", "passed": False, "detail": str(e)})

        # CHECK 2.3: research-bot entry added to device file
        try:
            dev_identities = dev_cfg.get("identities", [])
            dev_ids = [i.get("id") for i in dev_identities]
            research_in_device = research_bot_uuid and research_bot_uuid in dev_ids
            checks.append({
                "name": "Device identity file contains entry for research-bot",
                "passed": bool(research_in_device),
                "detail": f"research-bot UUID: {research_bot_uuid}, IDs in device file: {dev_ids}"
            })
        except Exception as e:
            checks.append({"name": "Device identity file research-bot entry", "passed": False, "detail": str(e)})

        # CHECK 2.4: research-bot device entry has channels: ["acp"]
        try:
            dev_identities = dev_cfg.get("identities", [])
            research_dev = next((i for i in dev_identities if i.get("id") == research_bot_uuid), None) if research_bot_uuid else None
            if research_dev:
                channels_ok = research_dev.get("channels") == ["acp"]
                checks.append({
                    "name": "research-bot device entry has channels: ['acp']",
                    "passed": channels_ok,
                    "detail": f"channels: {research_dev.get('channels')}"
                })
            else:
                checks.append({"name": "research-bot device entry has channels: ['acp']", "passed": False, "detail": "Entry not found in device file."})
        except Exception as e:
            checks.append({"name": "research-bot device entry channels field", "passed": False, "detail": str(e)})

        # CHECK 2.5: existing assistant-bot entry still in device file
        try:
            dev_identities = dev_cfg.get("identities", [])
            dev_ids = [i.get("id") for i in dev_identities]
            assistant_still_there = EXISTING_UUID in dev_ids
            checks.append({
                "name": "Device identity file still contains existing assistant-bot entry",
                "passed": assistant_still_there,
                "detail": f"IDs in device file: {dev_ids}"
            })
        except Exception as e:
            checks.append({"name": "Device identity file assistant-bot preserved", "passed": False, "detail": str(e)})

    # ==========================================
    # CHECK GROUP 3: agent.md files
    # ==========================================

    # CHECK 3.1: data-bot agent.md must be valid (fix the broken one)
    data_bot_agent_md_path = f"{HOME}/.acp-storage/AIDs/data-bot.agentcp.io/public/agent.md"
    try:
        with open(data_bot_agent_md_path, 'r') as f:
            content = f.read()
        
        # Must have YAML frontmatter
        fm_match = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
        has_frontmatter = fm_match is not None
        checks.append({
            "name": "data-bot agent.md has YAML frontmatter",
            "passed": has_frontmatter,
            "detail": f"Content preview: {content[:200]}"
        })

        if has_frontmatter:
            try:
                fm = yaml.safe_load(fm_match.group(1))
                # Required fields check
                required_fields = ["aid", "name", "type", "version", "description"]
                missing = [f for f in required_fields if not fm.get(f)]
                all_required = len(missing) == 0
                checks.append({
                    "name": "data-bot agent.md has all required frontmatter fields (aid, name, type, version, description)",
                    "passed": all_required,
                    "detail": f"Missing fields: {missing}. Found: {list(fm.keys())}"
                })

                # type must be one of allowed values
                allowed_types = ["human", "assistant", "avatar", "openclaw", "codeagent"]
                type_val = fm.get("type", "")
                type_ok = type_val in allowed_types
                checks.append({
                    "name": "data-bot agent.md 'type' field is a valid allowed value",
                    "passed": type_ok,
                    "detail": f"type: '{type_val}', allowed: {allowed_types}"
                })

                # aid must match data-bot.agentcp.io
                aid_val = fm.get("aid", "")
                aid_ok = "data-bot.agentcp.io" in str(aid_val)
                checks.append({
                    "name": "data-bot agent.md 'aid' field matches data-bot.agentcp.io",
                    "passed": aid_ok,
                    "detail": f"aid: '{aid_val}'"
                })
            except Exception as e:
                checks.append({"name": "data-bot agent.md frontmatter parsing", "passed": False, "detail": str(e)})
        else:
            checks.append({"name": "data-bot agent.md required fields", "passed": False, "detail": "No frontmatter found."})
            checks.append({"name": "data-bot agent.md type field", "passed": False, "detail": "No frontmatter found."})
            checks.append({"name": "data-bot agent.md aid field", "passed": False, "detail": "No frontmatter found."})

    except FileNotFoundError:
        checks.append({"name": "data-bot agent.md has YAML frontmatter", "passed": False, "detail": f"File not found: {data_bot_agent_md_path}"})
        checks.append({"name": "data-bot agent.md required fields", "passed": False, "detail": "File not found."})
        checks.append({"name": "data-bot agent.md type field", "passed": False, "detail": "File not found."})
        checks.append({"name": "data-bot agent.md aid field", "passed": False, "detail": "File not found."})
    except Exception as e:
        checks.append({"name": "data-bot agent.md has YAML frontmatter", "passed": False, "detail": str(e)})

    # CHECK 3.2: research-bot agent.md exists and is valid
    research_agent_md_path = f"{HOME}/.acp-storage/AIDs/research-bot.agentcp.io/public/agent.md"
    try:
        with open(research_agent_md_path, 'r') as f:
            content = f.read()
        
        fm_match = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
        has_frontmatter = fm_match is not None
        checks.append({
            "name": "research-bot agent.md exists with YAML frontmatter",
            "passed": has_frontmatter,
            "detail": f"Content preview: {content[:200]}"
        })

        if has_frontmatter:
            try:
                fm = yaml.safe_load(fm_match.group(1))
                required_fields = ["aid", "name", "type", "version", "description"]
                missing = [f for f in required_fields if not fm.get(f)]
                all_required = len(missing) == 0
                checks.append({
                    "name": "research-bot agent.md has all required frontmatter fields",
                    "passed": all_required,
                    "detail": f"Missing: {missing}. Found: {list(fm.keys())}"
                })

                allowed_types = ["human", "assistant", "avatar", "openclaw", "codeagent"]
                type_val = fm.get("type", "")
                type_ok = type_val in allowed_types
                checks.append({
                    "name": "research-bot agent.md 'type' field is valid",
                    "passed": type_ok,
                    "detail": f"type: '{type_val}'"
                })

                aid_val = fm.get("aid", "")
                aid_ok = "research-bot.agentcp.io" in str(aid_val)
                checks.append({
                    "name": "research-bot agent.md 'aid' matches research-bot.agentcp.io",
                    "passed": aid_ok,
                    "detail": f"aid: '{aid_val}'"
                })
            except Exception as e:
                checks.append({"name": "research-bot agent.md frontmatter parsing", "passed": False, "detail": str(e)})
        else:
            checks.append({"name": "research-bot agent.md required fields", "passed": False, "detail": "No frontmatter."})
            checks.append({"name": "research-bot agent.md type field", "passed": False, "detail": "No frontmatter."})
            checks.append({"name": "research-bot agent.md aid field", "passed": False, "detail": "No frontmatter."})

    except FileNotFoundError:
        checks.append({"name": "research-bot agent.md exists with YAML frontmatter", "passed": False, "detail": f"File not found: {research_agent_md_path}"})
        checks.append({"name": "research-bot agent.md required fields", "passed": False, "detail": "File not found."})
        checks.append({"name": "research-bot agent.md type field", "passed": False, "detail": "File not found."})
        checks.append({"name": "research-bot agent.md aid field", "passed": False, "detail": "File not found."})
    except Exception as e:
        checks.append({"name": "research-bot agent.md exists with YAML frontmatter", "passed": False, "detail": str(e)})

    # ==========================================
    # CHECK GROUP 4: Workspace files for new identities
    # ==========================================

    # CHECK 4.1: research-bot workspace exists with IDENTITY.md
    research_workspace = f"{HOME}/.openclaw/workspace-research-bot"
    identity_md_path = f"{research_workspace}/IDENTITY.md"
    try:
        exists = os.path.isfile(identity_md_path)
        checks.append({
            "name": "research-bot workspace IDENTITY.md exists",
            "passed": exists,
            "detail": f"Path: {identity_md_path}"
        })
    except Exception as e:
        checks.append({"name": "research-bot workspace IDENTITY.md exists", "passed": False, "detail": str(e)})

    # CHECK 4.2: research-bot workspace has SOUL.md
    soul_md_path = f"{research_workspace}/SOUL.md"
    try:
        exists = os.path.isfile(soul_md_path)
        checks.append({
            "name": "research-bot workspace SOUL.md exists",
            "passed": exists,
            "detail": f"Path: {soul_md_path}"
        })
    except Exception as e:
        checks.append({"name": "research-bot workspace SOUL.md exists", "passed": False, "detail": str(e)})

    # ==========================================
    # SCORING
    # ==========================================
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 3) if total > 0 else 0.0
    overall_passed = score >= 0.85

    result = {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~")
    run_eval(workspace)