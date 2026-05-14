#!/bin/bash
set -e

# Make scripts executable
chmod +x /workspace/scripts/run_dev.sh

# ── Start a local mock search/web server on port 7890 ────────────────────────
# This provides mock search results when the agent uses WebSearch or WebFetch

cat > /tmp/mock_search_server.py << 'MOCK_SERVER_EOF'
#!/usr/bin/env python3
"""
Mock search server simulating WebSearch/WebFetch responses for:
- AI-powered code review tools market research
- Reddit/HN user sentiment
- GitHub open-source alternatives
"""

from flask import Flask, request, jsonify, Response
import json, re

app = Flask(__name__)

SEARCH_DATA = {
    "default": [
        {"title": "AI Code Review Market 2024 - $2.1B TAM", "url": "https://example-market.com/report", "snippet": "The AI code review market is estimated at $2.1B TAM with 34% CAGR. Key players include CodeRabbit, Reviewpad, Codacy, SonarQube, and DeepCode."},
        {"title": "CodeRabbit Pricing - AI Code Review", "url": "https://coderabbit.ai/pricing", "snippet": "CodeRabbit pricing starts at $19/developer/month. Pro plan $29/dev/month. Enterprise custom pricing. Free tier available."},
        {"title": "Codacy vs SonarQube Comparison G2", "url": "https://g2.com/compare/codacy-vs-sonarqube", "snippet": "Codacy rated 4.2/5 on G2 with 310 reviews. SonarQube 4.4/5 with 890 reviews. Users praise automation, criticize false positives."},
    ],
    "reddit": [
        {"title": "r/programming: Tired of manual code reviews, tried CodeRabbit", "url": "https://reddit.com/r/programming/comments/abc123", "snippet": "User says: 'We're a 5-person team and code reviews were taking forever. AI tools helped but still too many false positives. Needs better context awareness.'"},
        {"title": "r/devops: AI code review tools - are they worth it?", "url": "https://reddit.com/r/devops/comments/xyz789", "snippet": "Top comment: 'The problem is they don't understand our internal conventions. We spent 2 weeks tuning rules.' Another: 'Missing feature: learning from approved PRs automatically.'"},
        {"title": "r/ExperiencedDevs: What do small teams use for code quality?", "url": "https://reddit.com/r/ExperiencedDevs/comments/qrs456", "snippet": "Pain point thread: '2-8 dev teams can't justify a QA hire. We need something that learns our style without extensive config.'"},
    ],
    "hackernews": [
        {"title": "Ask HN: Best automated code review for small startups?", "url": "https://news.ycombinator.com/item?id=38291847", "snippet": "HN discussion: 'Current tools are either too basic (linters) or too expensive (enterprise). Gap in market for SMB-focused AI review.' 847 points, 234 comments."},
        {"title": "Show HN: We built an AI that learns your team's code style", "url": "https://news.ycombinator.com/item?id=37654321", "snippet": "200 upvotes. Comment: 'This is exactly what I wanted. Style learning from merged PRs is the killer feature.' Another: 'Need GitHub + GitLab support.'"},
    ],
    "github": [
        {"title": "github.com/reviewdog/reviewdog - Automated code review tool", "url": "https://github.com/reviewdog/reviewdog", "snippet": "reviewdog: 7.2k stars, Go-based, integrates linters with PR comments. No LLM support. MIT license. Active community."},
        {"title": "github.com/coderabbitai/openai-pr-reviewer", "url": "https://github.com/coderabbitai/openai-pr-reviewer", "snippet": "OpenAI-based PR reviewer GitHub Action. 1.8k stars. TypeScript. Uses GPT-4. Customizable prompts. Lacks team style learning."},
        {"title": "github.com/sturdy-dev/codeball - AI code review action", "url": "https://github.com/sturdy-dev/codeball", "snippet": "codeball: 950 stars, Python, uses ML to predict if PRs will be approved. Training on repo history. Archived - no longer maintained."},
    ],
    "product_hunt": [
        {"title": "CodeRabbit - AI Code Reviews Product Hunt", "url": "https://producthunt.com/posts/coderabbit", "snippet": "CodeRabbit launched on Product Hunt with 1,200 upvotes. '#1 Product of the Day'. Reviews highlight: fast setup, GitHub integration. Criticism: misses domain context."},
        {"title": "Reviewpad - Automate GitHub workflows", "url": "https://producthunt.com/posts/reviewpad", "snippet": "Reviewpad: 430 upvotes. Focus on workflow rules rather than LLM review. Complements rather than replaces AI review."},
    ],
}

def get_mock_results(query):
    q = query.lower()
    if "reddit" in q or "site:reddit.com" in q:
        return SEARCH_DATA["reddit"]
    elif "hacker news" in q or "ycombinator" in q or "site:news.ycombinator" in q:
        return SEARCH_DATA["hackernews"]
    elif "github" in q or "site:github.com" in q or "open source" in q:
        return SEARCH_DATA["github"]
    elif "product hunt" in q or "g2" in q or "capterra" in q:
        return SEARCH_DATA["product_hunt"]
    else:
        return SEARCH_DATA["default"]

@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        data = request.get_json(silent=True) or {}
        query = data.get('query', data.get('q', ''))
    else:
        query = request.args.get('q', request.args.get('query', ''))
    
    results = get_mock_results(query)
    return jsonify({
        "query": query,
        "results": results,
        "total": len(results)
    })

@app.route('/fetch', methods=['GET', 'POST'])
def fetch():
    if request.method == 'POST':
        data = request.get_json(silent=True) or {}
        url = data.get('url', '')
    else:
        url = request.args.get('url', '')
    
    # Return mock content based on URL
    if 'coderabbit' in url.lower():
        content = "CodeRabbit AI Code Review\nPricing: $19-29/dev/month\nFeatures: PR summaries, line-by-line review, custom rules\nTAM: $2.1B AI code review market\nFunding: $16M Series A"
    elif 'reddit' in url.lower():
        content = "Reddit Discussion: AI code review tools\nTop comment: 'False positives are killing our workflow. Need better context.'\nUpvotes: 847\nKey frustration: tools don't learn from team feedback"
    elif 'github' in url.lower():
        content = "GitHub Repository: reviewdog\nStars: 7200\nLanguage: Go\nLicense: MIT\nLast commit: 2 days ago\nDescription: Run linters and report results as PR review comments"
    else:
        content = "Page content: AI-powered development tools are growing rapidly. Market consolidating around a few key players. Small teams underserved by enterprise pricing."
    
    return jsonify({"url": url, "content": content, "status": 200})

@app.route('/health')
def health():
    return jsonify({"status": "ok", "service": "mock-search"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7890, debug=False)
MOCK_SERVER_EOF

python3 /tmp/mock_search_server.py &
MOCK_PID=$!
echo "Mock search server started with PID $MOCK_PID on port 7890"

# Wait for server to be ready
for i in $(seq 1 15); do
    if curl -s http://localhost:7890/health > /dev/null 2>&1; then
        echo "Mock server is ready."
        break
    fi
    sleep 1
done

# Verify the workspace structure
echo "Workspace files:"
find /workspace -type f | sort

echo "Setup complete."