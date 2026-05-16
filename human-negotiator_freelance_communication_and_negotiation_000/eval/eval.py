import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir):
    checks = []
    
    def add_check(name, passed, detail):
        checks.append({"name": name, "passed": passed, "detail": detail})
    
    # --- Find response_drafts.json ---
    workspace = Path(workspace_dir)
    found_files = list(workspace.rglob("response_drafts.json"))
    
    if not found_files:
        add_check("file_exists", False, "response_drafts.json not found anywhere in workspace")
        return {"passed": False, "score": 0.0, "checks": checks}
    
    draft_file = found_files[0]
    add_check("file_exists", True, f"Found response_drafts.json at {draft_file}")
    
    # --- Parse JSON ---
    try:
        with open(draft_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        add_check("json_valid", False, f"Failed to parse JSON: {e}")
        return {"passed": False, "score": 0.0, "checks": checks}
    
    add_check("json_valid", True, "JSON parsed successfully")
    
    # Normalize: support both list and dict formats
    if isinstance(data, list):
        responses = {item.get("message_id", str(i)): item for i, item in enumerate(data)}
    elif isinstance(data, dict):
        # Could be keyed by message_id or contain a list under a key
        if "responses" in data:
            lst = data["responses"]
            responses = {item.get("message_id", str(i)): item for i, item in enumerate(lst)}
        else:
            responses = data
    else:
        add_check("structure_valid", False, "Top-level must be a list or dict of responses")
        return {"passed": False, "score": 0.0, "checks": checks}
    
    add_check("structure_valid", True, f"Found {len(responses)} response entries")
    
    # Helper: get response text for a message_id
    def get_response_text(msg_id):
        """Search for a response by message_id, flexible about key names."""
        # Direct key lookup
        if msg_id in responses:
            item = responses[msg_id]
            for key in ["response", "reply", "message", "content", "text", "response_text"]:
                if key in item:
                    return str(item[key])
            # If the item itself is a string
            if isinstance(item, str):
                return item
            # Return all string values concatenated
            return " ".join(str(v) for v in item.values() if isinstance(v, str))
        
        # Search by message_id field in list-style
        for key, item in responses.items():
            if isinstance(item, dict) and item.get("message_id") == msg_id:
                for k in ["response", "reply", "message", "content", "text", "response_text"]:
                    if k in item:
                        return str(item[k])
        return None
    
    score = 0.0
    max_score = 0.0
    
    # ================================================================
    # CHECK MSG-001: Coconala price negotiation + vague requirements
    # Expected: Japanese language, Plan A / Plan B structure, empathy-first,
    #           clarifying questions about requirements, keigo
    # ================================================================
    max_score += 20.0
    msg001 = get_response_text("MSG-001")
    if msg001 is None:
        add_check("msg001_exists", False, "No response for MSG-001 found")
    else:
        add_check("msg001_exists", True, f"MSG-001 response found ({len(msg001)} chars)")
        
        # Must be in Japanese (coconala platform)
        jp_chars = len(re.findall(r'[\u3040-\u309f\u30a0-\u30ff\u4e00-\u9fff]', msg001))
        is_japanese = jp_chars > 20
        add_check("msg001_japanese", is_japanese, 
                  f"Japanese platform requires Japanese response. JP char count: {jp_chars}")
        if is_japanese:
            score += 4.0
        
        # Must have Plan A / Plan B or equivalent two-option price structure
        has_two_plans = bool(
            re.search(r'プランA|案A|プランＡ|オプションA|プラン①', msg001, re.IGNORECASE) or
            re.search(r'A案|B案', msg001) or
            (re.search(r'プラン', msg001) and re.search(r'[AB①②1-2]', msg001))
        )
        # Also check for two distinct pricing/option blocks
        price_options = len(re.findall(r'(?:プラン|案|オプション)[AB①②一二1-9]|【[^】]*プラン[^】]*】', msg001))
        has_two_plans = has_two_plans or price_options >= 2
        
        add_check("msg001_two_plans", has_two_plans,
                  "Price negotiation must present two named plans (Plan A / Plan B or equivalent)")
        if has_two_plans:
            score += 6.0
        
        # Must show empathy/understanding of budget concern
        has_empathy = bool(re.search(r'ご予算|お気持ち|承知|なるほど|ご事情|ご状況|おっしゃる', msg001))
        add_check("msg001_empathy", has_empathy,
                  "Must acknowledge customer's budget concern with empathy")
        if has_empathy:
            score += 4.0
        
        # Must ask clarifying question about document type (vague requirement)
        has_clarification = bool(re.search(r'どのような|具体的|書類の種類|詳しく|お聞かせ|教えていただ|ヒアリング|ページ数|枚数', msg001))
        add_check("msg001_clarification", has_clarification,
                  "Vague requirements need clarifying questions about document details")
        if has_clarification:
            score += 6.0
    
    # ================================================================
    # CHECK MSG-002: Fiverr complaint handling (English)
    # Expected: English, acknowledge + apologize, summarize problem,
    #           explain cause as fact (not excuse), 2 concrete solutions,
    #           no escalation dismissal (serious quality complaint)
    # ================================================================
    max_score += 20.0
    msg002 = get_response_text("MSG-002")
    if msg002 is None:
        add_check("msg002_exists", False, "No response for MSG-002 found")
    else:
        add_check("msg002_exists", True, f"MSG-002 response found ({len(msg002)} chars)")
        
        # Must be in English
        en_words = len(re.findall(r'\b[a-zA-Z]{3,}\b', msg002))
        is_english = en_words > 15
        add_check("msg002_english", is_english,
                  f"Fiverr platform requires English response. EN word count: {en_words}")
        if is_english:
            score += 4.0
        
        # Must contain sincere apology
        has_apology = bool(re.search(r'sorry|apologize|apologi[sz]|sincerely|deeply|regret', msg002, re.IGNORECASE))
        add_check("msg002_apology", has_apology,
                  "Complaint handling must start with genuine apology")
        if has_apology:
            score += 4.0
        
        # Must summarize/acknowledge the specific issues mentioned
        acknowledges_issues = bool(re.search(r'mistranslat|key term|tone|business document|quality', msg002, re.IGNORECASE))
        add_check("msg002_acknowledges_issues", acknowledges_issues,
                  "Must acknowledge the specific quality issues (mistranslations, tone)")
        if acknowledges_issues:
            score += 4.0
        
        # Must offer concrete remedies (revision + refund options or specific fix plan)
        has_remedy = bool(re.search(r'revision|correct|fix|rework|refund|redo|re-translate|address', msg002, re.IGNORECASE))
        add_check("msg002_concrete_remedy", has_remedy,
                  "Must provide at least one concrete corrective action")
        if has_remedy:
            score += 4.0
        
        # Must NOT be dismissive or redirect without taking responsibility
        is_dismissive = bool(re.search(r'should have|your fault|you need to|not our|cannot help', msg002, re.IGNORECASE))
        add_check("msg002_not_dismissive", not is_dismissive,
                  "Response must not be dismissive or blame the customer")
        if not is_dismissive:
            score += 4.0
    
    # ================================================================
    # CHECK MSG-003: Coconala unreasonable/illegal request (competitor docs)
    # Expected: Japanese, polite decline, explain reason as fact (not accusation),
    #           offer 2 alternative solutions, connect to underlying goal
    # ================================================================
    max_score += 20.0
    msg003 = get_response_text("MSG-003")
    if msg003 is None:
        add_check("msg003_exists", False, "No response for MSG-003 found")
    else:
        add_check("msg003_exists", True, f"MSG-003 response found ({len(msg003)} chars)")
        
        # Must be in Japanese
        jp_chars003 = len(re.findall(r'[\u3040-\u309f\u30a0-\u30ff\u4e00-\u9fff]', msg003))
        is_japanese003 = jp_chars003 > 20
        add_check("msg003_japanese", is_japanese003,
                  f"Coconala requires Japanese. JP char count: {jp_chars003}")
        if is_japanese003:
            score += 4.0
        
        # Must politely decline
        has_decline = bool(re.search(r'難し|お断り|対応でき|できかね|遠慮|申し訳|ご対応が|お受けできない', msg003))
        add_check("msg003_polite_decline", has_decline,
                  "Must politely decline the request")
        if has_decline:
            score += 4.0
        
        # Must explain reason (legal/ethical concern, not accusation)
        has_reason = bool(re.search(r'法的|法律|規約|倫理|機密|不正|コンプライアンス|リスク|理由|情報の取|守秘', msg003))
        add_check("msg003_explains_reason", has_reason,
                  "Must explain the legal/ethical reason for declining")
        if has_reason:
            score += 4.0
        
        # Must offer alternatives (at least one alternative path)
        has_alternatives = bool(re.search(r'代わり|代替|その代|別の|以下.*可能|対応.*可能|ご提案|できること', msg003))
        add_check("msg003_offers_alternatives", has_alternatives,
                  "Unreasonable request decline must offer alternative solutions per SKILL.md")
        if has_alternatives:
            score += 4.0
        
        # Must connect to customer's underlying goal (翻訳ニーズ、英語情報収集など)
        connects_goal = bool(re.search(r'目的|お役に立|ご要望|英語.*情報|翻訳.*ニーズ|達成|お力|お手伝い', msg003))
        add_check("msg003_connects_to_goal", connects_goal,
                  "Must connect alternatives back to customer's underlying objective")
        if connects_goal:
            score += 4.0
    
    # ================================================================
    # CHECK MSG-004: Upwork price negotiation (English)
    # Expected: English, Plan A / Plan B structure with explicit merits for each,
    #           acknowledge budget, customer benefit stated for both options
    # ================================================================
    max_score += 20.0
    msg004 = get_response_text("MSG-004")
    if msg004 is None:
        add_check("msg004_exists", False, "No response for MSG-004 found")
    else:
        add_check("msg004_exists", True, f"MSG-004 response found ({len(msg004)} chars)")
        
        # Must be in English
        en_words004 = len(re.findall(r'\b[a-zA-Z]{3,}\b', msg004))
        is_english004 = en_words004 > 15
        add_check("msg004_english", is_english004,
                  f"Upwork requires English. EN word count: {en_words004}")
        if is_english004:
            score += 4.0
        
        # Must present two named plans/options
        has_two_options = bool(
            re.search(r'Plan\s*[AB12]|Option\s*[AB12]|Package\s*[AB12]', msg004, re.IGNORECASE) or
            (re.search(r'[Pp]lan\s*[Aa]', msg004) and re.search(r'[Pp]lan\s*[Bb]', msg004)) or
            (re.search(r'[Oo]ption\s*1', msg004) and re.search(r'[Oo]ption\s*2', msg004))
        )
        add_check("msg004_two_plans", has_two_options,
                  "Price negotiation must present two named plans with their respective merits")
        if has_two_options:
            score += 6.0
        
        # Each plan must have stated benefits/merits
        has_merits = bool(re.search(r'benefit|advantage|include|offer|feature|merit|provide', msg004, re.IGNORECASE))
        add_check("msg004_states_merits", has_merits,
                  "Each plan must explicitly state its advantages/merits")
        if has_merits:
            score += 5.0
        
        # Must acknowledge budget concern
        acknowledges_budget = bool(re.search(r'budget|understand.*cost|appreciate.*sharing|thank.*mention|$80|price concern', msg004, re.IGNORECASE))
        add_check("msg004_acknowledges_budget", acknowledges_budget,
                  "Must acknowledge the customer's budget constraint")
        if acknowledges_budget:
            score += 5.0
    
    # ================================================================
    # CHECK MSG-005: Fiverr vague inquiry (English)
    # Expected: English, thank/acknowledge, ask 2-3 clarifying questions,
    #           keep conversation going, professional tone
    # ================================================================
    max_score += 20.0
    msg005 = get_response_text("MSG-005")
    if msg005 is None:
        add_check("msg005_exists", False, "No response for MSG-005 found")
    else:
        add_check("msg005_exists", True, f"MSG-005 response found ({len(msg005)} chars)")
        
        # Must be in English
        en_words005 = len(re.findall(r'\b[a-zA-Z]{3,}\b', msg005))
        is_english005 = en_words005 > 10
        add_check("msg005_english", is_english005,
                  f"Fiverr requires English. EN word count: {en_words005}")
        if is_english005:
            score += 4.0
        
        # Must ask at least 2 clarifying questions (question marks)
        question_count = msg005.count("?")
        has_questions = question_count >= 2
        add_check("msg005_clarifying_questions", has_questions,
                  f"Vague inquiry must prompt at least 2 clarifying questions. Found: {question_count} '?'")
        if has_questions:
            score += 8.0
        
        # Must thank/acknowledge the inquiry
        has_thanks = bool(re.search(r'thank|appreciate|great to hear|happy to|glad', msg005, re.IGNORECASE))
        add_check("msg005_acknowledges_inquiry", has_thanks,
                  "Must acknowledge and thank the customer for reaching out")
        if has_thanks:
            score += 4.0
        
        # Must NOT give a price quote without knowing requirements
        # (giving a definite price without knowing details is a SKILL.md violation)
        gives_premature_price = bool(re.search(r'\$\d+|\d+\s*(?:USD|per page|total)', msg005, re.IGNORECASE))
        add_check("msg005_no_premature_quote", not gives_premature_price,
                  "Should not give a final price quote before understanding requirements")
        if not gives_premature_price:
            score += 4.0
    
    # ================================================================
    # BONUS CHECK: AI disclosure when relevant
    # MSG-001 or MSG-004 responses should mention AI assistance as a benefit
    # ================================================================
    max_score += 5.0
    all_response_texts = []
    for mid in ["MSG-001", "MSG-004"]:
        t = get_response_text(mid)
        if t:
            all_response_texts.append(t)
    
    combined = " ".join(all_response_texts)
    has_ai_disclosure = bool(re.search(
        r'AI|人工知能|効率|短納期|低価格|ツール.*活用|活用.*ツール|自動化|品質チェック|quality check|efficiently|automation',
        combined, re.IGNORECASE
    ))
    add_check("ai_disclosure_as_benefit", has_ai_disclosure,
              "Per SKILL.md, AI usage should be disclosed as a benefit (efficiency, cost, speed) rather than hidden")
    if has_ai_disclosure:
        score += 5.0
    
    # ================================================================
    # Final scoring
    # ================================================================
    final_score = round(score / max_score, 4) if max_score > 0 else 0.0
    passed = final_score >= 0.65  # Must pass at least 65% of checks
    
    return {
        "passed": passed,
        "score": final_score,
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "args", "passed": False, "detail": "No workspace path provided"}]}))
        sys.exit(1)
    
    result = evaluate(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False, indent=2))