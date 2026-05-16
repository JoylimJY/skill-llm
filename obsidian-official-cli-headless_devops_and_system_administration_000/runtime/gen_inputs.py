import os
import stat
import textwrap
from pathlib import Path

workspace = Path("/workspace")

# ── directory structure ──────────────────────────────────────────────────────
dirs = [
    "scripts",
    "references",
    "vault-data/daily",
    "vault-data/projects/alpha",
    "vault-data/projects/beta",
    "vault-data/archive/2023",
    "vault-data/archive/2024",
    "logs",
    "config-backups",
    "tmp/scratch",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# ── distractor files (at least 10) ──────────────────────────────────────────
distractors = {
    "vault-data/daily/2024-01-15.md": "# Jan 15\nMeeting with Prof. Chen.\n",
    "vault-data/daily/2024-01-16.md": "# Jan 16\nData pipeline review.\n",
    "vault-data/projects/alpha/README.md": "# Alpha Project\nHigh-energy physics simulation notes.\n",
    "vault-data/projects/beta/notes.md": "# Beta\nMachine learning experiment logs.\n",
    "vault-data/archive/2023/summary.md": "# 2023 Summary\nAnnual research digest.\n",
    "vault-data/archive/2024/q1.md": "# Q1 2024\nFirst quarter milestones.\n",
    "logs/install.log": "-- previous install attempt failed --\nmissing xvfb\n",
    "logs/cron.log": "0 6 * * * /usr/local/bin/obs daily:path\n",
    "config-backups/obsidian.json.bak": '{"vaults":{}}\n',
    "tmp/scratch/old_wrapper.sh": "#!/bin/bash\n# obsolete wrapper - do not use\nexec /usr/bin/obsidian \"$@\"\n",
    "tmp/scratch/notes.txt": "vault location confirmed: /root/research-vault\nuser: obsidian (to be created)\n",
    "references/architecture.md": textwrap.dedent("""\
        # Architecture Notes

        ## Why a non-root user?
        Obsidian (Electron) refuses to run as root on most systems.
        A dedicated `obsidian` system user sidesteps this.

        ## Why Xvfb?
        The CLI still initialises an Electron window internally.
        Xvfb provides a virtual framebuffer so no physical display is needed.

        ## Why ACLs over chown?
        When the vault sits under /root, chown would transfer ownership away
        from root. ACLs grant read/write to the obsidian user without touching
        ownership, preserving security boundaries.

        ## Wrapper design
        /usr/local/bin/obs wraps:
          su - obsidian -c 'cd <vault> && xvfb-run -a /usr/bin/obsidian --disable-gpu ...'
        This keeps display and user switching invisible to callers.
    """),
    "references/troubleshooting.md": textwrap.dedent("""\
        # Troubleshooting

        ## CLI hangs at startup
        Ensure Xvfb is running before invoking obsidian. Use xvfb-run -a.

        ## Permission denied on vault
        Check ACLs with: getfacl <vault_path>
        Re-run configure_official_cli.sh if ACL entries are missing.

        ## obsidian.json not found
        configure_official_cli.sh writes ~/.config/obsidian/obsidian.json
        for the obsidian user. Verify the file exists under that home dir.

        ## GPU errors in logs
        Always pass --disable-gpu on headless hosts.
    """),
}
for rel, content in distractors.items():
    p = workspace / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)

# ── scripts/install_official_obsidian.sh (mock – simulates real install) ─────
install_sh = workspace / "scripts/install_official_obsidian.sh"
install_sh.write_text(textwrap.dedent("""\
    #!/usr/bin/env bash
    # Mock: simulates official Obsidian .deb install on a headless server.
    set -euo pipefail

    OBSIDIAN_VERSION="1.7.4"
    OBSIDIAN_BIN="/usr/bin/obsidian"

    echo "[install] Creating obsidian system user..."
    if ! id obsidian &>/dev/null; then
        useradd --system --create-home --shell /bin/bash obsidian
    fi

    echo "[install] Installing Obsidian ${OBSIDIAN_VERSION} (mock)..."
    # Simulate binary placement
    cat > "${OBSIDIAN_BIN}" <<'MOCK_BIN'
#!/usr/bin/env bash
# Mock Obsidian CLI binary
VERSION="1.7.4"
CMD="${1:-}"
shift || true
case "${CMD}" in
    help)      echo "Obsidian CLI ${VERSION} -- help output" ;;
    vault)     echo "Active vault: ${OBSIDIAN_VAULT:-<none>}" ;;
    daily:path) echo "Daily note path: ${OBSIDIAN_VAULT:-<none>}/daily/$(date +%Y-%m-%d).md" ;;
    daily:append) echo "Appended to daily note." ;;
    daily:read) echo "Daily note content: (mock)" ;;
    search)    echo "Search results: (mock)" ;;
    *)         echo "Unknown command: ${CMD}"; exit 1 ;;
esac
MOCK_BIN
    chmod +x "${OBSIDIAN_BIN}"

    echo "[install] Recording installed version..."
    mkdir -p /var/lib/obsidian-cli
    echo "${OBSIDIAN_VERSION}" > /var/lib/obsidian-cli/version

    echo "[install] Done. Obsidian ${OBSIDIAN_VERSION} installed."
"""))
install_sh.chmod(0o755)

