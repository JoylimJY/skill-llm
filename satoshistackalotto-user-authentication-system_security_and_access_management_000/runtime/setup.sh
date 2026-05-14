#!/bin/bash
set -e

export OPENCLAW_DATA_DIR="/data"

# -----------------------------------------------------------------------
# Create the openclaw mock binary
# It implements the auth subcommands by manipulating the filesystem
# according to SKILL.md specifications.
# -----------------------------------------------------------------------

cat > /usr/local/bin/openclaw << 'OPENCLAW_MOCK'
#!/bin/bash
# Mock openclaw binary implementing auth subcommands per SKILL.md

set -e
OPENCLAW_DATA_DIR="${OPENCLAW_DATA_DIR:-/data}"
AUTH_DIR="${OPENCLAW_DATA_DIR}/auth"

log_error() { echo "ERROR: $1" >&2; }
log_info() { echo "$1"; }

now_iso() {
    date -u +"%Y-%m-%dT%H:%M:%S+00:00"
}

generate_temp_password() {
    # Generate a compliant temp password: meets policy requirements
    openssl rand -base64 16 | tr -d '/+=' | head -c 10
    echo "Aa1!xSecure"
}

hash_password() {
    local pass="$1"
    local salt
    salt=$(openssl rand -hex 8)
    echo "sha256:${salt}:$(echo -n "${salt}${pass}" | openssl dgst -sha256 | awk '{print $2}')"
}

cmd_user_create() {
    local username="" role="" full_name="" email=""
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --username) username="$2"; shift 2;;
            --role) role="$2"; shift 2;;
            --full-name) full_name="$2"; shift 2;;
            --email) email="$2"; shift 2;;
            *) shift;;
        esac
    done

    if [[ -z "$username" || -z "$role" || -z "$full_name" ]]; then
        log_error "Missing required parameters: --username, --role, --full-name"
        exit 1
    fi

    local user_dir="${AUTH_DIR}/users/${username}"
    if [[ -d "$user_dir" ]]; then
        log_error "User ${username} already exists"
        exit 1
    fi

    # Create directory structure per SKILL.md
    mkdir -p "${user_dir}/sessions"
    mkdir -p "${user_dir}/2fa"

    local created_at
    created_at=$(now_iso)

    # profile.json
    cat > "${user_dir}/profile.json" << EOF
{
  "username": "${username}",
  "full_name": "${full_name}",
  "email": "${email}",
  "role": "${role}",
  "status": "active",
  "created_at": "${created_at}",
  "created_by": "admin",
  "password_change_required": true,
  "2fa_enabled": false
}
EOF

    # credentials.json - password_change_required must be true for new users
    local temp_pass="TempPass1!secure"
    local pw_hash
    pw_hash=$(hash_password "$temp_pass")
    cat > "${user_dir}/credentials.json" << EOF
{
  "password_hash": "${pw_hash}",
  "password_set_at": "${created_at}",
  "password_change_required": true
}
EOF

    # permissions.json - exact structure from SKILL.md: {role, custom:[]}
    cat > "${user_dir}/permissions.json" << EOF
{
  "role": "${role}",
  "custom": []
}
EOF

    # Write admin audit log
    local log_dir="${AUTH_DIR}/logs/admin"
    mkdir -p "$log_dir"
    local log_file="${log_dir}/$(date -u +%Y%m%d).json"
    local entry
    entry=$(cat << EOF
{"timestamp": "${created_at}", "event_type": "administration.user_created", "username": "admin", "target": "${username}", "client_vat": null, "result": "success", "details": {"new_user": "${username}", "role": "${role}"}, "ip_address": "127.0.0.1", "session_id": "mock-session"}
EOF
)
    echo "$entry" >> "$log_file"

    log_info "User ${username} created with role ${role}. Password change required on first login."
    log_info "Temporary password: ${temp_pass}"
}

