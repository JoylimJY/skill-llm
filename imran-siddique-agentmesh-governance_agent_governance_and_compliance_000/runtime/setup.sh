#!/usr/bin/env bash
set -euo pipefail

# ─────────────────────────────────────────────────────────────────────────────
# Mock the AgentMesh governance scripts so they produce deterministic,
# spec-compliant JSON outputs matching the SKILL.md documentation.
# The agent must invoke these scripts with the correct flags.
# ─────────────────────────────────────────────────────────────────────────────

mkdir -p /workspace/scripts

# ── State directory (simulates persistent engine state) ───────────────────────
mkdir -p /workspace/.agentmesh_state
echo '{}' > /workspace/.agentmesh_state/trust_scores.json
echo '[]' > /workspace/.agentmesh_state/audit_chain.json
echo '{}' > /workspace/.agentmesh_state/identities.json

# ── scripts/generate-identity.sh ─────────────────────────────────────────────
cat > /workspace/scripts/generate-identity.sh << 'SCRIPT'
#!/usr/bin/env bash
set -euo pipefail

NAME=""
CAPABILITIES=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --name) NAME="$2"; shift 2 ;;
    --capabilities) CAPABILITIES="$2"; shift 2 ;;
    *) echo "Unknown arg: $1" >&2; exit 1 ;;
  esac
done

if [[ -z "$NAME" || -z "$CAPABILITIES" ]]; then
  echo '{"error":"--name and --capabilities are required"}' >&2
  exit 1
fi

# Deterministic DID based on name
HASH=$(echo -n "$NAME" | sha256sum | cut -c1-16)
DID="did:agentmesh:${HASH}"
PUBKEY="Ed25519PubKey_$(echo -n "${NAME}_pub" | base64 | tr -d '=')"

# Save identity
python3 -c "
import json, sys

state_file = '/workspace/.agentmesh_state/identities.json'
with open(state_file) as f:
    state = json.load(f)

caps = '${CAPABILITIES}'.split(',')
state['${NAME}'] = {
    'did': '${DID}',
    'public_key': '${PUBKEY}',
    'capabilities': caps
}

with open(state_file, 'w') as f:
    json.dump(state, f)

# Append to audit chain
import hashlib, time
audit_file = '/workspace/.agentmesh_state/audit_chain.json'
with open(audit_file) as f:
    chain = json.load(f)

prev_hash = chain[-1]['hash'] if chain else '0'*64
entry = {
    'index': len(chain),
    'event': 'generate_identity',
    'agent': '${NAME}',
    'did': '${DID}',
    'timestamp': '2024-07-01T10:00:00Z',
    'prev_hash': prev_hash
}
entry_str = json.dumps(entry, sort_keys=True)
entry['hash'] = hashlib.sha256((prev_hash + entry_str).encode()).hexdigest()
chain.append(entry)

with open(audit_file, 'w') as f:
    json.dump(chain, f)
"

cat << JSON
{
  "did": "${DID}",
  "name": "${NAME}",
  "public_key": "${PUBKEY}",
  "capabilities": [$(echo "$CAPABILITIES" | sed 's/,/","/g' | sed 's/^/"/;s/$/"/')],
  "capability_manifest": {
    "version": "1.0",
    "issued_at": "2024-07-01T10:00:00Z",
    "tools_authorized": [$(echo "$CAPABILITIES" | sed 's/,/","/g' | sed 's/^/"/;s/$/"/')],
    "governance": "agentmesh-v1"
  }
}
JSON
SCRIPT

# ── scripts/check-policy.sh ───────────────────────────────────────────────────
cat > /workspace/scripts/check-policy.sh << 'SCRIPT'
#!/usr/bin/env bash
set -euo pipefail

ACTION=""
TOKENS=""
POLICY_FILE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --action) ACTION="$2"; shift 2 ;;
    --tokens) TOKENS="$2"; shift 2 ;;
    --policy) POLICY_FILE="$2"; shift 2 ;;
    *) echo "Unknown arg: $1" >&2; exit 1 ;;
  esac
done

if [[ -z "$ACTION" || -z "$TOKENS" || -z "$POLICY_FILE" ]]; then
  echo '{"error":"--action, --tokens, and --policy are required"}' >&2
  exit 1
fi

if [[ ! -f "$POLICY_FILE" ]]; then
  echo "{\"error\":\"Policy file not found: ${POLICY_FILE}\"}" >&2
  exit 1
fi

python3 << PYEOF
import json, yaml, hashlib, sys

with open('${POLICY_FILE}') as f:
    policy = yaml.safe_load(f)

action = '${ACTION}'
tokens = int('${TOKENS}')

