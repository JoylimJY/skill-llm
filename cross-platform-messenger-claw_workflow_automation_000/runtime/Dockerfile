FROM python:3.11-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    bash \
    curl \
    jq \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

RUN pip install flask requests -i https://pypi.tuna.tsinghua.edu.cn/simple

# Create the openclaw mock CLI
RUN mkdir -p /usr/local/bin

RUN cat > /usr/local/bin/openclaw << 'OPENCLAW_EOF'
#!/usr/bin/env python3
import sys
import json
import argparse
import requests
import os

MOCK_URL = "http://127.0.0.1:19876"

def send_to_mock(payload):
    try:
        r = requests.post(f"{MOCK_URL}/record", json=payload, timeout=5)
        if r.status_code == 200:
            print(json.dumps({"status": "ok", "detail": r.json()}))
        else:
            print(json.dumps({"status": "error", "detail": r.text}))
            sys.exit(1)
    except Exception as e:
        print(json.dumps({"status": "error", "detail": str(e)}))
        sys.exit(1)

def cmd_send(args):
    payload = {
        "action": "send",
        "channel": args.channel,
        "target": args.target,
        "message": args.message,
    }
    if hasattr(args, 'media') and args.media:
        payload["media"] = args.media
    if hasattr(args, 'silent') and args.silent:
        payload["silent"] = True
    if hasattr(args, 'reply_to') and args.reply_to:
        payload["reply_to"] = args.reply_to
    if hasattr(args, 'dry_run') and args.dry_run:
        print(json.dumps({"status": "dry-run", "payload": payload}))
        return
    send_to_mock(payload)

def cmd_broadcast(args):
    payload = {
        "action": "broadcast",
        "channel": args.channel,
        "targets": args.targets,
        "message": args.message,
    }
    if hasattr(args, 'silent') and args.silent:
        payload["silent"] = True
    if hasattr(args, 'dry_run') and args.dry_run:
        print(json.dumps({"status": "dry-run", "payload": payload}))
        return
    send_to_mock(payload)

def main():
    parser = argparse.ArgumentParser(prog='openclaw')
    subparsers = parser.add_subparsers(dest='command')

    msg_parser = subparsers.add_parser('message')
    msg_subparsers = msg_parser.add_subparsers(dest='subcommand')

    send_parser = msg_subparsers.add_parser('send')
    send_parser.add_argument('--channel', required=True)
    send_parser.add_argument('--target', required=True)
    send_parser.add_argument('--message', required=True)
    send_parser.add_argument('--media', default=None)
    send_parser.add_argument('--silent', action='store_true')
    send_parser.add_argument('--reply-to', default=None)
    send_parser.add_argument('--dry-run', action='store_true')

    bc_parser = msg_subparsers.add_parser('broadcast')
    bc_parser.add_argument('--channel', required=True)
    bc_parser.add_argument('--targets', nargs='+', required=True)
    bc_parser.add_argument('--message', required=True)
    bc_parser.add_argument('--silent', action='store_true')
    bc_parser.add_argument('--dry-run', action='store_true')

    cron_parser = subparsers.add_parser('cron')

    args = parser.parse_args()

    if args.command == 'message':
        if args.subcommand == 'send':
            cmd_send(args)
        elif args.subcommand == 'broadcast':
            cmd_broadcast(args)
        else:
            parser.print_help()
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == '__main__':
    main()
OPENCLAW_EOF

RUN chmod +x /usr/local/bin/openclaw

RUN mkdir -p /workspace
WORKDIR /workspace