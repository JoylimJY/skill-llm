#!/bin/bash
set -e

# Create the mock flyai CLI that logs all invocations and returns realistic JSON
# This will be placed BEFORE the npm global bin in PATH after agent installs
# We create a wrapper that the agent's npm install will be shadowed by our mock
# Strategy: put mock in /usr/local/bin/flyai (high priority) that logs & returns data

cat > /usr/local/bin/flyai << 'FLYAI_MOCK_EOF'
#!/bin/bash

# Log ALL invocations with full arguments and environment
LOG_FILE="/workspace/.flyai_mock_logs/calls.log"
mkdir -p "$(dirname "$LOG_FILE")"

TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
TLS_REJECT="${NODE_TLS_REJECT_UNAUTHORIZED:-not_set}"
echo "CALL|${TIMESTAMP}|TLS_REJECT=${TLS_REJECT}|ARGS: $*" >> "$LOG_FILE"

COMMAND="$1"
shift

# Parse arguments into associative array
declare -A PARAMS
while [[ $# -gt 0 ]]; do
    case "$1" in
        --*=*)
            key="${1%%=*}"
            val="${1#*=}"
            PARAMS["$key"]="$val"
            shift
            ;;
        --*)
            key="$1"
            if [[ -n "$2" && "$2" != --* ]]; then
                PARAMS["$key"]="$2"
                shift 2
            else
                PARAMS["$key"]="true"
                shift
            fi
            ;;
        *)
            shift
            ;;
    esac
done

# Log parsed params
echo "PARAMS|$(declare -p PARAMS)" >> "$LOG_FILE"

