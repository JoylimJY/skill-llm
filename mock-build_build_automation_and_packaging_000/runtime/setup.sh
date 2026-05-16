#!/bin/bash
set -e

# ── Create a realistic fake 'mock' binary that validates arguments ─────────────
cat > /usr/local/bin/mock << 'MOCK_SCRIPT'
#!/usr/bin/env python3
"""
Simulated 'mock' binary for testing purposes.
Validates arguments and config file structure, produces realistic output.
"""
import sys
import os
import re
import json
import time
import argparse
import tempfile

LOG_FILE = "/var/log/mock/mock_invocations.jsonl"
os.makedirs("/var/log/mock", exist_ok=True)

def parse_config(cfg_path):
    """Parse a mock .cfg file and return config_opts dict."""
    config_opts = {}
    if not os.path.exists(cfg_path):
        return None, f"Config file not found: {cfg_path}"
    
    try:
        # Execute the config file as Python
        exec_globals = {"config_opts": config_opts}
        with open(cfg_path) as f:
            content = f.read()
        exec(compile(content, cfg_path, 'exec'), exec_globals)
        return exec_globals['config_opts'], None
    except SyntaxError as e:
        return None, f"Syntax error in config: {e}"
    except Exception as e:
        return None, f"Error parsing config: {e}"

def validate_config(config_opts):
    """Validate required config_opts keys."""
    errors = []
    required = ['root', 'target_arch', 'dist', 'releasever', 'yum.conf', 'chroot_setup_cmd']
    for key in required:
        if key not in config_opts:
            errors.append(f"Missing required config_opts key: '{key}'")
    
    # Validate chroot_setup_cmd starts with 'install' not 'yum install' etc.
    if 'chroot_setup_cmd' in config_opts:
        cmd = config_opts['chroot_setup_cmd'].strip()
        if not cmd.startswith('install '):
            errors.append(f"chroot_setup_cmd must start with 'install', got: '{cmd[:30]}'")
    
    # Validate legal_host_arches if present
    if 'legal_host_arches' in config_opts:
        lha = config_opts['legal_host_arches']
        if not isinstance(lha, (list, tuple)):
            errors.append("legal_host_arches must be a tuple or list")
    
    return errors

