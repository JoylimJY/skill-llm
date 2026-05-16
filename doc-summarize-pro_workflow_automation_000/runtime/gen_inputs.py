import os
import random
import string

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# ─── Create the doc-summarize-pro script structure ────────────────────────────
scripts_dir = os.path.join(workspace, "scripts")
os.makedirs(scripts_dir, exist_ok=True)

# The actual bash script implementing the skill
script_content = r"""#!/usr/bin/env bash
set -euo pipefail

TOOL_DIR="$HOME/.doc-summarize-pro"
CONFIG_FILE="$TOOL_DIR/config"
HISTORY_FILE="$TOOL_DIR/history.log"

mkdir -p "$TOOL_DIR"

# Initialize config with defaults if missing
if [[ ! -f "$CONFIG_FILE" ]]; then
    echo "summary_sentences=2" > "$CONFIG_FILE"
    echo "keyword_count=15"   >> "$CONFIG_FILE"
fi

get_config() {
    local key="$1"
    grep "^${key}=" "$CONFIG_FILE" 2>/dev/null | cut -d'=' -f2 | tail -1
}

log_history() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "$HISTORY_FILE"
}

cmd="${1:-help}"
shift || true

case "$cmd" in

  version)
    echo "doc-summarize-pro v3.0.0"
    log_history "version"
    ;;

  help)
    echo "doc-summarize-pro — Document Analysis Toolkit"
    echo ""
    echo "Commands:"
    echo "  summarize <file>         Generate document summary"
    echo "  keywords <file>          Extract keywords by frequency"
    echo "  outline <file>           Extract document outline/structure"
    echo "  stats <file>             Show document statistics"
    echo "  compare <file1> <file2>  Compare two documents"
    echo "  batch <dir>              Batch-summarize all text files in directory"
    echo "  export <file> <format>   Export summary (md|txt|json)"
    echo "  history                  Show processing history"
    echo "  config [key] [value]     View or update configuration"
    echo "  version                  Print version"
    echo "  help                     Show this help"
    ;;

  config)
    if [[ $# -eq 0 ]]; then
        echo "=== Configuration ==="
        cat "$CONFIG_FILE"
    elif [[ $# -eq 1 ]]; then
        val=$(get_config "$1")
        echo "$1=$val"
    elif [[ $# -eq 2 ]]; then
        key="$1"; val="$2"
        # Remove old entry and append new
        tmp=$(grep -v "^${key}=" "$CONFIG_FILE" 2>/dev/null || true)
        echo "$tmp" > "$CONFIG_FILE"
        echo "${key}=${val}" >> "$CONFIG_FILE"
        # Clean blank lines
        sed -i '/^[[:space:]]*$/d' "$CONFIG_FILE"
        echo "Config updated: ${key}=${val}"
        log_history "config ${key} ${val}"
    fi
    ;;

  stats)
    file="${1:?stats requires a file argument}"
    [[ -f "$file" ]] || { echo "ERROR: File not found: $file"; exit 1; }
    content=$(cat "$file")
    word_count=$(echo "$content" | wc -w | tr -d ' ')
    char_count=$(echo "$content" | wc -c | tr -d ' ')
    para_count=$(echo "$content" | awk 'BEGIN{p=0;blank=1} /^[[:space:]]*$/{blank=1} /^[^[:space:]]/{if(blank){p++};blank=0} END{print p}')
    sent_count=$(echo "$content" | grep -oE '[^.!?]+[.!?]' | wc -l | tr -d ' ')
    unique_words=$(echo "$content" | tr -cs 'A-Za-z' '\n' | tr 'A-Z' 'a-z' | sort -u | wc -l | tr -d ' ')
    reading_time=$(echo "$word_count / 200" | bc 2>/dev/null || echo "0")
    echo "=== Document Statistics: $file ==="
    echo "Word Count:       $word_count"
    echo "Character Count:  $char_count"
    echo "Paragraph Count:  $para_count"
    echo "Sentence Count:   $sent_count"
    echo "Unique Words:     $unique_words"
    echo "Reading Time:     ~${reading_time} min"
    log_history "stats $file"
    ;;

  summarize)
    file="${1:?summarize requires a file argument}"
    [[ -f "$file" ]] || { echo "ERROR: File not found: $file"; exit 1; }
    n=$(get_config "summary_sentences")
    n=${n:-2}
    echo "=== Summary: $file ==="
    awk -v n="$n" '
    BEGIN { para=""; blank=1 }
    /^[[:space:]]*$/ {
        if (para != "") {
            split(para, sents, /[.!?]+/)
            count=0
            for (i=1; i<=length(sents); i++) {
                s = sents[i]
                gsub(/^[ \t]+|[ \t]+$/, "", s)
                if (s != "" && count < n) {
                    print s "."
                    count++
                }
            }
            print ""
        }
        para=""
        blank=1
        next
    }
    /^#/ { next }
    {
        if (para == "") para = $0
        else para = para " " $0
        blank=0
    }
    END {
        if (para != "") {
            split(para, sents, /[.!?]+/)
            count=0
            for (i=1; i<=length(sents); i++) {
                s = sents[i]
                gsub(/^[ \t]+|[ \t]+$/, "", s)
                if (s != "" && count < n) {
                    print s "."
                    count++
                }
            }
        }
    }
    ' "$file"
    log_history "summarize $file"
    ;;

  keywords)
    file="${1:?keywords requires a file argument}"
    [[ -f "$file" ]] || { echo "ERROR: File not found: $file"; exit 1; }
    kc=$(get_config "keyword_count")
    kc=${kc:-15}
    echo "=== Keywords: $file ==="
    cat "$file" | tr -cs 'A-Za-z' '\n' | tr 'A-Z' 'a-z' | \
    grep -Ev '^(the|a|an|and|or|but|in|on|at|to|for|of|with|is|are|was|were|be|been|being|have|has|had|do|does|did|will|would|could|should|may|might|shall|that|this|these|those|it|its|we|our|you|your|they|their|he|she|his|her|i|me|my|us|as|by|from|into|about|up|out|if|then|than|so|not|no|can|all|any|each|more|also|when|which|who|what|how|there|here|after|before|over|under|just|been|very|also|only|such|same|other|through|both|however|therefore|thus|hence|while|since|because|although|though|within|between|among|against|during|without|toward|per|via|new|old|one|two|three|first|second|third|last|next|full|high|low|large|small|long|short|good|bad|great|little|many|much|most|few|some|every|own|even|well|far|still|back|off|now|then|again|where|need|make|made|take|taken|use|used|time|year|way|day|man|men|woman|women|part|place|case|world|system|number|line|hand|work|works|worked|point|get|set|go|come|know|think|see|look|want|give|find|tell|ask|seem|feel|try|leave|call|keep|let|begin|show|hear|play|run|move|live|stand|bring|buy|speak|write|read|hold|turn|return|start|provide|become|include|continue|follow|allow|add|create|change|help|open|close|end|place|produce|apply|require|build|plan|lead|means|must|need|able|available|based|related|used|given|each|many|another|own|three|way|place|general|specific|different|important|possible|major|local|national|public|private|political|economic|social|cultural|natural|physical|personal|human|international|american|large|small|few|long|short|early|young|old|high|low|true|false|real|simple|common|clear|open|rather|often|always|never|now|already|soon|almost|usually|perhaps|likely|possible|certainly|especially|particularly|therefore|moreover|however|although|whether|either|neither|instead|except|including|following|according|regarding|despite|during|within|outside|across|around|below|above|near|beyond|behind|beside|throughout|along|upon|off|ago|else)$' | \
    sort | uniq -c | sort -rn | head -"$kc" | \
    awk '{print $2, $1}'
    log_history "keywords $file"
    ;;

  outline)
    file="${1:?outline requires a file argument}"
    [[ -f "$file" ]] || { echo "ERROR: File not found: $file"; exit 1; }
    echo "=== Outline: $file ==="
    grep -nE '^#{1,6} .+|^[A-Z][A-Z ]{4,}$|^[0-9]+\.[0-9]*\.?[0-9]*\.? .+' "$file" 2>/dev/null || echo "(no outline detected)"
    log_history "outline $file"
    ;;

  compare)
    file1="${1:?compare requires two file arguments}"
    file2="${2:?compare requires two file arguments}"
    [[ -f "$file1" ]] || { echo "ERROR: File not found: $file1"; exit 1; }
    [[ -f "$file2" ]] || { echo "ERROR: File not found: $file2"; exit 1; }
    wc1=$(cat "$file1" | wc -w | tr -d ' ')
    wc2=$(cat "$file2" | wc -w | tr -d ' ')
    diff_wc=$(( wc2 - wc1 ))
    echo "=== Comparison: $file1 vs $file2 ==="
    echo "Word Count: $file1=$wc1  $file2=$wc2  diff=$diff_wc"
    # Shared and unique keywords
    kw1=$(cat "$file1" | tr -cs 'A-Za-z' '\n' | tr 'A-Z' 'a-z' | grep -Ev '^(the|a|an|and|or|but|in|on|at|to|for|of|with|is|are|was|were|it|this|that|be|by|we|you|they|he|she|its|as|not|no|can|will|from|has|have|had|do|does|did|about|which|when|who|what|how|there|here|one|two|three|also|more|some|any|all|each|our|your|their|was|were|been|being|may|might|shall|should|would|could|own|per|via|so|if|than|then|only|just|very|well|still|even|both|after|before|over|under)$' | sort | uniq -c | sort -rn | head -20 | awk '{print $2}')
    kw2=$(cat "$file2" | tr -cs 'A-Za-z' '\n' | tr 'A-Z' 'a-z' | grep -Ev '^(the|a|an|and|or|but|in|on|at|to|for|of|with|is|are|was|were|it|this|that|be|by|we|you|they|he|she|its|as|not|no|can|will|from|has|have|had|do|does|did|about|which|when|who|what|how|there|here|one|two|three|also|more|some|any|all|each|our|your|their|was|were|been|being|may|might|shall|should|would|could|own|per|via|so|if|than|then|only|just|very|well|still|even|both|after|before|over|under)$' | sort | uniq -c | sort -rn | head -20 | awk '{print $2}')
    shared=$(comm -12 <(echo "$kw1" | sort) <(echo "$kw2" | sort) | tr '\n' ',' | sed 's/,$//')
    unique1=$(comm -23 <(echo "$kw1" | sort) <(echo "$kw2" | sort) | tr '\n' ',' | sed 's/,$//')
    unique2=$(comm -13 <(echo "$kw1" | sort) <(echo "$kw2" | sort) | tr '\n' ',' | sed 's/,$//')
    echo "Shared Keywords:  ${shared:-(none)}"
    echo "Unique to $file1: ${unique1:-(none)}"
    echo "Unique to $file2: ${unique2:-(none)}"
    log_history "compare $file1 $file2"
    ;;

  batch)
    dir="${1:?batch requires a directory argument}"
    [[ -d "$dir" ]] || { echo "ERROR: Directory not found: $dir"; exit 1; }
    echo "=== Batch Summary: $dir ==="
    n=$(get_config "summary_sentences")
    n=${n:-2}
    find "$dir" -maxdepth 1 -type f \( -name "*.txt" -o -name "*.md" -o -name "*.rst" -o -name "*.log" \) | sort | while read -r f; do
        echo "--- $f ---"
        awk -v n="$n" '
        BEGIN { para=""; blank=1 }
        /^[[:space:]]*$/ {
            if (para != "") {
                split(para, sents, /[.!?]+/)
                count=0
                for (i=1; i<=length(sents); i++) {
                    s = sents[i]
                    gsub(/^[ \t]+|[ \t]+$/, "", s)
                    if (s != "" && count < n) {
                        print s "."
                        count++
                    }
                }
                print ""
            }
            para=""
            blank=1
            next
        }
        /^#/ { next }
        {
            if (para == "") para = $0
            else para = para " " $0
            blank=0
        }
        END {
            if (para != "") {
                split(para, sents, /[.!?]+/)
                count=0
                for (i=1; i<=length(sents); i++) {
                    s = sents[i]
                    gsub(/^[ \t]+|[ \t]+$/, "", s)
                    if (s != "" && count < n) {
                        print s "."
                        count++
                    }
                }
            }
        }
        ' "$f"
        echo ""
    done
    log_history "batch $dir"
    ;;

  export)
    file="${1:?export requires a file and format}"
    fmt="${2:?export requires a format: md, txt, or json}"
    [[ -f "$file" ]] || { echo "ERROR: File not found: $file"; exit 1; }
    n=$(get_config "summary_sentences")
    n=${n:-2}
    summary=$(awk -v n="$n" '
    BEGIN { para=""; blank=1 }
    /^[[:space:]]*$/ {
        if (para != "") {
            split(para, sents, /[.!?]+/)
            count=0
            for (i=1; i<=length(sents); i++) {
                s = sents[i]
                gsub(/^[ \t]+|[ \t]+$/, "", s)
                if (s != "" && count < n) {
                    print s "."
                    count++
                }
            }
            print ""
        }
        para=""
        blank=1
        next
    }
    /^#/ { next }
    {
        if (para == "") para = $0
        else para = para " " $0
        blank=0
    }
    END {
        if (para != "") {
            split(para, sents, /[.!?]+/)
            count=0
            for (i=1; i<=length(sents); i++) {
                s = sents[i]
                gsub(/^[ \t]+|[ \t]+$/, "", s)
                if (s != "" && count < n) {
                    print s "."
                    count++
                }
            }
        }
    }
    ' "$file")
    word_count=$(cat "$file" | wc -w | tr -d ' ')
    kc=$(get_config "keyword_count")
    kc=${kc:-15}
    keywords=$(cat "$file" | tr -cs 'A-Za-z' '\n' | tr 'A-Z' 'a-z' | \
    grep -Ev '^(the|a|an|and|or|but|in|on|at|to|for|of|with|is|are|was|were|be|been|being|have|has|had|do|does|did|will|would|could|should|may|might|shall|that|this|these|those|it|its|we|our|you|your|they|their|he|she|his|her|i|me|my|us|as|by|from|into|about|up|out|if|then|than|so|not|no|can|all|any|each|more|also|when|which|who|what|how|there|here|after|before|over|under|just|been|very|also|only|such|same|other|through|both|however|therefore|thus|hence|while|since|because|although|though|within|between|among|against|during|without|toward|per|via|new|old|one|two|three|first|second|third|last|next|full|high|low|large|small|long|short|good|bad|great|little|many|much|most|few|some|every|own|even|well|far|still|back|off|now|then|again|where|need|make|made|take|taken|use|used|time|year|way|day|man|men|woman|women|part|place|case|world|system|number|line|hand|work|works|worked|point|get|set|go|come|know|think|see|look|want|give|find|tell|ask|seem|feel|try|leave|call|keep|let|begin|show|hear|play|run|move|live|stand|bring|buy|speak|write|read|hold|turn|return|start|provide|become|include|continue|follow|allow|add|create|change|help|open|close|end|place|produce|apply|require|build|plan|lead|means|must|need|able|available|based|related|used|given|each|many|another|own|three|way|place|general|specific|different|important|possible|major|local|national|public|private|political|economic|social|cultural|natural|physical|personal|human|international|american|large|small|few|long|short|early|young|old|high|low|true|false|real|simple|common|clear|open|rather|often|always|never|now|already|soon|almost|usually|perhaps|likely|possible|certainly|especially|particularly|therefore|moreover|however|although|whether|either|neither|instead|except|including|following|according|regarding|despite|during|within|outside|across|around|below|above|near|beyond|behind|beside|throughout|along|upon|off|ago|else)$' | \
    sort | uniq -c | sort -rn | head -"$kc" | awk '{print $2}')
    bname=$(basename "$file")
    case "$fmt" in
      md)
        echo "# Summary: $bname"
        echo ""
        echo "## Summary"
        echo "$summary"
        echo ""
        echo "## Keywords"
        echo "$keywords" | awk '{print "- "$0}'
        echo ""
        echo "**Word Count:** $word_count"
        ;;
      txt)
        echo "Summary: $bname"
        echo "==============="
        echo "$summary"
        echo ""
        echo "Keywords:"
        echo "$keywords"
        echo ""
        echo "Word Count: $word_count"
        ;;
      json)
        # Build JSON
        summary_json=$(echo "$summary" | sed 's/\\/\\\\/g' | sed 's/"/\\"/g' | awk '{printf "%s\\n", $0}' | sed 's/\\n$//')
        kw_json=$(echo "$keywords" | sed 's/\\/\\\\/g' | sed 's/"/\\"/g' | awk '{printf "\"%s\",", $0}' | sed 's/,$//')
        echo "{"
        echo "  \"file\": \"$bname\","
        echo "  \"word_count\": $word_count,"
        echo "  \"summary\": \"$summary_json\","
        echo "  \"keywords\": [$kw_json]"
        echo "}"
        ;;
      *)
        echo "ERROR: Unknown format '$fmt'. Use: md, txt, json"
        exit 1
        ;;
    esac
    log_history "export $file $fmt"
    ;;

  history)
    if [[ -f "$HISTORY_FILE" ]]; then
        echo "=== Processing History ==="
        cat "$HISTORY_FILE"
    else
        echo "No history found."
    fi
    ;;

  *)
    echo "Unknown command: $cmd"
    echo "Run 'bash scripts/script.sh help' for usage."
    exit 1
    ;;
esac
"""

