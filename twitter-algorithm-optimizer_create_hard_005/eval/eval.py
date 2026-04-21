import sys
import os
import json
import re

def read_json_file(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        return None

def contains_keyword(text, keywords):
    text_lower = text.lower()
    for kw in keywords:
        if kw.lower() in text_lower:
            return True
    return False

def score_tweet(original, optimized, explanation):
    checks = []

    # Check 1: Original tweet text matches one of the known inputs
    valid_originals = [
        "just fixed some bugs in my code.",
        "our new app feature is live everyone check it out",
        "remote work is better than office work."
    ]
    passed_original = any(orig.lower() == original.lower() for orig in valid_originals)
    checks.append({
        "name": "Original tweet correctness",
        "passed": passed_original,
        "detail": f"Original tweet recognized: {passed_original}"
    })

    # Check 2: Optimized tweet improves engagement triggers (ask questions, use keywords)
    # Check for direct Q mark or invitation to reply
    engagement_triggers = ["?", "drop your", "thoughts", "opinions", "curious", "what do you think", "reply", "share"]
    passed_engagement = contains_keyword(optimized, engagement_triggers)

    # Check for niche community terms or specific data for SimClusters & TwHIN
    community_triggers = ["bug", "linter", "pdf", "export", "hybrid", "async", "collaboration", "framework", "team"]
    passed_community = contains_keyword(optimized, community_triggers)

    # Check for Tweepcred signals: authority or expertise language
    authority_triggers = ["spent", "expert", "3rd", "feature", "credible", "months", "improvement"]
    passed_authority = contains_keyword(optimized, authority_triggers)

    # Check explanation mentions key algorithm terms
    algorithm_terms = ["real-graph", "simclusters", "twhin", "tweepcred", "engagement", "replies", "retweets", "likes"]
    passed_explanation_terms = contains_keyword(explanation, algorithm_terms)

    # Check explanation explains what was changed and why
    passed_explanation_detail = len(explanation.strip()) > 30

    checks.append({
        "name": "Engagement triggers in optimized tweet",
        "passed": passed_engagement,
        "detail": f"Contains engagement trigger phrase: {passed_engagement}"
    })
    checks.append({
        "name": "Community resonance in optimized tweet",
        "passed": passed_community,
        "detail": f"Mentions niche/community terms: {passed_community}"
    })
    checks.append({
        "name": "Authority signals in optimized tweet",
        "passed": passed_authority,
        "detail": f"Mentions authority/credibility signals: {passed_authority}"
    })
    checks.append({
        "name": "Algorithm insight references in explanation",
        "passed": passed_explanation_terms,
        "detail": f"Explanation references algorithmic terms: {passed_explanation_terms}"
    })
    checks.append({
        "name": "Explanation provides detailed rationale",
        "passed": passed_explanation_detail,
        "detail": f"Explanation length > 30 chars: {passed_explanation_detail}"
    })

    return checks

def find_best_result(tweets_data):
    total_checks = len(tweets_data) * 6  # 6 checks per tweet
    passed_checks = 0
    details = []

    for tweet in tweets_data:
        original = tweet.get('original', '')
        optimized = tweet.get('optimized', '')
        explanation = tweet.get('explanation', '')

        checks = score_tweet(original, optimized, explanation)
        passed_checks += sum(1 for c in checks if c['passed'])
        details.extend(checks)

    score = passed_checks / total_checks if total_checks else 0.0
    passed = score >= 0.8

    return {
        "passed": passed,
        "score": score,
        "checks": details
    }

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "Argument count", "passed": False, "detail": "Expected workspace directory as single argument."}]}))
        sys.exit(1)

    workspace = sys.argv[1]

    # Look for output file optimized_tweets.json
    candidate_files = []
    for root, _, files in os.walk(workspace):
        for fname in files:
            if fname.lower() == 'optimized_tweets.json':
                candidate_files.append(os.path.join(root, fname))

    if not candidate_files:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "Output file presence", "passed": False, "detail": "optimized_tweets.json not found."}]}))
        sys.exit(1)

    # Evaluate each candidate and take best
    best_result = {"passed": False, "score": 0.0, "checks": []}

    for file_path in candidate_files:
        data = read_json_file(file_path)
        if not data or not isinstance(data.get('tweets'), list):
            continue
        result = find_best_result(data['tweets'])
        if result['score'] > best_result['score']:
            best_result = result

    print(json.dumps(best_result))