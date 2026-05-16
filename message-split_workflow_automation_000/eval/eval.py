import sys
import json
import re
from pathlib import Path

def split_text_reference(text, max_len):
    """Reference implementation exactly matching SKILL.md split_text()."""
    import re as _re
    sentence_split = _re.split(r'(?<=[。！？.!?])\s+', text)
    chunks = []
    current = ""
    for sentence in sentence_split:
        if len(current) + len(sentence) + 1 <= max_len:
            current += (" " + sentence if current else sentence)
        else:
            if current:
                chunks.append(current)
            if len(sentence) > max_len:
                for i in range(0, len(sentence), max_len - 100):
                    chunks.append(sentence[i:i + max_len - 100])
                current = ""
            else:
                current = sentence
    if current:
        chunks.append(current)
    return chunks

def compute_expected_messages(text, channel):
    """Compute expected output following send_long_message() logic from SKILL.md."""
    # Channel limits from SKILL.md
    channel_limits = {
        "signal": 700,
        "feishu": 3600,
        "telegram": 3600,
        "discord": 3600,
        "whatsapp": 3600,
        "imessage": 3600,
    }
    MAX_LEN = channel_limits.get(channel.lower(), 3600)

    if len(text) <= MAX_LEN:
        return [text]

    chunks = split_text_reference(text, MAX_LEN)
    total = len(chunks)
    messages = []
    for i, chunk in enumerate(chunks, 1):
        header = f"[{i}/{total}]\n" if total > 1 else ""
        messages.append(header + chunk)
    return messages