with open(os.path.join(scripts_dir, "script.sh"), "w") as f:
    f.write(script_content)

# ─── Market Research Documents ─────────────────────────────────────────────────
market_dir = os.path.join(workspace, "market_research")
os.makedirs(market_dir, exist_ok=True)

# Strategy doc v1
strategy_v1 = """# Global EV Market Strategy — Q1 Draft

EXECUTIVE OVERVIEW

The electric vehicle market has witnessed unprecedented growth in recent years. Battery costs have declined significantly, making EVs more accessible to mainstream consumers. Charging infrastructure investments are accelerating across major metropolitan regions.

Our competitive positioning relies heavily on partnerships with battery manufacturers in Southeast Asia. The supply chain resilience factor remains a key differentiator from legacy automakers. We project a 34 percent market share increase by the end of the fiscal year.

TECHNOLOGY ROADMAP

Solid-state battery integration is slated for the premium segment by Q4. Fast-charging networks will be expanded to cover 80 percent of major highways. Software-defined vehicle platforms will enable over-the-air updates for all features.

Consumer sentiment analysis indicates strong preference for longer range and faster charging. Brand loyalty scores have improved following the latest model refresh. Dealership digitalization programs are on track with pilot results exceeding expectations.

RISK ASSESSMENT

Regulatory uncertainty in key markets poses moderate risk to expansion timelines. Raw material sourcing for lithium and cobalt remains subject to geopolitical volatility. Competitor pricing pressure in the mid-range segment may compress margins.

Supply chain disruptions from recent geopolitical tensions require contingency planning. Insurance cost increases for EV fleets present an emerging challenge for fleet operators. Government subsidy phase-outs in several markets require proactive pricing adjustments.
"""

