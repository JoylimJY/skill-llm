import os
import random
import json

random.seed(42)

# --- Create directory structure ---
dirs = [
    "scripts",
    "campaigns/q3_tech_client/assets",
    "campaigns/q3_tech_client/drafts",
    "campaigns/q4_health_client/assets",
    "campaigns/q4_health_client/drafts",
    "archive/2023/posts",
    "archive/2024/posts",
    "raw_content",
    "output/social",
    "templates",
    "logs",
]
for d in dirs:
    os.makedirs(d, exist_ok=True)

# --- Distractor files ---
distractors = [
    ("campaigns/q3_tech_client/drafts/brief.md", "# Campaign Brief\nTarget: developers\nTone: technical, confident\n"),
    ("campaigns/q3_tech_client/assets/logo_notes.txt", "Logo colors: #0F4C81, #FFFFFF\nFont: Inter 700\n"),
    ("campaigns/q4_health_client/drafts/notes.txt", "Focus on longevity science and gut health trends for Q4.\n"),
    ("archive/2023/posts/old_ai_post.txt", "AI in 2023: what we got wrong and right. Original draft, not for repurposing.\n"),
    ("archive/2024/posts/climate_article.md", "# Climate Tech 2024\nDraft copy — awaiting legal approval.\n"),
    ("templates/linkedin_template.txt", "TEMPLATE (DO NOT USE DIRECTLY):\n[Hook]\n[Body - 3 key insights]\n[CTA]\n"),
    ("templates/twitter_thread_guide.txt", "Tweet 1: Hook\nTweet 2-6: Key points\nTweet 7: CTA + hashtags\n"),
    ("logs/repurpose_run_2024-11-01.log", "Run completed. 3 formats generated. Exit 0.\n"),
    ("output/social/.gitkeep", ""),
    ("raw_content/placeholder.txt", "Raw content inbox — drop articles here for processing.\n"),
]
for path, content in distractors:
    with open(path, "w") as f:
        f.write(content)

# --- MAIN INPUT ARTICLE 1: Tech article for Twitter + LinkedIn ---
article_tech = """The Rise of Agentic AI Systems in Enterprise Software

Over the past two years, a quiet revolution has been transforming how enterprises think about automation. 
Rather than static workflows and rule-based bots, companies are now deploying agentic AI systems—software 
agents that can reason, plan, and execute multi-step tasks with minimal human oversight.

What makes agentic AI different? Unlike a traditional chatbot that responds to individual queries, an AI 
agent can decompose a complex goal into subtasks, use tools like web search or code execution, and 
self-correct when it hits dead ends. Think of it as the difference between a calculator and an intern 
who can figure out what calculator to use.

Early enterprise adopters report dramatic productivity gains. A mid-sized logistics company cut its 
procurement research time by 74% after deploying an AI agent that autonomously monitors supplier 
catalogs, compares prices, and drafts purchase recommendations. A legal firm slashed contract review 
time from 8 hours to 40 minutes.

The key architectural shift enabling this? Retrieval-Augmented Generation (RAG) combined with 
tool-use APIs. Agents now have memory (via vector databases), perception (via document parsers and 
web scrapers), and action (via API calls). This trifecta has moved AI from a conversational novelty 
to an operational asset.

But the road isn't without potholes. Security teams are grappling with "agent sprawl"—hundreds of 
autonomous processes running in production with inconsistent audit trails. Hallucination rates, while 
lower than earlier models, still create liability concerns in regulated industries like finance and 
healthcare.

The companies winning with agentic AI share three traits: they start with narrow, well-defined tasks; 
they build human-in-the-loop checkpoints for high-stakes decisions; and they invest heavily in 
observability tooling to monitor agent behavior in real time.

The next frontier? Multi-agent collaboration—systems where specialized agents hand off work to each 
other, much like a well-coordinated team. Early prototypes are already handling end-to-end workflows 
that once required entire departments.

Agentic AI is not coming—it's already here. The question for enterprise leaders is no longer "should 
we explore this?" but "how fast can we safely scale it?"
"""

with open("raw_content/agentic_ai_enterprise.txt", "w") as f:
    f.write(article_tech)

