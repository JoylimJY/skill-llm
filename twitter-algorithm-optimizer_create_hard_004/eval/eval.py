import sys
import os
import json
import re

def load_text_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception:
        return None

def check_optimized_tweet(content):
    checks_passed = []

    # Check length > 20 chars
    checks_passed.append((len(content) > 20, 'Optimized tweet length > 20 chars'))

    # Check presence of at least one question to trigger replies
    has_question = any(qword in content.lower() for qword in ['?', 'what', 'why', 'how', 'thoughts', 'opinions', 'opinions?', 'share', 'comments', 'reply', 'debate'])
    checks_passed.append((has_question, 'Optimized tweet contains question or engagement invite'))

    # Check avoids engagement bait patterns (like 'retweet if') flatly
    bait_words = ['retweet if', 'like if', 'share if', 'please retweet', 'please like']
    no_bait = not any(b in content.lower() for b in bait_words)
    checks_passed.append((no_bait, 'Optimized tweet avoids engagement bait phrases'))

    # Check clear topical relevance or niche language:
    # Since original is about programming, check for programming-related keywords
    programming_terms = ['programming', 'code', 'bug', 'developer', 'function', 'javascript', 'python', 'rust', 'framework', 'debug', 'codebase']
    topical_relevance = any(term in content.lower() for term in programming_terms)
    checks_passed.append((topical_relevance, 'Optimized tweet includes programming-related topical terms'))

    # Real-graph trigger: presence of direct question or call to action to followers
    direct_question = re.search(r'\b(what|why|how|thoughts|opinions|share|reply|comments|debate)\b', content, re.IGNORECASE)
    checks_passed.append((direct_question is not None, 'Optimized tweet includes Real-graph follower engagement trigger'))

    return checks_passed

def check_optimization_explanation(content):
    checks = []

    # Explanation length >= 150 words
    word_count = len(re.findall(r'\w+', content))
    checks.append((word_count >= 150, 'Explanation is at least 150 words'))

    # Check mentions of core algorithm terms: Real-graph, SimClusters, TwHIN, Tweepcred
    keywords = ['real-graph', 'simclusters', 'twhin', 'tweepcred']
    found_keys = [kw for kw in keywords if kw in content.lower()]
    checks.append((len(found_keys) >= 3, 'Explanation mentions at least three core algorithm components'))

    # Check explanation refers to engagement signals (likes, replies, retweets, bookmarks)
    engagement_terms = ['likes', 'replies', 'retweets', 'bookmarks', 'engagement', 'signals']
    engagement_present = any(et in content.lower() for et in engagement_terms)
    checks.append((engagement_present, 'Explanation covers engagement signal concepts explicitly'))

    # Check avoidances of negative signals (bait, inflammatory, vague)
    negatives = ['bait', 'engagement bait', 'inflammatory', 'vague', 'blocks', 'reports']
    negatives_mentioned = any(neg in content.lower() for neg in negatives)
    checks.append((negatives_mentioned, 'Explanation mentions avoidance of negative signals'))

    return checks

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else '.'

    checks = []

    # Find optimized_tweet.txt file
    tweet_files = [f for f in os.listdir(workspace) if f.lower() == 'optimized_tweet.txt']
    tweet_scores = []
    for tweet_file in tweet_files:
        content = load_text_file(os.path.join(workspace, tweet_file))
        if content is None:
            continue
        tweet_checks = check_optimized_tweet(content)
        passed_count = sum(1 for p, _ in tweet_checks if p)
        score = passed_count / len(tweet_checks) if tweet_checks else 0
        tweet_scores.append((score, tweet_checks))

    # Pick best tweet file scoring
    if tweet_scores:
        best_score, best_checks = max(tweet_scores, key=lambda x: x[0])
        checks.extend([(f'Optimized Tweet - {desc}', p) for p, desc in best_checks])
    else:
        # Fail all if file missing or unreadable
        checks.extend([(f'Optimized Tweet - {desc}', False) for _, desc in check_optimized_tweet('')])

    # Find optimization_explanation.md file
    expl_files = [f for f in os.listdir(workspace) if f.lower() == 'optimization_explanation.md']
    expl_scores = []
    for expl_file in expl_files:
        content = load_text_file(os.path.join(workspace, expl_file))
        if content is None:
            continue
        expl_checks = check_optimization_explanation(content)
        passed_count = sum(1 for p, _ in expl_checks if p)
        score = passed_count / len(expl_checks) if expl_checks else 0
        expl_scores.append((score, expl_checks))

    if expl_scores:
        best_score, best_checks = max(expl_scores, key=lambda x: x[0])
        checks.extend([(f'Optimization Explanation - {desc}', p) for p, desc in best_checks])
    else:
        checks.extend([(f'Optimization Explanation - {desc}', False) for _, desc in check_optimization_explanation('')])

    # Calculate overall score
    total_checks = len(checks)
    total_passed = sum(1 for c in checks if c[1])
    score = total_passed / total_checks if total_checks > 0 else 0
    passed = score == 1.0 or score >= 0.8

    # Format detailed results
    detail_list = []
    for name, passed_check in checks:
        detail_list.append({
            "name": name,
            "passed": passed_check,
            "detail": ("Passed" if passed_check else "Failed")
        })

    result = {
        "passed": passed,
        "score": score,
        "checks": detail_list
    }

    print(json.dumps(result))

if __name__ == '__main__':
    main()
