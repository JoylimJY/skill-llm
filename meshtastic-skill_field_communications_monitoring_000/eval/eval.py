import sys
import json
import re
import os
from pathlib import Path

def run_eval(workspace_dir):
    workspace = Path(workspace_dir)
    checks = []
    total_score = 0.0

    # -------------------------------------------------------------------------
    # CHECK 1: mesh_report.json exists somewhere in workspace
    # -------------------------------------------------------------------------
    report_files = list(workspace.rglob("mesh_report.json"))
    if not report_files:
        checks.append({
            "name": "mesh_report.json_exists",
            "passed": False,
            "detail": "No mesh_report.json file found anywhere in workspace."
        })
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    report_path = report_files[0]
    checks.append({
        "name": "mesh_report.json_exists",
        "passed": True,
        "detail": f"Found at {report_path}"
    })
    total_score += 0.10

    # -------------------------------------------------------------------------
    # CHECK 2: mesh_report.json is valid JSON
    # -------------------------------------------------------------------------
    try:
        with open(report_path) as f:
            report = json.load(f)
        checks.append({
            "name": "mesh_report_valid_json",
            "passed": True,
            "detail": "File parses as valid JSON."
        })
        total_score += 0.05
    except Exception as e:
        checks.append({
            "name": "mesh_report_valid_json",
            "passed": False,
            "detail": f"JSON parse error: {e}"
        })
        print(json.dumps({"passed": False, "score": total_score, "checks": checks}))
        return

    # -------------------------------------------------------------------------
    # CHECK 3: Report contains filtered messages (noise excluded)
    # Noise: Hello!, hey, mqtt-test
    # The report must NOT include noisy message senders/texts
    # -------------------------------------------------------------------------
    noise_senders = {"!11111111", "!22222222", "!33333333", "!44444444", "!55555555",
                     "!66666666", "!77777777", "!88888888", "!99999999"}
    noise_texts_pattern = re.compile(r'\b(Hello!|hey|mqtt-test)\b', re.IGNORECASE)

    report_str = json.dumps(report).lower()

    # Check that no noise sender IDs appear in the report as senders of filtered messages
    noise_found = False
    for ns in noise_senders:
        if ns.lower() in report_str:
            # This could be incidental - check if noise text also near it
            pass  # We'll do a looser check below

    # More direct: the report should not list Hello!/hey/mqtt-test as interesting messages
    noise_text_in_report = bool(noise_texts_pattern.search(json.dumps(report)))
    
    if not noise_text_in_report:
        checks.append({
            "name": "noise_messages_excluded",
            "passed": True,
            "detail": "No noise messages (Hello!, hey, mqtt-test) appear in report."
        })
        total_score += 0.15
    else:
        checks.append({
            "name": "noise_messages_excluded",
            "passed": False,
            "detail": "Report still contains noise messages (Hello!, hey, or mqtt-test)."
        })

    # -------------------------------------------------------------------------
    # CHECK 4: Report includes interesting messages
    # Interesting senders: !a1b2c3d4, !b2c3d4e5, !c3d4e5f6, !d4e5f6a7,
    #                      !e5f6a7b8, !f6a7b8c9, !a7b8c9d0, !b8c9d0e1
    # At least 5 of these should be represented in the report
    # -------------------------------------------------------------------------
    interesting_senders = [
        "!a1b2c3d4", "!b2c3d4e5", "!c3d4e5f6", "!d4e5f6a7",
        "!e5f6a7b8", "!f6a7b8c9", "!a7b8c9d0", "!b8c9d0e1"
    ]
    report_str_raw = json.dumps(report)
    found_interesting = [s for s in interesting_senders if s in report_str_raw]
    
    if len(found_interesting) >= 5:
        checks.append({
            "name": "interesting_messages_included",
            "passed": True,
            "detail": f"Found {len(found_interesting)} interesting senders in report: {found_interesting}"
        })
        total_score += 0.15
    else:
        checks.append({
            "name": "interesting_messages_included",
            "passed": False,
            "detail": f"Only {len(found_interesting)} interesting senders found; need at least 5. Found: {found_interesting}"
        })

    # -------------------------------------------------------------------------
    # CHECK 5: Report contains distance-based region classification
    # The skill's distance table must be applied:
    # <500km -> neighboring, 500-1000 -> medium, 1000-1500 -> long,
    # 1500-2000 -> very long, >2000 -> MQTT-bridged
    # Check for presence of distance/region data in report
    # -------------------------------------------------------------------------
    # Look for region keywords or distance data structure
    region_keywords = ["neighbor", "medium", "long", "mqtt", "bridged", "range", "region",
                       "km", "distance", "<500", "500", "1000", "1500", "2000"]
    report_lower = report_str_raw.lower()
    region_kw_found = [kw for kw in region_keywords if kw in report_lower]

    # Check for actual distance values from the data
    distance_values_expected = ["387", "654", "1243", "1876", "2341", "892", "1102", "1654", "3102", "445"]
    dist_found = [d for d in distance_values_expected if d in report_str_raw]

    if len(dist_found) >= 5 or len(region_kw_found) >= 3:
        checks.append({
            "name": "distance_region_classification",
            "passed": True,
            "detail": f"Distance/region data present. Distances found: {dist_found}, Region keywords: {region_kw_found}"
        })
        total_score += 0.15
    else:
        checks.append({
            "name": "distance_region_classification",
            "passed": False,
            "detail": f"Insufficient distance/region data. Distances: {dist_found}, Keywords: {region_kw_found}"
        })

    # -------------------------------------------------------------------------
    # CHECK 6: Node listing from bridge socket query
    # Report should contain nodes from /tmp/mesh_nodes.json (obtained via {"cmd":"nodes"})
    # At least 6 node IDs should appear
    # -------------------------------------------------------------------------
    node_ids_expected = [
        "!a1b2c3d4", "!b2c3d4e5", "!c3d4e5f6", "!d4e5f6a7", "!e5f6a7b8",
        "!f6a7b8c9", "!a7b8c9d0", "!b8c9d0e1", "!c9d0e1f2", "!d0e1f2a3"
    ]
    nodes_in_report = [n for n in node_ids_expected if n in report_str_raw]

    if len(nodes_in_report) >= 6:
        checks.append({
            "name": "nodes_from_socket_query",
            "passed": True,
            "detail": f"Found {len(nodes_in_report)} node IDs in report from socket nodes query: {nodes_in_report}"
        })
        total_score += 0.15
    else:
        checks.append({
            "name": "nodes_from_socket_query",
            "passed": False,
            "detail": f"Only {len(nodes_in_report)} node IDs found in report; need >=6. Found: {nodes_in_report}"
        })

    # -------------------------------------------------------------------------
    # CHECK 7: A direct message was sent via socket to the most distant node
    # The most distant non-noise node is !e5f6a7b8 at 2341km
    # (or one of the top-distance nodes: !e5f6a7b8, !c9d0e1f2, !b8c9d0e1, !d4e5f6a7)
    # Check /tmp/mesh_sent.log for a "send" command with "to" being one of the top distant nodes
    # -------------------------------------------------------------------------
    SENT_LOG = "/tmp/mesh_sent.log"
    top_distant_nodes = {"!e5f6a7b8", "!c9d0e1f2", "!b8c9d0e1", "!d4e5f6a7"}
    
    try:
        sent_entries = []
        if os.path.exists(SENT_LOG):
            with open(SENT_LOG) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                        sent_entries.append(entry)
                    except:
                        pass

        # Check that at least one message was sent to a distant node
        sent_to_distant = [
            e for e in sent_entries
            if e.get("cmd") == "send" and e.get("to") in top_distant_nodes
        ]

        if sent_to_distant:
            checks.append({
                "name": "direct_message_sent_to_distant_node",
                "passed": True,
                "detail": f"Direct message sent via socket to distant node(s): {[e['to'] for e in sent_to_distant]}. Text: '{sent_to_distant[0].get('text', '')}'"
            })
            total_score += 0.15
        else:
            # Looser check: any "to" with ! prefix (not broadcast)
            sent_direct = [e for e in sent_entries if e.get("cmd") == "send" and e.get("to", "broadcast").startswith("!")]
            if sent_direct:
                checks.append({
                    "name": "direct_message_sent_to_distant_node",
                    "passed": False,
                    "detail": f"Direct message sent but not to a top-distant node. Sent to: {[e['to'] for e in sent_direct]}"
                })
            else:
                checks.append({
                    "name": "direct_message_sent_to_distant_node",
                    "passed": False,
                    "detail": f"No direct message found in /tmp/mesh_sent.log targeting a distant node. Log has {len(sent_entries)} entries."
                })
    except Exception as e:
        checks.append({
            "name": "direct_message_sent_to_distant_node",
            "passed": False,
            "detail": f"Error reading sent log: {e}"
        })

    # -------------------------------------------------------------------------
    # CHECK 8: Message text in the send command is non-empty and relevant
    # (not just empty or a test message)
    # -------------------------------------------------------------------------
    try:
        if os.path.exists(SENT_LOG):
            sent_entries_all = []
            with open(SENT_LOG) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        sent_entries_all.append(json.loads(line))
                    except:
                        pass
            
            meaningful_sends = [
                e for e in sent_entries_all
                if e.get("cmd") == "send"
                and len(e.get("text", "").strip()) > 5
                and e.get("to", "broadcast").startswith("!")
            ]
            
            if meaningful_sends:
                checks.append({
                    "name": "send_message_has_meaningful_text",
                    "passed": True,
                    "detail": f"Sent message with meaningful text: '{meaningful_sends[0].get('text', '')}' to {meaningful_sends[0].get('to')}"
                })
                total_score += 0.10
            else:
                checks.append({
                    "name": "send_message_has_meaningful_text",
                    "passed": False,
                    "detail": "No meaningful direct send found (text too short or not directed)."
                })
        else:
            checks.append({
                "name": "send_message_has_meaningful_text",
                "passed": False,
                "detail": "/tmp/mesh_sent.log does not exist."
            })
    except Exception as e:
        checks.append({
            "name": "send_message_has_meaningful_text",
            "passed": False,
            "detail": f"Error: {e}"
        })

    # -------------------------------------------------------------------------
    # Final scoring
    # -------------------------------------------------------------------------
    total_score = round(min(total_score, 1.0), 3)
    passed = total_score >= 0.65

    print(json.dumps({
        "passed": passed,
        "score": total_score,
        "checks": checks
    }, indent=2))


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    run_eval(workspace_dir)