# Strategy doc v2 (revised)
strategy_v2 = """# Global EV Market Strategy — Q2 Revised

EXECUTIVE OVERVIEW

The electric vehicle sector continues to outperform broader automotive industry benchmarks. Battery cost reductions have accelerated beyond initial projections, enabling aggressive price repositioning. Charging infrastructure deployment has reached critical mass in Tier 1 markets.

Our revised strategy emphasizes vertical integration of battery production to capture margin improvements. The partnership network with semiconductor suppliers strengthens our software-defined vehicle capabilities. We now project a 41 percent market share growth target for the revised fiscal outlook.

TECHNOLOGY ROADMAP

Solid-state battery production is being fast-tracked for mass market deployment, not just premium vehicles. Ultra-fast charging corridors are being co-developed with grid operators to reduce installation timelines. Autonomous driving features will be offered via subscription model beginning next quarter.

Consumer research reveals growing demand for vehicle-to-grid integration capabilities. Fleet operators represent an emerging high-value segment with strong return-on-investment metrics. Dealership transformation programs have been expanded following strong pilot performance metrics.

RISK ASSESSMENT

Regulatory frameworks in target markets are stabilizing following recent policy announcements. Lithium supply security has been addressed through long-term offtake agreements with mining partners. Aggressive pricing from Chinese competitors requires differentiated value proposition focus.

Cybersecurity requirements for connected vehicles are adding compliance overhead to development budgets. Battery recycling obligations present both a cost and a brand opportunity in environmentally conscious markets. Grid capacity constraints in suburban areas may slow residential charging adoption rates.
"""

