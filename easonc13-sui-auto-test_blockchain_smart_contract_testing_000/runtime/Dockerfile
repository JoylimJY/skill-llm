FROM debian:bookworm-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    bash \
    curl \
    git \
    coreutils \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --break-system-packages \
    toml \
    pyyaml \
    -i https://pypi.tuna.tsinghua.edu.cn/simple

# Create skill directory structure
RUN mkdir -p /root/clawd/skills/sui-coverage
RUN mkdir -p /usr/local/bin

# Create a mock 'sui' CLI that simulates Move test + coverage commands
RUN cat > /usr/local/bin/sui << 'SUIEOF'
#!/bin/bash
# Mock Sui CLI for testing environment

SUBCMD="$1"
shift

if [ "$SUBCMD" = "move" ]; then
    MOVECMD="$1"
    shift
    
    if [ "$MOVECMD" = "test" ]; then
        # Parse flags
        COVERAGE=false
        TRACE=false
        for arg in "$@"; do
            case $arg in
                --coverage) COVERAGE=true ;;
                --trace) TRACE=true ;;
            esac
        done
        
        # Find Move.toml to determine package
        PACKAGE_DIR="${SUI_PACKAGE_PATH:-.}"
        MOVE_TOML="$PACKAGE_DIR/Move.toml"
        
        if [ ! -f "$MOVE_TOML" ]; then
            echo "Error: Move.toml not found in $PACKAGE_DIR"
            exit 1
        fi
        
        # Extract package name
        PKG_NAME=$(grep 'name' "$MOVE_TOML" | head -1 | sed 's/.*=\s*"\(.*\)"/\1/')
        
        # Run Python test simulator
        python3 /usr/local/bin/sui_test_runner.py "$PACKAGE_DIR" "$COVERAGE" "$TRACE"
        EXIT_CODE=$?
        exit $EXIT_CODE
        
    elif [ "$MOVECMD" = "coverage" ]; then
        COVCMD="$1"
        shift
        if [ "$COVCMD" = "lcov" ]; then
            PACKAGE_DIR="${SUI_PACKAGE_PATH:-.}"
            python3 /usr/local/bin/sui_coverage_lcov.py "$PACKAGE_DIR"
        elif [ "$COVCMD" = "bytecode" ]; then
            MODULE=""
            for arg in "$@"; do
                case $arg in
                    --module) MODULE="$1"; shift ;;
                    *) ;;
                esac
            done
            echo "Bytecode coverage for module: $MODULE"
        fi
    fi
fi
SUIEOF
RUN chmod +x /usr/local/bin/sui

WORKDIR /workspace
CMD ["/bin/bash"]