def main():
    args = sys.argv[1:]
    
    # Record invocation
    invocation = {
        "timestamp": time.time(),
        "args": args,
        "cwd": os.getcwd(),
        "pid": os.getpid()
    }
    
    # Parse -r / --root argument
    config_name = None
    config_path = None
    
    for i, arg in enumerate(args):
        if arg in ('-r', '--root') and i + 1 < len(args):
            config_name = args[i + 1]
        elif arg.startswith('-r') and len(arg) > 2:
            config_name = arg[2:]

    invocation['config'] = config_name
    
    # Determine if it's a .cfg file path
    if config_name and (config_name.endswith('.cfg') or config_name.startswith('./')):
        config_path = config_name
    
    # ── Handle --list-chroots ─────────────────────────────────────────────
    if '--list-chroots' in args:
        print("Available chroots:")
        print("  fedora-39-x86_64")
        print("  fedora-40-x86_64")
        print("  epel-9-x86_64")
        print("  centos-stream-9-x86_64")
        invocation['action'] = 'list-chroots'
        invocation['success'] = True
        with open(LOG_FILE, 'a') as f:
            f.write(json.dumps(invocation) + '\n')
        sys.exit(0)

    # ── Validate config if .cfg path given ────────────────────────────────
    config_errors = []
    parsed_config = {}
    if config_path:
        opts, err = parse_config(config_path)
        if err:
            config_errors.append(err)
        else:
            parsed_config = opts
            val_errors = validate_config(opts)
            config_errors.extend(val_errors)
    
    invocation['config_errors'] = config_errors
    invocation['config_opts_keys'] = list(parsed_config.keys()) if parsed_config else []
    
    # ── Identify the primary action ───────────────────────────────────────
    action = 'build'
    if '--init' in args:
        action = 'init'
    elif '--clean' in args:
        action = 'clean'
    elif '--scrub=all' in args or any(a.startswith('--scrub') for a in args):
        action = 'scrub'
    elif '--shell' in args:
        action = 'shell'
    elif '--chroot' in args:
        action = 'chroot'
    elif '--rebuild' in args:
        action = 'rebuild'
    elif '--buildsrpm' in args:
        action = 'buildsrpm'
    elif '--print-result-path' in args:
        action = 'print-result-path'
    elif '--copyout' in args:
        action = 'copyout'
    elif '--install' in args:
        action = 'install'
    
    invocation['action'] = action
    
    # ── Validate buildsrpm requires --spec and --sources ──────────────────
    if action == 'buildsrpm':
        has_spec = '--spec' in args
        has_sources = '--sources' in args
        if not has_spec:
            config_errors.append("--buildsrpm requires --spec <specfile>")
        if not has_sources:
            config_errors.append("--buildsrpm requires --sources <sourcesdir>")
        invocation['has_spec'] = has_spec
        invocation['has_sources'] = has_sources
    
    # ── Find --resultdir ──────────────────────────────────────────────────
    resultdir = None
    for i, arg in enumerate(args):
        if arg == '--resultdir' and i + 1 < len(args):
            resultdir = args[i + 1]
        elif arg.startswith('--resultdir='):
            resultdir = arg.split('=', 1)[1]
    
    invocation['resultdir'] = resultdir
    
    # ── Find enabled plugins ──────────────────────────────────────────────
    plugins = []
    plugin_opts = []
    for arg in args:
        if arg.startswith('--enable-plugin='):
            plugins.append(arg.split('=', 1)[1])
        elif arg.startswith('--plugin-opt='):
            plugin_opts.append(arg.split('=', 1)[1])
    
    invocation['plugins'] = plugins
    invocation['plugin_opts'] = plugin_opts
    
    # ── Find source files (SRPM or spec) ─────────────────────────────────
    source_files = []
    for arg in args:
        if arg.endswith('.src.rpm') or arg.endswith('.spec'):
            source_files.append(arg)
    invocation['source_files'] = source_files
    
    # ── Simulate failure if config errors ─────────────────────────────────
    if config_errors and action not in ('list-chroots', 'init', 'clean', 'scrub'):
        print(f"ERROR: Configuration errors:", file=sys.stderr)
        for e in config_errors:
            print(f"  - {e}", file=sys.stderr)
        invocation['success'] = False
        with open(LOG_FILE, 'a') as f:
            f.write(json.dumps(invocation) + '\n')
        sys.exit(1)
    
    # ── Produce output ────────────────────────────────────────────────────
    if resultdir:
        os.makedirs(resultdir, exist_ok=True)
        
        # Produce realistic mock output files
        if action == 'buildsrpm':
            # Find spec file arg
            spec_file = None
            for i, arg in enumerate(args):
                if arg == '--spec' and i + 1 < len(args):
                    spec_file = args[i + 1]
            
            pkg_name = 'secpkg'
            if spec_file:
                bn = os.path.basename(spec_file)
                pkg_name = bn.replace('.spec', '')
            
            # Write SRPM
            srpm_name = f"{pkg_name}-2.1.0-1.fc39.src.rpm"
            with open(os.path.join(resultdir, srpm_name), 'wb') as f:
                f.write(b"\xed\xab\xee\xdb" + srpm_name.encode())
            
            # Write build log
            with open(os.path.join(resultdir, "build.log"), 'w') as f:
                f.write(f"Mock build log for {pkg_name}\n")
                f.write(f"Action: {action}\n")
                f.write(f"Plugins: {plugins}\n")
                f.write("BUILD SUCCESS\n")
            
            # Write state log
            with open(os.path.join(resultdir, "state.log"), 'w') as f:
                f.write(f"Start: {time.ctime()}\n")
                f.write("State: complete\n")
        
        elif action in ('build', 'rebuild'):
            # Find source SRPM
            src = source_files[0] if source_files else 'unknown.src.rpm'
            pkg_name = os.path.basename(src).split('-')[0]
            
            # Write RPM
            rpm_name = f"{pkg_name}-1.0-1.x86_64.rpm"
            with open(os.path.join(resultdir, rpm_name), 'wb') as f:
                f.write(b"\xed\xab\xee\xdb" + rpm_name.encode())
            
            # Write logs
            with open(os.path.join(resultdir, "build.log"), 'w') as f:
                f.write(f"Mock build log for {pkg_name}\n")
                f.write(f"Action: {action}\n")
                f.write(f"Config: {config_name}\n")
                f.write(f"Plugins: {plugins}\n")
                f.write(f"Plugin opts: {plugin_opts}\n")
                f.write("BUILD SUCCESS\n")
            
            with open(os.path.join(resultdir, "state.log"), 'w') as f:
                f.write(f"Start: {time.ctime()}\n")
                f.write("State: complete\n")
    
    # ── Print success messages ────────────────────────────────────────────
    action_msgs = {
        'init': f"Initialized chroot for {config_name}",
        'clean': f"Cleaned chroot for {config_name}",
        'scrub': f"Scrubbed all for {config_name}",
        'buildsrpm': f"Built SRPM successfully",
        'build': f"Build complete",
        'rebuild': f"Rebuild complete",
        'install': f"Package installed",
        'copyout': f"Files copied out",
        'print-result-path': f"/var/lib/mock/{config_name}/result/",
    }
    
    print(f"INFO: Mock {action} for config: {config_name}")
    print(action_msgs.get(action, f"Action '{action}' completed"))
    if resultdir:
        print(f"Results in: {resultdir}")
    
    invocation['success'] = True
    with open(LOG_FILE, 'a') as f:
        f.write(json.dumps(invocation) + '\n')
    
    sys.exit(0)

