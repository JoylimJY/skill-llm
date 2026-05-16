#!/bin/bash
set -e

# Make heartbeat script executable
chmod +x /workspace/scripts/cron/heartbeat.sh

# Create a mock flyai CLI that follows the CORRECT syntax from references/flyai-cli-docs.md
# i.e.: flyai flight search --from <origin> --to <dest> --date <date> [--type direct] [--json]
# This mock reads the pre-generated raw data when queried for bj->cd 2026-05-01

mkdir -p /usr/local/bin

cat > /usr/local/bin/flyai << 'FLYAI_MOCK'
#!/bin/bash
# Mock FlyAI CLI - implements syntax from references/flyai-cli-docs.md

if [[ "$1" == "--help" ]] || [[ "$1" == "-h" ]]; then
    echo "Fliggy travel CLI v2.2.2"
    echo "Usage: flyai <command> [options]"
    echo ""
    echo "Commands:"
    echo "  flight search    Search for flights"
    exit 0
fi

if [[ "$1" == "flight" ]] && [[ "$2" == "search" ]]; then
    shift 2
    FROM=""
    TO=""
    DATE=""
    TYPE="all"
    TIME_PREF=""
    JSON_MODE=false

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --from) FROM="$2"; shift 2 ;;
            --to)   TO="$2";   shift 2 ;;
            --date) DATE="$2"; shift 2 ;;
            --type) TYPE="$2"; shift 2 ;;
            --time) TIME_PREF="$2"; shift 2 ;;
            --json) JSON_MODE=true; shift ;;
            *) shift ;;
        esac
    done

    if [[ -z "$FROM" ]] || [[ -z "$TO" ]] || [[ -z "$DATE" ]]; then
        echo "Error: Missing required argument" >&2
        exit 1
    fi

    # Serve the Beijing-Chengdu data for the target route
    if [[ ("$FROM" == "北京" || "$FROM" == "PEK" || "$FROM" == "BJS") && \
          ("$TO" == "成都" || "$TO" == "CTU") && \
          "$DATE" == "2026-05-01" ]]; then
        cat /workspace/data/flights/raw/bj_cd_20260501_raw.json
        exit 0
    fi

    # Generic fallback
    echo '{"flights":[]}'
    exit 0
fi

# Wrong syntax guard - old-style commands from SKILL.md body should fail
if [[ "$1" == "search-flight" ]]; then
    echo "Error: Unknown command 'search-flight'. Did you mean 'flight search'?" >&2
    exit 1
fi

echo "Error: Unknown command '$1'" >&2
exit 1
FLYAI_MOCK

chmod +x /usr/local/bin/flyai

echo "Mock flyai CLI installed at /usr/local/bin/flyai"
flyai --help
echo "Setup complete."