# Several distractor documents (not the comparison targets)
sector_report = """# Semiconductor Supply Chain Analysis

OVERVIEW

The global semiconductor shortage has reshaped procurement strategies across multiple industries. Lead times for critical components have improved but remain elevated compared to pre-disruption benchmarks. Inventory buffers are being rebuilt cautiously given ongoing demand uncertainty.

FINDINGS

Automotive-grade chip demand is projected to grow at 12 percent annually through the next decade. Foundry capacity expansions in the United States and Europe will partially offset dependence on Asian manufacturing. Specialty analog chips remain the most constrained category impacting production schedules.

RECOMMENDATIONS

Dual-sourcing strategies should be implemented for all tier-one components. Long-term supply agreements with foundries should be prioritized over spot market procurement. Investment in chip design capabilities will reduce dependence on merchant silicon suppliers.
"""

consumer_survey = """Consumer Preference Survey Results — Mobility 2024

METHODOLOGY

Survey conducted across twelve metropolitan markets with a sample size of 4,200 respondents. Participants were screened for active vehicle ownership or purchase intent within 18 months. Responses were weighted by demographic and geographic distribution.

KEY FINDINGS

Range anxiety remains the top barrier to EV adoption among non-owners, cited by 58 percent of respondents. Total cost of ownership is increasingly recognized as favorable for electric vehicles over five-year horizon. Public charging experience rated as satisfactory by only 43 percent of current EV owners.

Brand preference data shows premium manufacturers maintaining strong loyalty while mainstream brands gain consideration share. Subscription models for software features received mixed reception with 38 percent expressing willingness to pay. Vehicle-to-grid technology awareness is low but interest is high among environmentally motivated segments.
"""