if __name__ == '__main__':
    main()
MOCK_SCRIPT

chmod +x /usr/local/bin/mock

# ── Create a fake mockchain binary ───────────────────────────────────────────
cat > /usr/local/bin/mockchain << 'MOCKCHAIN_SCRIPT'
#!/usr/bin/env python3
"""Simulated mockchain for chain-building multiple SRPMs."""
import sys
import os
import json
import time

LOG_FILE = "/var/log/mock/mockchain_invocations.jsonl"
os.makedirs("/var/log/mock", exist_ok=True)

args = sys.argv[1:]

invocation = {
    "timestamp": time.time(),
    "args": args,
    "cwd": os.getcwd(),
}

# Parse -r
config = None
for i, arg in enumerate(args):
    if arg == '-r' and i + 1 < len(args):
        config = args[i + 1]

# Parse --basedir
basedir = None
for i, arg in enumerate(args):
    if arg == '--basedir' and i + 1 < len(args):
        basedir = args[i + 1]
    elif arg.startswith('--basedir='):
        basedir = arg.split('=', 1)[1]

# Parse --localrepo
localrepo = None
for i, arg in enumerate(args):
    if arg == '--localrepo' and i + 1 < len(args):
        localrepo = args[i + 1]
    elif arg.startswith('--localrepo='):
        localrepo = arg.split('=', 1)[1]

# Find SRPMs
srpms = [a for a in args if a.endswith('.src.rpm')]

invocation.update({
    'config': config,
    'basedir': basedir,
    'localrepo': localrepo,
    'srpms': srpms,
})

errors = []
if not config:
    errors.append("No config specified (-r)")
if not basedir:
    errors.append("No --basedir specified")
if not localrepo:
    errors.append("No --localrepo specified")
if not srpms:
    errors.append("No SRPMs specified")

if errors:
    for e in errors:
        print(f"ERROR: {e}", file=sys.stderr)
    invocation['success'] = False
    with open(LOG_FILE, 'a') as f:
        f.write(json.dumps(invocation) + '\n')
    sys.exit(1)

# Produce output
print(f"mockchain: building {len(srpms)} packages with config {config}")
if basedir:
    os.makedirs(basedir, exist_ok=True)
if localrepo:
    os.makedirs(localrepo, exist_ok=True)
    # Write a fake repo metadata file
    with open(os.path.join(localrepo, "repomd.xml"), 'w') as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n<repomd/>\n')
    for srpm in srpms:
        pkg = os.path.basename(srpm).split('-')[0]
        rpm = f"{pkg}-built.x86_64.rpm"
        with open(os.path.join(localrepo, rpm), 'wb') as f:
            f.write(b"\xed\xab\xee\xdb" + rpm.encode())
        print(f"  Built: {rpm}")

print("mockchain: all builds complete")
invocation['success'] = True
with open(LOG_FILE, 'a') as f:
    f.write(json.dumps(invocation) + '\n')
sys.exit(0)
MOCKCHAIN_SCRIPT

chmod +x /usr/local/bin/mockchain

# ── Ensure workspace ownership ────────────────────────────────────────────────
chown -R root:mock /var/lib/mock /var/cache/mock /var/log/mock
chmod -R 775 /var/lib/mock /var/cache/mock /var/log/mock

echo "Setup complete. mock and mockchain are ready at /usr/local/bin/"
echo "Log file: /var/log/mock/mock_invocations.jsonl"