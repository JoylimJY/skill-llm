#!/usr/bin/env python3
"""
Evaluation script for the GROMACS conformational analysis pipeline task.
Checks:
1. trjconv was called with PBC correction (-pbc mol), centering (-center), fitting (-fit rot+trans)
2. rms was called with two group selections (Backbone for fit, C-alpha or Protein for RMSD)
3. gyrate was called to produce an Rg XVG file
4. sham was called with the correct -f (combined reaction coordinates), -ls output, and -tsham 300
5. The sham output file is a valid XPM file
6. A combined/merged XVG with both RMSD and Rg data was created as input for sham
"""

import sys
import json
import os
import re
from pathlib import Path

def find_files_by_pattern(workspace, pattern):
    """Find all files matching a glob pattern recursively."""
    return list(Path(workspace).rglob(pattern))

def read_meta(path):
    """Parse .meta sidecar files."""
    data = {}
    try:
        for line in Path(path).read_text().splitlines():
            if '=' in line:
                k, v = line.split('=', 1)
                data[k.strip()] = v.strip()
    except Exception:
        pass
    return data

def check_xvg_columns(path, min_data_cols=2):
    """
    Check an XVG file has at least min_data_cols data columns (excl. time).
    Returns (bool, num_data_cols, detail_str)
    """
    try:
        lines = Path(path).read_text().splitlines()
        data_lines = [l for l in lines if l.strip() and not l.strip().startswith(('#', '@', '&'))]
        if not data_lines:
            return False, 0, "No data lines found"
        # Check first data line
        cols = data_lines[0].split()
        num_cols = len(cols)
        # num_data_cols = total cols - 1 (time)
        data_cols = num_cols - 1
        if data_cols >= min_data_cols:
            return True, data_cols, f"{data_cols} data columns found"
        return False, data_cols, f"Only {data_cols} data column(s) found, need {min_data_cols}"
    except Exception as e:
        return False, 0, f"Error reading XVG: {e}"