# --- MAIN INPUT ARTICLE 2: Health/wellness article for summary (stdin) ---
article_health = """Why Sleep is the Ultimate Performance Enhancer

For decades, high performers wore sleep deprivation as a badge of honor. "I'll sleep when I'm dead" 
was the unofficial motto of Silicon Valley founders, Wall Street traders, and elite athletes alike. 
Modern sleep science has dismantled that myth with ruthless precision.

Sleep is not passive downtime—it is the body's most sophisticated maintenance protocol. During deep 
slow-wave sleep, the brain activates the glymphatic system, a waste-clearance network that flushes 
out metabolic toxins including amyloid-beta, a protein linked to Alzheimer's disease. Miss enough 
sleep and you're essentially skipping the nightly deep-clean.

Cognitive performance is the most measurable casualty of insufficient sleep. Research from the 
University of Pennsylvania showed that subjects sleeping six hours per night for two weeks performed 
as poorly on cognitive tasks as subjects who had been awake for 24 hours straight—yet the six-hour 
group consistently underestimated their own impairment. You don't know how tired you are.

Athletic performance tells the same story. A Stanford study on basketball players found that 
extending sleep to 10 hours per night improved sprint times by 5%, shooting accuracy by 9%, and 
reaction times significantly. Sleep is, functionally, a legal performance-enhancing drug.

The mechanisms are well-understood: during REM sleep, the brain consolidates procedural and emotional 
memories, regulates cortisol, and replenishes neurotransmitter stores. Growth hormone—critical for 
muscle repair and fat metabolism—is released almost exclusively during deep sleep stages.

So what does optimal sleep hygiene look like? Consistency beats duration: sleeping and waking at the 
same time every day, including weekends, stabilizes circadian rhythms more effectively than any 
supplement. Temperature matters: core body temperature must drop 1-2°F to initiate sleep, which is 
why a cool room (65-68°F) accelerates sleep onset. Light is the master regulator: morning sunlight 
exposure sets your internal clock, while blue light from screens delays melatonin release by up to 
90 minutes.

The evidence is unambiguous. Sleep is not a luxury or a weakness—it is the foundation on which every 
other health and performance intervention rests. Optimize everything else and neglect sleep, and you 
are, to use a technical term, leaving gains on the table.
"""

with open("raw_content/sleep_performance.txt", "w") as f:
    f.write(article_health)

