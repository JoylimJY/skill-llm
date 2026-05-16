FROM python:3.11-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    coreutils \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple \
    pytest

# Create the skill script at the expected path
RUN mkdir -p /root/.openclaw/skills/json-formatter-pro

# Write the formatter script
RUN cat > /root/.openclaw/skills/json-formatter-pro/json_formatter.py << 'PYEOF'
#!/usr/bin/env python3
import argparse
import json
import sys
import os

def main():
    parser = argparse.ArgumentParser(description='JSON Formatter Pro')
    parser.add_argument('command', choices=['format', 'validate'], help='Command to run')
    parser.add_argument('input', help='Input file or - for stdin')
    parser.add_argument('-o', '--output', help='Output file (default: stdout)')
    parser.add_argument('-i', '--indent', type=int, default=2, help='Indentation spaces (default: 2)')
    parser.add_argument('--sort-keys', action='store_true', help='Sort JSON keys alphabetically')

    args = parser.parse_args()

    # Read input
    try:
        if args.input == '-':
            content = sys.stdin.read()
        else:
            if not os.path.exists(args.input):
                print(f"Error: File not found: {args.input}", file=sys.stderr)
                sys.exit(2)
            with open(args.input, 'r') as f:
                content = f.read()
    except PermissionError as e:
        print(f"Error: Permission denied: {e}", file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(3)

    # Parse JSON
    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        print(f"Invalid JSON: {e}", file=sys.stderr)
        sys.exit(1)

    if args.command == 'validate':
        print("Valid JSON")
        sys.exit(0)

    # Format
    try:
        formatted = json.dumps(data, indent=args.indent, sort_keys=args.sort_keys)
        if args.output:
            with open(args.output, 'w') as f:
                f.write(formatted + '\n')
        else:
            print(formatted)
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(3)

if __name__ == '__main__':
    main()
PYEOF

RUN chmod +x /root/.openclaw/skills/json-formatter-pro/json_formatter.py

WORKDIR /workspace