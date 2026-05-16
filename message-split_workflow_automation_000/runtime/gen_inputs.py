import os
import json
import random

random.seed(42)

WORKSPACE = "/workspace"

# --- Create a realistic, deeply nested distractor structure ---
dirs = [
    "relay_bot/config",
    "relay_bot/handlers",
    "relay_bot/channels/feishu",
    "relay_bot/channels/telegram",
    "relay_bot/channels/signal",
    "relay_bot/channels/discord",
    "relay_bot/utils",
    "relay_bot/tests",
    "data/raw_tickets",
    "data/processed",
    "docs",
    "scripts",
]
for d in dirs:
    os.makedirs(os.path.join(WORKSPACE, d), exist_ok=True)

# Distractor files
distractor_files = {
    "relay_bot/config/settings.yaml": """\
bot_name: SupportRelayBot
default_channel: feishu
retry_attempts: 3
log_level: INFO
""",
    "relay_bot/config/channels.yaml": """\
feishu:
  max_chars: 4000
telegram:
  max_chars: 4096
discord:
  max_chars: 2000
signal:
  max_chars: 700
""",
    "relay_bot/handlers/ticket_handler.py": """\
# Handles incoming support tickets
class TicketHandler:
    def process(self, ticket):
        pass
""",
    "relay_bot/channels/feishu/sender.py": """\
# Feishu channel sender stub
def send(msg): pass
""",
    "relay_bot/channels/telegram/sender.py": """\
# Telegram channel sender stub
def send(msg): pass
""",
    "relay_bot/channels/signal/sender.py": """\
# Signal channel sender stub
def send(msg): pass
""",
    "relay_bot/channels/discord/sender.py": """\
# Discord channel sender stub
def send(msg): pass
""",
    "relay_bot/utils/formatter.py": """\
# Text formatting utilities (not for splitting)
def bold(text): return f'**{text}**'
def italic(text): return f'_{text}_'
""",
    "relay_bot/utils/logger.py": """\
import logging
logger = logging.getLogger('relay_bot')
""",
    "relay_bot/tests/test_handlers.py": """\
# Placeholder tests
def test_placeholder():
    assert True
""",
    "docs/architecture.md": """\
# Architecture

The relay bot receives AI-generated summaries and distributes them to configured channels.
Each channel has its own sender module.
""",
    "scripts/deploy.sh": """\
#!/bin/bash
echo 'Deploying relay bot...'
""",
}

for path, content in distractor_files.items():
    with open(os.path.join(WORKSPACE, path), "w") as f:
        f.write(content)

# --- THE PROBLEM: Create the raw input data the agent must process ---
# A long AI-generated support summary to be relayed to a Signal channel.
# This text is carefully crafted so that:
#   1. It far exceeds Signal's 700-char limit.
#   2. It contains sentence-ending punctuation (.!?) with whitespace after them,
#      so split_text() will try sentence-boundary splitting first.
#   3. One "sentence" is deliberately longer than 700 chars to trigger the
#      max_len - 100 (i.e., 600-char stride) sub-split path.

long_summary = (
    "Customer ticket #TK-9021 escalation summary for internal team review. "
    "The customer, Acme Corp, reported intermittent API failures starting on 2024-06-01 affecting their production pipeline. "
    "Our on-call engineer confirmed the root cause as a misconfigured rate-limiter in the EU-WEST-2 datacenter that was silently dropping requests above 150 req/s without returning proper 429 status codes. "
    "This caused their retry logic to exhaust all attempts without backoff, resulting in cascading timeouts across three downstream services including their billing module, reporting dashboard, and real-time inventory tracker. "
    "The following long technical note was appended by the senior engineer and must be relayed verbatim: TECHNICAL_DETAIL_START: The rate-limiter misconfiguration was introduced in deployment build #4471 on 2024-05-30 when an infrastructure-as-code template was merged that accidentally set the per-service token bucket refill rate to 0.02 tokens per millisecond instead of 0.20, a tenfold reduction caused by a missing leading zero in the YAML config file under the key `rate_limit.refill_rate_tpm`; this was not caught by the automated config validator because the validator schema only enforced a minimum value of 0.001 and a maximum of 1.0, both of which were satisfied by 0.02, and the integration test suite did not include a load test scenario above 100 req/s for EU-WEST-2 specifically, as that region was added to the test matrix only in Q3 2023 and the high-load scenarios had not been backfilled :TECHNICAL_DETAIL_END. "
    "Immediate remediation was applied at 14:32 UTC by rolling back the IaC template to build #4470 and triggering a forced config refresh on all 12 load-balancer nodes in the affected region. "
    "Customer impact window: 2024-06-01 06:15 UTC to 2024-06-01 14:35 UTC, approximately 8 hours 20 minutes. "
    "SLA breach confirmed! A P1 incident report has been filed under INC-20240601-EU2. "
    "Next steps: backfill high-load test scenarios for all non-primary regions, add schema validation rule for refill_rate_tpm minimum threshold of 0.1, and schedule post-mortem for 2024-06-05 with Acme Corp stakeholders. "
    "Please acknowledge receipt and confirm availability for the post-mortem call."
)

input_data = {
    "channel": "signal",
    "summary": long_summary
}

with open(os.path.join(WORKSPACE, "data/raw_tickets/escalation_TK9021.json"), "w") as f:
    json.dump(input_data, f, indent=2)

# Also write a plain text version for convenience
with open(os.path.join(WORKSPACE, "data/raw_tickets/escalation_TK9021.txt"), "w") as f:
    f.write(long_summary)

print(f"Input summary length: {len(long_summary)} chars")
print(f"Workspace prepared at {WORKSPACE}")