import json
import os
import sys
from pathlib import Path


def norm(s):
    try:
        return ''.join(ch.lower() for ch in str(s) if ch.isalnum())
    except Exception:
        return ''


def safe_read_text(path):
    try:
        return Path(path).read_text(encoding='utf-8', errors='ignore')
    except Exception as e:
        return None, str(e)


def get_value_with_fallback(data, *keys):
    """Try multiple possible key names and return the first match."""
    if not isinstance(data, dict):
        return None
    for key in keys:
        if key in data:
            return data[key]
    return None


def search_in_nested(obj, search_terms):
    """Recursively search for terms in nested structures."""
    if isinstance(obj, dict):
        for key, value in obj.items():
            if search_in_nested(value, search_terms):
                return True
    elif isinstance(obj, list):
        for item in obj:
            if search_in_nested(item, search_terms):
                return True
    elif isinstance(obj, str):
        obj_norm = norm(obj)
        for term in search_terms:
            if norm(term) in obj_norm:
                return True
    return False


def has_history_content(data):
    """Check if history content exists in any valid location."""
    # Check top-level history keys
    hist = get_value_with_fallback(data, 'relevant_history', 'history')
    if hist is not None:
        return True
    
    # Check top-level key_points
    key_points = get_value_with_fallback(data, 'key_points')
    if key_points:
        return True
    
    # Check summary.key_points
    summary = get_value_with_fallback(data, 'summary')
    if summary and isinstance(summary, dict):
        kp = summary.get('key_points', [])
        if kp:
            return True
    
    # Check if recent_conversations exist (they inherently contain conversation history)
    recent = get_value_with_fallback(data, 'recent_conversations', 'latest_conversations', 'conversations')
    if recent and isinstance(recent, list) and len(recent) > 0:
        return True
    
    return False


