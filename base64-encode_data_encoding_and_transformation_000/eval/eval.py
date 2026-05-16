import sys
import json
import base64
from pathlib import Path
from urllib.parse import unquote

def evaluate(workspace: str):
    checks = []

    # ---------------------------------------------------------------
    # STEP 1: Find the output file
    # ---------------------------------------------------------------
    output_candidates = list(Path(workspace).rglob("encoded_payload.txt"))
    if not output_candidates:
        checks.append({
            "name": "output_file_exists",
            "passed": False,
            "detail": "Could not find 'encoded_payload.txt' anywhere in workspace."
        })
        return {"passed": False, "score": 0.0, "checks": checks}

    output_file = output_candidates[0]
    checks.append({
        "name": "output_file_exists",
        "passed": True,
        "detail": f"Found output file at: {output_file}"
    })

    try:
        raw_content = output_file.read_text(encoding="utf-8").strip()
    except Exception as e:
        checks.append({
            "name": "output_file_readable",
            "passed": False,
            "detail": f"Could not read output file: {e}"
        })
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append({
        "name": "output_file_readable",
        "passed": True,
        "detail": f"File content (first 120 chars): {raw_content[:120]}"
    })

    # ---------------------------------------------------------------
    # STEP 2: Independently compute the CORRECT answer
    # ---------------------------------------------------------------

    # -- Stage A: URL-decode the input --
    url_encoded = "%3CArticle%3E%20%22H%C3%A9ros%20%26%20Champions%22%20%E2%80%94%20It%27s%20%27legendary%27!"
    try:
        step_a_decoded = unquote(url_encoded, encoding="utf-8")
        # Expected: <Article> "Héros & Champions" — It's 'legendary'!
    except Exception as e:
        checks.append({"name": "internal_url_decode", "passed": False, "detail": str(e)})
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append({
        "name": "internal_url_decode_sanity",
        "passed": True,
        "detail": f"URL-decoded intermediate: {step_a_decoded}"
    })

    # -- Stage B: HTML-encode per SKILL.md exact rules --
    # Only these 5 substitutions, IN ORDER (& must come first to avoid double-encoding)
    def html_encode(s: str) -> str:
        s = s.replace("&", "&amp;")
        s = s.replace("<", "&lt;")
        s = s.replace(">", "&gt;")
        s = s.replace('"', "&quot;")
        s = s.replace("'", "&#39;")   # SKILL.md mandates &#39; NOT &apos;
        return s

    step_b_html = html_encode(step_a_decoded)
    # Expected: &lt;Article&gt; &quot;H&#233;... wait, é is NOT in the 5 chars list, stays literal
    # é stays as é (only 5 chars are mapped), — stays as — (em-dash, not in list)
    # So: &lt;Article&gt; &quot;Héros &amp; Champions&quot; — It&#39;s &#39;legendary&#39;!

    checks.append({
        "name": "internal_html_encode_sanity",
        "passed": True,
        "detail": f"HTML-encoded intermediate: {step_b_html}"
    })

    # -- Stage C: Base64-encode with UTF-8 awareness --
    # Algorithm: btoa(unescape(encodeURIComponent(input)))
    # Python equivalent: base64.b64encode(step_b_html.encode('utf-8'))
    step_c_b64_bytes = base64.b64encode(step_b_html.encode("utf-8"))
    expected_final = step_c_b64_bytes.decode("ascii")
    # Must end with = padding if needed

    checks.append({
        "name": "expected_final_computed",
        "passed": True,
        "detail": f"Expected Base64 output: {expected_final}"
    })

    # ---------------------------------------------------------------
    # STEP 3: Validate agent output
    # ---------------------------------------------------------------

    # Check exact match of the base64 string
    agent_b64 = raw_content

    exact_match = (agent_b64 == expected_final)
    checks.append({
        "name": "exact_base64_match",
        "passed": exact_match,
        "detail": (
            f"Agent produced: {agent_b64[:120]}\nExpected: {expected_final[:120]}"
            if not exact_match else
            "Exact match confirmed."
        )
    })

    if not exact_match:
        # Drill down: try decoding the agent's b64 output to give partial credit info
        try:
            agent_decoded_b64 = base64.b64decode(agent_b64).decode("utf-8")
            checks.append({
                "name": "partial_decode_agent_b64",
                "passed": False,
                "detail": f"Agent's b64 decodes to: {agent_decoded_b64}"
            })

            # Check if the agent got HTML encoding right but wrong b64
            html_correct = (agent_decoded_b64 == step_b_html)
            checks.append({
                "name": "html_encoding_correct",
                "passed": html_correct,
                "detail": (
                    f"HTML layer correct: {html_correct}. Agent HTML: {agent_decoded_b64}"
                )
            })

            # Specifically check for the &#39; vs &apos; trap
            used_correct_apos = "&#39;" in agent_decoded_b64
            used_wrong_apos = "&apos;" in agent_decoded_b64
            checks.append({
                "name": "single_quote_encoding_correct",
                "passed": used_correct_apos and not used_wrong_apos,
                "detail": (
                    f"Uses &#39; (correct): {used_correct_apos}, "
                    f"Uses &apos; (wrong): {used_wrong_apos}"
                )
            })

        except Exception as e:
            checks.append({
                "name": "partial_decode_agent_b64",
                "passed": False,
                "detail": f"Could not decode agent's b64 output: {e}. Output was: {agent_b64[:80]}"
            })
    else:
        # Full pass — also surface the &#39; check as a named passing check
        checks.append({
            "name": "single_quote_encoding_correct",
            "passed": True,
            "detail": "&#39; used correctly for single quotes (confirmed via exact match)."
        })
        checks.append({
            "name": "html_encoding_correct",
            "passed": True,
            "detail": "HTML encoding layer confirmed correct via exact match."
        })

    # ---------------------------------------------------------------
    # STEP 4: Compute score
    # ---------------------------------------------------------------
    passed_checks = [c for c in checks if c["passed"]]
    total_checks = len(checks)
    score = len(passed_checks) / total_checks if total_checks > 0 else 0.0
    overall_passed = exact_match

    return {
        "passed": overall_passed,
        "score": round(score, 4),
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, indent=2, ensure_ascii=False))