competitor_brief = """Competitive Intelligence Brief — Rival OEM Analysis

Subject: Competitor Product Launch Assessment

The rival OEM has announced an aggressive product refresh cycle targeting the mid-range EV segment. Pricing strategy undercuts our current portfolio by approximately 8 to 12 percent at comparable trim levels. Range specifications match but charging speed lags our platform by a measurable margin.

Distribution expansion through direct sales channels bypasses traditional dealer margins. Software ecosystem lock-in strategy presents customer retention risks for our cross-platform users. Fleet sales division has secured three major corporate contracts that we had targeted.

Mitigation actions include accelerated launch timeline review and enhanced trade-in incentive programs. Sales force training on competitive differentiation points is being scheduled for regional meetings. Legal review of patent exposure related to announced charging interface design is underway.
"""

financial_summary = """Financial Performance Summary — Internal

Revenue growth of 22 percent year-over-year exceeded analyst consensus estimates. Gross margin improvement of 180 basis points driven by manufacturing efficiency gains. Operating expenses increased 31 percent reflecting accelerated investment in software and autonomy capabilities.

Free cash flow generation remains robust supporting continued capital allocation flexibility. Debt-to-equity ratio improved following convertible note settlement earlier in the quarter. Forward guidance reflects continued revenue momentum with margin expansion expected in second half.

Working capital management has been a focus area with inventory days reduced through supply chain optimization. Capital expenditure commitments for new production capacity are on track with board-approved budget. Share repurchase program has been suspended to preserve liquidity for strategic acquisition opportunities.
"""