violations = []
recommendations = []

max_tokens = policy.get('max_tokens', 4096)
allowed_tools = policy.get('allowed_tools', [])
blocked_tools = policy.get('blocked_tools', [])

if tokens > max_tokens:
    violations.append(f'Token limit exceeded: {tokens} > {max_tokens}')
    recommendations.append(f'Reduce token usage to below {max_tokens}')

if blocked_tools and action in blocked_tools:
    violations.append(f'Tool blocked by policy: {action}')
    recommendations.append(f'Use an alternative tool from the allowlist')

if allowed_tools and action not in allowed_tools and action not in blocked_tools:
    violations.append(f'Tool not in allowlist: {action}')
    recommendations.append(f'Add {action} to allowed_tools or use a permitted tool')

allowed = len(violations) == 0

# Append to audit chain
import time
audit_file = '/workspace/.agentmesh_state/audit_chain.json'
with open(audit_file) as f:
    chain = json.load(f)

prev_hash = chain[-1]['hash'] if chain else '0'*64
entry = {
    'index': len(chain),
    'event': 'check_policy',
    'agent': 'quant-analyst-agent',
    'action': action,
    'tokens': tokens,
    'allowed': allowed,
    'violations': violations,
    'timestamp': f'2024-07-01T10:{10+len(chain):02d}:00Z',
    'prev_hash': prev_hash
}
entry_str = json.dumps(entry, sort_keys=True)
entry['hash'] = hashlib.sha256((prev_hash + entry_str).encode()).hexdigest()
chain.append(entry)
with open(audit_file, 'w') as f:
    json.dump(chain, f)

result = {
    'action': action,
    'tokens': tokens,
    'allowed': allowed,
    'policy': policy.get('name', 'unknown'),
    'violations': violations,
    'recommendations': recommendations
}
print(json.dumps(result, indent=2))
PYEOF
SCRIPT

# ── scripts/trust-score.sh ────────────────────────────────────────────────────
cat > /workspace/scripts/trust-score.sh << 'SCRIPT'
#!/usr/bin/env bash
set -euo pipefail

AGENT=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --agent) AGENT="$2"; shift 2 ;;
    *) echo "Unknown arg: $1" >&2; exit 1 ;;
  esac
done

if [[ -z "$AGENT" ]]; then
  echo '{"error":"--agent is required"}' >&2
  exit 1
fi

python3 << PYEOF
import json

state_file = '/workspace/.agentmesh_state/trust_scores.json'
with open(state_file) as f:
    scores = json.load(f)

agent = '${AGENT}'
score_data = scores.get(agent, {
    'composite': 0.70,
    'dimensions': {
        'policy_compliance': 0.70,
        'resource_efficiency': 0.70,
        'output_quality': 0.70,
        'security_posture': 0.70,
        'collaboration_health': 0.70
    },
    'interaction_count': 0
})

composite = score_data['composite']
blocked = composite < 0.5

result = {
    'agent': agent,
    'composite_trust_score': round(composite, 4),
    'dimensions': score_data['dimensions'],
    'interaction_count': score_data['interaction_count'],
    'status': 'blocked' if blocked else 'active',
    'delegation_allowed': not blocked,
    'minimum_threshold': 0.5
}
print(json.dumps(result, indent=2))
PYEOF
SCRIPT

# ── scripts/record-interaction.sh ────────────────────────────────────────────
cat > /workspace/scripts/record-interaction.sh << 'SCRIPT'
#!/usr/bin/env bash
set -euo pipefail

AGENT=""
OUTCOME=""
SEVERITY="0.0"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --agent) AGENT="$2"; shift 2 ;;
    --outcome) OUTCOME="$2"; shift 2 ;;
    --severity) SEVERITY="$2"; shift 2 ;;
    *) echo "Unknown arg: $1" >&2; exit 1 ;;
  esac
done

if [[ -z "$AGENT" || -z "$OUTCOME" ]]; then
  echo '{"error":"--agent and --outcome are required"}' >&2
  exit 1
fi

python3 << PYEOF
import json, hashlib

state_file = '/workspace/.agentmesh_state/trust_scores.json'
with open(state_file) as f:
    scores = json.load(f)

agent = '${AGENT}'
outcome = '${OUTCOME}'
severity = float('${SEVERITY}')

# Initialize if needed
if agent not in scores:
    scores[agent] = {
        'composite': 0.70,
        'dimensions': {
            'policy_compliance': 0.70,
            'resource_efficiency': 0.70,
            'output_quality': 0.70,
            'security_posture': 0.70,
            'collaboration_health': 0.70
        },
        'interaction_count': 0
    }

