#!/usr/bin/env python3
"""
Generate the sandbox workspace for the Gmail Label Manager skill task.
Creates a realistic workspace with distractor files and a mock `gog` CLI.
"""

import os
import json
import stat
import random
from pathlib import Path

random.seed(42)

WORKSPACE = Path(os.environ.get("WORKSPACE_DIR", "/workspace"))

# ─── Directory structure ────────────────────────────────────────────────────
dirs = [
    WORKSPACE / "logs",
    WORKSPACE / "archive",
    WORKSPACE / "archive" / "2024",
    WORKSPACE / "archive" / "2023",
    WORKSPACE / "config",
    WORKSPACE / "scripts" / "helpers",
    WORKSPACE / "scripts" / "tests",
    WORKSPACE / "weekly-reports",
    WORKSPACE / "tmp",
    WORKSPACE / "docs",
]
for d in dirs:
    d.mkdir(parents=True, exist_ok=True)

# ─── Distractor files ───────────────────────────────────────────────────────
distractor_files = {
    WORKSPACE / "docs" / "setup_guide.txt": (
        "Setup guide for the email manager.\n"
        "1. Install dependencies\n2. Configure gog CLI\n3. Run script.sh\n"
    ),
    WORKSPACE / "config" / "old_config.json": json.dumps({
        "version": "1.0",
        "max_emails": 5,
        "labels": ["Personal", "Work", "Family"],
        "deprecated": True
    }, indent=2),
    WORKSPACE / "config" / "contacts_backup.json": json.dumps({
        "family": ["grandma@family.net", "uncle@family.net"],
        "vip": ["boss@company.com"],
        "school": ["principal@school.com"]
    }, indent=2),
    WORKSPACE / "archive" / "2024" / "processed_emails.txt": (
        "Processed emails log - 2024\n"
        "2024-01-15: newsletter@updates.example.com -> A_Personal/Newsletter\n"
        "2024-02-10: bills@utility.com -> A_Personal/Bills\n"
    ),
    WORKSPACE / "archive" / "2023" / "processed_emails.txt": (
        "Processed emails log - 2023\n"
        "2023-12-01: newsletter@updates.example.com -> A_Personal/Newsletter\n"
    ),
    WORKSPACE / "weekly-reports" / "report_2024_W01.txt": (
        "Weekly report - Week 1 2024\n"
        "Total emails processed: 47\n"
        "Labels applied: A_Personal/Newsletter (12), A_Work/Updates (8)\n"
    ),
    WORKSPACE / "weekly-reports" / "report_2024_W02.txt": (
        "Weekly report - Week 2 2024\n"
        "Total emails processed: 52\n"
    ),
    WORKSPACE / "scripts" / "helpers" / "label_utils.sh": (
        "#!/bin/bash\n# Helper utilities for label management\n"
        "# NOT THE MAIN SCRIPT - helpers only\n"
        "get_labels() { echo 'A_Personal/Newsletter A_Work/Updates'; }\n"
    ),
    WORKSPACE / "scripts" / "tests" / "test_labels.sh": (
        "#!/bin/bash\n# Test suite for label operations\necho 'Running tests...'\n"
    ),
    WORKSPACE / "tmp" / "draft_email.txt": (
        "Subject: Test draft\nFrom: test@test.com\nBody: This is a draft.\n"
    ),
    WORKSPACE / "tmp" / "label_cache.json": json.dumps({
        "newsletter@updates.example.com": "A_Personal/Newsletter",
        "bills@utility.com": "A_Personal/Bills",
        "cached_at": "2024-01-01T00:00:00Z",
        "WARNING": "This cache is stale and should not be used"
    }, indent=2),
}

for path, content in distractor_files.items():
    path.write_text(content)

# ─── config.json (valid but minimal, won't affect test) ─────────────────────
(WORKSPACE / "config.json").write_text(json.dumps({
    "contacts": {
        "family": ["grandma@family.net"],
        "vip": ["friend@gmail.com"],
        "school": ["@school.com"],
        "work": ["@work.com"],
        "insurance": ["@ss.com"]
    }
}, indent=2))

# ─── GOG CLI MOCK ────────────────────────────────────────────────────────────
# The mock `gog` binary logs all calls and returns realistic JSON responses.
# Call log is written to /workspace/logs/gog_calls.log

GOG_CALL_LOG = "/workspace/logs/gog_calls.log"

# Unread email data
UNREAD_EMAIL_ID = "msg_unread_001"
UNREAD_THREAD_ID = "thread_abc123"
SENDER_EMAIL = "newsletter@updates.example.com"

