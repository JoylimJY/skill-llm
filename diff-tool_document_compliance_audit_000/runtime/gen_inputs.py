import os
import random
import json

random.seed(42)

workspace = "/workspace"

# --- Create the scripts directory with the diff tool ---
scripts_dir = os.path.join(workspace, "scripts")
os.makedirs(scripts_dir, exist_ok=True)

diff_tool_code = r'''#!/usr/bin/env python3
"""
diff.py - Text Difference Comparison Tool
Compares two texts or files and highlights additions, deletions, and modifications.
"""

import sys
import json
import argparse
import difflib


def normalize_lines(lines, ignore_space=False):
    if ignore_space:
        return [line.replace(" ", "").replace("\t", "") for line in lines]
    return lines


def compute_diff(lines_a, lines_b, ignore_space=False):
    """
    Compute a semantic diff between two lists of lines.
    Returns a list of diff entries: {type, line_number_a, line_number_b, content_a, content_b}
    """
    norm_a = normalize_lines(lines_a, ignore_space)
    norm_b = normalize_lines(lines_b, ignore_space)

    matcher = difflib.SequenceMatcher(None, norm_a, norm_b)
    differences = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'equal':
            continue
        elif tag == 'insert':
            for j in range(j1, j2):
                differences.append({
                    "type": "added",
                    "line_number_a": None,
                    "line_number_b": j + 1,
                    "content_a": None,
                    "content_b": lines_b[j].rstrip('\n')
                })
        elif tag == 'delete':
            for i in range(i1, i2):
                differences.append({
                    "type": "deleted",
                    "line_number_a": i + 1,
                    "line_number_b": None,
                    "content_a": lines_a[i].rstrip('\n'),
                    "content_b": None
                })
        elif tag == 'replace':
            len_a = i2 - i1
            len_b = j2 - j1
            common = min(len_a, len_b)
            for k in range(common):
                differences.append({
                    "type": "modified",
                    "line_number_a": i1 + k + 1,
                    "line_number_b": j1 + k + 1,
                    "content_a": lines_a[i1 + k].rstrip('\n'),
                    "content_b": lines_b[j1 + k].rstrip('\n')
                })
            if len_a > common:
                for i in range(i1 + common, i2):
                    differences.append({
                        "type": "deleted",
                        "line_number_a": i + 1,
                        "line_number_b": None,
                        "content_a": lines_a[i].rstrip('\n'),
                        "content_b": None
                    })
            if len_b > common:
                for j in range(j1 + common, j2):
                    differences.append({
                        "type": "added",
                        "line_number_a": None,
                        "line_number_b": j + 1,
                        "content_a": None,
                        "content_b": lines_b[j].rstrip('\n')
                    })

    return differences


def build_stats(differences):
    added = sum(1 for d in differences if d["type"] == "added")
    deleted = sum(1 for d in differences if d["type"] == "deleted")
    modified = sum(1 for d in differences if d["type"] == "modified")
    return {
        "added": added,
        "deleted": deleted,
        "modified": modified,
        "total_changes": added + deleted + modified
    }


def format_standard(lines_a, lines_b, differences, stats=False):
    output = []
    diff = difflib.unified_diff(lines_a, lines_b, lineterm='')
    for line in diff:
        if line.startswith('+'):
            output.append(f"\033[32m{line}\033[0m")
        elif line.startswith('-'):
            output.append(f"\033[31m{line}\033[0m")
        elif line.startswith('@'):
            output.append(f"\033[33m{line}\033[0m")
        else:
            output.append(line)
    if stats:
        s = build_stats(differences)
        output.append(f"\n--- Stats ---")
        output.append(f"Added: {s['added']}  Deleted: {s['deleted']}  Modified: {s['modified']}  Total: {s['total_changes']}")
    return '\n'.join(output)


def format_simple(differences, stats=False):
    output = []
    for d in differences:
        if d["type"] == "added":
            output.append(f"+ [{d['line_number_b']}] {d['content_b']}")
        elif d["type"] == "deleted":
            output.append(f"- [{d['line_number_a']}] {d['content_a']}")
        elif d["type"] == "modified":
            output.append(f"~ [{d['line_number_a']}] {d['content_a']} => {d['content_b']}")
    if stats:
        s = build_stats(differences)
        output.append(f"\nAdded: {s['added']}  Deleted: {s['deleted']}  Modified: {s['modified']}")
    return '\n'.join(output)


def format_json(differences, stats=False):
    result = {"differences": differences}
    if stats:
        result["stats"] = build_stats(differences)
    return json.dumps(result, ensure_ascii=False, indent=2)


def get_lines_from_string(text):
    return [line + '\n' for line in text.split('\n')]


def get_lines_from_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.readlines()


def main():
    parser = argparse.ArgumentParser(description='Text diff tool')
    subparsers = parser.add_subparsers(dest='mode')

    # string mode
    sp = subparsers.add_parser('string')
    sp.add_argument('text_a')
    sp.add_argument('text_b')
    sp.add_argument('--format', choices=['standard', 'simple', 'json'], default='standard')
    sp.add_argument('--stats', action='store_true')
    sp.add_argument('--ignore-space', action='store_true')

    # file mode
    fp = subparsers.add_parser('file')
    fp.add_argument('file_a')
    fp.add_argument('file_b')
    fp.add_argument('--format', choices=['standard', 'simple', 'json'], default='standard')
    fp.add_argument('--stats', action='store_true')
    fp.add_argument('--ignore-space', action='store_true')

    args = parser.parse_args()

    if args.mode == 'string':
        lines_a = get_lines_from_string(args.text_a)
        lines_b = get_lines_from_string(args.text_b)
    elif args.mode == 'file':
        lines_a = get_lines_from_file(args.file_a)
        lines_b = get_lines_from_file(args.file_b)
    else:
        parser.print_help()
        sys.exit(1)

    ignore_space = getattr(args, 'ignore_space', False)
    differences = compute_diff(lines_a, lines_b, ignore_space=ignore_space)

    fmt = args.format
    show_stats = args.stats

    if fmt == 'standard':
        print(format_standard(lines_a, lines_b, differences, stats=show_stats))
    elif fmt == 'simple':
        print(format_simple(differences, stats=show_stats))
    elif fmt == 'json':
        print(format_json(differences, stats=show_stats))


if __name__ == '__main__':
    main()
'''

