#!/bin/bash
set -e

# Create open_calls log file
touch /tmp/open_calls.log
chmod 666 /tmp/open_calls.log

# Create mock 'mdfind' that simulates Spotlight behavior
# CRITICAL: mdfind for 'DevUtils' returns NO RESULTS (to force ls fallback)
cat > /usr/local/bin/mdfind << 'MDFIND_EOF'
#!/bin/bash
# Mock mdfind simulating macOS Spotlight

QUERY=""
NAME_FILTER=""
DIRS=("/Applications" "/Applications/Utilities" "/System/Applications" "/System/Applications/Utilities")

# Parse arguments: mdfind "kMDItemKind == 'Application'" -name "<keyword>"
while [[ $# -gt 0 ]]; do
    case "$1" in
        -name)
            NAME_FILTER="$2"
            shift 2
            ;;
        -onlyin)
            # ignore for mock
            shift 2
            ;;
        *)
            QUERY="$1"
            shift
            ;;
    esac
done

# Only respond to Application kind queries
if [[ "$QUERY" != *"kMDItemKind"* ]] && [[ "$QUERY" != *"Application"* ]]; then
    exit 0
fi

# DevUtils is NOT indexed by Spotlight in this system (simulates mdfind blind spot)
# This forces the agent to fall back to ls + grep
if [[ -n "$NAME_FILTER" ]]; then
    LOWER_FILTER=$(echo "$NAME_FILTER" | tr '[:upper:]' '[:lower:]')
    if [[ "$LOWER_FILTER" == *"devutil"* ]]; then
        # Return nothing - simulates Spotlight not indexing ~/Applications
        exit 0
    fi
fi

# Search fake app directories for matching .app bundles
for dir in "${DIRS[@]}"; do
    if [[ -d "$dir" ]]; then
        if [[ -n "$NAME_FILTER" ]]; then
            find "$dir" -maxdepth 1 -iname "*${NAME_FILTER}*" -name "*.app" 2>/dev/null
        else
            find "$dir" -maxdepth 1 -name "*.app" 2>/dev/null
        fi
    fi
done
MDFIND_EOF

chmod +x /usr/local/bin/mdfind

# Create mock 'open' command that logs calls
cat > /usr/local/bin/open << 'OPEN_EOF'
#!/bin/bash
# Mock open command simulating macOS 'open'

LOG_FILE="/tmp/open_calls.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

APP_FLAG=false
APP_NAME=""
APP_PATH=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        -a)
            APP_FLAG=true
            APP_NAME="$2"
            shift 2
            ;;
        *)
            APP_PATH="$1"
            shift
            ;;
    esac
done

if [[ "$APP_FLAG" == "true" ]] && [[ -n "$APP_NAME" ]]; then
    echo "[$TIMESTAMP] open -a \"${APP_NAME}\"" >> "$LOG_FILE"
    echo "Opening ${APP_NAME}..."
    exit 0
fi

if [[ -n "$APP_PATH" ]]; then
    # Validate that the path exists and ends with .app
    if [[ "$APP_PATH" == *.app ]] && [[ -d "$APP_PATH" ]]; then
        echo "[$TIMESTAMP] open \"${APP_PATH}\"" >> "$LOG_FILE"
        echo "Opening ${APP_PATH}..."
        exit 0
    elif [[ "$APP_PATH" == *.app ]]; then
        echo "[$TIMESTAMP] open \"${APP_PATH}\" [PATH_NOT_FOUND]" >> "$LOG_FILE"
        echo "Error: The file ${APP_PATH} does not exist." >&2
        exit 1
    else
        echo "[$TIMESTAMP] open \"${APP_PATH}\" [NOT_AN_APP]" >> "$LOG_FILE"
        echo "Error: Not a .app bundle: ${APP_PATH}" >&2
        exit 1
    fi
fi

echo "Usage: open [-a appname] [path]" >&2
exit 1
OPEN_EOF

chmod +x /usr/local/bin/open

# Make sure /workspace is writable
chmod 777 /workspace

# Create the ~/Applications directory properly
mkdir -p ~/Applications
# Ensure DevUtils.app is there (from gen_inputs, but home might differ)
HOME_DIR=$(eval echo "~")
mkdir -p "${HOME_DIR}/Applications/DevUtils.app/Contents/MacOS"
echo '#!/bin/bash' > "${HOME_DIR}/Applications/DevUtils.app/Contents/MacOS/DevUtils"
chmod +x "${HOME_DIR}/Applications/DevUtils.app/Contents/MacOS/DevUtils"

echo "Mock environment ready."
echo "mdfind: $(which mdfind)"
echo "open: $(which open)"