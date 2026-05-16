#!/bin/bash
set -e

# Create a stateful mock `dawn` CLI binary
# State is persisted in /tmp/dawn_state/

mkdir -p /tmp/dawn_state

cat > /usr/local/bin/dawn << 'DAWN_EOF'
#!/bin/bash

STATE_DIR="/tmp/dawn_state"
mkdir -p "$STATE_DIR"

CMD1="${1:-}"
CMD2="${2:-}"
CMD3="${3:-}"
CMD4="${4:-}"
CMD5="${5:-}"

# Helper: read state
get_state() { cat "$STATE_DIR/$1" 2>/dev/null || echo ""; }
set_state() { echo "$2" > "$STATE_DIR/$1"; }

case "$CMD1" in

  version)
    echo "dawn/2.4.1 linux-x64 node-v20.11.0"
    ;;

  --help|help)
    echo "Dawn CLI - Prediction Market Strategy Automation"
    echo ""
    echo "Usage: dawn <command> [options]"
    echo ""
    echo "Commands:"
    echo "  auth login|status|logout"
    echo "  account overview|fund|wallet"
    echo "  strategy create|list|status|revise|rules|code|launch|positions"
    echo "  run list|status|logs|stop"
    ;;

  auth)
    case "$CMD2" in
      login)
        set_state "auth_status" "authenticated"
        set_state "auth_user" "testuser@dawnai.com"
        echo "✓ Authenticated as testuser@dawnai.com"
        ;;
      status)
        AUTH=$(get_state "auth_status")
        if [ "$AUTH" = "authenticated" ]; then
          echo "✓ Logged in as testuser@dawnai.com"
        else
          echo "Not authenticated. Run: dawn auth login"
          exit 1
        fi
        ;;
      logout)
        rm -f "$STATE_DIR/auth_status"
        echo "✓ Logged out"
        ;;
    esac
    ;;

  account)
    AUTH=$(get_state "auth_status")
    if [ "$AUTH" != "authenticated" ]; then
      echo "Not authenticated. Run: dawn auth login"; exit 1
    fi
    case "$CMD2" in
      overview)
        echo "Account: testuser@dawnai.com"
        echo "Balance: \$500.00 (paper) / \$0.00 (live)"
        echo "Active runs: $(get_state 'run_active' | grep -c '.' || echo 0)"
        ;;
      fund)
        echo "Funding path: Paper balance pre-loaded (\$500 available for paper runs)"
        echo "For live runs, connect wallet at: https://dawn.ai/wallet"
        ;;
      wallet)
        echo "Wallet: Not connected (paper mode only)"
        ;;
    esac
    ;;

  strategy)
    AUTH=$(get_state "auth_status")
    if [ "$AUTH" != "authenticated" ]; then
      echo "Not authenticated. Run: dawn auth login"; exit 1
    fi

    case "$CMD2" in
      create)
        PROMPT="$CMD3"
        if [ -z "$PROMPT" ]; then
          echo "Error: strategy text required"; exit 1
        fi
        CONV_ID="conv_$(cat /proc/sys/kernel/random/uuid | tr -d '-' | head -c 12)"
        set_state "conversation_id" "$CONV_ID"
        set_state "conv_${CONV_ID}_status" "drafting"
        set_state "conv_${CONV_ID}_rules_approved" "false"
        set_state "conv_${CONV_ID}_code_generated" "false"
        set_state "conv_${CONV_ID}_prompt" "$PROMPT"
        echo "✓ Strategy conversation created"
        echo "  conversationId: $CONV_ID"
        echo "  Status: drafting"
        echo ""
        echo "Next steps:"
        echo "  Review rules:   dawn strategy rules $CONV_ID list"
        echo "  Approve rules:  dawn strategy rules $CONV_ID approve-all"
        echo "  Generate code:  dawn strategy code $CONV_ID generate"
        ;;

      list)
        CONV_ID=$(get_state "conversation_id")
        if [ -z "$CONV_ID" ]; then
          echo "No strategies found."
        else
          STATUS=$(get_state "conv_${CONV_ID}_status")
          echo "Strategies:"
          echo "  - conversationId: $CONV_ID  status: $STATUS"
        fi
        ;;

      status)
        CONV_ID="$CMD3"
        if [ -z "$CONV_ID" ]; then
          echo "Error: conversationId required"; exit 1
        fi
        STATUS=$(get_state "conv_${CONV_ID}_status")
        if [ -z "$STATUS" ]; then
          echo "Error: conversation not found: $CONV_ID"; exit 1
        fi
        RULES=$(get_state "conv_${CONV_ID}_rules_approved")
        CODE=$(get_state "conv_${CONV_ID}_code_generated")
        echo "conversationId: $CONV_ID"
        echo "status: $STATUS"
        echo "rulesApproved: $RULES"
        echo "codeGenerated: $CODE"
        ;;

      revise)
        CONV_ID="$CMD3"
        REVISION="$CMD4"
        STATUS=$(get_state "conv_${CONV_ID}_status")
        if [ -z "$STATUS" ]; then
          echo "Error: conversation not found: $CONV_ID"; exit 1
        fi
        set_state "conv_${CONV_ID}_status" "revised"
        echo "✓ Strategy revised for conversation $CONV_ID"
        echo "  New status: revised"
        ;;

      rules)
        CONV_ID="$CMD3"
        SUBCMD="$CMD4"
        STATUS=$(get_state "conv_${CONV_ID}_status")
        if [ -z "$STATUS" ]; then
          echo "Error: conversation not found: $CONV_ID"; exit 1
        fi
        case "$SUBCMD" in
          list)
            echo "Rules for $CONV_ID:"
            echo "  [0] Max position size: \$20 per market"
            echo "  [1] Exit after 48h or 15% profit"
            echo "  [2] Only trade on verified prediction markets"
            echo "  [3] No leverage allowed in paper mode"
            APPROVED=$(get_state "conv_${CONV_ID}_rules_approved")
            echo "  Approved: $APPROVED"
            ;;
          approve)
            RULE_IDX="$CMD5"
            echo "✓ Rule [$RULE_IDX] approved for $CONV_ID"
            ;;
          approve-all)
            set_state "conv_${CONV_ID}_rules_approved" "true"
            echo "✓ All rules approved for conversation $CONV_ID"
            echo "  Next: dawn strategy code $CONV_ID generate"
            ;;
        esac
        ;;

      code)
        CONV_ID="$CMD3"
        SUBCMD="$CMD4"
        STATUS=$(get_state "conv_${CONV_ID}_status")
        if [ -z "$STATUS" ]; then
          echo "Error: conversation not found: $CONV_ID"; exit 1
        fi

        case "$SUBCMD" in
          status)
            CODE=$(get_state "conv_${CONV_ID}_code_generated")
            echo "Code generation status for $CONV_ID:"
            echo "  generated: $CODE"
            if [ "$CODE" = "true" ]; then
              echo "  files: strategy.py, config.json, rules.json"
            fi
            ;;
          generate)
            RULES=$(get_state "conv_${CONV_ID}_rules_approved")
            if [ "$RULES" != "true" ]; then
              echo "Error: Rules must be approved before generating code."
              echo "  Run: dawn strategy rules $CONV_ID approve-all"
              exit 1
            fi
            set_state "conv_${CONV_ID}_code_generated" "true"
            echo "✓ Code generated for conversation $CONV_ID"
            echo "  Files: strategy.py, config.json, rules.json"
            ;;
          export)
            CODE=$(get_state "conv_${CONV_ID}_code_generated")
            if [ "$CODE" != "true" ]; then
              echo "Error: No code generated yet. Run: dawn strategy code $CONV_ID generate"
              exit 1
            fi
            # Parse flags
            USE_JSON=false
            OUT_PATH=""
            shift 4  # skip 'dawn strategy code <id>'
            while [[ $# -gt 0 ]]; do
              case "$1" in
                --json) USE_JSON=true ;;
                --out) OUT_PATH="$2"; shift ;;
              esac
              shift
            done
            if [ "$USE_JSON" = "true" ]; then
              EXPORT_DATA="{\"strategy.py\": \"import dawn_sdk\\nclass PoliticalMarketStrategy:\\n    def on_tick(self, market): pass\\n\", \"config.json\": \"{\\\"max_exposure\\\": 20, \\\"exit_hours\\\": 48}\", \"rules.json\": \"{\\\"approved\\\": true, \\\"count\\\": 4}\"}"
              if [ -n "$OUT_PATH" ]; then
                echo "$EXPORT_DATA" > "$OUT_PATH"
                echo "✓ Code exported (JSON map) to $OUT_PATH"
              else
                echo "$EXPORT_DATA"
              fi
            else
              if [ -n "$OUT_PATH" ]; then
                echo "# strategy.py - Political Market Strategy" > "$OUT_PATH"
                echo "✓ Code exported to $OUT_PATH"
              else
                echo "# strategy.py"
                echo "import dawn_sdk"
                echo "class PoliticalMarketStrategy:"
                echo "    def on_tick(self, market): pass"
              fi
            fi
            ;;
          upload)
            FILEPATH="$CMD5"
            if [ ! -f "$FILEPATH" ]; then
              echo "Error: File not found: $FILEPATH"; exit 1
            fi
            set_state "conv_${CONV_ID}_code_generated" "true"
            set_state "conv_${CONV_ID}_uploaded_file" "$FILEPATH"
            echo "✓ Strategy code uploaded from $FILEPATH"
            echo "  conversationId: $CONV_ID"
            ;;
        esac
        ;;

      launch)
        CONV_ID="$CMD3"
        STATUS=$(get_state "conv_${CONV_ID}_status")
        if [ -z "$STATUS" ]; then
          echo "Error: conversation not found: $CONV_ID"; exit 1
        fi
        CODE=$(get_state "conv_${CONV_ID}_code_generated")
        if [ "$CODE" != "true" ]; then
          echo "Error: No strategy version found. Generate or upload code first."
          exit 1
        fi
        # Parse flags
        BUDGET=""
        LIVE=false
        HOURS=""
        shift 3
        while [[ $# -gt 0 ]]; do
          case "$1" in
            --budget) BUDGET="$2"; shift ;;
            --live) LIVE=true ;;
            --hours) HOURS="$2"; shift ;;
          esac
          shift
        done
        if [ -z "$BUDGET" ]; then
          echo "Error: --budget is required"; exit 1
        fi
        STRAT_ID="strat_$(cat /proc/sys/kernel/random/uuid | tr -d '-' | head -c 10)"
        set_state "conv_${CONV_ID}_strategy_id" "$STRAT_ID"
        set_state "conv_${CONV_ID}_live" "$LIVE"
        set_state "conv_${CONV_ID}_budget" "$BUDGET"
        set_state "conv_${CONV_ID}_hours" "${HOURS:-24}"
        set_state "conv_${CONV_ID}_running" "true"
        set_state "run_active" "$CONV_ID"
        MODE="paper"
        if [ "$LIVE" = "true" ]; then MODE="live"; fi
        echo "✓ Strategy launched"
        echo "  conversationId: $CONV_ID"
        echo "  strategyId: $STRAT_ID"
        echo "  mode: $MODE"
        echo "  budget: \$$BUDGET"
        echo "  hours: ${HOURS:-24}"
        echo "  isRunning: true"
        ;;

      positions)
        CONV_ID="$CMD3"
        STRAT_ID=$(get_state "conv_${CONV_ID}_strategy_id")
        # Support --strategy-id flag
        shift 3
        while [[ $# -gt 0 ]]; do
          case "$1" in
            --strategy-id) STRAT_ID="$2"; shift ;;
          esac
          shift
        done
        RUNNING=$(get_state "conv_${CONV_ID}_running")
        if [ "$RUNNING" != "true" ]; then
          echo "No active positions (run not active)"
        else
          echo "Positions for $CONV_ID (strategyId: $STRAT_ID):"
          echo "  MARKET: 2024-US-ELECTION-DEM  SIDE: YES  SHARES: 150  ENTRY: \$0.52  CURRENT: \$0.61  PnL: +\$13.50"
          echo "  MARKET: 2024-EU-PARLIAMENT    SIDE: NO   SHARES: 80   ENTRY: \$0.48  CURRENT: \$0.45  PnL: -\$2.40"
          echo "  Total PnL: +\$11.10"
        fi
        ;;
    esac
    ;;

  run)
    AUTH=$(get_state "auth_status")
    if [ "$AUTH" != "authenticated" ]; then
      echo "Not authenticated. Run: dawn auth login"; exit 1
    fi

    case "$CMD2" in
      list)
        ACTIVE=$(get_state "run_active")
        if [ -z "$ACTIVE" ]; then
          echo "No active runs."
        else
          STRAT_ID=$(get_state "conv_${ACTIVE}_strategy_id")
          RUNNING=$(get_state "conv_${ACTIVE}_running")
          LIVE=$(get_state "conv_${ACTIVE}_live")
          MODE="paper"
          if [ "$LIVE" = "true" ]; then MODE="live"; fi
          echo "Active runs:"
          echo "  conversationId: $ACTIVE  strategyId: $STRAT_ID  mode: $MODE  isRunning: $RUNNING"
        fi
        ;;

      status)
        CONV_ID="$CMD3"
        if [ -z "$CONV_ID" ]; then
          echo "Error: conversationId required"; exit 1
        fi
        STRAT_ID=$(get_state "conv_${CONV_ID}_strategy_id")
        RUNNING=$(get_state "conv_${CONV_ID}_running")
        LIVE=$(get_state "conv_${CONV_ID}_live")
        BUDGET=$(get_state "conv_${CONV_ID}_budget")
        HOURS=$(get_state "conv_${CONV_ID}_hours")
        if [ -z "$RUNNING" ]; then
          echo "No run found for conversationId: $CONV_ID"
          exit 1
        fi
        MODE="paper"
        if [ "$LIVE" = "true" ]; then MODE="live"; fi
        echo "Run status for $CONV_ID:"
        echo "  strategyId: $STRAT_ID"
        echo "  isRunning: $RUNNING"
        echo "  mode: $MODE"
        echo "  budget: \$$BUDGET"
        echo "  hours: $HOURS"
        TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
        echo "  timestamp: $TIMESTAMP"
        ;;

      logs)
        CONV_ID="$CMD3"
        LIMIT=10
        shift 3
        while [[ $# -gt 0 ]]; do
          case "$1" in
            --limit) LIMIT="$2"; shift ;;
          esac
          shift
        done
        RUNNING=$(get_state "conv_${CONV_ID}_running")
        if [ -z "$RUNNING" ]; then
          echo "No logs found for: $CONV_ID"; exit 1
        fi
        STRAT_ID=$(get_state "conv_${CONV_ID}_strategy_id")
        TS=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
        echo "Logs for $CONV_ID (last $LIMIT):"
        echo "  [$TS] INFO  strategyId=$STRAT_ID  event=TICK  market=2024-US-ELECTION-DEM"
        echo "  [$TS] INFO  strategyId=$STRAT_ID  event=ORDER_PLACED  side=YES  shares=150"
        echo "  [$TS] INFO  strategyId=$STRAT_ID  event=TICK  market=2024-EU-PARLIAMENT"
        echo "  [$TS] INFO  strategyId=$STRAT_ID  event=ORDER_PLACED  side=NO  shares=80"
        echo "  [$TS] INFO  strategyId=$STRAT_ID  event=PNL_UPDATE  total_pnl=+11.10"
        ;;

      stop)
        CONV_ID="$CMD3"
        RUNNING=$(get_state "conv_${CONV_ID}_running")
        if [ -z "$RUNNING" ]; then
          echo "No strategies found for this agent. Verify conversationId."; exit 1
        fi
        if [ "$RUNNING" != "true" ]; then
          echo "Run already stopped for: $CONV_ID"
        else
          set_state "conv_${CONV_ID}_running" "false"
          STRAT_ID=$(get_state "conv_${CONV_ID}_strategy_id")
          echo "✓ Run stopped"
          echo "  conversationId: $CONV_ID"
          echo "  strategyId: $STRAT_ID"
          echo "  isRunning: false"
        fi
        ;;
    esac
    ;;

  *)
    echo "Unknown command: $CMD1"
    echo "Run 'dawn --help' for usage"
    exit 1
    ;;
esac
DAWN_EOF

chmod +x /usr/local/bin/dawn

# Verify mock dawn works
dawn version

echo "Mock dawn CLI installed and verified."