with open(os.path.join(scripts_dir, "diff.py"), "w") as f:
    f.write(diff_tool_code)

# --- Create distractor files and nested directory structure ---
# Legal department structure
dirs = [
    "contracts/software_licenses",
    "contracts/vendor_agreements",
    "contracts/nda",
    "compliance/audits/2023",
    "compliance/audits/2024",
    "compliance/policies",
    "internal/hr/onboarding",
    "internal/finance/reports",
    "internal/it/security",
    "internal/it/access_control",
    "logs/system",
    "logs/audit_trail",
]

for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files
distractor_contents = {
    "contracts/vendor_agreements/vendor_acme_2024.txt": "Vendor: ACME Corp\nContract valid from Jan 2024 to Dec 2024\nPayment: Net-30\n",
    "contracts/nda/nda_template_v1.txt": "NON-DISCLOSURE AGREEMENT\nThis agreement is entered into as of [DATE]\nParties: [PARTY_A] and [PARTY_B]\n",
    "compliance/audits/2023/audit_summary_2023.txt": "Audit Year: 2023\nFindings: 3 minor, 1 major\nResolution: All resolved\n",
    "compliance/audits/2024/pending_items.txt": "Item 1: Review access logs\nItem 2: Update password policy\n",
    "compliance/policies/data_retention_policy.txt": "Data retention: 7 years for financial records, 3 years for communications.\n",
    "internal/hr/onboarding/checklist.txt": "1. Issue laptop\n2. Setup email\n3. Sign NDA\n4. Enroll in training\n",
    "internal/finance/reports/q3_2024_summary.txt": "Q3 Revenue: $4.2M\nExpenses: $3.1M\nNet: $1.1M\n",
    "internal/it/security/vulnerability_scan_oct2024.txt": "Scan date: 2024-10-15\nCritical: 0\nHigh: 2\nMedium: 5\n",
    "internal/it/access_control/user_permissions.txt": "admin: full\nanalyst: read-only\naudit: read, append\n",
    "logs/system/system_errors_nov2024.log": "[ERROR] 2024-11-01 disk_usage 95%\n[WARN]  2024-11-02 memory_pressure moderate\n",
    "logs/audit_trail/access_log_2024.log": "2024-10-01 09:01 user=john action=login\n2024-10-01 09:15 user=john action=view_contract\n",
}

for path, content in distractor_contents.items():
    full_path = os.path.join(workspace, path)
    with open(full_path, "w") as f:
        f.write(content)

