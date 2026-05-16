import sys
import json
import re
from pathlib import Path

def find_output_file(workspace):
    # Look for the expected output file anywhere in the workspace
    candidates = list(Path(workspace).rglob("permissions_reference.json"))
    if candidates:
        return candidates[0]
    return None

def check(name, condition, detail):
    return {"name": name, "passed": bool(condition), "detail": detail}

def run_eval(workspace):
    checks = []

    output_file = find_output_file(workspace)
    if output_file is None:
        checks.append(check("output_file_exists", False, "permissions_reference.json not found anywhere in workspace"))
        return checks, 0.0

    checks.append(check("output_file_exists", True, f"Found at {output_file}"))

    try:
        import json as _json
        with open(output_file) as f:
            data = _json.load(f)
    except Exception as e:
        checks.append(check("output_file_parseable", False, f"JSON parse error: {e}"))
        return checks, 0.0

    checks.append(check("output_file_parseable", True, "Valid JSON"))

    # Helper: find entry by label
    def get_entry(label):
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    lbl = item.get("label", "").strip().upper()
                    if lbl == label.upper():
                        return item
        elif isinstance(data, dict):
            return data.get(label)
        return None

    def field(entry, *keys):
        """Try multiple possible key names for a field."""
        for k in keys:
            if k in entry:
                return str(entry[k]).strip()
        return None

    # ── ENTRY_A: rwsr-xr-x ──────────────────────────────────────────────────
    # Symbolic input with setuid (owner has execute, so lowercase 's')
    # Numeric: 4755, Symbolic: rwsr-xr-x
    # Symbolic chmod: chmod u+rwx,g+rx,o+rx,u+s filename  OR  chmod u+rwxs,g+rx,o+rx filename
    # Accept any reasonable ordering/grouping as long as setuid is present
    ea = get_entry("ENTRY_A")
    if ea is None:
        checks.append(check("ENTRY_A_present", False, "ENTRY_A not found in output"))
    else:
        checks.append(check("ENTRY_A_present", True, "ENTRY_A found"))
        num_a = field(ea, "numeric", "octal", "numeric_notation")
        sym_a = field(ea, "symbolic", "symbolic_notation")
        checks.append(check("ENTRY_A_numeric", num_a in ("4755",), f"Expected 4755, got {num_a}"))
        checks.append(check("ENTRY_A_symbolic", sym_a == "rwsr-xr-x", f"Expected rwsr-xr-x, got {sym_a}"))
        # Symbolic chmod must contain u+s
        sym_cmd_a = field(ea, "symbolic_command", "chmod_symbolic", "command_symbolic")
        has_us = sym_cmd_a is not None and "u+s" in sym_cmd_a
        checks.append(check("ENTRY_A_symbolic_cmd_has_setuid", has_us, f"Expected 'u+s' in symbolic command, got: {sym_cmd_a}"))

    # ── ENTRY_B: rwxr-sr-x ──────────────────────────────────────────────────
    # setgid: group execute position is 's' (execute is set → lowercase)
    # Numeric: 2755
    eb = get_entry("ENTRY_B")
    if eb is None:
        checks.append(check("ENTRY_B_present", False, "ENTRY_B not found"))
    else:
        checks.append(check("ENTRY_B_present", True, "ENTRY_B found"))
        num_b = field(eb, "numeric", "octal", "numeric_notation")
        sym_b = field(eb, "symbolic", "symbolic_notation")
        checks.append(check("ENTRY_B_numeric", num_b in ("2755",), f"Expected 2755, got {num_b}"))
        checks.append(check("ENTRY_B_symbolic", sym_b == "rwxr-sr-x", f"Expected rwxr-sr-x, got {sym_b}"))
        sym_cmd_b = field(eb, "symbolic_command", "chmod_symbolic", "command_symbolic")
        has_gs = sym_cmd_b is not None and "g+s" in sym_cmd_b
        checks.append(check("ENTRY_B_symbolic_cmd_has_setgid", has_gs, f"Expected 'g+s' in symbolic command, got: {sym_cmd_b}"))

    # ── ENTRY_C: rwxr-xr-t ──────────────────────────────────────────────────
    # sticky bit, others have execute → lowercase 't'
    # Numeric: 1755
    ec = get_entry("ENTRY_C")
    if ec is None:
        checks.append(check("ENTRY_C_present", False, "ENTRY_C not found"))
    else:
        checks.append(check("ENTRY_C_present", True, "ENTRY_C found"))
        num_c = field(ec, "numeric", "octal", "numeric_notation")
        sym_c = field(ec, "symbolic", "symbolic_notation")
        checks.append(check("ENTRY_C_numeric", num_c in ("1755",), f"Expected 1755, got {num_c}"))
        checks.append(check("ENTRY_C_symbolic", sym_c == "rwxr-xr-t", f"Expected rwxr-xr-t, got {sym_c}"))
        sym_cmd_c = field(ec, "symbolic_command", "chmod_symbolic", "command_symbolic")
        has_sticky = sym_cmd_c is not None and "+t" in sym_cmd_c
        checks.append(check("ENTRY_C_symbolic_cmd_has_sticky", has_sticky, f"Expected '+t' in symbolic command, got: {sym_cmd_c}"))

    # ── ENTRY_D: rw-r--r-- ──────────────────────────────────────────────────
    # Standard 644 — no special bits
    ed = get_entry("ENTRY_D")
    if ed is None:
        checks.append(check("ENTRY_D_present", False, "ENTRY_D not found"))
    else:
        checks.append(check("ENTRY_D_present", True, "ENTRY_D found"))
        num_d = field(ed, "numeric", "octal", "numeric_notation")
        sym_d = field(ed, "symbolic", "symbolic_notation")
        checks.append(check("ENTRY_D_numeric", num_d in ("644",), f"Expected 644, got {num_d}"))
        checks.append(check("ENTRY_D_symbolic", sym_d == "rw-r--r--", f"Expected rw-r--r--, got {sym_d}"))

    # ── ENTRY_E: 4750 ───────────────────────────────────────────────────────
    # Numeric input 4750 → setuid + owner rwx + group rx + others nothing
    # Symbolic: rwsr-x---
    # Symbolic chmod: chmod u+rwxs,g+rx filename  (NO 'o+' clause since others=0)
    ee = get_entry("ENTRY_E")
    if ee is None:
        checks.append(check("ENTRY_E_present", False, "ENTRY_E not found"))
    else:
        checks.append(check("ENTRY_E_present", True, "ENTRY_E found"))
        num_e = field(ee, "numeric", "octal", "numeric_notation")
        sym_e = field(ee, "symbolic", "symbolic_notation")
        checks.append(check("ENTRY_E_numeric", num_e in ("4750",), f"Expected 4750, got {num_e}"))
        checks.append(check("ENTRY_E_symbolic", sym_e == "rwsr-x---", f"Expected rwsr-x---, got {sym_e}"))
        # Symbolic command must NOT contain o+ (others has no permissions)
        sym_cmd_e = field(ee, "symbolic_command", "chmod_symbolic", "command_symbolic")
        no_o_clause = sym_cmd_e is not None and "o+" not in sym_cmd_e
        checks.append(check("ENTRY_E_no_others_clause", no_o_clause, f"'o+' should be absent (others=---), got: {sym_cmd_e}"))
        has_us_e = sym_cmd_e is not None and "u+s" in sym_cmd_e
        checks.append(check("ENTRY_E_has_setuid_in_cmd", has_us_e, f"Expected 'u+s' in symbolic command, got: {sym_cmd_e}"))

    # ── ENTRY_F: 2640 ───────────────────────────────────────────────────────
    # setgid + owner rw + group r + others nothing
    # Symbolic: rw-r-----   with setgid in group execute → group execute is NOT set → uppercase 'S'
    # So symbolic = rw-r-S---
    ef = get_entry("ENTRY_F")
    if ef is None:
        checks.append(check("ENTRY_F_present", False, "ENTRY_F not found"))
    else:
        checks.append(check("ENTRY_F_present", True, "ENTRY_F found"))
        num_f = field(ef, "numeric", "octal", "numeric_notation")
        sym_f = field(ef, "symbolic", "symbolic_notation")
        checks.append(check("ENTRY_F_numeric", num_f in ("2640",), f"Expected 2640, got {num_f}"))
        # group digit = 4 (read only, no execute), setgid → S (uppercase because execute NOT set)
        checks.append(check("ENTRY_F_symbolic", sym_f == "rw-r-S---", f"Expected rw-r-S---, got {sym_f}"))
        sym_cmd_f = field(ef, "symbolic_command", "chmod_symbolic", "command_symbolic")
        has_gs_f = sym_cmd_f is not None and "g+s" in sym_cmd_f
        checks.append(check("ENTRY_F_setgid_in_cmd", has_gs_f, f"Expected 'g+s' in symbolic command, got: {sym_cmd_f}"))

    # ── ENTRY_G: 1777 ───────────────────────────────────────────────────────
    # sticky + full access → others execute IS set → lowercase 't'
    # Numeric: 1777, Symbolic: rwxrwxrwt
    eg = get_entry("ENTRY_G")
    if eg is None:
        checks.append(check("ENTRY_G_present", False, "ENTRY_G not found"))
    else:
        checks.append(check("ENTRY_G_present", True, "ENTRY_G found"))
        num_g = field(eg, "numeric", "octal", "numeric_notation")
        sym_g = field(eg, "symbolic", "symbolic_notation")
        checks.append(check("ENTRY_G_numeric", num_g in ("1777",), f"Expected 1777, got {num_g}"))
        checks.append(check("ENTRY_G_symbolic", sym_g == "rwxrwxrwt", f"Expected rwxrwxrwt, got {sym_g}"))
        # Should include security warning about 777 level access
        desc_g = str(eg).lower()
        has_warning = "warn" in desc_g or "risk" in desc_g or "avoid" in desc_g or "security" in desc_g or "danger" in desc_g
        checks.append(check("ENTRY_G_777_warning", has_warning, f"Expected security warning for 777, entry text: {str(eg)[:200]}"))

    # ── ENTRY_H: rwSr--r-- ──────────────────────────────────────────────────
    # Setuid but owner execute NOT set → 'S' (uppercase)
    # Owner: rw (no x) → digit 6, setuid → 4xxx → but execute not set
    # Numeric: 4644  (setuid=4, owner=6, group=4, others=4)
    # Symbolic: rwSr--r--
    eh = get_entry("ENTRY_H")
    if eh is None:
        checks.append(check("ENTRY_H_present", False, "ENTRY_H not found"))
    else:
        checks.append(check("ENTRY_H_present", True, "ENTRY_H found"))
        num_h = field(eh, "numeric", "octal", "numeric_notation")
        sym_h = field(eh, "symbolic", "symbolic_notation")
        checks.append(check("ENTRY_H_numeric", num_h in ("4644",), f"Expected 4644, got {num_h}"))
        # Uppercase S because owner execute is NOT set
        checks.append(check("ENTRY_H_symbolic_uppercase_S", sym_h == "rwSr--r--", f"Expected rwSr--r-- (uppercase S = no execute), got {sym_h}"))

    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = passed_count / total if total > 0 else 0.0
    return checks, score

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    checks, score = run_eval(workspace)
    passed = score >= 0.75
    print(json.dumps({
        "passed": passed,
        "score": round(score, 4),
        "checks": checks
    }, indent=2))

if __name__ == "__main__":
    main()