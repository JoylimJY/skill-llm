from pathlib import Path
import json
import random
import textwrap

random.seed(1337)
root = Path('.')
dist = root / 'dist'
scripts = root / 'scripts'
dist.mkdir(exist_ok=True)
scripts.mkdir(exist_ok=True)

live = dist / 'agent-runner.runtime-BWpOtdxK.js'
stale = dist / 'reply-OLD123.js'
other = dist / 'compact-ZZZ999.js'
backup = dist / 'agent-runner.runtime-BWpOtdxK.js.bak.telegram-footer.20240101T000000Z'
marker = 'TELEGRAM_FOOTER_PATCH_MARKER'
footer = '🧠 Model + 💭 Think + 📊 Context'

live.write_text(textwrap.dedent(f'''
    function formatTokens(x) {{
      return x.join(' ');
    }}
    function sendReply(message) {{
      const body = formatTokens([message]);
      return body;
    }}
    // {marker}: live reply path candidate
    const LIVE_PATH = true;
''').strip() + '\n', encoding='utf-8')

stale.write_text(textwrap.dedent(f'''
    export function sendReply(message) {{
      return message;
    }}
    // old bundle without live path
''').strip() + '\n', encoding='utf-8')

other.write_text(textwrap.dedent('''
    function compactReply(t){ return t; }
    const helper = { name: 'compact' };
''').strip() + '\n', encoding='utf-8')

backup.write_text(textwrap.dedent(f'''
    function formatTokens(x) {{
      return x.join(' ');
    }}
    function sendReply(message) {{
      const body = formatTokens([message]);
      return body;
    }}
    // backup copy for rollback tests
''').strip() + '\n', encoding='utf-8')

(scripts / 'patch_reply_footer.py').write_text(textwrap.dedent('''
    #!/usr/bin/env python3
    from pathlib import Path
    import argparse
    import json
    import re
    import shutil
    import sys

    FOOTER = "🧠 Model + 💭 Think + 📊 Context"
    MARKER = "TELEGRAM_FOOTER_PATCH_MARKER"

    def discover(dist):
        files = sorted(Path(dist).rglob('*.js'))
        ranked = []
        for f in files:
            try:
                text = f.read_text(encoding='utf-8')
            except Exception:
                continue
            score = 0
            if 'sendReply' in text:
                score += 3
            if 'formatTokens' in text:
                score += 2
            if 'LIVE_PATH' in text or MARKER in text:
                score += 5
            ranked.append((score, str(f), text))
        ranked.sort(reverse=True)
        return ranked

    def patch_file(path):
        p = Path(path)
        text = p.read_text(encoding='utf-8')
        bak = p.with_suffix(p.suffix + '.bak.telegram-footer.20240101T000000Z')
        if not bak.exists():
            shutil.copy2(p, bak)
        if FOOTER in text:
            return 'already'
        if MARKER in text:
            text = re.sub(r'//\s*' + re.escape(MARKER) + r'.*', f'// {MARKER}\n// {FOOTER}', text)
        else:
            text += f"\n// {MARKER}\n// {FOOTER}\n"
        p.write_text(text, encoding='utf-8')
        return 'patched'

    def main():
        ap = argparse.ArgumentParser()
        ap.add_argument('--dist', default='dist')
        ap.add_argument('--dry-run', action='store_true')
        ap.add_argument('--auto-discover', action='store_true')
        ap.add_argument('--verify', action='store_true')
        ap.add_argument('--list-targets', action='store_true')
        ap.add_argument('--rollback', action='store_true')
        args = ap.parse_args()
        ranked = discover(args.dist)
        if args.list_targets:
            for score, path, text in ranked:
                print(f'{path} candidate=true marker={MARKER in text} score={score}')
            return 0
        if args.dry_run:
            for score, path, text in ranked[:3]:
                print(f'dry-run {path} candidate=true marker={MARKER in text}')
            return 0
        if args.rollback:
            for score, path, text in ranked:
                p = Path(path)
                bak = p.with_suffix(p.suffix + '.bak.telegram-footer.20240101T000000Z')
                if bak.exists():
                    shutil.copy2(bak, p)
            return 0
        if args.auto_discover:
            for score, path, text in ranked:
                if score >= 5:
                    patch_file(path)
            if args.verify:
                for score, path, text in ranked:
                    if score >= 5 and FOOTER not in Path(path).read_text(encoding='utf-8'):
                        raise SystemExit(1)
            return 0
        return 0

    if __name__ == '__main__':
        sys.exit(main())
''').lstrip(), encoding='utf-8')

(scripts / 'revert_reply_footer.py').write_text(textwrap.dedent('''
    #!/usr/bin/env python3
    from pathlib import Path
    import shutil
    import sys

    def main():
        dist = Path('dist')
        for p in dist.rglob('*.js'):
            bak = p.with_suffix(p.suffix + '.bak.telegram-footer.20240101T000000Z')
            if bak.exists():
                shutil.copy2(bak, p)
        return 0

    if __name__ == '__main__':
        sys.exit(main())
''').lstrip(), encoding='utf-8')

(scripts / 'smoke_test_footer_patch.sh').write_text(textwrap.dedent('''
    #!/usr/bin/env bash
    set -euo pipefail
    echo smoke-test-ready
''').lstrip(), encoding='utf-8')

print(json.dumps({
    'files': [str(live), str(stale), str(other), str(backup)],
    'marker': marker,
    'footer': footer,
}, ensure_ascii=False, indent=2))
