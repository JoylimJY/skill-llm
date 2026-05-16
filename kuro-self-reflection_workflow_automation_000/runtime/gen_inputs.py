import os
import random

random.seed(42)

# Create deeply nested workspace structure
dirs = [
    "workspace/projects/sprint_42",
    "workspace/projects/sprint_42/src",
    "workspace/projects/sprint_42/tests",
    "workspace/projects/sprint_43",
    "workspace/docs/team",
    "workspace/docs/archive",
    "workspace/logs/2024-Q1",
    "workspace/logs/2024-Q2",
    "workspace/meetings/standups",
    "workspace/meetings/retros",
    "workspace/personal/notes",
    "workspace/personal/goals",
    "workspace/tools/scripts",
    "workspace/tools/configs",
]
for d in dirs:
    os.makedirs(d, exist_ok=True)

# Distractor files - realistic but irrelevant
files = {
    "workspace/projects/sprint_42/src/auth_service.py": """
# Authentication Service
def authenticate(user, password):
    # TODO: implement proper hashing
    return user == "admin" and password == "pass"
""",
    "workspace/projects/sprint_42/src/payment_processor.py": """
# Payment Processor - v1.2
import time

def process_payment(amount, card_number):
    time.sleep(0.1)  # Simulate API call
    if amount > 10000:
        raise ValueError("Amount exceeds limit")
    return {"status": "success", "transaction_id": "TXN_001"}
""",
    "workspace/projects/sprint_42/tests/test_auth.py": """
import pytest
def test_authenticate():
    # Only happy path tested
    assert authenticate("admin", "pass") == True
""",
    "workspace/projects/sprint_42/tests/test_payment.py": """
def test_payment_basic():
    result = process_payment(100, "4111111111111111")
    assert result["status"] == "success"
# Missing: edge cases, failure scenarios
""",
    "workspace/projects/sprint_42/sprint_notes.txt": """Sprint 42 Notes
Duration: 2024-01-08 to 2024-01-19
Team: Alice (Backend), Bob (Frontend), Carol (QA)
Goal: Payment module launch

Status: SHIPPED - but production issues found
- 3 critical bugs reported by users post-launch
- Payment timeout not handled
- Refund flow broken for amounts > 1000
- Auth token expiry causes silent failures
""",
    "workspace/logs/2024-Q1/production_errors.log": """2024-01-20 08:12:33 ERROR PaymentTimeout: Request timed out after 30s for user_id=1042
2024-01-20 09:45:11 ERROR RefundFailed: amount=1500, reason=validation_error
2024-01-20 11:02:58 ERROR AuthExpiry: token_expired, user silently logged out
2024-01-21 14:33:20 ERROR PaymentTimeout: Request timed out after 30s for user_id=2087
2024-01-22 09:10:05 ERROR RefundFailed: amount=2200, reason=validation_error
""",
    "workspace/logs/2024-Q1/deployment_log.txt": """2024-01-19 17:45:00 DEPLOY sprint_42 v1.0.0 -> production
2024-01-19 17:46:12 HEALTH_CHECK PASS
2024-01-19 17:47:00 SMOKE_TEST PASS (3/3 tests)
Deployed by: Carol
Approved by: Manager
""",
    "workspace/meetings/standups/2024-01-18.md": """# Standup 2024-01-18

## Alice
- Yesterday: Finished payment integration
- Today: Code review with Bob
- Blockers: None

## Bob
- Yesterday: Frontend payment form
- Today: Testing
- Blockers: None

## Carol
- Yesterday: Writing test cases
- Today: Final QA sign-off
- Blockers: Running out of time, only core paths tested
""",
    "workspace/meetings/retros/sprint_41_retro.md": """# Sprint 41 Retrospective (Quick Notes)

What went well: Feature delivered on time
What didn't: Some edge cases missed in testing
Action: Will improve test coverage next sprint

[No formal action items tracked]
""",
    "workspace/docs/team/coding_standards.md": """# Team Coding Standards v1.1

- Use type hints
- Write unit tests for all public methods  
- Code review required before merge
- Maximum function length: 50 lines
""",
    "workspace/docs/team/deployment_checklist.md": """# Deployment Checklist (DRAFT)
- [ ] All tests pass
- [ ] Code reviewed
- [ ] Staging tested
""",
    "workspace/docs/archive/sprint_40_summary.txt": "Sprint 40 completed. Minor bugs. No formal retrospective.",
    "workspace/personal/notes/random_thoughts.txt": "Need to improve testing practices. Keep forgetting edge cases.",
    "workspace/personal/goals/2024_goals.txt": "1. Improve code quality\n2. Better work-life balance\n3. Learn Kubernetes",
    "workspace/tools/configs/pytest.ini": "[pytest]\ntestpaths = tests\naddopts = -v",
    "workspace/tools/scripts/run_tests.sh": "#!/bin/bash\npython -m pytest tests/ -v",
    "workspace/projects/sprint_43/planning.md": "# Sprint 43 Planning\nFocus: Bug fixes from sprint 42\nTeam capacity: Reduced (Carol on leave)",
}

for path, content in files.items():
    with open(path, "w") as f:
        f.write(content.strip())

# Create the scenario brief that triggers the reflection
scenario = """SPRINT 42 POST-MORTEM REQUEST
==============================
From: Engineering Manager
To: Tech Lead (Alice)
Date: 2024-01-23

Alice,

Sprint 42 shipped last Friday but we have 3 critical production bugs:
1. Payment timeouts not handled - users losing money
2. Refund amounts > 1000 broken  
3. Auth token expiry silently fails

Users are angry. This is the second sprint in a row with post-launch bugs
(same pattern as Sprint 41).

I need you to:
1. Conduct a thorough deep retrospective analysis of what went wrong
2. Create a formal improvement plan with specific priorities
3. Create a checklist so this doesn't happen again

Evidence available:
- production_errors.log: 5 errors in first 3 days
- sprint_notes.txt: team context
- test files: what was actually tested
- Previous retro: sprint_41_retro.md (same issues, no real follow-through)

Please produce the deliverables in the workspace. This will be reviewed
in tomorrow's all-hands.

- Manager
"""

with open("workspace/SCENARIO_BRIEF.txt", "w") as f:
    f.write(scenario)

print("Workspace created successfully.")
print("Files created:")
for path in sorted(files.keys()):
    print(f"  {path}")