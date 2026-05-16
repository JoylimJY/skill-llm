#!/bin/bash
set -e

# ── Install finml-toolkit as a real bash script ──────────────────────────────
cat > /usr/local/bin/finml-toolkit << 'FINML_SCRIPT'
#!/usr/bin/env bash
# finml-toolkit v2.0.0
# Powered by BytesAgain | bytesagain.com

DATA_DIR="${FINML_TOOLKIT_DIR:-$HOME/.local/share/finml-toolkit}"
mkdir -p "$DATA_DIR"

HISTORY_FILE="$DATA_DIR/history.log"
VERSION="v2.0.0"

timestamp() {
    date '+%Y-%m-%d %H:%M'
}

log_entry() {
    local cmd="$1"
    local input="$2"
    local log_file="$DATA_DIR/${cmd}.log"
    local ts
    ts=$(timestamp)
    echo "${ts}|${input}" >> "$log_file"
    echo "${ts}|${cmd}|${input}" >> "$HISTORY_FILE"
    echo "[finml-toolkit] ${cmd}: ${input}"
}

show_recent_cmd() {
    local cmd="$1"
    local log_file="$DATA_DIR/${cmd}.log"
    if [[ -f "$log_file" ]]; then
        echo "=== Recent ${cmd} entries ==="
        tail -10 "$log_file"
    else
        echo "No ${cmd} entries found."
    fi
}

cmd_stats() {
    echo "=== finml-toolkit stats ==="
    local total=0
    for log_file in "$DATA_DIR"/*.log; do
        [[ -f "$log_file" ]] || continue
        local base
        base=$(basename "$log_file" .log)
        [[ "$base" == "history" ]] && continue
        local count
        count=$(wc -l < "$log_file")
        echo "  ${base}: ${count} entries"
        total=$((total + count))
    done
    echo "  TOTAL: ${total} entries"
}

cmd_export() {
    local fmt="${1:-json}"
    local out_file="$DATA_DIR/export.${fmt}"
    case "$fmt" in
        json)
            echo "{" > "$out_file"
            echo '  "exported_at": "'$(timestamp)'",' >> "$out_file"
            echo '  "entries": [' >> "$out_file"
            local first=1
            while IFS='|' read -r ts cmd_name input; do
                [[ -z "$ts" ]] && continue
                if [[ $first -eq 0 ]]; then
                    echo '    ,' >> "$out_file"
                fi
                echo '    {"timestamp": "'"$ts"'", "command": "'"$cmd_name"'", "input": "'"$input"'"}' >> "$out_file"
                first=0
            done < "$HISTORY_FILE"
            echo '  ]' >> "$out_file"
            echo '}' >> "$out_file"
            echo "[finml-toolkit] Exported to $out_file"
            ;;
        csv)
            echo "timestamp,command,input" > "$out_file"
            while IFS='|' read -r ts cmd_name input; do
                [[ -z "$ts" ]] && continue
                echo "\"$ts\",\"$cmd_name\",\"$input\"" >> "$out_file"
            done < "$HISTORY_FILE"
            echo "[finml-toolkit] Exported to $out_file"
            ;;
        txt)
            cp "$HISTORY_FILE" "$out_file" 2>/dev/null || touch "$out_file"
            echo "[finml-toolkit] Exported to $out_file"
            ;;
        *)
            echo "[finml-toolkit] Unknown export format: $fmt"
            exit 1
            ;;
    esac
}

cmd_search() {
    local term="$1"
    echo "=== Search results for: ${term} ==="
    if [[ -f "$HISTORY_FILE" ]]; then
        grep -i "$term" "$HISTORY_FILE" || echo "(no results)"
    else
        echo "(no history found)"
    fi
}

cmd_recent() {
    echo "=== 20 most recent entries ==="
    if [[ -f "$HISTORY_FILE" ]]; then
        tail -20 "$HISTORY_FILE"
    else
        echo "(no history found)"
    fi
}

cmd_status() {
    local input="$1"
    if [[ -n "$input" ]]; then
        log_entry "status" "$input"
    else
        echo "=== finml-toolkit status ==="
        echo "  Version: $VERSION"
        echo "  Data dir: $DATA_DIR"
        local count=0
        [[ -f "$HISTORY_FILE" ]] && count=$(wc -l < "$HISTORY_FILE")
        echo "  Total entries: $count"
        echo "  Disk usage: $(du -sh "$DATA_DIR" 2>/dev/null | cut -f1)"
    fi
}

cmd_help() {
    echo "finml-toolkit $VERSION"
    echo ""
    echo "Commands:"
    echo "  run <input>      Log a run entry"
    echo "  check <input>    Log a check entry"
    echo "  convert <input>  Log a convert entry"
    echo "  analyze <input>  Log an analyze entry"
    echo "  generate <input> Log a generate entry"
    echo "  preview <input>  Log a preview entry"
    echo "  batch <input>    Log a batch entry"
    echo "  compare <input>  Log a compare entry"
    echo "  export <fmt>     Export all data (json, csv, txt)"
    echo "  config <input>   Log a config entry"
    echo "  status [input]   Health check or log status entry"
    echo "  report <input>   Log a report entry"
    echo "  stats            Show summary statistics"
    echo "  search <term>    Search all log entries"
    echo "  recent           Show 20 most recent entries"
    echo "  help             Show this help"
    echo "  version          Show version"
}

CMD="${1}"
shift || true
INPUT="$*"

case "$CMD" in
    run)
        if [[ -z "$INPUT" ]]; then show_recent_cmd "run"; else log_entry "run" "$INPUT"; fi ;;
    check)
        if [[ -z "$INPUT" ]]; then show_recent_cmd "check"; else log_entry "check" "$INPUT"; fi ;;
    convert)
        if [[ -z "$INPUT" ]]; then show_recent_cmd "convert"; else log_entry "convert" "$INPUT"; fi ;;
    analyze)
        if [[ -z "$INPUT" ]]; then show_recent_cmd "analyze"; else log_entry "analyze" "$INPUT"; fi ;;
    generate)
        if [[ -z "$INPUT" ]]; then show_recent_cmd "generate"; else log_entry "generate" "$INPUT"; fi ;;
    preview)
        if [[ -z "$INPUT" ]]; then show_recent_cmd "preview"; else log_entry "preview" "$INPUT"; fi ;;
    batch)
        if [[ -z "$INPUT" ]]; then show_recent_cmd "batch"; else log_entry "batch" "$INPUT"; fi ;;
    compare)
        if [[ -z "$INPUT" ]]; then show_recent_cmd "compare"; else log_entry "compare" "$INPUT"; fi ;;
    export)
        cmd_export "$INPUT" ;;
    config)
        if [[ -z "$INPUT" ]]; then show_recent_cmd "config"; else log_entry "config" "$INPUT"; fi ;;
    status)
        cmd_status "$INPUT" ;;
    report)
        if [[ -z "$INPUT" ]]; then show_recent_cmd "report"; else log_entry "report" "$INPUT"; fi ;;
    stats)
        cmd_stats ;;
    search)
        cmd_search "$INPUT" ;;
    recent)
        cmd_recent ;;
    help)
        cmd_help ;;
    version)
        echo "finml-toolkit $VERSION" ;;
    *)
        echo "[finml-toolkit] Unknown command: $CMD"
        echo "Run 'finml-toolkit help' for usage."
        exit 1 ;;
esac
FINML_SCRIPT

chmod +x /usr/local/bin/finml-toolkit

echo "finml-toolkit installed at /usr/local/bin/finml-toolkit"
finml-toolkit version