import sys
import os
import json
import re


def find_all_text_files(path):
    candidates = []
    for root, _, files in os.walk(path):
        for fname in files:
            if fname.lower().endswith('.txt'):
                candidates.append(os.path.join(root, fname))
    return candidates


def normalize_text(text):
    # Normalize whitespace and case
    return re.sub(r'\s+', ' ', text.strip()).lower()


def contains_any(text, keywords):
    text_lower = text.lower()
    return any(kw.lower() in text_lower for kw in keywords)


def check_question_presence(text):
    # Check for presence of a question mark or common interrogative words
    if '?' in text:
        return True
    keywords = ['what', 'why', 'how', 'when', 'who', 'which', 'where', 'do you', 'your']
    return any(kw in text.lower() for kw in keywords)


def evaluate_optimized_tweet(text):
    # Run all checks and return dict of booleans with details
    results = {}

    # Check 1: Addresses a developer community (SimClusters)
    # Look for keywords strongly associated with software dev community
    dev_keywords = ['debugging', 'bug', 'semicolon', 'linter', 'code', 'programmer', 'developer', 'stack overflow', 'github', 'python', 'java', 'rust', 'js', 'javascript']
    results['simcluster_targeting'] = contains_any(text, dev_keywords)

    # Check 2: Contains a direct question inviting replies (Real-graph)
    results['direct_question'] = check_question_presence(text)

    # Check 3: Establishes authority or relatability (Tweepcred)
    # Look for words like 'spent', 'relatable', 'shared', 'best', 'my', or indicating experience
    authority_keywords = ['spent', 'relate', 'relatable', 'my', 'we', 'experience', 'relates', 'story']
    results['authority_relatability'] = contains_any(text, authority_keywords)

    # Check 4: Avoids vague or generic statements
    # Look for signs that tweet is specific and not just "I fixed a bug today"
    vague_phrases = ['i fixed a bug today', 'just did something', 'generic', 'test', 'something']
    results['no_vague_generic'] = not contains_any(text, vague_phrases)

    # Check 5: The tweet is actionable or sparks discussion
    # Presence of verbs that invite action or discussion
    actionable_keywords = ['drop', 'share', 'reply', 'tell', 'thoughts', 'opinions', 'how', 'why', 'what']
    results['actionable_discussion'] = contains_any(text, actionable_keywords)

    return results


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "input_argument", "passed": False, "detail": "Expected workspace directory path argument."}]}))
        return

    workspace = sys.argv[1]
    text_files = find_all_text_files(workspace)

    if not text_files:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "file_presence", "passed": False, "detail": "No .txt output files found to evaluate."}]}))
        return

    # Evaluate all candidate files, keep best scoring one
    best_score = 0.0
    best_details = None

    for fpath in text_files:
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            continue

        normalized = normalize_text(content)
        results = evaluate_optimized_tweet(normalized)

        passed_checks = [v for v in results.values() if v]
        score = len(passed_checks) / len(results)

        if score > best_score:
            best_score = score
            best_details = results

    # Determine overall pass if score >= 0.8 (all or all but 1 check)
    passed = best_score >= 0.8

    # Format detailed checks
    checks_formatted = []
    if best_details is not None:
        for k, v in best_details.items():
            name = {
                'simcluster_targeting': 'SimCluster developer community targeting',
                'direct_question': 'Contains direct question for replies',
                'authority_relatability': 'Establishes authority or relatability',
                'no_vague_generic': 'Avoids vague/generic statements',
                'actionable_discussion': 'Actionable or sparks discussion'
            }.get(k, k)
            detail = 'Passed' if v else 'Failed'
            checks_formatted.append({'name': name, 'passed': v, 'detail': detail})
    else:
        checks_formatted.append({'name': 'Evaluation', 'passed': False, 'detail': 'No valid content found.'})

    score_val = best_score if best_details is not None else 0.0

    result = {
        "passed": passed,
        "score": score_val,
        "checks": checks_formatted
    }

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