def evaluate(workspace_dir):
    checks = []

    # --- Load input data ---
    input_path = Path(workspace_dir) / "data/raw_tickets/escalation_TK9021.json"
    try:
        with open(input_path) as f:
            input_data = json.load(f)
        channel = input_data["channel"]
        summary = input_data["summary"]
    except Exception as e:
        checks.append({"name": "input_data_readable", "passed": False, "detail": str(e)})
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append({"name": "input_data_readable", "passed": True, "detail": f"Channel={channel}, summary_len={len(summary)}"})

    # --- Find output file ---
    candidates = list(Path(workspace_dir).rglob("signal_chunks.json"))
    if not candidates:
        checks.append({"name": "output_file_exists", "passed": False, "detail": "signal_chunks.json not found anywhere in workspace"})
        return {"passed": False, "score": 0.0, "checks": checks}

    output_path = candidates[0]
    checks.append({"name": "output_file_exists", "passed": True, "detail": str(output_path)})

    # --- Load agent output ---
    try:
        with open(output_path) as f:
            agent_output = json.load(f)
    except Exception as e:
        checks.append({"name": "output_json_valid", "passed": False, "detail": f"JSON parse error: {e}"})
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append({"name": "output_json_valid", "passed": True, "detail": "JSON parsed successfully"})

    # --- Extract messages list ---
    if isinstance(agent_output, list):
        agent_messages = agent_output
    elif isinstance(agent_output, dict) and "messages" in agent_output:
        agent_messages = agent_output["messages"]
    else:
        checks.append({"name": "output_structure_valid", "passed": False,
                        "detail": "Expected a JSON array or object with 'messages' key"})
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append({"name": "output_structure_valid", "passed": True, "detail": f"Found {len(agent_messages)} messages"})

    # --- Compute expected ---
    expected_messages = compute_expected_messages(summary, channel)
    expected_count = len(expected_messages)

    # --- Check 1: Correct channel limit used (Signal = 700) ---
    # All chunks (excluding header) must be <= 700 chars
    correct_channel_limit = True
    over_limit_details = []
    for idx, msg in enumerate(agent_messages):
        if len(msg) > 700:
            correct_channel_limit = False
            over_limit_details.append(f"msg[{idx}] len={len(msg)}>700")
    checks.append({
        "name": "signal_700_char_limit_respected",
        "passed": correct_channel_limit,
        "detail": "All messages <= 700 chars" if correct_channel_limit else "; ".join(over_limit_details[:3])
    })

    # --- Check 2: Correct total chunk count ---
    count_match = len(agent_messages) == expected_count
    checks.append({
        "name": "correct_chunk_count",
        "passed": count_match,
        "detail": f"Expected {expected_count} chunks, got {len(agent_messages)}"
    })

    # --- Check 3: Sequence headers present and correct format ---
    header_pattern = re.compile(r'^\[(\d+)/(\d+)\]\n')
    header_checks_passed = True
    header_detail = []
    for idx, msg in enumerate(agent_messages):
        m = header_pattern.match(msg)
        if expected_count > 1:
            if not m:
                header_checks_passed = False
                header_detail.append(f"msg[{idx}] missing header")
            else:
                i_val = int(m.group(1))
                total_val = int(m.group(2))
                if i_val != idx + 1 or total_val != expected_count:
                    header_checks_passed = False
                    header_detail.append(f"msg[{idx}] header [{i_val}/{total_val}] expected [{idx+1}/{expected_count}]")
        else:
            # Single chunk: no header expected
            if header_pattern.match(msg):
                header_checks_passed = False
                header_detail.append("Single chunk should NOT have a header")

    checks.append({
        "name": "sequence_headers_correct",
        "passed": header_checks_passed,
        "detail": "All headers correct" if header_checks_passed else "; ".join(header_detail[:5])
    })

    # --- Check 4: Content completeness (all text present when headers stripped) ---
    try:
        agent_content = ""
        for msg in agent_messages:
            # Strip the [i/total]\n header if present
            content = header_pattern.sub("", msg)
            agent_content += content

        expected_content = ""
        for msg in expected_messages:
            content = header_pattern.sub("", msg)
            expected_content += content

        content_complete = (agent_content == expected_content)
        checks.append({
            "name": "content_completeness",
            "passed": content_complete,
            "detail": "Full text preserved across all chunks" if content_complete
                      else f"Content mismatch: agent_len={len(agent_content)}, expected_len={len(expected_content)}"
        })
    except Exception as e:
        checks.append({"name": "content_completeness", "passed": False, "detail": str(e)})

    # --- Check 5: Sentence-boundary splitting respected (sub-split stride = max_len - 100 = 600) ---
    # Verify that the oversized sentence chunk lengths match the 600-stride pattern.
    # We detect this by confirming NO chunk body (excluding header) exceeds 700 chars
    # AND that the first large-sentence sub-chunk is exactly 600 chars (stride = 700-100).
    try:
        expected_bodies = [header_pattern.sub("", m) for m in expected_messages]
        agent_bodies = [header_pattern.sub("", m) for m in agent_messages]

        # Find first expected body that is exactly 600 chars (evidence of 700-100 stride)
        stride_600_chunks = [b for b in expected_bodies if len(b) == 600]
        if stride_600_chunks:
            # Check agent also has 600-char body chunks
            agent_600_chunks = [b for b in agent_bodies if len(b) == 600]
            stride_correct = len(agent_600_chunks) >= len(stride_600_chunks)
            checks.append({
                "name": "subsplit_stride_600_chars",
                "passed": stride_correct,
                "detail": f"Expected {len(stride_600_chunks)} chunks of 600 chars (max_len-100), agent has {len(agent_600_chunks)}"
            })
        else:
            checks.append({
                "name": "subsplit_stride_600_chars",
                "passed": True,
                "detail": "No oversized single sentence detected; stride check N/A"
            })
    except Exception as e:
        checks.append({"name": "subsplit_stride_600_chars", "passed": False, "detail": str(e)})

    # --- Final score ---
    critical = ["signal_700_char_limit_respected", "correct_chunk_count", "sequence_headers_correct", "content_completeness"]
    bonus = ["subsplit_stride_600_chars"]

    critical_results = [c for c in checks if c["name"] in critical]
    bonus_results = [c for c in checks if c["name"] in bonus]

    critical_passed = all(c["passed"] for c in critical_results)
    critical_score = sum(c["passed"] for c in critical_results) / len(critical) if critical else 0
    bonus_score = sum(c["passed"] for c in bonus_results) / len(bonus) if bonus else 0

    score = round(critical_score * 0.85 + bonus_score * 0.15, 3)
    passed = critical_passed and all(c["passed"] for c in bonus_results)

    return {"passed": passed, "score": score, "checks": checks}


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, indent=2))