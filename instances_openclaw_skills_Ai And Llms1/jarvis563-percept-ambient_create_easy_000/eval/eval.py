import json
import os
import re
import sys
from pathlib import Path

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
checks = []

def add_check(name, passed, detail):
    checks.append({'name': name, 'passed': bool(passed), 'detail': detail})

try:
    out = workspace / 'context_packet.json'
    if not out.exists():
        add_check('output_exists', False, 'context_packet.json is missing')
    else:
        add_check('output_exists', True, 'context_packet.json found')
except Exception as e:
    add_check('output_exists', False, f'Error checking output file: {e}')

packet = None
try:
    if (workspace / 'context_packet.json').exists():
        packet = json.loads((workspace / 'context_packet.json').read_text(encoding='utf-8'))
        add_check('json_parse', True, 'context_packet.json parsed successfully')
    else:
        add_check('json_parse', False, 'Skipped because file is missing')
except Exception as e:
    add_check('json_parse', False, f'Could not parse JSON: {e}')

try:
    if isinstance(packet, dict):
        # Check for recent_conversations (accept conversation_history as alternative)
        has_recent = ('recent_conversations' in packet and isinstance(packet.get('recent_conversations'), list)) or \
                     ('conversation_history' in packet and isinstance(packet.get('conversation_history'), list))
        add_check('has_recent_conversations', has_recent, 'Present and list-typed' if has_recent else 'recent_conversations missing or not a list')
        
        # Check for resolved_entities (accept dict or list)
        has_entities = 'resolved_entities' in packet and isinstance(packet.get('resolved_entities'), (dict, list))
        add_check('has_resolved_entities', has_entities, 'Present and dict/list-typed' if has_entities else 'resolved_entities missing or not a dict/list')
        
        # Check for relationships (must be list)
        has_relationships = 'relationships' in packet and isinstance(packet.get('relationships'), list)
        add_check('has_relationships', has_relationships, 'Present and list-typed' if has_relationships else 'relationships missing or not a list')
        
        # Check for relevant_history (accept history or conversation_history as alternative)
        has_history = ('relevant_history' in packet and isinstance(packet.get('relevant_history'), list)) or \
                      ('history' in packet and isinstance(packet.get('history'), list)) or \
                      ('conversation_history' in packet and isinstance(packet.get('conversation_history'), list))
        add_check('has_relevant_history', has_history, 'Present and list-typed' if has_history else 'relevant_history missing or not a list')
    else:
        add_check('has_recent_conversations', False, 'Packet unavailable')
        add_check('has_resolved_entities', False, 'Packet unavailable')
        add_check('has_relationships', False, 'Packet unavailable')
        add_check('has_relevant_history', False, 'Packet unavailable')
except Exception as e:
    add_check('schema_check', False, f'Error inspecting schema: {e}')

try:
    text_blob = ''
    if isinstance(packet, dict):
        text_blob = json.dumps(packet, ensure_ascii=False).lower()
    marker_ok = 'orbit-17' in text_blob
    add_check('marker_present', marker_ok, 'Marker ORBIT-17 found' if marker_ok else 'Marker ORBIT-17 not found in output')
except Exception as e:
    add_check('marker_present', False, f'Error searching marker: {e}')

try:
    expected_entities = ['alice', 'bob', 'carol', 'project atlas', 'northwind labs']
    blob = json.dumps(packet, ensure_ascii=False).lower() if isinstance(packet, dict) else ''
    found = [ent for ent in expected_entities if re.search(re.escape(ent), blob, flags=re.I)]
    passed = len(found) >= 4
    add_check('entity_coverage', passed, f'Found entities: {found}' if found else 'No expected entities found')
except Exception as e:
    add_check('entity_coverage', False, f'Error checking entities: {e}')

try:
    passed_count = sum(1 for c in checks if c['passed'])
    total = len(checks) if checks else 1
    score = passed_count / total
    result = {'passed': passed_count == total, 'score': score, 'checks': checks}
    print(json.dumps(result, ensure_ascii=False))
except Exception:
    fallback = {'passed': False, 'score': 0.0, 'checks': checks}
    print(json.dumps(fallback, ensure_ascii=False))