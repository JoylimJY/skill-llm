#!/usr/bin/env python3
"""
Evaluation script for the mock RPM build pipeline task.
Usage: python3 eval_script.py /workspace
"""

import sys
import os
import json
import re
from pathlib import Path

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")

checks = []
total_score = 0.0
max_score = 0.0

def check(name, passed, detail, weight=1.0):
    checks.append({"name": name, "passed": passed, "detail": detail})
    global total_score, max_score
    max_score += weight
    if passed:
        total_score += weight

# ─────────────────────────────────────────────────────────────────────────────
# PART 1: Custom configuration file validation
# ─────────────────────────────────────────────────────────────────────────────

# Find the custom cfg file (should be named something like custom.cfg, 
# secpkg-build.cfg, isolated-build.cfg, etc. — NOT the broken distractor ones)
cfg_candidates = []
for f in workspace.rglob("*.cfg"):
    fname = f.name
    # Exclude known distractor configs
    if fname not in ("broken_old.cfg", "incomplete.cfg", "wrong_setup.cfg", "template_bad.cfg"):
        cfg_candidates.append(f)

cfg_file = None
cfg_opts = {}
cfg_parse_error = None

for candidate in cfg_candidates:
    try:
        config_opts = {}
        exec_globals = {"config_opts": config_opts}
        with open(candidate) as f:
            content = f.read()
        exec(compile(content, str(candidate), 'exec'), exec_globals)
        fetched = exec_globals['config_opts']
        # Must have at least root + yum.conf to be a valid candidate
        if 'root' in fetched and 'yum.conf' in fetched:
            cfg_file = candidate
            cfg_opts = fetched
            break
    except Exception as e:
        cfg_parse_error = str(e)
        continue

# CHECK 1.1: Custom config file exists and is parseable Python
if cfg_file is not None:
    check("custom_cfg_exists_and_parseable",
          True,
          f"Found valid custom cfg: {cfg_file}",
          weight=1.5)
else:
    check("custom_cfg_exists_and_parseable",
          False,
          f"No valid custom .cfg file found. Parse error: {cfg_parse_error}. "
          f"Candidates examined: {[str(c) for c in cfg_candidates]}",
          weight=1.5)

# CHECK 1.2: Required config_opts keys present
required_keys = ['root', 'target_arch', 'legal_host_arches', 'dist', 'releasever',
                 'yum.conf', 'chroot_setup_cmd', 'chroot_additional_packages']
missing_keys = [k for k in required_keys if k not in cfg_opts]
check("cfg_has_required_keys",
      len(missing_keys) == 0,
      f"Missing keys: {missing_keys}" if missing_keys else
      f"All required keys present: {required_keys}",
      weight=1.5)

# CHECK 1.3: chroot_setup_cmd starts with 'install' (NOT 'yum install' etc.)
if 'chroot_setup_cmd' in cfg_opts:
    cmd = cfg_opts['chroot_setup_cmd'].strip()
    correct = cmd.startswith('install ')
    check("cfg_chroot_setup_cmd_format",
          correct,
          f"chroot_setup_cmd = '{cmd[:60]}...' — "
          + ("CORRECT (starts with 'install')" if correct
             else "WRONG (must start with 'install', not 'yum install' or similar)"),
          weight=1.5)
else:
    check("cfg_chroot_setup_cmd_format",
          False,
          "chroot_setup_cmd key not found in config",
          weight=1.5)

# CHECK 1.4: legal_host_arches is a tuple/list
if 'legal_host_arches' in cfg_opts:
    lha = cfg_opts['legal_host_arches']
    correct = isinstance(lha, (tuple, list)) and len(lha) > 0
    check("cfg_legal_host_arches_is_tuple",
          correct,
          f"legal_host_arches = {repr(lha)} — "
          + ("CORRECT (tuple/list)" if correct else "WRONG (must be tuple or list)"),
          weight=1.0)
else:
    check("cfg_legal_host_arches_is_tuple",
          False,
          "legal_host_arches key not found",
          weight=1.0)

# CHECK 1.5: yum.conf contains [main] section and at least one repo
if 'yum.conf' in cfg_opts:
    yum_conf = cfg_opts['yum.conf']
    has_main = '[main]' in yum_conf
    has_repo = bool(re.search(r'\[(?!main)[^\]]+\]', yum_conf))
    check("cfg_yum_conf_valid",
          has_main and has_repo,
          f"yum.conf has [main]: {has_main}, has repo section: {has_repo}",
          weight=1.0)
else:
    check("cfg_yum_conf_valid",
          False,
          "yum.conf key not found",
          weight=1.0)

# ─────────────────────────────────────────────────────────────────────────────
# PART 2: Mock invocation log analysis
# ─────────────────────────────────────────────────────────────────────────────

log_path = Path("/var/log/mock/mock_invocations.jsonl")
invocations = []
try:
    with open(log_path) as f:
        for line in f:
            line = line.strip()
            if line:
                invocations.append(json.loads(line))
except FileNotFoundError:
    pass
except Exception as e:
    pass

# CHECK 2.1: --buildsrpm was called with both --spec and --sources
buildsrpm_calls = [inv for inv in invocations if inv.get('action') == 'buildsrpm']
valid_buildsrpm = [inv for inv in buildsrpm_calls
                   if inv.get('has_spec') and inv.get('has_sources') and inv.get('success')]
check("buildsrpm_called_with_spec_and_sources",
      len(valid_buildsrpm) > 0,
      f"Found {len(valid_buildsrpm)} valid --buildsrpm calls (with --spec and --sources). "
      f"Total buildsrpm attempts: {len(buildsrpm_calls)}",
      weight=2.0)