cmd_assign_clients() {
    local username="" all_clients=false
    local clients=()
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --username) username="$2"; shift 2;;
            --clients) 
                IFS=',' read -ra clients <<< "$2"
                shift 2;;
            --all-clients) all_clients=true; shift;;
            *) shift;;
        esac
    done

    if [[ -z "$username" ]]; then
        log_error "Missing --username"
        exit 1
    fi

    local assignments_path="${AUTH_DIR}/access/client_assignments.json"
    
    if [[ "$all_clients" == "true" ]]; then
        # Update assignments: set all_clients=true
        local tmp
        tmp=$(jq --arg user "$username" \
            '.[$user] = {"all_clients": true, "clients": []}' \
            "$assignments_path")
        echo "$tmp" > "$assignments_path"
        log_info "User ${username} assigned all-client access."
    else
        # Merge new clients into existing
        local clients_json
        clients_json=$(printf '%s\n' "${clients[@]}" | jq -R . | jq -s .)
        local tmp
        tmp=$(jq --arg user "$username" \
            --argjson new_clients "$clients_json" \
            'if .[$user] then
               .[$user].clients = ((.[$user].clients + $new_clients) | unique) |
               .[$user].all_clients = false
             else
               .[$user] = {"all_clients": false, "clients": $new_clients}
             end' \
            "$assignments_path")
        echo "$tmp" > "$assignments_path"
        log_info "Clients assigned to ${username}: ${clients[*]}"
    fi

    # Audit log
    local log_dir="${AUTH_DIR}/logs/admin"
    local log_file="${log_dir}/$(date -u +%Y%m%d).json"
    local now
    now=$(now_iso)
    echo "{\"timestamp\": \"${now}\", \"event_type\": \"administration.clients_assigned\", \"username\": \"admin\", \"target\": \"${username}\", \"result\": \"success\"}" >> "$log_file"
}

cmd_user_list() {
    local format="table"
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --format) format="$2"; shift 2;;
            *) shift;;
        esac
    done
    
    echo "=== User List ==="
    for user_dir in "${AUTH_DIR}/users"/*/; do
        local profile="${user_dir}profile.json"
        if [[ -f "$profile" ]]; then
            jq -r '[.username, .role, .status] | @tsv' "$profile"
        fi
    done
}

cmd_user_deactivate() {
    local username="" reason="" revoke_sessions=false
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --username) username="$2"; shift 2;;
            --reason) reason="$2"; shift 2;;
            --revoke-sessions) revoke_sessions=true; shift;;
            *) shift;;
        esac
    done
    local profile="${AUTH_DIR}/users/${username}/profile.json"
    if [[ ! -f "$profile" ]]; then
        log_error "User ${username} not found"
        exit 1
    fi
    local tmp
    tmp=$(jq '.status = "inactive"' "$profile")
    echo "$tmp" > "$profile"
    log_info "User ${username} deactivated. Reason: ${reason}"
}

# Main dispatch
if [[ "$1" != "auth" ]]; then
    echo "Usage: openclaw auth <command> [options]"
    exit 1
fi
shift

subcmd="$1"
shift

case "$subcmd" in
    user-create) cmd_user_create "$@";;
    assign-clients) cmd_assign_clients "$@";;
    user-list) cmd_user_list "$@";;
    user-deactivate) cmd_user_deactivate "$@";;
    user-update|password-reset|password-policy|role-list|role-create|\
    check-access|access-matrix|security-log|failed-logins|audit-report|\
    2fa-enable|sessions-list|session-revoke)
        log_info "Command '${subcmd}' executed (mock).";;
    *)
        log_error "Unknown auth subcommand: ${subcmd}"
        exit 1;;
esac
OPENCLAW_MOCK

chmod +x /usr/local/bin/openclaw

# Set up OPENCLAW_DATA_DIR env in /etc/environment for all shells
echo "export OPENCLAW_DATA_DIR=/data" >> /etc/profile
echo "export OPENCLAW_DATA_DIR=/data" >> /etc/bash.bashrc

# Set initial permissions on auth dir (permissive initially — agent must harden)
chmod 755 /data/auth/
find /data/auth/users -name "credentials.json" -exec chmod 644 {} \;
find /data/auth/users -name "*.json" -exec chmod 644 {} \;
find /data/auth/roles -name "*.json" -exec chmod 644 {} \;

echo "Setup complete. openclaw mock binary installed at /usr/local/bin/openclaw"
openclaw auth user-list 2>/dev/null || true