ops_log = """operations_pipeline.log

2024-01-15 09:23:11 Pipeline job START batch_id=20240115_A
2024-01-15 09:23:45 Loaded 847 records from upstream feed
2024-01-15 09:24:02 Validation PASS schema_check=OK null_check=OK
2024-01-15 09:24:30 Transform stage completed duration=28s
2024-01-15 09:25:01 Output written to staging zone record_count=847
2024-01-15 09:25:02 Pipeline job END status=SUCCESS

2024-01-16 10:11:08 Pipeline job START batch_id=20240116_A
2024-01-16 10:11:52 Loaded 1203 records from upstream feed
2024-01-16 10:12:15 Validation WARN null_check=3_nulls_found
2024-01-16 10:12:44 Transform stage completed duration=32s
2024-01-16 10:13:01 Output written to staging zone record_count=1200
2024-01-16 10:13:01 Pipeline job END status=SUCCESS_WITH_WARNINGS
"""

# Write files
with open(os.path.join(market_dir, "strategy_q1.md"), "w") as f:
    f.write(strategy_v1)

with open(os.path.join(market_dir, "strategy_q2.md"), "w") as f:
    f.write(strategy_v2)

with open(os.path.join(market_dir, "semiconductor_supply.txt"), "w") as f:
    f.write(sector_report)

