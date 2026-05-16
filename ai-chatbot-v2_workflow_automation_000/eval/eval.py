#!/usr/bin/env python3
"""
Evaluation script for the MedTech customer service initialization task.
Checks:
1. All 3 FAQ entries from medtech_faq_import.json were added to the knowledge base
2. The 3-turn conversation was conducted (including complaint/negative sentiment messages)
3. service_stats_report.json exists with valid system statistics data
"""

import sys
import json
import os
from pathlib import Path

def run_eval(workspace: str):
    checks = []
    total_score = 0.0
    max_score = 3.0

    # ── Helper ──────────────────────────────────────────────────────────────
    def make_check(name, passed, detail):
        return {"name": name, "passed": passed, "detail": detail}

    # ════════════════════════════════════════════════════════════════════════
    # CHECK 1: Knowledge Base contains all 3 MedTech FAQs
    # ════════════════════════════════════════════════════════════════════════
    EXPECTED_FAQS = [
        {
            "question": "血压计的保修期是多长时间？",
            "answer_keywords": ["2年", "质保", "维修"]
        },
        {
            "question": "设备出现故障如何申请维修？",
            "answer_keywords": ["400-800-1234", "48小时", "维修"]
        },
        {
            "question": "是否支持医院批量采购优惠？",
            "answer_keywords": ["8折", "批量", "10台"]
        },
    ]

    try:
        kb_path = Path.home() / ".ai_customer_service" / "knowledge_base.json"
        if not kb_path.exists():
            checks.append(make_check(
                "knowledge_base_faq_added",
                False,
                f"Knowledge base file not found at {kb_path}. The agent may not have called the add command."
            ))
        else:
            with open(kb_path, encoding='utf-8') as f:
                kb_entries = json.load(f)

            kb_questions = {entry.get("question", ""): entry.get("answer", "") for entry in kb_entries}

            missing_faqs = []
            wrong_answer_faqs = []

            for faq in EXPECTED_FAQS:
                q = faq["question"]
                if q not in kb_questions:
                    missing_faqs.append(q)
                else:
                    answer = kb_questions[q]
                    missing_kw = [kw for kw in faq["answer_keywords"] if kw not in answer]
                    if missing_kw:
                        wrong_answer_faqs.append(f"'{q}' missing keywords: {missing_kw}")

            if missing_faqs:
                checks.append(make_check(
                    "knowledge_base_faq_added",
                    False,
                    f"Missing {len(missing_faqs)} FAQ(s) from knowledge base: {missing_faqs}"
                ))
            elif wrong_answer_faqs:
                checks.append(make_check(
                    "knowledge_base_faq_added",
                    False,
                    f"FAQ answer content incorrect: {wrong_answer_faqs}"
                ))
            else:
                checks.append(make_check(
                    "knowledge_base_faq_added",
                    True,
                    f"All 3 MedTech FAQs found in knowledge base with correct content. KB has {len(kb_entries)} total entries."
                ))
                total_score += 1.0

    except json.JSONDecodeError as e:
        checks.append(make_check("knowledge_base_faq_added", False, f"KB file JSON parse error: {e}"))
    except Exception as e:
        checks.append(make_check("knowledge_base_faq_added", False, f"Unexpected error reading KB: {e}"))

    # ════════════════════════════════════════════════════════════════════════
    # CHECK 2: Session history shows 3-turn conversation with complaint messages
    # ════════════════════════════════════════════════════════════════════════
    try:
        session_path = Path.home() / ".ai_customer_service" / "session.json"
        stats_path = Path.home() / ".ai_customer_service" / "stats.json"

        # Check stats for evidence of conversations
        conversation_evidence = False
        complaint_detected = False
        transfer_triggered = False
        detail_parts = []

        if stats_path.exists():
            with open(stats_path, encoding='utf-8') as f:
                stats_data = json.load(f)

            total_msg = stats_data.get("total_messages", 0)
            complaints = stats_data.get("intent_counts", {}).get("complaint", 0)
            negative_sentiments = stats_data.get("sentiment_counts", {}).get("negative", 0)
            transfers = stats_data.get("transfers_to_human", 0)

            if total_msg >= 3:
                conversation_evidence = True
                detail_parts.append(f"total_messages={total_msg}")

            if complaints >= 1 or negative_sentiments >= 1:
                complaint_detected = True
                detail_parts.append(f"complaint_intents={complaints}, negative_sentiments={negative_sentiments}")

            if transfers >= 1:
                transfer_triggered = True
                detail_parts.append(f"transfers_to_human={transfers}")

        # Also check session file if it exists
        if session_path.exists():
            with open(session_path, encoding='utf-8') as f:
                session_data = json.load(f)
            history = session_data.get("history", [])
            user_messages = [m["content"] for m in history if m.get("role") == "user"]
            # Look for the specific test messages
            has_inquiry = any("血压计" in m or "售后" in m or "了解" in m for m in user_messages)
            has_complaint1 = any("坏了" in m or "太差" in m or "投诉" in m for m in user_messages)
            has_complaint2 = any("失望" in m or "退款" in m for m in user_messages)
            detail_parts.append(f"session_user_msgs={len(user_messages)}")
            detail_parts.append(f"has_inquiry={has_inquiry}, has_complaint1={has_complaint1}, has_complaint2={has_complaint2}")

        if conversation_evidence and complaint_detected:
            checks.append(make_check(
                "complaint_conversation_conducted",
                True,
                f"3-turn complaint conversation verified. Details: {', '.join(detail_parts)}"
            ))
            total_score += 1.0
        else:
            checks.append(make_check(
                "complaint_conversation_conducted",
                False,
                f"Conversation insufficient. conversation_evidence={conversation_evidence}, complaint_detected={complaint_detected}. Details: {', '.join(detail_parts) if detail_parts else 'no stats file found'}"
            ))

    except json.JSONDecodeError as e:
        checks.append(make_check("complaint_conversation_conducted", False, f"Session/stats JSON parse error: {e}"))
    except Exception as e:
        checks.append(make_check("complaint_conversation_conducted", False, f"Unexpected error: {e}"))

    # ════════════════════════════════════════════════════════════════════════
    # CHECK 3: service_stats_report.json exists with valid, non-trivial stats
    # ════════════════════════════════════════════════════════════════════════
    try:
        # Search for the file anywhere in workspace
        report_files = list(Path(workspace).rglob("service_stats_report.json"))

        if not report_files:
            checks.append(make_check(
                "stats_report_saved",
                False,
                "service_stats_report.json not found anywhere in the workspace directory."
            ))
        else:
            report_path = report_files[0]
            with open(report_path, encoding='utf-8') as f:
                report_data = json.load(f)

            # Must be a non-empty dict with real stats fields
            required_fields = ["total_conversations", "total_messages", "kb_entry_count"]
            missing_fields = [f for f in required_fields if f not in report_data]

            if missing_fields:
                checks.append(make_check(
                    "stats_report_saved",
                    False,
                    f"service_stats_report.json exists at {report_path} but missing required fields: {missing_fields}. Found fields: {list(report_data.keys())}"
                ))
            else:
                total_msgs = report_data.get("total_messages", 0)
                kb_count = report_data.get("kb_entry_count", 0)
                total_convos = report_data.get("total_conversations", 0)

                if total_msgs < 3:
                    checks.append(make_check(
                        "stats_report_saved",
                        False,
                        f"Stats report exists but total_messages={total_msgs} < 3. The stats were not captured after the conversation, or conversation was incomplete."
                    ))
                elif kb_count < 11:  # 8 builtin + 3 added = 11 minimum
                    checks.append(make_check(
                        "stats_report_saved",
                        False,
                        f"Stats report shows kb_entry_count={kb_count}, expected >= 11 (8 built-in + 3 added). FAQs may not have been added before stats were captured."
                    ))
                else:
                    checks.append(make_check(
                        "stats_report_saved",
                        True,
                        f"service_stats_report.json found at {report_path} with valid data: total_messages={total_msgs}, kb_entry_count={kb_count}, total_conversations={total_convos}."
                    ))
                    total_score += 1.0

    except json.JSONDecodeError as e:
        checks.append(make_check("stats_report_saved", False, f"service_stats_report.json found but JSON parse failed: {e}"))
    except Exception as e:
        checks.append(make_check("stats_report_saved", False, f"Unexpected error reading stats report: {e}"))

    # ════════════════════════════════════════════════════════════════════════
    # Final result
    # ════════════════════════════════════════════════════════════════════════
    final_score = round(total_score / max_score, 4)
    all_passed = all(c["passed"] for c in checks)

    result = {
        "passed": all_passed,
        "score": final_score,
        "checks": checks
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    run_eval(workspace_dir)