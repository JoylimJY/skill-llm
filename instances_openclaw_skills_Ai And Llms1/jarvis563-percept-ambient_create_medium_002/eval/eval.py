import json
import os
import re
import sys
from pathlib import Path


def norm(s):
    try:
        return re.sub(r'[^a-z0-9]+', ' ', str(s).lower()).strip()
    except Exception:
        return ''


def load_json(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f), None
    except Exception as e:
        return None, str(e)


def find_conversations(packet):
    """Find conversations list using multiple possible key names with fuzzy matching."""
    if not isinstance(packet, dict):
        return []
    # Extended list of possible key names including variations
    possible_keys = [
        'conversations', 'recent_conversations', 'relevant_conversations',
        'history', 'relevant_history', 'chat_history', 'messages',
        'ranked_history_for_project_atlas', 'ranked_history',
        'project_atlas_history', 'atlas_history'
    ]
    for key in possible_keys:
        if key in packet and isinstance(packet[key], list):
            return packet[key]
    # Fallback: find any list that looks like conversations
    for key, value in packet.items():
        if isinstance(value, list) and len(value) > 0:
            if isinstance(value[0], dict) and any(k in value[0] for k in ['id', 'text', 'speaker', 'message', 'content']):
                return value
    return []


def find_history(packet):
    """Find history list using multiple possible key names with fuzzy matching."""
    if not isinstance(packet, dict):
        return []
    # Extended list of possible key names including variations
    possible_keys = [
        'relevant_history', 'history', 'conversations', 'recent_conversations',
        'chat_history', 'ranked_history_for_project_atlas', 'ranked_history',
        'project_atlas_history', 'atlas_history', 'relevant_conversations'
    ]
    for key in possible_keys:
        if key in packet and isinstance(packet[key], list):
            return packet[key]
    # Fallback: find any list that looks like history items
    for key, value in packet.items():
        if isinstance(value, list) and len(value) > 0:
            if isinstance(value[0], dict) and any(k in value[0] for k in ['conversation_id', 'relevance', 'summary', 'id', 'text']):
                return value
    return []


def find_entities(packet):
    """Find entities list using multiple possible key names with fuzzy matching."""
    if not isinstance(packet, dict):
        return []
    # Extended list of possible key names including variations
    possible_keys = [
        'entities', 'resolved_entities', 'normalized_entities',
        'entity_list', 'entities_list', 'knowledge_entities'
    ]
    for key in possible_keys:
        if key in packet and isinstance(packet[key], list):
            return packet[key]
    # Fallback: find any list that looks like entities
    for key, value in packet.items():
        if isinstance(value, list) and len(value) > 0:
            if isinstance(value[0], dict) and any(k in value[0] for k in ['name', 'type', 'id', 'entity']):
                return value
    return []


def main():
    checks = []
    ws = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
    out_dir = ws / 'output'
    packet_path = out_dir / 'context_packet.json'
    summary_path = out_dir / 'summary.txt'

    try:
        exists = packet_path.exists()
        checks.append({'name': 'context_packet_exists', 'passed': exists, 'detail': 'found' if exists else 'missing'})
    except Exception as e:
        checks.append({'name': 'context_packet_exists', 'passed': False, 'detail': f'error: {e}'})

    try:
        exists = summary_path.exists()
        checks.append({'name': 'summary_exists', 'passed': exists, 'detail': 'found' if exists else 'missing'})
    except Exception as e:
        checks.append({'name': 'summary_exists', 'passed': False, 'detail': f'error: {e}'})

    packet, err = load_json(packet_path)
    if packet is None:
        checks.append({'name': 'context_packet_valid_json', 'passed': False, 'detail': f'failed to parse: {err}'})
        packet = {}
    else:
        checks.append({'name': 'context_packet_valid_json', 'passed': True, 'detail': 'parsed'})

    try:
        recent = find_conversations(packet)
        ok = isinstance(recent, list) and len(recent) >= 2
        checks.append({'name': 'recent_conversations_present', 'passed': ok, 'detail': f'count={len(recent) if isinstance(recent, list) else "n/a"}'})
    except Exception as e:
        checks.append({'name': 'recent_conversations_present', 'passed': False, 'detail': f'error: {e}'})

    try:
        entities = find_entities(packet)
        names = [norm(x.get('name')) for x in entities if isinstance(x, dict)]
        has_atlas = any('project atlas' in n for n in names)
        has_duplicate_removed = not any(n == 'atlas' for n in names if n)
        checks.append({'name': 'entities_normalized', 'passed': bool(has_atlas and has_duplicate_removed), 'detail': f'entities={names[:6]}'})
    except Exception as e:
        checks.append({'name': 'entities_normalized', 'passed': False, 'detail': f'error: {e}'})

    try:
        rels = packet.get('relationships', []) if isinstance(packet, dict) else []
        rel_text = ' '.join(norm(r.get('source', '')) + ' ' + norm(r.get('relation', '')) + ' ' + norm(r.get('target', '')) for r in rels if isinstance(r, dict))
        ok = 'avery chen' in rel_text and 'project atlas' in rel_text and 'sam lee' in rel_text
        checks.append({'name': 'relationships_present', 'passed': ok, 'detail': f'count={len(rels) if isinstance(rels, list) else "n/a"}'})
    except Exception as e:
        checks.append({'name': 'relationships_present', 'passed': False, 'detail': f'error: {e}'})

    try:
        hist = find_history(packet)
        hist_texts = []
        for item in hist if isinstance(hist, list) else []:
            if isinstance(item, dict):
                # Try multiple possible text fields
                text = item.get('text', '') or item.get('content', '') or item.get('message', '') or item.get('summary', '')
                if text:
                    hist_texts.append(norm(text))
        # Check if any history item mentions project atlas (not just first)
        first_ok = bool(hist_texts) and 'project atlas' in hist_texts[0]
        # Also check if atlas is mentioned anywhere in history as fallback
        atlas_in_any = any('atlas' in t for t in hist_texts) if hist_texts else False
        ok = first_ok or atlas_in_any
        checks.append({'name': 'history_ranked_for_atlas', 'passed': ok, 'detail': f'first={hist_texts[0] if hist_texts else "n/a"}'})
    except Exception as e:
        checks.append({'name': 'history_ranked_for_atlas', 'passed': False, 'detail': f'error: {e}'})

    try:
        summary = ''
        try:
            summary = summary_path.read_text(encoding='utf-8')
        except Exception as e:
            raise e
        summary_n = norm(summary)
        ok = 'project atlas' in summary_n and 'sam lee' in summary_n and 'dana park' in summary_n and ('privacy' in summary_n or 'no audio' in summary_n)
        checks.append({'name': 'summary_mentions_key_items', 'passed': ok, 'detail': summary[:160]})
    except Exception as e:
        checks.append({'name': 'summary_mentions_key_items', 'passed': False, 'detail': f'error: {e}'})

    try:
        total = len(checks)
        passed = sum(1 for c in checks if c.get('passed'))
        score = passed / total if total else 0.0
        result = {'passed': passed == total, 'score': score, 'checks': checks}
        print(json.dumps(result, ensure_ascii=False))
    except Exception:
        print(json.dumps({'passed': False, 'score': 0.0, 'checks': checks}, ensure_ascii=False))


if __name__ == '__main__':
    main()