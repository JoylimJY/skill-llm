import sys
import json
import re
from pathlib import Path

def evaluate(workspace: str):
    checks = []
    workspace_path = Path(workspace)

    # ── Locate the output file ───────────────────────────────────────────────
    candidates = list(workspace_path.rglob("newsletter-signup.html"))
    file_found = len(candidates) > 0
    checks.append({
        "name": "output_file_exists",
        "passed": file_found,
        "detail": f"Found {len(candidates)} file(s) named newsletter-signup.html" if file_found else "newsletter-signup.html not found anywhere in workspace"
    })
    if not file_found:
        score = 0.0
        return {"passed": False, "score": score, "checks": checks}

    target = candidates[0]
    try:
        content = target.read_text(encoding="utf-8")
    except Exception as e:
        checks.append({"name": "file_readable", "passed": False, "detail": str(e)})
        return {"passed": False, "score": 0.0, "checks": checks}

    from bs4 import BeautifulSoup
    soup = BeautifulSoup(content, "lxml")

    # ── CHECK 1: type="email" on input (not type="text") ────────────────────
    email_inputs = soup.find_all("input", {"type": "email"})
    text_inputs_for_email = soup.find_all("input", {"type": "text"})
    # Also detect inputs without type (defaults to text)
    has_email_type_input = len(email_inputs) > 0
    checks.append({
        "name": "input_type_email",
        "passed": has_email_type_input,
        "detail": f"Found {len(email_inputs)} input(s) with type='email'. Using type='email' enables mobile keyboard optimisation as required."
    })

    # ── CHECK 2: Proper <label> with for/id association ──────────────────────
    # Must have <label for="X"> and corresponding <input id="X">
    labels = soup.find_all("label", {"for": True})
    label_for_id_match = False
    label_detail = "No <label for=...> found"
    for label in labels:
        for_val = label.get("for", "")
        matching_input = soup.find("input", {"id": for_val})
        if matching_input:
            label_for_id_match = True
            label_detail = f"<label for='{for_val}'> properly associated with <input id='{for_val}'>"
            break
    checks.append({
        "name": "label_for_id_association",
        "passed": label_for_id_match,
        "detail": label_detail
    })

    # ── CHECK 3: Placeholder does NOT replace label (both must exist) ────────
    # Check that any input with placeholder also has a corresponding label
    inputs_with_placeholder = soup.find_all("input", {"placeholder": True})
    placeholder_supplements_label = True
    placeholder_detail = "No placeholder-only inputs found (good)"
    for inp in inputs_with_placeholder:
        inp_id = inp.get("id", "")
        if inp_id:
            # Check if a label exists for this input
            assoc_label = soup.find("label", {"for": inp_id})
            if not assoc_label:
                placeholder_supplements_label = False
                placeholder_detail = f"Input id='{inp_id}' has placeholder but no associated <label> — placeholder must not replace label"
                break
        else:
            # No id means label association is impossible
            placeholder_supplements_label = False
            placeholder_detail = "Input has placeholder but no id, making label association impossible"
            break
    checks.append({
        "name": "placeholder_supplements_not_replaces_label",
        "passed": placeholder_supplements_label,
        "detail": placeholder_detail
    })

    # ── CHECK 4: Submit button touch target ≥44×44px ─────────────────────────
    # Check for min-width/min-height or explicit width/height >= 44px on button
    # Accept inline style or CSS patterns referencing 44
    button_els = soup.find_all(["button", "input"], {"type": ["submit", "button"]})
    # Also check generic buttons
    button_els += soup.find_all("button")
    button_els = list({id(b): b for b in button_els}.values())  # deduplicate

    touch_target_ok = False
    touch_detail = "No submit button found or touch target size not specified"

    full_text = content  # check raw content for style references
    # Look for 44px pattern in style blocks or inline styles anywhere near buttons
    px44_pattern = re.compile(r'(min-height|min-width|height|width)\s*:\s*(4[4-9]|[5-9]\d|\d{3,})px')
    rem44_pattern = re.compile(r'(min-height|min-width|height|width)\s*:\s*(2\.75|2\.[8-9]|[3-9]\.|[0-9]{2,}\.)rem')

    if px44_pattern.search(full_text) or rem44_pattern.search(full_text):
        touch_target_ok = True
        match = px44_pattern.search(full_text) or rem44_pattern.search(full_text)
        touch_detail = f"Touch target size specified: '{match.group()}'"

    # Also accept padding that implies 44px (12px top+bottom = 24px, but with font ~16px → ~40px, borderline)
    # Be strict: require explicit min-height or height >= 44 or padding ≥ 14px top/bottom
    # Check for padding approach: padding: 14px or padding: 16px or similar
    padding_pattern = re.compile(r'padding\s*:\s*(1[4-9]|[2-9]\d)px\s+(1\d|[2-9]\d)px')
    padding_shorthand = re.compile(r'padding\s*:\s*(1[4-9]|[2-9]\d)px')  # vertical padding
    if not touch_target_ok and (padding_pattern.search(full_text) or padding_shorthand.search(full_text)):
        touch_target_ok = True
        touch_detail = "Large padding implies adequate touch target size (≥14px vertical)"

    checks.append({
        "name": "submit_button_touch_target_44px",
        "passed": touch_target_ok,
        "detail": touch_detail
    })

    # ── CHECK 5: Email-only form (minimal fields — no unnecessary fields) ─────
    # Count non-hidden inputs in the form
    forms = soup.find_all("form")
    minimal_fields_ok = False
    minimal_detail = "No <form> element found"
    for form in forms:
        # Skip any form that looks like the referral form (id=referral)
        if form.get("id") == "referral":
            continue
        visible_inputs = [
            i for i in form.find_all("input")
            if i.get("type", "text").lower() not in ("hidden", "submit", "button", "checkbox", "radio")
        ]
        if len(visible_inputs) == 1:
            minimal_fields_ok = True
            minimal_detail = f"Form has exactly 1 visible input field (email-only) — optimal for conversion"
            break
        elif len(visible_inputs) <= 2:
            minimal_fields_ok = True
            minimal_detail = f"Form has {len(visible_inputs)} visible input fields (acceptable minimal design)"
            break
        else:
            minimal_detail = f"Form has {len(visible_inputs)} visible inputs — too many fields reduce conversion"

    checks.append({
        "name": "minimal_fields_email_only",
        "passed": minimal_fields_ok,
        "detail": minimal_detail
    })

    # ── CHECK 6: Value proposition references the lead magnet ────────────────
    lead_magnet_keywords = ["mindfulness", "starter kit", "7-day", "7 day", "executive", "pdf", "guide"]
    content_lower = content.lower()
    magnet_found = any(kw in content_lower for kw in lead_magnet_keywords)
    checks.append({
        "name": "value_proposition_references_lead_magnet",
        "passed": magnet_found,
        "detail": f"Lead magnet keywords found: {[kw for kw in lead_magnet_keywords if kw in content_lower]}" if magnet_found else "No reference to the '7-Day Executive Mindfulness Starter Kit' lead magnet from project-context.md"
    })

    # ── CHECK 7: Privacy policy link present ─────────────────────────────────
    privacy_links = soup.find_all("a", href=True)
    privacy_link_ok = any(
        "privacy" in (a.get("href", "") + a.get_text()).lower()
        for a in privacy_links
    )
    # Also check for text references
    if not privacy_link_ok:
        privacy_link_ok = "privacy" in content_lower
    checks.append({
        "name": "privacy_policy_link_present",
        "passed": privacy_link_ok,
        "detail": "Privacy policy reference found (GDPR/CCPA compliance)" if privacy_link_ok else "No privacy policy link/reference found — required for GDPR/CCPA compliance"
    })

    # ── CHECK 8: Double opt-in mentioned ─────────────────────────────────────
    double_optin_ok = any(kw in content_lower for kw in ["double opt-in", "double opt in", "confirm", "confirmation email", "confirm your", "check your email"])
    checks.append({
        "name": "double_optin_mentioned",
        "passed": double_optin_ok,
        "detail": "Double opt-in confirmation mentioned" if double_optin_ok else "Double opt-in not mentioned — required by project policy and GDPR jurisdiction"
    })

    # ── CHECK 9: Placement is NOT inline (due to competing referral form) ────
    # The signup form should be popup, header, or footer bar — NOT another inline section
    # Heuristic: check if the form is wrapped in popup/modal/overlay/header/footer keywords
    placement_keywords_ok = any(kw in content_lower for kw in [
        "popup", "pop-up", "modal", "overlay", "header", "sticky", "footer-bar",
        "slide-in", "banner", "top-bar", "hero", "fixed"
    ])
    # Also check class/id attributes
    placement_attrs = str(soup.find_all(class_=True)).lower() + str(soup.find_all(id=True)).lower()
    placement_in_attrs = any(kw in placement_attrs for kw in [
        "popup", "pop-up", "modal", "overlay", "header", "sticky", "banner", "hero", "fixed"
    ])
    placement_ok = placement_keywords_ok or placement_in_attrs

    # Negative: ensure form is not placed as plain inline content with no placement indicator
    # (if none of the placement keywords are present, it's likely plain inline — penalise)
    checks.append({
        "name": "non_competing_placement",
        "passed": placement_ok,
        "detail": f"Appropriate non-competing placement detected (popup/header/sticky/modal)" if placement_ok else "No explicit non-inline placement detected — an existing inline referral form is on the page; agent should choose popup, header, or footer bar"
    })

    # ── CHECK 10: Keyboard / Enter submit support ─────────────────────────────
    # A proper <form> with <button type="submit"> or <input type="submit"> enables Enter key
    has_submit_mechanism = False
    for form in soup.find_all("form"):
        if form.find("button", {"type": "submit"}) or form.find("input", {"type": "submit"}) or form.find("button"):
            has_submit_mechanism = True
            break
    # Also check that there are no onclick-only divs used as submit
    onclick_divs = soup.find_all("div", {"onclick": True})
    onclick_divs += soup.find_all("span", {"onclick": True})
    accessible_submit = has_submit_mechanism and len(onclick_divs) == 0
    checks.append({
        "name": "keyboard_accessible_submit",
        "passed": accessible_submit,
        "detail": "Proper <button> or <input type='submit'> found; no onclick-div anti-patterns" if accessible_submit else "Missing proper submit mechanism or using onclick-div (not keyboard accessible)"
    })

    # ── Score & verdict ───────────────────────────────────────────────────────
    passed_checks = [c for c in checks if c["passed"]]
    score = round(len(passed_checks) / len(checks), 3)
    # Must pass critical checks to overall pass
    critical = ["output_file_exists", "input_type_email", "label_for_id_association",
                "placeholder_supplements_not_replaces_label", "minimal_fields_email_only",
                "value_proposition_references_lead_magnet", "privacy_policy_link_present"]
    critical_passed = all(
        next((c["passed"] for c in checks if c["name"] == crit), False)
        for crit in critical
    )
    overall_passed = critical_passed and score >= 0.75

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace_dir)
    print(json.dumps(result, indent=2))