def check_xpm_valid(path):
    """Check if file is a valid XPM format."""
    try:
        content = Path(path).read_text()
        if '/* XPM */' in content or 'XPM' in content:
            return True, "Valid XPM format"
        return False, "Not a valid XPM file"
    except Exception as e:
        return False, f"Error: {e}"

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    workspace = Path(workspace)

    checks = []
    
    # ── CHECK 1: trjconv output exists ────────────────────────────────────────
    trjconv_meta_files = list(workspace.rglob("*.xtc.meta"))
    # Filter to those that say command=trjconv
    trjconv_metas = []
    for mf in trjconv_meta_files:
        meta = read_meta(mf)
        if meta.get('command') == 'trjconv':
            trjconv_metas.append(meta)
    
    trjconv_found = len(trjconv_metas) > 0
    checks.append({
        "name": "trjconv_executed",
        "passed": trjconv_found,
        "detail": f"Found {len(trjconv_metas)} trjconv execution(s)" if trjconv_found else "No trjconv execution found"
    })
    
    # ── CHECK 2: trjconv used -pbc mol ────────────────────────────────────────
    trjconv_pbc_ok = False
    pbc_detail = "trjconv not found"
    if trjconv_metas:
        for meta in trjconv_metas:
            if meta.get('pbc', '').lower() in ('mol', 'res', 'whole', 'atom', 'nojump'):
                trjconv_pbc_ok = True
                pbc_detail = f"PBC correction applied: {meta.get('pbc')}"
                break
        if not trjconv_pbc_ok:
            pbc_detail = f"PBC not properly set. Got: {[m.get('pbc') for m in trjconv_metas]}"
    checks.append({
        "name": "trjconv_pbc_correction",
        "passed": trjconv_pbc_ok,
        "detail": pbc_detail
    })
    
    # ── CHECK 3: trjconv used -center ─────────────────────────────────────────
    trjconv_center_ok = False
    center_detail = "trjconv not found"
    if trjconv_metas:
        for meta in trjconv_metas:
            if meta.get('center', 'False').lower() == 'true':
                trjconv_center_ok = True
                center_detail = "Centering applied"
                break
        if not trjconv_center_ok:
            center_detail = "No centering applied in trjconv"
    checks.append({
        "name": "trjconv_centering",
        "passed": trjconv_center_ok,
        "detail": center_detail
    })
    
    # ── CHECK 4: trjconv used -fit rot+trans (or similar rotation fit) ────────
    trjconv_fit_ok = False
    fit_detail = "trjconv not found"
    if trjconv_metas:
        for meta in trjconv_metas:
            fit_val = meta.get('fit', 'none').lower()
            if 'rot' in fit_val or 'trans' in fit_val:
                trjconv_fit_ok = True
                fit_detail = f"Fitting applied: {fit_val}"
                break
        if not trjconv_fit_ok:
            fit_detail = f"No rotation+translation fit applied. Got: {[m.get('fit') for m in trjconv_metas]}"
    checks.append({
        "name": "trjconv_fitting",
        "passed": trjconv_fit_ok,
        "detail": fit_detail
    })
    
    # ── CHECK 5: rms executed with two group selections ────────────────────────
    rms_meta_files = list(workspace.rglob("*.xvg.meta"))
    rms_metas = []
    for mf in rms_meta_files:
        meta = read_meta(mf)
        if meta.get('command') == 'rms':
            rms_metas.append(meta)
    
    rms_found = len(rms_metas) > 0
    checks.append({
        "name": "rms_executed",
        "passed": rms_found,
        "detail": f"Found {len(rms_metas)} rms execution(s)" if rms_found else "No rms execution found"
    })
    
    rms_two_groups = False
    groups_detail = "rms not found"
    if rms_metas:
        for meta in rms_metas:
            sel_str = meta.get('selections', '[]')
            # selections stored as repr of list
            try:
                # Count items: should have at least 2 selections
                sel_list = eval(sel_str) if sel_str.startswith('[') else []
                if len(sel_list) >= 2:
                    rms_two_groups = True
                    groups_detail = f"Two groups provided: {sel_list[:2]}"
                    break
            except Exception:
                pass
        if not rms_two_groups:
            # Also accept if backbone/c-alpha appear in any selection
            for meta in rms_metas:
                sel_str = meta.get('selections', '').lower()
                if ('backbone' in sel_str or 'c-alpha' in sel_str or 'calpha' in sel_str or
                        'ca' in sel_str or 'protein' in sel_str):
                    rms_two_groups = True
                    groups_detail = f"Recognized group selection: {sel_str[:100]}"
                    break
        if not rms_two_groups:
            groups_detail = f"Less than 2 group selections for rms. Raw: {[m.get('selections') for m in rms_metas]}"
    checks.append({
        "name": "rms_two_group_selections",
        "passed": rms_two_groups,
        "detail": groups_detail
    })
    
    # ── CHECK 6: rms output XVG file exists and has data ─────────────────────
    rmsd_xvg_files = list(workspace.rglob("rmsd*.xvg"))
    rmsd_xvg_ok = len(rmsd_xvg_files) > 0
    rmsd_detail = f"Found: {[str(f.relative_to(workspace)) for f in rmsd_xvg_files]}" if rmsd_xvg_ok else "No rmsd*.xvg file found"
    checks.append({
        "name": "rmsd_xvg_produced",
        "passed": rmsd_xvg_ok,
        "detail": rmsd_detail
    })
    
    # ── CHECK 7: gyrate executed ──────────────────────────────────────────────
    gyrate_metas = []
    for mf in rms_meta_files:
        meta = read_meta(mf)
        if meta.get('command') == 'gyrate':
            gyrate_metas.append(meta)
    
    # Also search for Rg/gyrate output files
    rg_files = list(workspace.rglob("rg*.xvg")) + list(workspace.rglob("gyrate*.xvg")) + list(workspace.rglob("radius*.xvg"))
    gyrate_found = len(gyrate_metas) > 0 or len(rg_files) > 0
    gyrate_detail = (f"gyrate metadata: {len(gyrate_metas)}, Rg XVG files: {[str(f.relative_to(workspace)) for f in rg_files]}"
                     if gyrate_found else "No gyrate execution or Rg XVG file found")
    checks.append({
        "name": "gyrate_executed",
        "passed": gyrate_found,
        "detail": gyrate_detail
    })
    
    # ── CHECK 8: sham executed ────────────────────────────────────────────────
    # Find .xpm.meta files from sham
    xpm_meta_files = list(workspace.rglob("*.xpm.meta"))
    sham_metas = []
    for mf in xpm_meta_files:
        meta = read_meta(mf)
        if meta.get('command') == 'sham':
            sham_metas.append(meta)
    
    sham_found = len(sham_metas) > 0
    checks.append({
        "name": "sham_executed",
        "passed": sham_found,
        "detail": f"Found {len(sham_metas)} sham execution(s)" if sham_found else "No sham execution found"
    })
    
    # ── CHECK 9: sham used -ls for output (not just -o) ───────────────────────
    sham_ls_ok = False
    sham_ls_detail = "sham not found"
    if sham_metas:
        for meta in sham_metas:
            if meta.get('output_ls', '') and meta.get('output_ls') != 'gibbs.xpm':
                # Custom output name used
                sham_ls_ok = True
                sham_ls_detail = f"sham -ls used: {meta.get('output_ls')}"
                break
            elif meta.get('output_ls', ''):
                sham_ls_ok = True
                sham_ls_detail = f"sham -ls used: {meta.get('output_ls')}"
                break
        if not sham_ls_ok:
            sham_ls_detail = f"sham -ls not found in metadata: {sham_metas}"
    checks.append({
        "name": "sham_uses_ls_flag",
        "passed": sham_ls_ok,
        "detail": sham_ls_detail
    })
    
    # ── CHECK 10: sham used -tsham 300 (temperature) ─────────────────────────
    sham_temp_ok = False
    sham_temp_detail = "sham not found"
    if sham_metas:
        for meta in sham_metas:
            tsham = meta.get('tsham', '')
            try:
                temp = float(tsham)
                if 295 <= temp <= 305:  # 300K ± 5
                    sham_temp_ok = True
                    sham_temp_detail = f"Temperature set correctly: {temp}K"
                    break
                else:
                    sham_temp_detail = f"Temperature set but not 300K: {temp}K"
            except (ValueError, TypeError):
                sham_temp_detail = f"Temperature not set or invalid: '{tsham}'"
    checks.append({
        "name": "sham_temperature_300K",
        "passed": sham_temp_ok,
        "detail": sham_temp_detail
    })
    
    # ── CHECK 11: sham input XVG has 2+ reaction coordinate columns ──────────
    sham_input_ok = False
    sham_input_detail = "sham not found or no valid input"
    if sham_metas:
        for meta in sham_metas:
            inp_f = meta.get('input', '')
            if inp_f and os.path.exists(inp_f):
                ok, ncols, detail = check_xvg_columns(inp_f, min_data_cols=2)
                if ok:
                    sham_input_ok = True
                    sham_input_detail = f"sham input '{inp_f}' has {ncols} data columns (RMSD + Rg)"
                    break
                else:
                    sham_input_detail = f"sham input '{inp_f}': {detail}"
            elif inp_f:
                sham_input_detail = f"sham input file not found: '{inp_f}'"
    # Fallback: look for any 2-column XVG files that could be combined data
    if not sham_input_ok:
        combined_candidates = list(workspace.rglob("combined*.xvg")) + \
                              list(workspace.rglob("reaction*.xvg")) + \
                              list(workspace.rglob("fel_input*.xvg")) + \
                              list(workspace.rglob("pc*.xvg")) + \
                              list(workspace.rglob("2d*.xvg"))
        for cf in combined_candidates:
            ok, ncols, detail = check_xvg_columns(cf, min_data_cols=2)
            if ok:
                sham_input_ok = True
                sham_input_detail = f"Found combined XVG: '{cf.name}' with {ncols} columns"
                break
    checks.append({
        "name": "sham_input_has_two_reaction_coords",
        "passed": sham_input_ok,
        "detail": sham_input_detail
    })
    
    # ── CHECK 12: FEL XPM output exists and is valid ─────────────────────────
    xpm_files = list(workspace.rglob("*.xpm"))
    # Exclude the mock metadata xpms
    valid_xpms = []
    for xf in xpm_files:
        ok, detail = check_xpm_valid(xf)
        if ok:
            valid_xpms.append(xf)
    
    fel_xpm_ok = len(valid_xpms) > 0
    checks.append({
        "name": "fel_xpm_output_exists",
        "passed": fel_xpm_ok,
        "detail": (f"Valid XPM files: {[str(f.relative_to(workspace)) for f in valid_xpms]}"
                   if fel_xpm_ok else "No valid XPM output file found")
    })
    
    # ── SCORING ───────────────────────────────────────────────────────────────
    # Weight critical checks more heavily
    weights = {
        "trjconv_executed": 1,
        "trjconv_pbc_correction": 2,
        "trjconv_centering": 1,
        "trjconv_fitting": 2,
        "rms_executed": 1,
        "rms_two_group_selections": 2,
        "rmsd_xvg_produced": 1,
        "gyrate_executed": 2,
        "sham_executed": 1,
        "sham_uses_ls_flag": 3,   # proprietary trap: must use -ls not -o
        "sham_temperature_300K": 2,
        "sham_input_has_two_reaction_coords": 3,  # must combine RMSD+Rg
        "fel_xpm_output_exists": 1,
    }
    
    total_weight = sum(weights.values())
    earned_weight = sum(weights[c["name"]] for c in checks if c["passed"] and c["name"] in weights)
    score = earned_weight / total_weight
    
    all_critical = all(
        c["passed"] for c in checks
        if c["name"] in ("sham_uses_ls_flag", "sham_input_has_two_reaction_coords",
                         "trjconv_pbc_correction", "rms_two_group_selections", "gyrate_executed")
    )
    
    passed = score >= 0.70 and all_critical
    
    result = {
        "passed": passed,
        "score": round(score, 3),
        "checks": checks
    }
    
    print(json.dumps(result, indent=2))
    return 0 if passed else 1

if __name__ == "__main__":
    sys.exit(main())