# CHECK 2.2: ccache plugin was enabled in at least one build call
ccache_calls = [inv for inv in invocations
                if 'ccache' in inv.get('plugins', []) and inv.get('success')]
check("ccache_plugin_enabled",
      len(ccache_calls) > 0,
      f"Found {len(ccache_calls)} successful build calls with ccache plugin enabled",
      weight=1.5)

# CHECK 2.3: --resultdir was specified in build calls
resultdir_calls = [inv for inv in invocations
                   if inv.get('resultdir') and inv.get('success')]
check("resultdir_specified",
      len(resultdir_calls) > 0,
      f"Found {len(resultdir_calls)} successful calls specifying --resultdir",
      weight=1.0)

# CHECK 2.4: Custom cfg file was used (not just a preset name like fedora-39-x86_64)
custom_cfg_calls = [inv for inv in invocations
                    if inv.get('config') and (
                        inv['config'].endswith('.cfg') or '/' in inv['config']
                    ) and inv.get('success')]
check("custom_cfg_used_in_mock_call",
      len(custom_cfg_calls) > 0,
      f"Found {len(custom_cfg_calls)} successful calls using a custom .cfg file path",
      weight=1.5)

# CHECK 2.5: The config used in mock call passes validation (no config_errors)
valid_cfg_calls = [inv for inv in custom_cfg_calls
                   if not inv.get('config_errors')]
check("custom_cfg_passes_mock_validation",
      len(valid_cfg_calls) > 0,
      f"Found {len(valid_cfg_calls)} calls where custom cfg passed mock validation "
      f"(no config_errors). "
      f"Config errors seen: {[inv.get('config_errors') for inv in custom_cfg_calls if inv.get('config_errors')]}",
      weight=2.0)

# ─────────────────────────────────────────────────────────────────────────────
# PART 3: Batch build validation
# ─────────────────────────────────────────────────────────────────────────────

# CHECK 3.1: At least 3 different rebuild/build calls (for the 3 SRPMs)
rebuild_calls = [inv for inv in invocations
                 if inv.get('action') in ('rebuild', 'build') and inv.get('success')]
srpms_built = set()
for inv in rebuild_calls:
    for sf in inv.get('source_files', []):
        srpms_built.add(os.path.basename(sf))

check("batch_build_multiple_srpms",
      len(srpms_built) >= 3 or len(rebuild_calls) >= 3,
      f"Built SRPMs: {srpms_built}, Total rebuild calls: {len(rebuild_calls)}",
      weight=2.0)

# CHECK 3.2: Different result directories used per package in batch build
result_dirs = set()
for inv in rebuild_calls:
    if inv.get('resultdir'):
        result_dirs.add(inv['resultdir'])

check("batch_build_separate_resultdirs",
      len(result_dirs) >= 2,
      f"Distinct result directories used in batch build: {result_dirs}",
      weight=1.5)

# ─────────────────────────────────────────────────────────────────────────────
# PART 4: Result files produced
# ─────────────────────────────────────────────────────────────────────────────

# CHECK 4.1: Build log exists in a results directory
build_logs = list(workspace.rglob("build.log"))
check("build_log_produced",
      len(build_logs) > 0,
      f"Found {len(build_logs)} build.log files at: {[str(l) for l in build_logs[:3]]}",
      weight=1.0)

# CHECK 4.2: A shell script or Makefile containing the batch build workflow exists
script_files = list(workspace.rglob("*.sh")) + list(workspace.rglob("Makefile"))
batch_script = None
for sf in script_files:
    try:
        content = sf.read_text(errors='replace')
        # Must contain mock and loop pattern or multiple mock calls for srpms
        if ('mock' in content and
            ('src.rpm' in content) and
            (('for ' in content and 'do' in content) or
             content.count('mock') >= 3 or
             'mockchain' in content)):
            # Exclude the old distractor script
            if 'old_build.sh' not in str(sf):
                batch_script = sf
                break
    except Exception:
        pass

check("batch_build_script_exists",
      batch_script is not None,
      f"Found batch build script: {batch_script}" if batch_script else
      "No batch build script found that loops over SRPMs",
      weight=1.5)

# CHECK 4.3: Script uses --rebuild flag for SRPM batch builds
if batch_script:
    try:
        content = batch_script.read_text(errors='replace')
        has_rebuild = '--rebuild' in content
        check("batch_script_uses_rebuild_flag",
              has_rebuild,
              f"Script {'contains' if has_rebuild else 'MISSING'} --rebuild flag",
              weight=1.0)
    except Exception as e:
        check("batch_script_uses_rebuild_flag",
              False,
              f"Error reading batch script: {e}",
              weight=1.0)
else:
    # Check if rebuild was used in actual invocations
    check("batch_script_uses_rebuild_flag",
          len([inv for inv in invocations if inv.get('action') == 'rebuild']) >= 3,
          f"No script found; checking invocations: "
          f"{len([inv for inv in invocations if inv.get('action') == 'rebuild'])} rebuild calls",
          weight=1.0)

# ─────────────────────────────────────────────────────────────────────────────
# Final score calculation
# ─────────────────────────────────────────────────────────────────────────────

score = round(total_score / max_score, 3) if max_score > 0 else 0.0
passed = score >= 0.70  # 70% threshold to pass

result = {
    "passed": passed,
    "score": score,
    "checks": checks
}

print(json.dumps(result, indent=2))