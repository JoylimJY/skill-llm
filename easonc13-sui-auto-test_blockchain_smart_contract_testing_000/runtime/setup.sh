#!/bin/bash
set -e

# Make skill scripts executable
chmod +x /root/clawd/skills/sui-coverage/analyze_source.py
chmod +x /root/clawd/skills/sui-coverage/analyze.py
chmod +x /root/clawd/skills/sui-coverage/parse_bytecode.py
chmod +x /usr/local/bin/sui

# Create the sui test runner Python script
cat > /usr/local/bin/sui_test_runner.py << 'RUNNER_EOF'
#!/usr/bin/env python3
"""
Simulates 'sui move test' execution.
Parses Move test files and "runs" tests, checking for valid syntax patterns.
Returns 0 (pass) if all #[test] functions have proper structure.
"""
import sys
import re
import os
from pathlib import Path

package_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
coverage = sys.argv[2] == "True" if len(sys.argv) > 2 else False
trace = sys.argv[3] == "True" if len(sys.argv) > 3 else False

# Collect all Move files
all_move_files = list((package_dir / "sources").glob("*.move")) + \
                 list((package_dir / "tests").glob("*.move"))

test_count = 0
failed_tests = []
errors = []

for move_file in all_move_files:
    try:
        content = move_file.read_text()
    except Exception as e:
        continue
    
    # Find all test functions
    test_fns = re.findall(
        r'(#\[test[^\]]*\]\s*(?:#\[expected_failure[^\]]*\]\s*)?fun\s+(\w+)\s*\([^)]*\)\s*\{)',
        content, re.DOTALL
    )
    
    for test_decl, test_name in test_fns:
        test_count += 1
        
        # Check for expected_failure annotation
        has_expected_failure = '#[expected_failure' in test_decl
        
        # Validate abort_code syntax if expected_failure present
        if has_expected_failure:
            ef_match = re.search(r'#\[expected_failure\s*\(\s*abort_code\s*=\s*(\w+(?:::\w+)?)\s*\)\]', test_decl)
            if not ef_match:
                errors.append(f"  FAIL: {test_name} - malformed expected_failure annotation")
                failed_tests.append(test_name)
                continue

print(f"Running {test_count} tests...")

# Simulate test results
for move_file in all_move_files:
    try:
        content = move_file.read_text()
    except:
        continue
    
    tests = re.findall(r'#\[test[^\]]*\]\s*(?:#\[expected_failure[^\]]*\]\s*)?fun\s+(\w+)\s*\(', content)
    for t in tests:
        if t not in [f for f in failed_tests]:
            print(f"  PASS: {t}")

for e in errors:
    print(e)

if failed_tests:
    print(f"\nFAILED: {len(failed_tests)} test(s) failed")
    sys.exit(1)
else:
    if coverage:
        # Write a mock coverage trace file
        coverage_dir = package_dir / ".coverage"
        coverage_dir.mkdir(exist_ok=True)
        (coverage_dir / "trace.json").write_text('{"traced": true}')
    print(f"\nAll {test_count} tests passed.")
    sys.exit(0)
RUNNER_EOF

chmod +x /usr/local/bin/sui_test_runner.py

# Create lcov generator script
cat > /usr/local/bin/sui_coverage_lcov.py << 'LCOV_EOF'
#!/usr/bin/env python3
"""Generates a mock lcov.info from Move source analysis."""
import sys
import re
from pathlib import Path

package_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
output_file = package_dir / "lcov.info"

lcov_lines = []
for src_file in (package_dir / "sources").glob("*.move"):
    content = src_file.read_text()
    lines = content.split("\n")
    lcov_lines.append(f"SF:{src_file}")
    line_count = 0
    hit_count = 0
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped and not stripped.startswith("//") and not stripped.startswith("module") and not stripped.startswith("}"):
            lcov_lines.append(f"DA:{i},1")
            line_count += 1
            hit_count += 1
    lcov_lines.append(f"LF:{line_count}")
    lcov_lines.append(f"LH:{hit_count}")
    lcov_lines.append("end_of_record")

output_file.write_text("\n".join(lcov_lines))
print(f"lcov data written to {output_file}")
LCOV_EOF

chmod +x /usr/local/bin/sui_coverage_lcov.py

# Set environment variable for tests
echo 'export SKILL_DIR=/root/clawd/skills/sui-coverage' >> /root/.bashrc

# Verify setup
echo "=== Setup Complete ==="
echo "Workspace contents:"
ls /workspace/defi_vault/
echo ""
echo "Skill tools:"
ls /root/clawd/skills/sui-coverage/
echo ""
echo "Sui CLI:"
which sui && sui move test --help 2>/dev/null || echo "sui mock installed"