case "$COMMAND" in
    "--help"|"help")
        echo "FlyAI CLI v2.1.0"
        echo "Commands: search-flight, search-hotel, search-poi, keyword-search"
        echo "Use --help with any command for details."
        ;;

    "keyword-search")
        echo '{"status":"ok","results":[{"type":"flight","summary":"北京出发多条航班可选","count":12}]}'
        ;;

    "search-flight")
        ORIGIN="${PARAMS[--origin]}"
        DEST="${PARAMS[--destination]}"
        SORT_TYPE="${PARAMS[--sort-type]}"
        DEP_HOUR_START="${PARAMS[--dep-hour-start]}"

        # Log specific flags for eval
        echo "FLIGHT_SORT_TYPE|${SORT_TYPE}" >> "$LOG_FILE"
        echo "FLIGHT_DEP_HOUR_START|${DEP_HOUR_START}" >> "$LOG_FILE"
        echo "FLIGHT_ORIGIN|${ORIGIN}" >> "$LOG_FILE"
        echo "FLIGHT_DEST|${DEST}" >> "$LOG_FILE"

        # Return different results based on destination
        case "$DEST" in
            *"上海"*|*"SHA"*)
                cat << 'JSON'
{"status":"ok","flights":[{"flightNo":"CA1234","depTime":"13:30","arrTime":"15:50","price":980,"remainSeats":8,"jumpUrl":"https://www.fliggy.com/flight/CA1234","origin":"北京","dest":"上海"},{"flightNo":"MU5678","depTime":"14:15","arrTime":"16:40","price":860,"remainSeats":3,"jumpUrl":"https://www.fliggy.com/flight/MU5678","origin":"北京","dest":"上海"}]}
JSON
                ;;
            *"成都"*|*"CTU"*)
                cat << 'JSON'
{"status":"ok","flights":[{"flightNo":"3U8888","depTime":"13:50","arrTime":"16:30","price":1240,"remainSeats":12,"jumpUrl":"https://www.fliggy.com/flight/3U8888","origin":"北京","dest":"成都"},{"flightNo":"CA4567","depTime":"14:30","arrTime":"17:10","price":1380,"remainSeats":5,"jumpUrl":"https://www.fliggy.com/flight/CA4567","origin":"北京","dest":"成都"}]}
JSON
                ;;
            *"西安"*|*"SIA"*)
                cat << 'JSON'
{"status":"ok","flights":[{"flightNo":"MU2341","depTime":"13:20","arrTime":"15:10","price":760,"remainSeats":20,"jumpUrl":"https://www.fliggy.com/flight/MU2341","origin":"北京","dest":"西安"},{"flightNo":"HU7890","depTime":"15:00","arrTime":"16:50","price":890,"remainSeats":7,"jumpUrl":"https://www.fliggy.com/flight/HU7890","origin":"北京","dest":"西安"}]}
JSON
                ;;
            *"杭州"*|*"HGH"*)
                cat << 'JSON'
{"status":"ok","flights":[{"flightNo":"CZ3322","depTime":"13:45","arrTime":"15:55","price":820,"remainSeats":15,"jumpUrl":"https://www.fliggy.com/flight/CZ3322","origin":"北京","dest":"杭州"},{"flightNo":"CA8801","depTime":"14:50","arrTime":"17:05","price":910,"remainSeats":2,"jumpUrl":"https://www.fliggy.com/flight/CA8801","origin":"北京","dest":"杭州"}]}
JSON
                ;;
            *)
                cat << 'JSON'
{"status":"ok","flights":[{"flightNo":"ZH1122","depTime":"14:00","arrTime":"16:30","price":1100,"remainSeats":6,"jumpUrl":"https://www.fliggy.com/flight/ZH1122","origin":"北京","dest":"青岛"}]}
JSON
                ;;
        esac
        ;;

    "search-hotel")
        DEST="${PARAMS[--dest-name]}"
        SORT="${PARAMS[--sort]}"

        # Log specific flags for eval
        echo "HOTEL_SORT|${SORT}" >> "$LOG_FILE"
        echo "HOTEL_DEST|${DEST}" >> "$LOG_FILE"

        cat << JSON
{"status":"ok","hotels":[{"name":"${DEST}悦享精选酒店","price":580,"rating":4.7,"available":true,"jumpUrl":"https://www.fliggy.com/hotel/H001","address":"${DEST}市中心区"},{"name":"${DEST}如家商务酒店","price":320,"rating":4.2,"available":true,"jumpUrl":"https://www.fliggy.com/hotel/H002","address":"${DEST}火车站附近"}]}
JSON
        ;;

    "search-poi")
        CITY="${PARAMS[--city-name]}"
        POI_LEVEL="${PARAMS[--poi-level]}"

        # Log specific flags for eval
        echo "POI_LEVEL|${POI_LEVEL}" >> "$LOG_FILE"
        echo "POI_CITY|${CITY}" >> "$LOG_FILE"

        case "$CITY" in
            *"上海"*)
                cat << 'JSON'
{"status":"ok","pois":[{"name":"外滩","type":"景观","rating":4.9,"jumpUrl":"https://www.fliggy.com/poi/P001","openTime":"全天"},{"name":"豫园","type":"历史文化","rating":4.6,"jumpUrl":"https://www.fliggy.com/poi/P002","openTime":"08:30-17:00"},{"name":"南京路步行街","type":"购物","rating":4.5,"jumpUrl":"https://www.fliggy.com/poi/P003","openTime":"全天"}]}
JSON
                ;;
            *"成都"*)
                cat << 'JSON'
{"status":"ok","pois":[{"name":"宽窄巷子","type":"历史文化","rating":4.7,"jumpUrl":"https://www.fliggy.com/poi/P010","openTime":"全天"},{"name":"锦里古街","type":"历史文化","rating":4.6,"jumpUrl":"https://www.fliggy.com/poi/P011","openTime":"09:00-22:00"},{"name":"大熊猫繁育研究基地","type":"自然","rating":4.9,"jumpUrl":"https://www.fliggy.com/poi/P012","openTime":"07:30-18:00"}]}
JSON
                ;;
            *"西安"*)
                cat << 'JSON'
{"status":"ok","pois":[{"name":"兵马俑","type":"历史文化","rating":4.9,"jumpUrl":"https://www.fliggy.com/poi/P020","openTime":"08:30-18:30"},{"name":"西安城墙","type":"历史文化","rating":4.7,"jumpUrl":"https://www.fliggy.com/poi/P021","openTime":"08:00-22:00"},{"name":"回民街","type":"美食","rating":4.6,"jumpUrl":"https://www.fliggy.com/poi/P022","openTime":"全天"}]}
JSON
                ;;
            *)
                cat << JSON
{"status":"ok","pois":[{"name":"${CITY}历史博物馆","type":"历史文化","rating":4.5,"jumpUrl":"https://www.fliggy.com/poi/P099","openTime":"09:00-17:00"},{"name":"${CITY}老城区","type":"景观","rating":4.4,"jumpUrl":"https://www.fliggy.com/poi/P098","openTime":"全天"}]}
JSON
                ;;
        esac
        ;;

    *)
        echo '{"status":"error","message":"Unknown command: '"$COMMAND"'"}'
        exit 1
        ;;
esac
FLYAI_MOCK_EOF

chmod +x /usr/local/bin/flyai

# Ensure log directory exists with correct permissions
mkdir -p /workspace/.flyai_mock_logs
chmod 777 /workspace/.flyai_mock_logs

# Ensure ~/.flyai directory exists (was created by gen_inputs but let's be safe)
mkdir -p ~/.flyai

echo "Mock flyai CLI installed at /usr/local/bin/flyai"
echo "Call logs will be written to /workspace/.flyai_mock_logs/calls.log"
flyai --help