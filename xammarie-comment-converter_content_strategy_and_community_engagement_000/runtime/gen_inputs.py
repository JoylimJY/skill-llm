import os
import json
import random

random.seed(42)

workspace = "/workspace"

# --- Deep directory structure with distractor files ---
dirs = [
    "workspace/marketing/campaigns/q3",
    "workspace/marketing/campaigns/q4",
    "workspace/marketing/assets/images",
    "workspace/marketing/assets/copy",
    "workspace/community/threads/archived",
    "workspace/community/threads/active",
    "workspace/community/responses/drafts",
    "workspace/community/responses/published",
    "workspace/product/roadmap",
    "workspace/product/changelog",
    "workspace/analytics/reports",
    "workspace/analytics/raw_data",
    "workspace/ops/infra",
    "workspace/ops/scripts",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# --- Distractor files ---
distractor_files = {
    "workspace/marketing/campaigns/q3/email_sequence.txt": "Subject: Are you struggling with CI/CD?\nBody: We help teams ship faster...",
    "workspace/marketing/campaigns/q4/budget.json": json.dumps({"q4_budget": 12000, "channels": ["linkedin", "reddit", "hn"]}),
    "workspace/marketing/assets/copy/taglines.txt": "Tagline 1: Ship faster, break nothing.\nTagline 2: From commit to deploy in 90 seconds.",
    "workspace/marketing/assets/copy/value_props.md": "# Value Props\n- 60% reduction in flaky tests\n- Zero-config setup\n- Works with any CI\n",
    "workspace/community/threads/archived/hn_thread_2023.txt": "Thread: Ask HN: How do you handle test flakiness?\nTop comment: We just retry 3 times lol",
    "workspace/community/threads/archived/old_reddit_responses.txt": "r/devops old thread - responses about Jenkins vs CircleCI",
    "workspace/community/responses/published/nov_response_1.txt": "Hey great question! We actually open-sourced our retry logic...",
    "workspace/community/responses/drafts/rough_ideas.txt": "Maybe mention the 90-second deploy time?\nTalk about the open source angle?\nDon't be too salesy",
    "workspace/product/roadmap/2024_initiatives.md": "## Q1\n- Parallel test execution\n- Slack integration\n## Q2\n- GitHub Actions native support",
    "workspace/product/changelog/v2.3.md": "## v2.3.0\n- Fixed flaky test detection algorithm\n- Reduced cold start time by 40%",
    "workspace/analytics/reports/reddit_engagement_oct.csv": "subreddit,impressions,clicks,comments\nr/devops,1200,43,8\nr/programming,890,21,3",
    "workspace/analytics/raw_data/session_logs.jsonl": '{"user":"u1","action":"visit","source":"reddit"}\n{"user":"u2","action":"signup","source":"reddit"}\n',
    "workspace/ops/infra/docker_compose.yml": "version: '3'\nservices:\n  app:\n    image: testrunner:latest\n    ports:\n      - '8080:8080'",
    "workspace/ops/scripts/deploy.sh": "#!/bin/bash\necho 'Deploying...'\ndocker build -t testrunner:latest .\ndocker push testrunner:latest",
}

for rel_path, content in distractor_files.items():
    abs_path = os.path.join(workspace, rel_path)
    with open(abs_path, "w") as f:
        f.write(content)

# --- THE ACTUAL TASK INPUTS ---

# The messy Reddit thread context
thread_post = """
Title: Our CI pipeline takes 47 minutes. Is this normal for a 200-person eng team?
Subreddit: r/devops

We're at about 200 engineers, monorepo, ~18k tests (mix of unit, integration, E2E). 
Our main CI pipeline has ballooned to 47 minutes end-to-end. Leadership is starting 
to ask questions and honestly I don't know what a "good" benchmark is for teams our size.

We've tried:
- Splitting unit vs integration runs
- Caching node_modules 
- Running some jobs in parallel

Still sitting at 47 min. Is this just the cost of scale or are we doing something wrong?
Some context: we're on GitHub Actions, Node.js/TypeScript stack, AWS infrastructure.
"""

top_comments = [
    {
        "author": "u/k8s_greybeard",
        "score": 847,
        "text": "47 mins is rough but not uncommon for that scale without proper optimization. The real question is what your p95 looks like – if avg is 47 but some runs hit 90+, you have a flakiness/retry tax eating your time. We went from 52 min to 11 min mostly by killing flaky tests and enabling test splitting by file size not count."
    },
    {
        "author": "u/shipit_or_quit",
        "score": 412,
        "text": "What's your test distribution? 18k sounds high but depends heavily on how many are E2E. E2E tests are usually 10-20x slower than unit. If you have >1000 E2E tests running sequentially you've found your culprit. Most teams at your scale should target <15 min for the critical path."
    },
    {
        "author": "u/devops_dana",
        "score": 298,
        "text": "GitHub Actions has some brutal cold start issues at scale. Each runner spin-up can cost 2-4 minutes. If you're running 20+ parallel jobs you're burning a lot on just bootstrap time. Self-hosted runners or something like Depot/BuildJet might give you 30-40% improvement just from faster hardware and warm caches."
    },
    {
        "author": "u/pragmatic_pete",
        "score": 187,
        "text": "Honest take: most of the 'optimize your CI' advice ignores the human side. Your engineers are checking Slack/HN for those 47 minutes. That's the real cost. Even if you can't fix it technically, breaking the pipeline into a fast 8-min smoke test that gates PRs and a slow nightly full suite can change dev behavior immediately."
    },
    {
        "author": "u/test_skeptic",
        "score": 156,
        "text": "Unpopular opinion: audit your test suite before optimizing infrastructure. We had 3,000 tests that were basically testing implementation details, not behavior. Deleted them. CI went from 38 min to 19 min with zero actual coverage loss. More tests != better coverage."
    }
]

# Founder's viewpoint and context
founder_viewpoint = """
I'm the founder of a developer tool that specifically addresses CI/CD optimization for 
mid-to-large engineering teams. Our product, PipelineIQ, uses ML-based test impact analysis 
to run only the tests affected by a given change. In our customer data across 47 enterprise 
deployments, we've seen an average reduction from 45 min pipelines down to 8-12 min on 
the first week alone.

I want to contribute genuinely to this thread because:
1. This is exactly our ICP (200-400 person eng teams on GH Actions)
2. The top comments are good but miss test impact analysis entirely
3. I don't want to be the "hi I made a thing" guy — I want to give real value first

My conversion goal: get the OP or engaged commenters to visit our site or DM me for 
the benchmark report we published (covers 47 enterprise CI audits with specific numbers).
"""

# Write inputs to the active thread folder — messy naming, realistic
thread_dir = os.path.join(workspace, "workspace/community/threads/active")

with open(os.path.join(thread_dir, "thread_raw_dump.txt"), "w") as f:
    f.write("=== ORIGINAL POST ===\n")
    f.write(thread_post.strip())
    f.write("\n\n=== TOP COMMENTS ===\n")
    for i, c in enumerate(top_comments, 1):
        f.write(f"\n--- Comment {i} ---\n")
        f.write(f"Author: {c['author']} | Score: {c['score']}\n")
        f.write(c['text'] + "\n")

with open(os.path.join(thread_dir, "founder_brief.txt"), "w") as f:
    f.write(founder_viewpoint.strip())

# A config-like file that is a red herring
with open(os.path.join(thread_dir, "thread_meta.json"), "w") as f:
    json.dump({
        "thread_url": "https://reddit.com/r/devops/comments/xyz123/our_ci_pipeline_takes_47_minutes",
        "scraped_at": "2024-11-14T09:32:00Z",
        "subreddit": "r/devops",
        "post_score": 1243,
        "comment_count": 89,
        "status": "active",
        "assigned_to": "founder_outreach",
        "notes": "High-intent thread. OP fits ICP exactly. Respond before it dies."
    }, f, indent=2)

# Another distractor in community folder
with open(os.path.join(workspace, "workspace/community/responses/drafts/ci_thread_attempt1.txt"), "w") as f:
    f.write("ROUGH DRAFT - DO NOT USE\n\nHey! Great question. At PipelineIQ we've helped teams like yours...\n[too salesy, rejected]\n")

print("Workspace generated successfully.")
print(f"Task inputs written to: {thread_dir}")