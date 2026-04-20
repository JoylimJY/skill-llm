import json
import re
import sys
from pathlib import Path


def norm(s):
    try:
        s = str(s)
    except Exception:
        return ""
    s = s.lower()
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def safe_read(path):
    try:
        return Path(path).read_text(encoding='utf-8'), None
    except Exception as e:
        return None, str(e)


def find_line(lines, name):
    target = norm(name)
    for line in lines:
        if target in norm(line):
            return line
    return None


def has_date_line(line, day, month, year=None):
    try:
        txt = norm(line)
        ddmm = f"{day:02d}.{month:02d}"
        if ddmm not in txt:
            return False
        if year is not None and f"{year}" not in txt:
            return False
        return True
    except Exception:
        return False


def main():
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
    checks = []

    try:
        target = workspace / 'home' / 'clawd' / 'clawd' / 'data' / 'birthdays.md'
        text, err = safe_read(target)
        if text is None:
            checks.append({'name': 'output file exists and readable', 'passed': False, 'detail': f'missing or unreadable: {err}'})
        else:
            checks.append({'name': 'output file exists and readable', 'passed': True, 'detail': 'readable'})

            lines = [ln.rstrip('\n') for ln in text.splitlines()]

            # Preserve marker / unrelated content
            marker_ok = any('birthday-input-seed-2025-04-19' in norm(ln) for ln in lines)
            checks.append({'name': 'marker preserved', 'passed': marker_ok, 'detail': 'marker line present' if marker_ok else 'marker line missing'})

            unrelated_ok = any('unrelated note' in norm(ln) and 'keep this line intact' in norm(ln) for ln in lines)
            checks.append({'name': 'unrelated content preserved', 'passed': unrelated_ok, 'detail': 'unrelated line preserved' if unrelated_ok else 'unrelated line changed or missing'})

            expected = [
                ('Ada', 5, 2, 2012, True),
                ('Valentina', 14, 2, 2000, True),
                ('Marta', 14, 2, None, False),
                ('Max', 15, 3, 1990, True),
                ('Oskar', 28, 12, None, False),
                ('Lina', 1, 1, 1988, True),
            ]

            # Because the file should be sorted by month/day, check presence and rough ordering of day/month pairs.
            order_pairs = []
            for name, d, m, y, should_have_year in expected:
                line = find_line(lines, name)
                ok = line is not None and has_date_line(line, d, m, y if should_have_year else None)
                detail = f"{name}: " + (line if line is not None else 'missing')
                checks.append({'name': f'entry for {name}', 'passed': ok, 'detail': detail[:220]})
                if line is not None:
                    order_pairs.append((m, d, name))

            # Ensure no duplicate Valentina-style duplicated names by checking unique name occurrences lightly.
            unique_names_ok = True
            dup_detail = []
            for name, *_ in expected:
                count = sum(1 for ln in lines if norm(name) in norm(ln))
                if count != 1:
                    unique_names_ok = False
                    dup_detail.append(f'{name} appears {count} times')
            checks.append({'name': 'no duplicate target names', 'passed': unique_names_ok, 'detail': '; '.join(dup_detail) if dup_detail else 'each target name appears once'})

            # Sort check: compare the sequence of month/day in the order names appear in file among target entries only.
            positions = []
            for idx, ln in enumerate(lines):
                for name, d, m, y, should_have_year in expected:
                    if norm(name) in norm(ln):
                        positions.append((idx, m, d, name))
                        break
            sorted_ok = True
            if positions:
                md_seq = [(m, d) for _, m, d, _ in positions]
                sorted_ok = md_seq == sorted(md_seq)
            else:
                sorted_ok = False
            checks.append({'name': 'target entries sorted by month/day', 'passed': sorted_ok, 'detail': str(positions[:20])})

    except Exception as e:
        checks.append({'name': 'evaluation runtime', 'passed': False, 'detail': f'exception: {e}'})

    total = len(checks)
    passed = sum(1 for c in checks if c.get('passed'))
    result = {'passed': passed == total, 'score': (passed / total) if total else 0.0, 'checks': checks}
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()