import sys
import os
import json
import re

def check_optimized_tweet_content(text):
    text_lower = text.lower()
    checks = []

    # Check 1: improved tweet text exists and is longer/more engaging than original
    # Original is simple statement: "Just finished my workout session. Feeling good."
    # Optimized should contain at least one question or call to action
    engagement_triggers = ['?', 'thoughts', 'opinions', 'how do you', 'what is', 'drop a comment', 'share your', '👇', 'tell me', 'any tips']
    has_question_or_cta = any(trigger in text_lower for trigger in engagement_triggers)
    checks.append((has_question_or_cta, 'Tweet contains question or call to action for engagement'))

    # Check 2: Tweet references a specific aspect or value to followers (Real-graph)
    real_graph_terms = ['workout type', 'favorite exercise', 'post-workout routine', 'energy boost']
    real_graph_mention = any(term in text_lower for term in real_graph_terms)
    checks.append((real_graph_mention or 'workout' in text_lower, 'Tweet targets workout-related interests (Real-graph)'))

    # Check 3: Explanation section exists with heading and some keywords related to algorithm
    has_explanation = bool(re.search(r'(##|###)\s*explanation', text, re.IGNORECASE))
    checks.append((has_explanation, 'Explanation section present in markdown'))
    algo_keywords = ['real-graph', 'simclusters', 'twhin', 'engagement', 'followers', 'community', 'question', 'reply', 'retweet']
    keyword_hits = sum(kw in text_lower for kw in algo_keywords)
    checks.append((keyword_hits >= 2, 'Explanation contains algorithm keywords'))

    # Check 4: Summary section exists with engagement signal terms
    has_summary = bool(re.search(r'(##|###)\s*summary', text, re.IGNORECASE))
    checks.append((has_summary, 'Summary section present in markdown'))
    sig_keywords = ['likes', 'replies', 'retweets', 'bookmarks', 'engagement']
    sig_hits = sum(kw in text_lower for kw in sig_keywords)
    checks.append((sig_hits >= 2, 'Summary includes engagement signal keywords'))

    # Calculate final score
    passed_checks = sum(c[0] for c in checks)
    total_checks = len(checks)
    score = passed_checks / total_checks
    passed = score >= 0.8

    # Build detailed results
    detailed = []
    for name, (passed_check, detail) in enumerate(checks, 1):
        detailed.append({"name": f"Check {name}: {detail}", "passed": passed_check, "detail": detail})

    return {"passed": passed, "score": score, "checks": detailed}


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"passed":False, "score":0.0, "checks":[{"name":"No argument","passed":False,"detail":"No workspace path provided"}]}))
        return
    workspace = sys.argv[1]

    # Find optimized_tweet.md file
    candidates = [f for f in os.listdir(workspace) if f.lower().endswith('.md') and 'optimized' in f.lower()]
    if not candidates:
        print(json.dumps({"passed":False, "score":0.0, "checks":[{"name":"File check","passed":False,"detail":"No optimized_tweet.md file found"}]}))
        return

    best_result = None
    for fname in candidates:
        try:
            with open(os.path.join(workspace, fname), 'r', encoding='utf-8') as f:
                content = f.read()
            result = check_optimized_tweet_content(content)
            if not best_result or result['score'] > best_result['score']:
                best_result = result
        except Exception as e:
            continue
    if best_result is None:
        print(json.dumps({"passed":False, "score":0.0, "checks":[{"name":"Evaluation","passed":False,"detail":"Could not read any optimized tweet file"}]}))
    else:
        print(json.dumps(best_result))

if __name__ == '__main__':
    main()