# Archived emails from same sender with labels
# A_Personal/Newsletter appears 3x, A_Work/Updates appears 1x
# So correct label = A_Personal/Newsletter
ARCHIVED_EMAILS_JSON = json.dumps({
    "messages": [
        {
            "id": "msg_arch_001",
            "threadId": "thread_arch_001",
            "subject": "Monthly Newsletter - January",
            "from": f"Newsletter <{SENDER_EMAIL}>",
            "labels": ["A_Personal/Newsletter", "CATEGORY_PROMOTIONS"]
        },
        {
            "id": "msg_arch_002",
            "threadId": "thread_arch_002",
            "subject": "Monthly Newsletter - February",
            "from": f"Newsletter <{SENDER_EMAIL}>",
            "labels": ["A_Personal/Newsletter", "CATEGORY_UPDATES"]
        },
        {
            "id": "msg_arch_003",
            "threadId": "thread_arch_003",
            "subject": "Special Update",
            "from": f"Newsletter <{SENDER_EMAIL}>",
            "labels": ["A_Work/Updates"]
        },
        {
            "id": "msg_arch_004",
            "threadId": "thread_arch_004",
            "subject": "Monthly Newsletter - March",
            "from": f"Newsletter <{SENDER_EMAIL}>",
            "labels": ["A_Personal/Newsletter", "CATEGORY_PROMOTIONS"]
        }
    ]
})

UNREAD_SEARCH_JSON = json.dumps({
    "messages": [
        {
            "id": UNREAD_EMAIL_ID,
            "threadId": UNREAD_THREAD_ID,
            "subject": "April Newsletter - Special Edition",
            "from": f"Newsletter <{SENDER_EMAIL}>",
            "labels": ["INBOX", "UNREAD", "CATEGORY_PROMOTIONS"]
        }
    ]
})

THREAD_FULL_JSON = json.dumps({
    "id": UNREAD_THREAD_ID,
    "messages": [
        {
            "id": UNREAD_EMAIL_ID,
            "threadId": UNREAD_THREAD_ID,
            "subject": "April Newsletter - Special Edition",
            "from": f"Newsletter <{SENDER_EMAIL}>",
            "labels": ["INBOX", "UNREAD", "CATEGORY_PROMOTIONS"],
            "body": "Welcome to our April Newsletter. This month we have special updates for our subscribers."
        }
    ]
})

MODIFY_SUCCESS_JSON = json.dumps({"success": True, "threadId": UNREAD_THREAD_ID})

# Write the mock gog script
gog_script = rf'''#!/bin/bash
# Mock gog CLI for Gmail Label Manager testing
# Logs all calls and returns realistic responses

LOG_FILE="{GOG_CALL_LOG}"
mkdir -p "$(dirname "$LOG_FILE")"

# Log the full command
echo "$@" >> "$LOG_FILE"

ARGS="$*"

# Route based on subcommand pattern
if echo "$ARGS" | grep -q 'gmail messages search.*is:unread.*--max.*--json'; then
    cat <<'ENDJSON'
{UNREAD_SEARCH_JSON}
ENDJSON

elif echo "$ARGS" | grep -q 'gmail messages search.*is:archived.*--max.*--json'; then
    cat <<'ENDJSON'
{ARCHIVED_EMAILS_JSON}
ENDJSON

elif echo "$ARGS" | grep -q 'gmail thread get.*--full.*--json'; then
    cat <<'ENDJSON'
{THREAD_FULL_JSON}
ENDJSON

elif echo "$ARGS" | grep -q 'gmail thread modify'; then
    cat <<'ENDJSON'
{MODIFY_SUCCESS_JSON}
ENDJSON

elif echo "$ARGS" | grep -q 'calendar event create'; then
    echo '{{"success": true}}'

else
    echo "Unknown command: $ARGS" >&2
    exit 1
fi

exit 0
'''

# Substitute actual JSON content
gog_script = gog_script.replace("{UNREAD_SEARCH_JSON}", UNREAD_SEARCH_JSON)
gog_script = gog_script.replace("{ARCHIVED_EMAILS_JSON}", ARCHIVED_EMAILS_JSON)
gog_script = gog_script.replace("{THREAD_FULL_JSON}", THREAD_FULL_JSON)
gog_script = gog_script.replace("{MODIFY_SUCCESS_JSON}", MODIFY_SUCCESS_JSON)