def main():
    checks = []
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')

    output_path = workspace / 'output.json'
    try:
        if output_path.exists():
            data = json.loads(output_path.read_text(encoding='utf-8', errors='ignore'))
            passed = isinstance(data, dict)
            checks.append({
                'name': 'output_exists_and_parses',
                'passed': passed,
                'detail': 'output.json parsed successfully' if passed else 'output.json is not a JSON object'
            })
        else:
            checks.append({
                'name': 'output_exists_and_parses',
                'passed': False,
                'detail': 'output.json is missing'
            })
            data = {}
    except Exception as e:
        checks.append({'name': 'output_exists_and_parses', 'passed': False, 'detail': f'failed to parse output.json: {e}'})
        data = {}

    try:
        # Accept multiple valid key names for each required section
        conversations_key = get_value_with_fallback(data, 'recent_conversations', 'latest_conversations', 'conversations')
        entities_key = get_value_with_fallback(data, 'resolved_entities', 'entities')
        relationships_key = get_value_with_fallback(data, 'relationships')
        
        # History can be in multiple locations (more flexible check)
        has_history = has_history_content(data)
        
        has_conversations = conversations_key is not None
        has_entities = entities_key is not None
        has_relationships = relationships_key is not None
        
        passed = has_conversations and has_entities and has_relationships and has_history
        missing = []
        if not has_conversations:
            missing.append('recent_conversations (or latest_conversations/conversations)')
        if not has_entities:
            missing.append('resolved_entities (or entities)')
        if not has_relationships:
            missing.append('relationships')
        if not has_history:
            missing.append('relevant_history (or history/key_points/recent_conversations)')
        
        checks.append({
            'name': 'required_top_level_keys',
            'passed': passed,
            'detail': 'all required keys present' if passed else f'missing keys: {missing}'
        })
    except Exception as e:
        checks.append({'name': 'required_top_level_keys', 'passed': False, 'detail': f'error checking keys: {e}'})

    try:
        recent = get_value_with_fallback(data, 'recent_conversations', 'latest_conversations', 'conversations')
        passed = isinstance(recent, list) and len(recent) >= 2
        checks.append({
            'name': 'recent_conversations_content',
            'passed': passed,
            'detail': f'found {len(recent) if isinstance(recent, list) else "non-list"} recent conversations'
        })
    except Exception as e:
        checks.append({'name': 'recent_conversations_content', 'passed': False, 'detail': f'error checking recent_conversations: {e}'})

    try:
        entities = get_value_with_fallback(data, 'resolved_entities', 'entities')
        entity_blob = ' '.join(json.dumps(entities, ensure_ascii=False) if isinstance(entities, (list, dict)) else [str(entities)])
        target_markers = ['orion', 'northstar', 'labs', 'avery', 'nina', 'marco']
        matched = sum(1 for m in target_markers if norm(m) in norm(entity_blob))
        passed = matched >= 4
        checks.append({
            'name': 'resolved_entities_markers',
            'passed': passed,
            'detail': f'matched {matched}/{len(target_markers)} entity markers'
        })
    except Exception as e:
        checks.append({'name': 'resolved_entities_markers', 'passed': False, 'detail': f'error checking entities: {e}'})

    try:
        rels = get_value_with_fallback(data, 'relationships')
        rel_blob = json.dumps(rels, ensure_ascii=False) if isinstance(rels, (list, dict)) else str(rels)
        rel_blob_norm = norm(rel_blob)
        # Normalize search terms to match the normalized blob
        passed = ('workson' in rel_blob_norm) or ('clientof' in rel_blob_norm) or ('works_on' in rel_blob)
        checks.append({
            'name': 'relationships_include_expected_types',
            'passed': passed,
            'detail': 'relationship types mention works_on/client_of' if passed else 'missing expected relationship types'
        })
    except Exception as e:
        checks.append({'name': 'relationships_include_expected_types', 'passed': False, 'detail': f'error checking relationships: {e}'})

    try:
        # Search for history content in multiple possible locations
        hist = get_value_with_fallback(data, 'relevant_history', 'history')
        history_terms = ['privacy', 'sqlite', 'lancedb', 'storage', 'local']
        
        passed = False
        if hist is not None:
            if isinstance(hist, list):
                passed = any(search_in_nested(x, history_terms) for x in hist)
            elif isinstance(hist, dict):
                passed = search_in_nested(hist, history_terms)
            elif isinstance(hist, str):
                passed = any(norm(term) in norm(hist) for term in history_terms)
        
        # Also check summary and key_points
        if not passed:
            summary = get_value_with_fallback(data, 'summary')
            if summary and isinstance(summary, dict):
                key_points = summary.get('key_points', [])
                if key_points:
                    passed = any(search_in_nested(kp, history_terms) for kp in key_points)
        
        # Also check top-level key_points
        if not passed:
            key_points = get_value_with_fallback(data, 'key_points')
            if key_points:
                passed = any(search_in_nested(kp, history_terms) for kp in key_points)
        
        # Also check recent_conversations text
        if not passed:
            recent = get_value_with_fallback(data, 'recent_conversations', 'latest_conversations', 'conversations')
            if recent and isinstance(recent, list):
                for conv in recent:
                    if isinstance(conv, dict) and 'text' in conv:
                        if search_in_nested(conv['text'], history_terms):
                            passed = True
                            break
        
        checks.append({
            'name': 'relevant_history_mentions_privacy_or_storage',
            'passed': passed,
            'detail': 'history mentions privacy or storage' if passed else 'no privacy/storage history found'
        })
    except Exception as e:
        checks.append({'name': 'relevant_history_mentions_privacy_or_storage', 'passed': False, 'detail': f'error checking relevant_history: {e}'})

    total = len(checks)
    passed_count = sum(1 for c in checks if c.get('passed'))
    score = passed_count / total if total else 0.0
    result = {'passed': passed_count == total, 'score': score, 'checks': checks}
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()