with open(os.path.join(market_dir, "consumer_survey_2024.txt"), "w") as f:
    f.write(consumer_survey)

with open(os.path.join(market_dir, "competitor_brief.txt"), "w") as f:
    f.write(competitor_brief)

with open(os.path.join(market_dir, "financial_summary.txt"), "w") as f:
    f.write(financial_summary)

with open(os.path.join(market_dir, "ops_pipeline.log"), "w") as f:
    f.write(ops_log)

# ─── Deep distractor directory tree ────────────────────────────────────────────
archive_dir = os.path.join(workspace, "archive")
os.makedirs(os.path.join(archive_dir, "2023", "q3", "reports"), exist_ok=True)
os.makedirs(os.path.join(archive_dir, "2023", "q4", "drafts"), exist_ok=True)
os.makedirs(os.path.join(archive_dir, "templates"), exist_ok=True)

old_report = """Q3 2023 Market Overview

This document covers third quarter performance metrics and market observations. Growth rates in target segments were consistent with prior guidance. No material deviations from strategic plan were identified.

Operational efficiency improvements contributed to margin stabilization. Customer acquisition costs trended lower following campaign optimization. Retention metrics showed continued improvement across all cohorts.
"""

draft_note = """Draft notes for Q4 review — INTERNAL

These are preliminary observations pending final data. Market positioning appears stable but competitive pressure is intensifying. Budget reallocation requests are pending CFO review.

Product pipeline milestones are behind schedule by approximately 3 weeks. Engineering teams have identified root cause and mitigation plan is in review. Executive update scheduled for next week.
"""

template_file = """Document Template v2

[SECTION: OVERVIEW]
Provide a high-level summary of the subject matter. Keep to 2-3 paragraphs.

[SECTION: FINDINGS]
List key findings in order of significance. Use clear and direct language.

[SECTION: RECOMMENDATIONS]
Actionable recommendations should follow findings. Each recommendation should be traceable to a specific finding.

[SECTION: APPENDIX]
Supporting data and methodology notes.
"""

with open(os.path.join(archive_dir, "2023", "q3", "reports", "q3_overview.txt"), "w") as f:
    f.write(old_report)

with open(os.path.join(archive_dir, "2023", "q4", "drafts", "q4_draft_notes.txt"), "w") as f:
    f.write(draft_note)

with open(os.path.join(archive_dir, "templates", "report_template.txt"), "w") as f:
    f.write(template_file)

# More distractors
misc_dir = os.path.join(workspace, "misc")
os.makedirs(misc_dir, exist_ok=True)

for i, content in enumerate([
    "Meeting notes from strategy session. Key decisions: accelerate roadmap, revisit pricing model, expand partnerships.",
    "Action items list: review vendor contracts, update forecast models, schedule stakeholder briefings.",
    "Glossary of terms used in competitive analysis reports and market sizing methodologies.",
]):
    with open(os.path.join(misc_dir, f"note_{i+1}.txt"), "w") as f:
        f.write(content + "\n")

# data dir
data_dir = os.path.join(workspace, "data")
os.makedirs(data_dir, exist_ok=True)
with open(os.path.join(data_dir, "raw_metrics.txt"), "w") as f:
    f.write("metric,value\nchurn_rate,0.042\nNPS,67\nCAC,312\nLTV,2840\n")

print("Workspace generation complete.")
print(f"Files created in: {workspace}")