# --- Fake repurpose.py stub to show it exists but is a placeholder ---
# (Per directive 3: scripts already exist in workspace, we just create stub)
repurpose_stub = '''#!/usr/bin/env python3
"""
Content Repurposer - scripts/repurpose.py
Repurpose articles into multiple social media formats.

Usage:
  python scripts/repurpose.py url <url> [--formats LIST] [-f FORMAT] [-o DIR]
  python scripts/repurpose.py file <path> [--formats LIST] [-f FORMAT] [-o DIR]
  python scripts/repurpose.py stdin [--formats LIST] [-f FORMAT]

Formats: twitter, linkedin, instagram, email, summary
Output types: text (default), json
"""
import argparse
import sys
import json
import os
import re

PLATFORM_LIMITS = {
    "twitter": {"max_chars_per_tweet": 280, "min_tweets": 5, "max_tweets": 8},
    "linkedin": {"max_chars": 1300},
    "instagram": {"max_chars": 2200, "min_hashtags": 20, "max_hashtags": 30},
    "email": {"fields": ["subject", "preview", "body"]},
    "summary": {"sentences": 3},
}

ALL_FORMATS = ["twitter", "linkedin", "instagram", "email", "summary"]


def extract_text_from_url(url):
    try:
        import urllib.request
        from bs4 import BeautifulSoup
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read()
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["nav", "footer", "sidebar", "script", "style", "header"]):
            tag.decompose()
        return soup.get_text(separator=" ", strip=True)[:8000]
    except Exception as e:
        print(f"Error fetching URL: {e}", file=sys.stderr)
        sys.exit(1)


def read_file(path):
    with open(path, "r") as f:
        return f.read()


def read_stdin():
    return sys.stdin.read()


def generate_twitter(text):
    words = text.split()
    title_words = words[:8]
    title = " ".join(title_words)
    hooks = [
        f"🧵 Thread: {title}...",
        f"Here\'s what you need to know about {title[:60]}:",
        f"Key insights on {title[:70]} 👇",
    ]
    import random
    random.seed(hash(text[:100]) % (2**31))
    hook = random.choice(hooks)
    sentences = [s.strip() for s in re.split(r"[.!?]", text) if len(s.strip()) > 30]
    tweets = [hook[:270]]
    for i, sent in enumerate(sentences[1:7], 1):
        tweet = f"{i}/ {sent[:250]}"
        tweets.append(tweet)
    cta = f"{len(tweets)+1}/ What\'s your take? Drop your thoughts below. 👇 #AI #Tech #Innovation"
    tweets.append(cta[:280])
    # Enforce <=280 per tweet
    tweets = [t[:280] for t in tweets]
    # Ensure 5-8 tweets
    while len(tweets) < 5:
        tweets.append(f"Read more for the full breakdown. #Thread")
    tweets = tweets[:8]
    return tweets


def generate_linkedin(text):
    words = text.split()
    first_sent = " ".join(words[:20])
    paragraphs = [p.strip() for p in text.split("\\n\\n") if len(p.strip()) > 50]
    body_parts = []
    for p in paragraphs[:3]:
        body_parts.append(p[:200])
    body = "\\n\\n".join(body_parts)
    cta = "\\n\\nWhat has your experience been? I\'d love to hear your perspective in the comments."
    post = f"💡 {first_sent}...\\n\\n{body}{cta}"
    return post[:1300]


def generate_instagram(text):
    words = text.split()
    caption_body = " ".join(words[:200])
    hashtags_pool = ["#growth", "#mindset", "#innovation", "#tech", "#ai", "#productivity",
                     "#leadership", "#business", "#entrepreneur", "#success", "#future",
                     "#digitalmarketing", "#contentstrategy", "#socialmedia", "#startup",
                     "#knowledge", "#learning", "#motivation", "#inspired", "#trends",
                     "#data", "#transformation", "#agile", "#strategy", "#insights",
                     "#creator", "#community", "#impact", "#work", "#career"]
    import random
    random.seed(hash(text[:50]) % (2**31))
    hashtags = random.sample(hashtags_pool, 25)
    hashtag_str = " ".join(hashtags)
    caption = f"✨ {caption_body}\\n\\n{hashtag_str}"
    return caption[:2200]


def generate_email(text):
    words = text.split()
    subject = "Must-read: " + " ".join(words[:8])
    preview = " ".join(words[8:25]) + "..."
    body_sents = [s.strip() for s in re.split(r"[.!?]", text) if len(s.strip()) > 40]
    body = " ".join(body_sents[:5])
    return {"subject": subject[:80], "preview": preview[:150], "body": body[:500]}


def generate_summary(text):
    sentences = [s.strip() for s in re.split(r"[.!?]", text) if len(s.strip()) > 40]
    chosen = sentences[:3]
    while len(chosen) < 3:
        chosen.append("See the full article for more details.")
    return " ".join(chosen[:3])


GENERATORS = {
    "twitter": generate_twitter,
    "linkedin": generate_linkedin,
    "instagram": generate_instagram,
    "email": generate_email,
    "summary": generate_summary,
}


def main():
    parser = argparse.ArgumentParser(description="Content Repurposer")
    subparsers = parser.add_subparsers(dest="command")

    url_p = subparsers.add_parser("url")
    url_p.add_argument("url_arg")
    url_p.add_argument("--formats", type=str, default=",".join(ALL_FORMATS))
    url_p.add_argument("-f", "--output-format", default="text")
    url_p.add_argument("-o", "--output-dir", default=None)

    file_p = subparsers.add_parser("file")
    file_p.add_argument("file_path")
    file_p.add_argument("--formats", type=str, default=",".join(ALL_FORMATS))
    file_p.add_argument("-f", "--output-format", default="text")
    file_p.add_argument("-o", "--output-dir", default=None)

    stdin_p = subparsers.add_parser("stdin")
    stdin_p.add_argument("--formats", type=str, default=",".join(ALL_FORMATS))
    stdin_p.add_argument("-f", "--output-format", default="text")
    stdin_p.add_argument("-o", "--output-dir", default=None)

    args = parser.parse_args()

    if args.command == "url":
        text = extract_text_from_url(args.url_arg)
    elif args.command == "file":
        text = read_file(args.file_path)
    elif args.command == "stdin":
        text = read_stdin()
    else:
        parser.print_help()
        sys.exit(1)

    formats = [f.strip() for f in args.formats.split(",")]
    results = {}
    for fmt in formats:
        if fmt in GENERATORS:
            results[fmt] = GENERATORS[fmt](text)

    if args.output_dir:
        os.makedirs(args.output_dir, exist_ok=True)
        for fmt, content in results.items():
            filepath = os.path.join(args.output_dir, f"{fmt}.txt")
            with open(filepath, "w") as fh:
                if isinstance(content, list):
                    fh.write("\\n---\\n".join(content))
                elif isinstance(content, dict):
                    for k, v in content.items():
                        fh.write(f"{k.upper()}: {v}\\n")
                else:
                    fh.write(content)
        if args.output_format == "json":
            with open(os.path.join(args.output_dir, "repurposed.json"), "w") as jf:
                json.dump(results, jf, indent=2)
            print(json.dumps(results, indent=2))
        else:
            for fmt, content in results.items():
                print(f"\\n=== {fmt.upper()} ===")
                if isinstance(content, list):
                    for t in content:
                        print(t)
                elif isinstance(content, dict):
                    for k, v in content.items():
                        print(f"{k}: {v}")
                else:
                    print(content)
    else:
        if args.output_format == "json":
            print(json.dumps(results, indent=2))
        else:
            for fmt, content in results.items():
                print(f"\\n=== {fmt.upper()} ===")
                if isinstance(content, list):
                    for t in content:
                        print(t)
                elif isinstance(content, dict):
                    for k, v in content.items():
                        print(f"{k}: {v}")
                else:
                    print(content)


if __name__ == "__main__":
    main()
'''

with open("scripts/repurpose.py", "w") as f:
    f.write(repurpose_stub)

print("Workspace initialized successfully.")
print("Files created:")
for root, dirs, files in os.walk("."):
    for file in files:
        print(f"  {os.path.join(root, file)}")