gog_path = Path("/usr/local/bin/gog")
gog_path.write_text(gog_script)
gog_path.chmod(gog_path.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

# ─── script.sh ───────────────────────────────────────────────────────────────
# The skill's main script already exists per instructions.
# We create it here since the SKILL.md says it's part of the workspace.
script_sh_content = r'''#!/bin/bash
#
# Intelligent Gmail Manager Script - Personalized
# Automatically classifies and processes emails based on content patterns
#

set -euo pipefail

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly LOG_DIR="${SCRIPT_DIR}/logs"
readonly LOG_FILE="${LOG_DIR}/gmail-label-log.txt"
readonly TELEGRAM_LOG="${LOG_DIR}/telegram-log.txt"
readonly DIGEST_FILE="${SCRIPT_DIR}/weekly-digest.txt"
readonly CONFIG_FILE="${SCRIPT_DIR}/config.json"
readonly MAX_EMAILS=1

readonly TELEGRAM_BOT_TOKEN="${TELEGRAM_BOT_TOKEN:-}"
readonly TELEGRAM_CHAT_ID="${TELEGRAM_CHAT_ID:-}"

readonly LABEL_PREFIX="A_Personal,A_Work"
readonly REMOVE_LABELS="CATEGORY_UPDATES,CATEGORY_PROMOTIONS,UNREAD"

declare -a CHILDREN_NAMES=("Kid1" "Kid2" "Kid3")
declare -a CHILDREN_FULL_NAMES=("Kid1 Lastname" "Kid2 Lastname" "Kid3 Lastname")
declare -a WIFE_NAMES=("Wife's name")

readonly SCHOOL_NAME="School"
readonly SCHOOL_FULL_NAME="Elementary School"
readonly SCHOOL_DOMAIN="school.com"

readonly WIFE_WORK="Work"
readonly WIFE_WORK_FULL="Workplace Name"
readonly WIFE_WORK_DOMAIN="work.com"

readonly HEALTH_INSURANCE="INS"
readonly SOCIAL_SECURITY_1="SS"

declare -a HOSPITALS=("Hospital")
declare -a HOSPITAL_DOMAINS=("hospital.com")
declare -a INSURANCE_CONTACTS=()

load_insurance_contacts() {
  if [ -f "$CONFIG_FILE" ]; then
    INSURANCE_CONTACTS=($(jq -r '.contacts.insurance[]?' "$CONFIG_FILE" 2>/dev/null || echo ""))
  fi
  if [ ${#INSURANCE_CONTACTS[@]} -eq 0 ]; then
    INSURANCE_CONTACTS=("@ss.com" "ss")
  fi
}

declare -A EMAIL_PATTERNS=(
  ["payment_confirmation"]="WOW Membership fee has been paid|handle_coupang_payment|high|Coupang WOW membership payment"
  ["card_transaction"]="card ending|handle_card_transaction|high|Credit/debit card transaction"
  ["bank_transfer"]="transfer.*completed|handle_bank_transfer|high|Bank transfer notification"
  ["payment_receipt"]="payment.*receipt|handle_payment_receipt|high|Payment receipt"
  ["invoice"]="invoice|handle_invoice|medium|Invoice received"
  ["subscription"]="subscription.*renewed|handle_subscription|medium|Subscription renewal"
  ["order_confirmation"]="order.*confirmed|handle_order_confirmation|high|Order confirmation"
  ["shipment_tracking"]="shipped|tracking|handle_shipment|medium|Shipment notification"
  ["delivery_notification"]="delivered|arrived|handle_delivery|high|Delivery confirmation"
  ["delivery_schedule"]="delivery.*scheduled|handle_delivery_schedule|medium|Delivery scheduled"
  ["school_absence"]="Absence Notification|handle_absence_notification|critical|school child absence notification"
  ["school_event"]="(school).*(event|meeting|conference)|handle_school_event|high|school school event"
  ["school_grade"]="grade.*report|academic.*progress|report card|handle_grade_report|high|school grade/academic report"
  ["school_announcement"]="(school).*announcement|handle_school_announcement|medium|school school announcement"
  ["school_homework"]="homework|assignment.*due|handle_homework|low|school homework reminder"
  ["school_attendance"]="attendance|tardy|late|handle_attendance|medium|school attendance notification"
  ["school_permission"]="permission.*slip|field.*trip|excursion|handle_permission_slip|high|school permission slip"
  ["school_parent_teacher"]="parent.*teacher.*conference|PTC|handle_parent_teacher|high|school parent-teacher conference"
  ["school_lunch"]="lunch.*menu|cafeteria|handle_school_lunch|low|school lunch information"
  ["school_discipline"]="behavior|discipline|incident|handle_discipline|critical|school discipline notification"
  ["work_travel"]="business.*trip|travel.*approval|mission|handle_work_travel|high|Work travel notification"
  ["child_mentioned"]="(kid1|kid2|kid3)|handle_child_mention|high|Email mentioning children"
  ["wife_mentioned"]="(wifesname)|handle_wife_mention|high|Email mentioning wife"
  ["meeting_invitation"]="meeting.*invitation|invited.*you|handle_meeting_invitation|medium|Meeting invitation"
  ["event_reminder"]="event.*reminder|upcoming.*event|handle_event_reminder|medium|Event reminder"
  ["appointment_confirmation"]="appointment.*confirmed|handle_appointment|high|Appointment confirmation"
  ["reservation"]="reservation.*confirmed|booking.*confirmed|handle_reservation|high|Reservation/booking"
  ["family_email"]="FAMILY_SENDER|handle_family_email|critical|Email from family member"
  ["vip_contact"]="VIP_SENDER|handle_vip_email|high|Email from VIP contact"
  ["utility_bill"]="electricity.*bill|water.*bill|gas.*bill|handle_utility_bill|medium|Utility bill"
  ["phone_bill"]="mobile.*bill|phone.*bill|handle_phone_bill|medium|Phone bill"
  ["internet_bill"]="internet.*bill|broadband.*bill|handle_internet_bill|medium|Internet bill"
  ["medical_appointment"]="medical.*appointment|doctor.*appointment|handle_medical_appointment|high|Medical appointment"
  ["prescription_ready"]="prescription.*ready|medication.*available|handle_prescription|high|Prescription ready"
  ["lab_results"]="lab.*results|test.*results|handle_lab_results|critical|Lab/test results"
  ["vaccination"]="vaccination|immunization|vaccine|handle_vaccination|high|Vaccination notification"
  ["flight_booking"]="flight.*confirmation|boarding.*pass|handle_flight_booking|high|Flight booking"
  ["hotel_reservation"]="hotel.*confirmation|accommodation|handle_hotel_reservation|medium|Hotel reservation"
  ["travel_itinerary"]="itinerary|travel.*plan|handle_travel_itinerary|medium|Travel itinerary"
  ["visa_passport"]="visa|passport|immigration|handle_visa_passport|high|Visa/passport notification"
  ["security_alert"]="security.*alert|suspicious.*activity|handle_security_alert|critical|Security alert"
  ["password_reset"]="password.*reset|verify.*account|handle_password_reset|high|Password reset"
  ["login_notification"]="new.*login|login.*detected|handle_login_notification|medium|Login notification"
  ["dosz_insurance"]="(DOSZ|health insurance claim|insurance reimbursement)|handle_health_insurance|high|DOSZ health insurance"
  ["rsz_social"]="(Rsz|RSZ|social security contribution)|handle_social_security|high|Rsz social security"
  ["onss_social"]="(ONSS|rijksdienst|social security)|handle_social_security|high|ONSS social security"
  ["insurance_claim"]="claim.*approved|reimbursement.*processed|claim.*rejected|handle_insurance_claim|high|Insurance claim status"
  ["insurance_renewal"]="insurance.*renewal|policy.*expir|handle_insurance_renewal|high|Insurance renewal"
  ["insurance_card"]="insurance.*card|membership.*card|handle_insurance_card|medium|Insurance card notification"
  ["bnh_hospital"]="(BNH|Bangkok Nursing Home)|handle_hospital_communication|high|BNH Hospital communication"
  ["samitivej_hospital"]="Samitivej|handle_hospital_communication|high|Samitivej Hospital communication"
  ["hospital_bill"]="hospital.*bill|medical.*invoice|treatment.*cost|handle_hospital_bill|critical|Hospital bill"
  ["test_results"]="test.*results|lab.*report|blood.*work|handle_test_results|critical|Medical test results"
  ["hospital_appointment"]="hospital.*appointment|clinic.*visit|follow.*up.*appointment|handle_hospital_appointment|high|Hospital appointment"
  ["surgery_schedule"]="surgery.*scheduled|operation.*date|procedure.*planned|handle_surgery_notification|critical|Surgery notification"
  ["discharge_summary"]="discharge.*summary|hospital.*discharge|treatment.*summary|handle_discharge_summary|high|Hospital discharge"
  ["medication_prescription"]="prescription|medication.*prescribed|pharmacy|handle_prescription_hospital|high|Hospital prescription"
  ["emergency_contact"]="emergency|urgent.*medical|immediate.*attention|handle_medical_emergency|critical|Medical emergency"
  ["vaccination_reminder"]="vaccination.*due|immunization.*reminder|vaccine.*schedule|handle_vaccination|high|Vaccination reminder"
  ["pre_approval"]="pre-approval|pre-authorization|prior.*authorization|treatment.*approval|handle_pre_approval|critical|Insurance pre-approval"
  ["coverage_inquiry"]="coverage.*inquiry|benefits.*check|eligible.*treatment|handle_coverage_inquiry|medium|Coverage inquiry"
)

declare -a FAMILY_CONTACTS=()
declare -a VIP_CONTACTS=()
declare -a WORK_CONTACTS=()
declare -a SCHOOL_CONTACTS=()

load_contacts() {
  if [ -f "$CONFIG_FILE" ]; then
    FAMILY_CONTACTS=($(jq -r '.contacts.family[]?' "$CONFIG_FILE" 2>/dev/null || echo ""))
    VIP_CONTACTS=($(jq -r '.contacts.vip[]?' "$CONFIG_FILE" 2>/dev/null || echo ""))
    WORK_CONTACTS=($(jq -r '.contacts.work[]?' "$CONFIG_FILE" 2>/dev/null || echo ""))
    SCHOOL_CONTACTS=($(jq -r '.contacts.school[]?' "$CONFIG_FILE" 2>/dev/null || echo ""))
  fi
  if [ ${#FAMILY_CONTACTS[@]} -eq 0 ]; then
    FAMILY_CONTACTS=("dad@dad.com")
  fi
  if [ ${#VIP_CONTACTS[@]} -eq 0 ]; then
    VIP_CONTACTS=("friend@gmail.com")
  fi
  if [ ${#SCHOOL_CONTACTS[@]} -eq 0 ]; then
    SCHOOL_CONTACTS=("@school.com" "office@school.com")
  fi
  if [ ${#WORK_CONTACTS[@]} -eq 0 ]; then
    WORK_CONTACTS=("@work.com")
  fi
}

mkdir -p "$LOG_DIR"

for cmd in jq curl; do
  if ! command -v "$cmd" &>/dev/null; then
    echo "Error: Required command '$cmd' is not installed" >&2
    exit 1
  fi
done

if ! command -v gog &>/dev/null; then
  echo "Error: 'gog' command not found. Please install the Google CLI tool." >&2
  exit 1
fi

load_contacts
load_insurance_contacts

log() {
  local level="${1:-INFO}"
  shift
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] [$level] $*" | tee -a "$LOG_FILE"
}

log_error() { log "ERROR" "$@" >&2; }
log_warn()  { log "WARN"  "$@"; }
log_info()  { log "INFO"  "$@"; }
log_debug() { log "DEBUG" "$@"; }

send_telegram() {
  local message="$1"
  local priority="${2:-normal}"
  if [ -z "$TELEGRAM_BOT_TOKEN" ] || [ -z "$TELEGRAM_CHAT_ID" ]; then
    log_warn "Telegram credentials not configured. Skipping notification."
    return 1
  fi
  return 0
}

add_to_digest() {
  local category="$1"
  local entry="$2"
  local priority="${3:-normal}"
  {
    echo ""
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [${priority^^}]"
    echo "Category: $category"
    echo "$entry"
    echo "---"
  } >> "$DIGEST_FILE"
}

add_calendar_event() {
  local title="$1"
  local date="$2"
  local all_day="${3:-true}"
  local time="${4:-}"
  local description="${5:-}"
  log_info "Creating calendar event: $title on $date"
  local cmd="gog calendar event create --title \"$title\" --startDate \"$date\""
  if [ "$all_day" = "true" ]; then
    cmd="$cmd --allDay true"
  elif [ -n "$time" ]; then
    cmd="$cmd --startTime \"$time\""
  fi
  if [ -n "$description" ]; then
    cmd="$cmd --description \"$description\""
  fi
  local result
  result=$(eval "$cmd" 2>&1) || log_warn "Failed to create calendar event: $result"
  return 0
}

get_unread_emails() {
  local unread_emails
  unread_emails=$(gog gmail messages search "is:unread" --max "$MAX_EMAILS" --json 2>&1)
  if [ $? -ne 0 ]; then
    log_error "Failed to search for unread emails: $unread_emails"
    return 1
  fi
  echo "$unread_emails"
}

extract_email_data() {
  local email_json="$1"
  local field="$2"
  local value
  value=$(echo "$email_json" | jq -r ".${field} // empty")
  echo "$value"
}

get_thread_content() {
  local thread_id="$1"
  local content
  content=$(gog gmail thread get "$thread_id" --full --json 2>&1)
  if [ $? -ne 0 ]; then
    log_error "Failed to get thread content: $content"
    echo ""
    return 1
  fi
  echo "$content"
}

apply_label() {
  local thread_id="$1"
  local label="$2"
  log_info "Applying label '$label' to thread $thread_id"
  local result
  result=$(gog gmail thread modify "$thread_id" --add "$label" 2>&1)
  if [ $? -ne 0 ]; then
    log_error "Failed to apply label: $result"
    return 1
  fi
  return 0
}

remove_labels() {
  local thread_id="$1"
  local result
  result=$(gog gmail thread modify "$thread_id" --remove "$REMOVE_LABELS" 2>&1)
  if [ $? -ne 0 ]; then
    log_warn "Failed to remove labels: $result"
    return 1
  fi
  return 0
}

archive_email() {
  local thread_id="$1"
  log_info "Archiving thread $thread_id"
  local result
  result=$(gog gmail thread modify "$thread_id" --remove INBOX 2>&1)
  if [ $? -ne 0 ]; then
    log_error "Failed to archive email: $result"
    return 1
  fi
  return 0
}

get_label_pattern() {
  local sender="$1"
  local archived_emails
  archived_emails=$(gog gmail messages search "is:archived from:\"${sender}\"" --max 20 --json 2>&1)
  if [ $? -ne 0 ]; then
    echo ""
    return 1
  fi
  local label_pattern
  label_pattern=$(echo "$archived_emails" | jq -r "
    [.messages[]? | .labels[]? | select(startswith(\"A_Personal\") or startswith(\"A_Work\"))]
    | group_by(.)
    | map({label: .[0], count: length})
    | sort_by(.count)
    | reverse
    | .[0].label // empty
  ")
  echo "$label_pattern"
}

check_sender_category() {
  local sender="$1"
  for contact in "${SCHOOL_CONTACTS[@]}"; do
    if [[ "$sender" =~ $contact ]]; then echo "school"; return 0; fi
  done
  for contact in "${FAMILY_CONTACTS[@]}"; do
    if [[ "$sender" =~ $contact ]]; then echo "family"; return 0; fi
  done
  for contact in "${VIP_CONTACTS[@]}"; do
    if [[ "$sender" =~ $contact ]]; then echo "vip"; return 0; fi
  done
  for contact in "${WORK_CONTACTS[@]}"; do
    if [[ "$sender" =~ $contact ]]; then echo "work"; return 0; fi
  done
  echo "unknown"
}

check_family_mention() {
  local text="$1"
  for child in "${CHILDREN_NAMES[@]}"; do
    if echo "$text" | grep -qiE "\b${child}\b"; then echo "$child"; return 0; fi
  done
  for name in "${WIFE_NAMES[@]}"; do
    if echo "$text" | grep -qiE "\b${name}\b"; then echo "Wife's Name"; return 0; fi
  done
  echo ""
}

classify_email() {
  local subject="$1"
  local sender="$2"
  local content="$3"
  local matches=()
  local combined_text="${subject} ${content}"
  local sender_category
  sender_category=$(check_sender_category "$sender")
  if [ "$sender_category" = "school" ]; then matches+=("school_email:critical"); fi
  if [ "$sender_category" = "family" ]; then
    matches+=("family_email:critical")
  elif [ "$sender_category" = "vip" ]; then
    matches+=("vip_contact:high")
  elif [ "$sender_category" = "work" ]; then
    matches+=("work:high")
  fi
  local family_mention
  family_mention=$(check_family_mention "$combined_text")
  if [ -n "$family_mention" ]; then matches+=("child_mentioned:high"); fi
  for pattern_key in "${!EMAIL_PATTERNS[@]}"; do
    local pattern_data="${EMAIL_PATTERNS[$pattern_key]}"
    IFS='|' read -r pattern handler priority description <<< "$pattern_data"
    if [ "$pattern" = "FAMILY_SENDER" ] || [ "$pattern" = "VIP_SENDER" ]; then continue; fi
    if echo "$combined_text" | grep -qiE "$pattern"; then
      matches+=("${pattern_key}:${priority}")
    fi
  done
  if [ ${#matches[@]} -gt 0 ]; then
    printf '%s\n' "${matches[@]}" | jq -R . | jq -s .
  else
    echo "[]"
  fi
}

extract_amount() {
  local text="$1"
  local amount=""
  if [ -z "$amount" ]; then
    amount=$(echo "$text" | grep -oP '\$\s*[0-9,]+\.?[0-9]*' | head -n 1 | tr -d '$ ' | tr -d ',')
  fi
  if [ -z "$amount" ]; then
    amount=$(echo "$text" | grep -oP '€\s*[0-9,]+\.?[0-9]*' | head -n 1 | tr -d '€ ' | tr -d ',')
  fi
  if [ -z "$amount" ]; then
    amount=$(echo "$text" | grep -oiP '(amount|total|price|cost).*?[0-9,]+\.?[0-9]*' | grep -oP '[0-9,]+\.?[0-9]*' | head -n 1 | tr -d ',')
  fi
  echo "$amount"
}

extract_date() {
  local text="$1"
  local format="${2:-any}"
  local date_found=""
  case "$format" in
    iso) date_found=$(echo "$text" | grep -oP '\d{4}-\d{2}-\d{2}' | head -n 1) ;;
    natural) date_found=$(echo "$text" | grep -oP '(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}|\d{1,2}\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}' | head -n 1) ;;
    *)
      date_found=$(echo "$text" | grep -oP '\d{4}-\d{2}-\d{2}' | head -n 1)
      if [ -z "$date_found" ]; then
        date_found=$(echo "$text" | grep -oP '(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}|\d{1,2}\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}' | head -n 1)
      fi
      if [ -z "$date_found" ]; then
        date_found=$(echo "$text" | grep -oP '(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}' | head -n 1)
      fi
      ;;
  esac
  echo "$date_found"
}

extract_time() {
  local text="$1"
  local time_found
  time_found=$(echo "$text" | grep -oiP '\d{1,2}:\d{2}\s*(AM|PM|am|pm)?' | head -n 1)
  echo "$time_found"
}

extract_tracking_number() {
  local text="$1"
  local tracking
  tracking=$(echo "$text" | grep -oP '(tracking|shipment|parcel).*?([A-Z0-9]{8,20})' | grep -oP '[A-Z0-9]{8,20}' | head -n 1)
  echo "$tracking"
}

extract_child_name() {
  local text="$1"
  for child in "${CHILDREN_NAMES[@]}"; do
    if echo "$text" | grep -qiE "\b${child}\b"; then echo "$child"; return 0; fi
  done
  for child_full in "${CHILDREN_FULL_NAMES[@]}"; do
    if echo "$text" | grep -qiE "${child_full}"; then
      echo "$child_full" | awk '{print $1}'
      return 0
    fi
  done
  echo ""
}

handle_child_mention() {
  local email_content="$1"; local subject="$2"; local sender="$3"
  local child_name; child_name=$(extract_child_name "$email_content $subject")
  log_info "Processing email mentioning child: ${child_name:-one of the children}"
  send_telegram "Child mentioned: ${child_name}" "high" || true
  add_to_digest "Family/Children" "[Child Mentioned: ${child_name}]" "high"
  return 0
}

handle_wife_mention() {
  local email_content="$1"; local subject="$2"; local sender="$3"
  log_info "Processing email mentioning wife"
  send_telegram "Wife mentioned" "high" || true
  add_to_digest "Family/Spouse" "[Wife Mentioned]" "high"
  return 0
}

handle_work() {
  local email_content="$1"; local subject="$2"; local sender="$3"
  log_info "Processing work-related email"
  send_telegram "Work email" "high" || true
  add_to_digest "Work" "[Work Email]" "high"
  return 0
}

handle_school_email() {
  local email_content="$1"; local subject="$2"; local sender="$3"
  log_info "Processing school email"
  return 0
}

handle_absence_notification() {
  local email_content="$1"; local subject="$2"
  log_info "Processing absence notification"
  return 0
}

handle_school_event()        { log_info "school event"; return 0; }
handle_grade_report()        { log_info "grade report"; return 0; }
handle_school_announcement() { log_info "school announcement"; return 0; }
handle_homework()            { log_info "homework"; return 0; }
handle_attendance()          { log_info "attendance"; return 0; }
handle_permission_slip()     { log_info "permission slip"; return 0; }
handle_parent_teacher()      { log_info "parent teacher"; return 0; }
handle_school_lunch()        { log_info "school lunch"; return 0; }
handle_discipline()          { log_info "discipline"; return 0; }
handle_work_travel()         { log_info "work travel"; return 0; }
handle_meeting_invitation()  { log_info "meeting invitation"; return 0; }
handle_event_reminder()      { log_info "event reminder"; return 0; }
handle_appointment()         { log_info "appointment"; return 0; }
handle_reservation()         { log_info "reservation"; return 0; }
handle_family_email()        { log_info "family email"; return 0; }
handle_vip_email()           { log_info "vip email"; return 0; }
handle_coupang_payment()     { log_info "coupang payment"; return 0; }
handle_card_transaction()    { log_info "card transaction"; return 0; }
handle_bank_transfer()       { log_info "bank transfer"; return 0; }
handle_payment_receipt()     { log_info "payment receipt"; return 0; }
handle_invoice()             { log_info "invoice"; return 0; }
handle_subscription()        { log_info "subscription"; return 0; }
handle_order_confirmation()  { log_info "order confirmation"; return 0; }
handle_shipment()            { log_info "shipment"; return 0; }
handle_delivery()            { log_info "delivery"; return 0; }
handle_delivery_schedule()   { log_info "delivery schedule"; return 0; }
handle_utility_bill()        { log_info "utility bill"; return 0; }
handle_phone_bill()          { log_info "phone bill"; return 0; }
handle_internet_bill()       { log_info "internet bill"; return 0; }
handle_medical_appointment() { log_info "medical appointment"; return 0; }
handle_prescription()        { log_info "prescription"; return 0; }
handle_lab_results()         { log_info "lab results"; return 0; }
handle_vaccination()         { log_info "vaccination"; return 0; }
handle_flight_booking()      { log_info "flight booking"; return 0; }
handle_hotel_reservation()   { log_info "hotel reservation"; return 0; }
handle_travel_itinerary()    { log_info "travel itinerary"; return 0; }
handle_visa_passport()       { log_info "visa passport"; return 0; }
handle_security_alert()      { log_info "security alert"; return 0; }
handle_password_reset()      { log_info "password reset"; return 0; }
handle_login_notification()  { log_info "login notification"; return 0; }
handle_health_insurance()    { log_info "health insurance"; return 0; }
handle_social_security()     { log_info "social security"; return 0; }
handle_insurance_claim()     { log_info "insurance claim"; return 0; }
handle_insurance_renewal()   { log_info "insurance renewal"; return 0; }
handle_insurance_card()      { log_info "insurance card"; return 0; }
handle_hospital_communication() { log_info "hospital communication"; return 0; }
handle_hospital_bill()       { log_info "hospital bill"; return 0; }
handle_test_results()        { log_info "test results"; return 0; }
handle_hospital_appointment(){ log_info "hospital appointment"; return 0; }
handle_surgery_notification(){ log_info "surgery notification"; return 0; }
handle_discharge_summary()   { log_info "discharge summary"; return 0; }
handle_prescription_hospital(){ log_info "prescription hospital"; return 0; }
handle_medical_emergency()   { log_info "medical emergency"; return 0; }
handle_pre_approval()        { log_info "pre approval"; return 0; }
handle_coverage_inquiry()    { log_info "coverage inquiry"; return 0; }

process_single_email() {
  local email_json="$1"
  local email_id thread_id subject sender
  email_id=$(extract_email_data "$email_json" "id")
  thread_id=$(extract_email_data "$email_json" "threadId")
  subject=$(extract_email_data "$email_json" "subject")
  sender=$(extract_email_data "$email_json" "from")
  if [ -z "$email_id" ] || [ -z "$thread_id" ]; then
    log_warn "Skipping email with missing ID or thread ID"
    return 1
  fi
  if [ -z "$sender" ]; then sender="unknown"; fi
  if [ -z "$subject" ]; then subject="(No Subject)"; fi
  log_info "=========================================="
  log_info "Processing: $subject"
  log_info "From: $sender"
  log_info "Thread ID: $thread_id"
  log_info "=========================================="
  local email_content
  email_content=$(get_thread_content "$thread_id")
  if [ -z "$email_content" ]; then
    log_warn "Failed to retrieve email content, skipping classification"
    email_content=""
  fi
  local classifications
  classifications=$(classify_email "$subject" "$sender" "$email_content")
  local num_matches
  num_matches=$(echo "$classifications" | jq 'length')
  log_info "Found $num_matches pattern match(es)"
  if [ "$num_matches" -gt 0 ]; then
    for i in $(seq 0 $((num_matches - 1))); do
      local match
      match=$(echo "$classifications" | jq -r ".[$i]")
      IFS=':' read -r pattern_key priority <<< "$match"
      log_info "Handling pattern: $pattern_key (priority: $priority)"
      local pattern_data="${EMAIL_PATTERNS[$pattern_key]:-}"
      if [ -z "$pattern_data" ]; then
        log_warn "No handler data found for pattern: $pattern_key"
        continue
      fi
      IFS='|' read -r pattern handler_func handler_priority description <<< "$pattern_data"
      if declare -f "$handler_func" > /dev/null 2>&1; then
        $handler_func "$email_content" "$subject" "$sender" || log_warn "Handler $handler_func failed"
      else
        log_warn "Handler function not found: $handler_func"
      fi
    done
  else
    log_info "No special patterns matched - applying standard label processing"
  fi
  local label_pattern
  label_pattern=$(get_label_pattern "$sender")
  local label_applied=false
  if [ -n "$label_pattern" ]; then
    if apply_label "$thread_id" "$label_pattern"; then
      label_applied=true
    fi
  else
    log_info "No label pattern found for sender"
  fi
  remove_labels "$thread_id"
  if [ "$label_applied" = true ] || [ "$num_matches" -gt 0 ]; then
    archive_email "$thread_id"
  else
    log_info "Email not archived (no label and no classification)"
  fi
  log_info "Email processing completed"
  echo ""
  return 0
}

process_all_emails() {
  log_info "Starting email batch processing (max: $MAX_EMAILS emails)"
  local unread_emails
  unread_emails=$(get_unread_emails)
  if [ -z "$unread_emails" ]; then
    log_info "No unread emails found"
    return 0
  fi
  local email_count
  email_count=$(echo "$unread_emails" | jq '.messages | length')
  if [ "$email_count" -eq 0 ]; then
    log_info "No unread emails to process"
    return 0
  fi
  log_info "Found $email_count unread email(s)"
  for i in $(seq 0 $((email_count - 1))); do
    local email_json
    email_json=$(echo "$unread_emails" | jq ".messages[$i]")
    process_single_email "$email_json" || log_warn "Failed to process email $((i+1))"
    sleep 0
  done
  log_info "Batch processing completed"
  return 0
}

main() {
  log_info "==========================================="
  log_info "Intelligent Gmail Manager Started"
  log_info "==========================================="
  if ! process_all_emails; then
    log_error "Email processing failed"
    exit 1
  fi
  log_info "==========================================="
  log_info "Intelligent Gmail Manager Finished"
  log_info "==========================================="
  exit 0
}

main "$@"
'''

script_path = WORKSPACE / "script.sh"
script_path.write_text(script_sh_content)
script_path.chmod(script_path.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

print(f"Workspace generated at: {WORKSPACE}")
print(f"Files created:")
for f in sorted(WORKSPACE.rglob("*")):
    if f.is_file():
        print(f"  {f.relative_to(WORKSPACE)}")