#!/bin/bash
set -e

# -----------------------------------------------------------------------
# Mock obsidian-cli: a bash script that simulates vault operations
# It stores vault data in /workspace/.obsidian-cli-state/
# -----------------------------------------------------------------------

mkdir -p /workspace/.obsidian-cli-state

cat > /usr/local/bin/obsidian-cli << 'OBSIDIAN_CLI_EOF'
#!/bin/bash

STATE_DIR="/workspace/.obsidian-cli-state"
DEFAULT_FILE="$STATE_DIR/default_vault"
VAULTS_DIR="$STATE_DIR/vaults"

mkdir -p "$STATE_DIR" "$VAULTS_DIR"

# Helper: get active vault name
get_vault() {
    local vault=""
    # parse --vault "NAME" from args
    local args=("$@")
    for i in "${!args[@]}"; do
        if [[ "${args[$i]}" == "--vault" ]]; then
            vault="${args[$((i+1))]}"
        fi
    done
    if [[ -z "$vault" ]]; then
        if [[ -f "$DEFAULT_FILE" ]]; then
            vault=$(cat "$DEFAULT_FILE")
        fi
    fi
    echo "$vault"
}

# Helper: get vault root dir
vault_dir() {
    local vname="$1"
    # sanitize name
    local safe=$(echo "$vname" | tr ' /' '__')
    echo "$VAULTS_DIR/$safe"
}

CMD="$1"
shift || true

case "$CMD" in

  set-default)
    VNAME="$1"
    echo "$VNAME" > "$DEFAULT_FILE"
    VD=$(vault_dir "$VNAME")
    mkdir -p "$VD"
    echo "Default vault set to: $VNAME"
    ;;

  print-default)
    if [[ "$1" == "--path-only" ]]; then
        if [[ -f "$DEFAULT_FILE" ]]; then
            VNAME=$(cat "$DEFAULT_FILE")
            VD=$(vault_dir "$VNAME")
            echo "$VD"
        else
            exit 1
        fi
    else
        if [[ -f "$DEFAULT_FILE" ]]; then
            cat "$DEFAULT_FILE"
        else
            exit 1
        fi
    fi
    ;;

  daily)
    VAULT=$(get_vault "$@")
    if [[ -z "$VAULT" ]]; then
        echo "ERROR: No vault configured. Run: obsidian-cli set-default VAULT_NAME" >&2
        exit 1
    fi
    VD=$(vault_dir "$VAULT")
    mkdir -p "$VD"
    TODAY=$(date +%Y-%m-%d)
    # Also create today's note if missing (but we still need the create --append for content)
    NOTEFILE="$VD/$TODAY.md"
    if [[ ! -f "$NOTEFILE" ]]; then
        touch "$NOTEFILE"
    fi
    echo "Opened daily note: $TODAY"
    ;;

  create)
    # obsidian-cli create "PATH" --content "TEXT" [--append] [--vault "NAME"]
    FILEPATH="$1"
    shift
    CONTENT=""
    APPEND=false
    VAULT=$(get_vault "$@")

    # parse remaining args
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --content)
                CONTENT="$2"
                shift 2
                ;;
            --append)
                APPEND=true
                shift
                ;;
            --vault)
                shift 2
                ;;
            *)
                shift
                ;;
        esac
    done

    if [[ -z "$VAULT" ]]; then
        if [[ -f "$DEFAULT_FILE" ]]; then
            VAULT=$(cat "$DEFAULT_FILE")
        else
            echo "ERROR: No vault configured." >&2
            exit 1
        fi
    fi

    VD=$(vault_dir "$VAULT")
    FULLPATH="$VD/$FILEPATH"
    mkdir -p "$(dirname "$FULLPATH")"

    if [[ "$APPEND" == "true" ]]; then
        printf '%s' "$CONTENT" >> "$FULLPATH"
        echo "Appended to: $FILEPATH"
    else
        printf '%s' "$CONTENT" > "$FULLPATH"
        echo "Created: $FILEPATH"
    fi
    ;;

  print)
    FILEPATH="$1"
    shift
    VAULT=$(get_vault "$@")

    if [[ -z "$VAULT" ]]; then
        if [[ -f "$DEFAULT_FILE" ]]; then
            VAULT=$(cat "$DEFAULT_FILE")
        else
            echo "ERROR: No vault configured." >&2
            exit 1
        fi
    fi

    VD=$(vault_dir "$VAULT")
    FULLPATH="$VD/$FILEPATH"

    if [[ ! -f "$FULLPATH" ]]; then
        echo "ERROR: Note not found: $FILEPATH" >&2
        exit 1
    fi
    cat "$FULLPATH"
    ;;

  search-content)
    TERM="$1"
    shift
    VAULT=$(get_vault "$@")

    if [[ -z "$VAULT" ]]; then
        if [[ -f "$DEFAULT_FILE" ]]; then
            VAULT=$(cat "$DEFAULT_FILE")
        else
            echo "ERROR: No vault configured." >&2
            exit 1
        fi
    fi

    VD=$(vault_dir "$VAULT")

    if [[ ! -d "$VD" ]]; then
        echo "No notes found."
        exit 0
    fi

    # Search all .md files
    FOUND=0
    while IFS= read -r -d '' f; do
        if grep -qi "$TERM" "$f" 2>/dev/null; then
            REL="${f#$VD/}"
            echo "=== $REL ==="
            grep -i "$TERM" "$f"
            FOUND=1
        fi
    done < <(find "$VD" -name "*.md" -print0 2>/dev/null)

    if [[ $FOUND -eq 0 ]]; then
        echo "No results found for: $TERM"
    fi
    ;;

  search)
    echo "Interactive search not available in non-TTY mode." >&2
    exit 1
    ;;

  *)
    echo "Unknown command: $CMD" >&2
    exit 1
    ;;

esac
OBSIDIAN_CLI_EOF

chmod +x /usr/local/bin/obsidian-cli

# Verify mock works
obsidian-cli print-default --path-only 2>/dev/null && echo "Vault pre-configured (unexpected)" || echo "obsidian-cli mock ready — no default vault set"

echo "Setup complete."