old_score = scores[agent]['composite']

if outcome == 'success':
    delta = 0.01
elif outcome == 'failure':
    delta = -severity
else:
    print(json.dumps({'error': f'Unknown outcome: {outcome}'}))
    exit(1)

new_score = round(old_score + delta, 6)
scores[agent]['composite'] = new_score
scores[agent]['dimensions']['collaboration_health'] = round(
    scores[agent]['dimensions']['collaboration_health'] + delta, 6
)
scores[agent]['interaction_count'] += 1

blocked = new_score < 0.5

with open(state_file, 'w') as f:
    json.dump(scores, f)

# Append to audit chain
audit_file = '/workspace/.agentmesh_state/audit_chain.json'
with open(audit_file) as f:
    chain = json.load(f)

prev_hash = chain[-1]['hash'] if chain else '0'*64
entry = {
    'index': len(chain),
    'event': 'record_interaction',
    'agent': agent,
    'outcome': outcome,
    'severity': severity,
    'score_before': old_score,
    'score_after': new_score,
    'timestamp': f'2024-07-01T11:{len(chain):02d}:00Z',
    'prev_hash': prev_hash
}
entry_str = json.dumps(entry, sort_keys=True)
entry['hash'] = hashlib.sha256((prev_hash + entry_str).encode()).hexdigest()
chain.append(entry)
with open(audit_file, 'w') as f:
    json.dump(chain, f)

result = {
    'agent': agent,
    'outcome': outcome,
    'score_before': old_score,
    'score_after': new_score,
    'delta': delta,
    'status': 'blocked' if blocked else 'active',
    'blocked': blocked
}
print(json.dumps(result, indent=2))
PYEOF
SCRIPT

# ── scripts/audit-log.sh ──────────────────────────────────────────────────────
cat > /workspace/scripts/audit-log.sh << 'SCRIPT'
#!/usr/bin/env bash
set -euo pipefail

LAST=""
AGENT_FILTER=""
VERIFY=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --last) LAST="$2"; shift 2 ;;
    --agent) AGENT_FILTER="$2"; shift 2 ;;
    --verify) VERIFY=true; shift ;;
    *) echo "Unknown arg: $1" >&2; exit 1 ;;
  esac
done

python3 << PYEOF
import json, hashlib

audit_file = '/workspace/.agentmesh_state/audit_chain.json'
with open(audit_file) as f:
    chain = json.load(f)

last = '${LAST}'
agent_filter = '${AGENT_FILTER}'
verify = '${VERIFY}' == 'true'

entries = chain
if agent_filter:
    entries = [e for e in entries if e.get('agent') == agent_filter]
if last:
    entries = entries[-int(last):]

integrity_valid = True
if verify:
    for i, entry in enumerate(chain):
        if i == 0:
            prev_h = '0'*64
        else:
            prev_h = chain[i-1]['hash']
        stored_hash = entry.get('hash', '')
        entry_copy = {k: v for k, v in entry.items() if k != 'hash'}
        entry_str = json.dumps(entry_copy, sort_keys=True)
        computed = hashlib.sha256((prev_h + entry_str).encode()).hexdigest()
        if computed != stored_hash:
            integrity_valid = False
            break

result = {
    'entries': entries,
    'total_in_chain': len(chain),
    'returned': len(entries)
}
if verify:
    result['integrity_verified'] = integrity_valid
    result['merkle_chain_valid'] = integrity_valid

print(json.dumps(result, indent=2))
PYEOF
SCRIPT

# ── scripts/verify-identity.sh ────────────────────────────────────────────────
cat > /workspace/scripts/verify-identity.sh << 'SCRIPT'
#!/usr/bin/env bash
set -euo pipefail

DID=""
MESSAGE=""
SIGNATURE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --did) DID="$2"; shift 2 ;;
    --message) MESSAGE="$2"; shift 2 ;;
    --signature) SIGNATURE="$2"; shift 2 ;;
    *) echo "Unknown arg: $1" >&2; exit 1 ;;
  esac
done

python3 << PYEOF
import json

state_file = '/workspace/.agentmesh_state/identities.json'
with open(state_file) as f:
    identities = json.load(f)

did = '${DID}'
found = any(v.get('did') == did for v in identities.values())

print(json.dumps({
    'did': did,
    'verified': found,
    'message': '${MESSAGE}',
    'signature_valid': found,
    'identity_registered': found
}))
PYEOF
SCRIPT

# Make all scripts executable
chmod +x /workspace/scripts/*.sh

echo "AgentMesh mock scripts installed and ready."
ls -la /workspace/scripts/