# ── scripts/configure_official_cli.sh (mock) ─────────────────────────────────
configure_sh = workspace / "scripts/configure_official_cli.sh"
configure_sh.write_text(textwrap.dedent("""\
    #!/usr/bin/env bash
    # Mock: configures obsidian user, ACLs, obsidian.json, and obs wrapper.
    set -euo pipefail

    VAULT_PATH="${1:?Usage: configure_official_cli.sh <vault_path>}"

    echo "[configure] Vault path: ${VAULT_PATH}"

    # Ensure obsidian user exists
    if ! id obsidian &>/dev/null; then
        echo "[configure] ERROR: run install script first." >&2
        exit 1
    fi

    OBSIDIAN_HOME=$(getent passwd obsidian | cut -d: -f6)

    echo "[configure] Applying ACLs to vault..."
    mkdir -p "${VAULT_PATH}"
    # Grant obsidian user rwx on the vault tree
    setfacl -R -m u:obsidian:rwx "${VAULT_PATH}" 2>/dev/null || \
        chmod -R o+rwx "${VAULT_PATH}"  # fallback if no ACL support

    echo "[configure] Writing obsidian.json for obsidian user..."
    CONF_DIR="${OBSIDIAN_HOME}/.config/obsidian"
    mkdir -p "${CONF_DIR}"
    VAULT_ID="$(echo "${VAULT_PATH}" | md5sum | cut -c1-8)"
    cat > "${CONF_DIR}/obsidian.json" <<JSON
{
  "vaults": {
    "${VAULT_ID}": {
      "path": "${VAULT_PATH}",
      "ts": $(date +%s)000,
      "open": true
    }
  }
}
JSON
    chown -R obsidian:obsidian "${CONF_DIR}"

    echo "[configure] Writing /usr/local/bin/obs wrapper..."
    cat > /usr/local/bin/obs <<WRAPPER
#!/usr/bin/env bash
# obs – headless Obsidian CLI wrapper
# Generated by configure_official_cli.sh
VAULT="${VAULT_PATH}"
exec su - obsidian -c "cd \${VAULT} && OBSIDIAN_VAULT=\${VAULT} xvfb-run -a /usr/bin/obsidian --disable-gpu \$*"
WRAPPER
    chmod +x /usr/local/bin/obs

    echo "[configure] Recording active vault..."
    mkdir -p /var/lib/obsidian-cli
    echo "${VAULT_PATH}" > /var/lib/obsidian-cli/active-vault

    echo "[configure] Done."
"""))
configure_sh.chmod(0o755)

# ── scripts/verify_official_cli.sh (mock) ────────────────────────────────────
verify_sh = workspace / "scripts/verify_official_cli.sh"
verify_sh.write_text(textwrap.dedent("""\
    #!/usr/bin/env bash
    # Mock: verifies the obs wrapper and key CLI commands.
    set -euo pipefail

    VAULT_PATH="${1:-$(cat /var/lib/obsidian-cli/active-vault 2>/dev/null || echo '/root/obsidian-vault')}"
    PASS=0
    FAIL=0
    RESULTS=""

    run_check() {
        local label="$1"; shift
        if output=$(obs "$@" 2>&1); then
            echo "  [OK]  ${label}: ${output}"
            RESULTS="${RESULTS}${label}=OK\\n"
            PASS=$((PASS+1))
        else
            echo "  [FAIL] ${label}"
            RESULTS="${RESULTS}${label}=FAIL\\n"
            FAIL=$((FAIL+1))
        fi
    }

    echo "=== Obsidian CLI Verification ==="
    echo "Vault: ${VAULT_PATH}"
    echo ""

    run_check "help"         help
    run_check "vault"        vault
    run_check "daily:path"   daily:path
    run_check "daily:append" daily:append content="skill verification"
    run_check "daily:read"   daily:read
    run_check "search"       search query="skill verification"

    echo ""
    echo "=== Results: ${PASS} passed, ${FAIL} failed ==="

    mkdir -p /var/lib/obsidian-cli
    printf "${RESULTS}" > /var/lib/obsidian-cli/verify-results

    [ "${FAIL}" -eq 0 ]
"""))
verify_sh.chmod(0o755)

# ── intentionally broken/incomplete config as red herring ────────────────────
(workspace / "config-backups" / "partial_wrapper.sh").write_text(textwrap.dedent("""\
    #!/bin/bash
    # Incomplete wrapper found during server audit - DO NOT USE
    # Missing: xvfb-run, user switching, vault cd
    exec /usr/bin/obsidian "$@"
"""))

(workspace / "config-backups" / "old_obsidian.json").write_text(
    '{"vaults": {"deadbeef": {"path": "/tmp/old-vault", "ts": 1700000000000}}}\n'
)

print("Workspace generated successfully.")
print("Vault for this task: /root/research-vault")