# --- Create the TWO KEY document versions for the compliance task ---
# These are two versions of a software license policy document
# Designed so that:
#   - Without --ignore-space, there are EXTRA whitespace-only "changes"
#   - With --ignore-space, only truly semantic changes remain
#   - There are added, deleted, and modified lines

policy_v1 = """\
SOFTWARE LICENSE COMPLIANCE POLICY
Version: 1.0
Effective Date: 2023-01-01
Review Date: 2024-01-01

SECTION 1: PURPOSE
This policy establishes guidelines for the acquisition and use of software licenses
within the organization to ensure compliance with licensing agreements.

SECTION 2: SCOPE
This policy applies to all employees, contractors, and third-party vendors who
install, use, or manage software on organizational systems.

SECTION 3: LICENSE CATEGORIES
3.1 Commercial Software
    All commercial software must be purchased through the IT Procurement team.
    Unauthorized installations are strictly prohibited.

3.2 Open Source Software
    Open source software may be used subject to approval from the Legal department.
    License obligations (e.g., attribution, copyleft) must be met.

3.3 Freeware
    Freeware may be used for personal productivity with manager approval.

SECTION 4: RESPONSIBILITIES
4.1 IT Department
    Maintain an inventory of all installed software and licenses.
    Conduct quarterly audits to verify license compliance.

4.2 Employees
    Report any unlicensed or unauthorized software to the IT helpdesk immediately.

4.3 Legal Department
    Review and approve any new software license agreements.

SECTION 5: NON-COMPLIANCE
Violations of this policy may result in disciplinary action, up to and including
termination of employment.

SECTION 6: REVIEW
This policy will be reviewed annually by the Compliance Committee.
"""

policy_v2 = """\
SOFTWARE LICENSE COMPLIANCE POLICY
Version: 2.0
Effective Date: 2024-01-01
Review Date: 2025-01-01

SECTION 1: PURPOSE
This policy establishes guidelines for the acquisition and use of software licenses
within the organization to ensure compliance with all applicable licensing agreements.

SECTION 2: SCOPE
This policy applies to all employees, contractors, and third-party vendors who
install, use, or manage software on organizational systems and cloud environments.

SECTION 3: LICENSE CATEGORIES
3.1 Commercial Software
    All commercial software must be purchased through the IT Procurement team.
    Unauthorized installations are strictly prohibited.

3.2 Open Source Software
    Open source software may be used subject to approval from the Legal department.
    License obligations (e.g., attribution, copyleft, patent clauses) must be met.

3.3 Freeware
    Freeware may be used for personal productivity with manager approval.

3.4 SaaS and Cloud-Based Software
    All SaaS subscriptions must be registered with IT and Legal prior to activation.

SECTION 4: RESPONSIBILITIES
4.1 IT Department
    Maintain an inventory of all installed software and licenses.
    Conduct monthly audits to verify license compliance.

4.2 Employees
    Report any unlicensed or unauthorized software to the IT helpdesk immediately.
    Complete annual license compliance training.

4.3 Legal Department
    Review and approve any new software license agreements.
    Maintain a register of all active third-party software licenses.

SECTION 5: NON-COMPLIANCE
Violations of this policy may result in disciplinary action, up to and including
termination of employment or contract, and potential legal action.

SECTION 6: REVIEW
This policy will be reviewed annually by the Compliance and Legal Committee.
"""

# Intentionally add some whitespace-only variation lines to v2 (spacing noise)
# These lines will appear as changes WITHOUT --ignore-space but not WITH --ignore-space
# We'll insert lines that differ only in leading spaces
policy_v2_with_whitespace_noise = policy_v2.replace(
    "SECTION 3: LICENSE CATEGORIES",
    "SECTION 3:  LICENSE CATEGORIES"  # extra space — whitespace noise
).replace(
    "SECTION 4: RESPONSIBILITIES",
    "SECTION 4:  RESPONSIBILITIES"   # extra space — whitespace noise
)

v1_path = os.path.join(workspace, "contracts/software_licenses/license_policy_v1.txt")
v2_path = os.path.join(workspace, "contracts/software_licenses/license_policy_v2.txt")

with open(v1_path, "w") as f:
    f.write(policy_v1)

with open(v2_path, "w") as f:
    f.write(policy_v2_with_whitespace_noise)

print("Workspace initialized successfully.")
print(f"V1 policy: {v1_path}")
print(f"V2 policy: {v2_path}")