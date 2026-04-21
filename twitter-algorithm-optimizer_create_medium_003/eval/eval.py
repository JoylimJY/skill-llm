import sys
import os
import json
import re

def read_file(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception:
        return None

def contains_any(text, keywords):
    text_lc = text.lower()
    return any(keyword.lower() in text_lc for keyword in keywords)

def check_optimized_tweet(text):
    checks = []
    # 1. Check length > original
    passed_len = len(text.strip()) > 40
    checks.append({'name': 'Sufficient length of optimized tweet', 'passed': passed_len, 'detail': f'Length is {len(text.strip())}'})

    # 2. No engagement bait (like "retweet if", "like if")
    bait_phrases = ['retweet if', 'like if', 'share if', 'please retweet']
    bait_found = contains_any(text, bait_phrases)
    checks.append({'name': 'No engagement bait phrases', 'passed': not bait_found, 'detail': 'Engagement bait phrases found' if bait_found else 'None found'})

    # 3. Includes at least one question (for replies)
    question_mark = '?' in text
    checks.append({'name': 'Question present to trigger replies', 'passed': question_mark, 'detail': f'Q mark present: {question_mark}'})

    # 4. Includes specific topic or hashtags
    topic_keywords = ['ai', 'artificial intelligence', 'machine learning', '#future', '#tech']
    topic_mentioned = contains_any(text, topic_keywords)
    checks.append({'name': 'Mentions relevant topic or hashtags', 'passed': topic_mentioned, 'detail': 'Topic or hashtag found' if topic_mentioned else 'Not found'})

    # 5. Avoids vague statements like "I think" alone
    vague_phrases = ['i think', 'maybe', 'possibly']
    vague_found = contains_any(text, vague_phrases)
    checks.append({'name': 'No vague or weak phrasing', 'passed': not vague_found, 'detail': 'Vague terms found' if vague_found else 'None found'})

    return checks

def check_explanation(text):
    checks = []
    # 1. Length at least 150 words
    words = re.findall(r'\b\w+\b', text)
    enough_length = len(words) >= 150
    checks.append({'name': 'Explanation has at least 150 words', 'passed': enough_length, 'detail': f'Word count: {len(words)}'})

    # 2. Mentions all five algorithm strategies
    keywords = ['real-graph', 'simclusters', 'twhin', 'tweepcred', 'engagement signals']
    mentions_all = all(kw.lower() in text.lower() for kw in keywords)
    checks.append({'name': 'Mentions all required algorithm strategies', 'passed': mentions_all, 'detail': 'All found' if mentions_all else 'Missing some terms'})

    # 3. Contains examples referencing optimized tweet content (look for "question", "topic", "engagement")
    example_terms = ['question', 'engagement', 'topic', 'replies', 'retweets']
    examples_present = contains_any(text, example_terms)
    checks.append({'name': 'Explanation references engagement or content examples', 'passed': examples_present, 'detail': 'Engagement example terms present' if examples_present else 'Not found'})

    return checks

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else '.'

    optimized_tweet_path = None
    optimization_explanation_path = None

    # Find files
    for fname in os.listdir(workspace):
        if fname.lower() == 'optimized_tweet.txt':
            optimized_tweet_path = os.path.join(workspace, fname)
        elif fname.lower() == 'optimization_explanation.md':
            optimization_explanation_path = os.path.join(workspace, fname)

    checks = []

    if not optimized_tweet_path:
        checks.append({'name': 'Optimized tweet file presence', 'passed': False, 'detail': 'File optimized_tweet.txt not found'})
    else:
        opt_text = read_file(optimized_tweet_path) or ''
        checks.extend(check_optimized_tweet(opt_text))

    if not optimization_explanation_path:
        checks.append({'name': 'Optimization explanation file presence', 'passed': False, 'detail': 'File optimization_explanation.md not found'})
    else:
        expl_text = read_file(optimization_explanation_path) or ''
        checks.extend(check_explanation(expl_text))

    passed_count = sum(1 for c in checks if c['passed'])
    total = len(checks)
    score = passed_count / total if total > 0 else 0.0
    passed = score == 1.0

    print(json.dumps({'passed': passed, 'score': score, 'checks': checks}, indent=2))

if __name__ == '__main__':
    main()
