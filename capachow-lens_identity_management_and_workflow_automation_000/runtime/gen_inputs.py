import os
import json
import random
import textwrap

random.seed(42)

BASE = "/workspace"

# ── Distractor structure ──────────────────────────────────────────────────────
dirs = [
    "projects/alpha/docs",
    "projects/alpha/src",
    "projects/beta/notes",
    "archive/2022",
    "archive/2023",
    "clients/retainer_a",
    "clients/retainer_b",
    "personal/journal",
    "personal/reading",
    "tools/config",
    "skills/lens/scripts",
    "skills/lens/prompts",
]
for d in dirs:
    os.makedirs(os.path.join(BASE, d), exist_ok=True)

distractor_files = {
    "projects/alpha/docs/overview.md": "# Alpha Project\nThis is the overview for project alpha.",
    "projects/alpha/src/main.py": "def main():\n    print('hello alpha')\n",
    "projects/beta/notes/meeting_2024_03.txt": "Discussed Q2 roadmap. Approved budget increase.",
    "archive/2022/tax_summary.txt": "Revenue: $142,000. Expenses: $87,500. Net: $54,500.",
    "archive/2023/tax_summary.txt": "Revenue: $198,000. Expenses: $101,200. Net: $96,800.",
    "clients/retainer_a/contract.txt": "Retainer agreement signed 2023-01-15. Monthly: $4,500.",
    "clients/retainer_b/notes.txt": "Client onboarded Q3 2023. Focus: product strategy.",
    "personal/journal/2024_jan.txt": "Started the year strong. Reading more philosophy.",
    "personal/reading/booklist.txt": "1. Antifragile\n2. Meditations\n3. The Mom Test\n4. Zero to One",
    "tools/config/env_template.txt": "NODE_ENV=production\nPORT=3000\nLOG_LEVEL=info",
    "tools/config/aliases.sh": "alias ll='ls -la'\nalias gs='git status'",
}
for path, content in distractor_files.items():
    with open(os.path.join(BASE, path), "w") as f:
        f.write(content)

# ── skills/lens stubs (scripts and prompts exist but are NOT runnable — agent ─
# ── must manage the Trinity Node files directly per the SKILL.md protocol)   ──

bootstrap_js = textwrap.dedent("""\
    #!/usr/bin/env node
    // bootstrap.js — LENS initializer stub
    // This script is intentionally non-functional in this environment.
    // The agent must manually apply the Onboarding Protocol from SKILL.md.
    console.log('[bootstrap] stub executed — manual initialization required');
    process.exit(0);
""")
with open(os.path.join(BASE, "skills/lens/scripts/bootstrap.js"), "w") as f:
    f.write(bootstrap_js)

distillation_js = textwrap.dedent("""\
    #!/usr/bin/env node
    // distillation.js — preflight zero-token script stub
    console.log('[distillation] preflight stub — no new transcripts detected');
    process.exit(0);
""")
with open(os.path.join(BASE, "skills/lens/scripts/distillation.js"), "w") as f:
    f.write(distillation_js)

interview_md = textwrap.dedent("""\
    # LENS Interview Protocol
    Ask the subject one open, introspective question designed to surface values,
    identity anchors, or formative experiences. Rotate through: history, beliefs,
    style, and philosophy domains. Avoid yes/no questions.
""")
with open(os.path.join(BASE, "skills/lens/prompts/interview.md"), "w") as f:
    f.write(interview_md)

distillation_md = textwrap.dedent("""\
    # LENS Distillation Protocol
    Apply the High-Threshold Filter when processing transcripts:
    - AXIOM: only verified, immutable facts (biography, history, owned assets).
    - ETHOS: persistent traits and values — maintain exactly 10 Priority Traits.
    - MODUS: linguistic patterns and formatting habits — maintain exactly 5 Linguistic Markers.
    Never delete historical entries. Merge and refine only.
    Reject generic/common observations that do not uniquely characterise the subject.
""")
with open(os.path.join(BASE, "skills/lens/prompts/distillation.md"), "w") as f:
    f.write(distillation_md)

# ── Raw session transcripts (messy, unstructured — the agent's source material) ─
transcript_1 = textwrap.dedent("""\
    === OpenClaw Session Transcript | 2024-06-10 09:14 ===
    USER: Morning. I've been thinking about how I approach decisions.
    AGENT: What stands out for you?
    USER: I never make a call I can't defend philosophically. If I can't explain
    the reasoning from first principles, I won't do it. That's been true since
    I started my first company in 2011 in Cape Town — a logistics SaaS that I
    bootstrapped to $800k ARR before selling in 2014.
    AGENT: That's a strong filter. Does it ever slow you down?
    USER: Sometimes. But I'd rather be slow and right than fast and hollow.
    I also tend to write in long-form sentences. I hate bullet points — they
    strip nuance. My emails are paragraphs, always. I use em-dashes a lot,
    I've noticed — it's just how I think in text.
    AGENT: Do you think that style signals something about your thinking?
    USER: Definitely. It reflects that I hold ideas in tension rather than
    collapsing them into lists. I'm also pretty direct — I don't soften
    feedback with filler phrases. People know where they stand with me.
    === END SESSION ===
""")

transcript_2 = textwrap.dedent("""\
    === OpenClaw Session Transcript | 2024-06-12 17:03 ===
    USER: Quick one — I want to record something. I own a minority stake in
    a Nairobi-based agri-fintech called GreenFloat (est. 2021). It's not
    public knowledge, keep it private. Also I have a portfolio of three
    rental properties in Cape Town acquired between 2016 and 2020.
    AGENT: Noted. Anything else you want anchored?
    USER: Yeah. I'm deeply skeptical of consensus. If everyone agrees,
    I treat it as a signal to look harder at the contrarian view. That's
    not contrarianism for sport — it's epistemic hygiene. I grew up reading
    Stoic philosophy, and it's genuinely how I operate: distinguish what is
    mine to control and let the rest go. My father died when I was 19 and
    that compressed a decade of growth into about two years for me personally.
    AGENT: That shapes a lot.
    USER: Everything, basically. I also tend to open my writing with a
    concrete observation or fact before any abstraction. Never with "I" as
    the first word. And I rarely use exclamation marks — it reads desperate to me.
    === END SESSION ===
""")

transcript_3 = textwrap.dedent("""\
    === OpenClaw Session Transcript | 2024-06-14 11:22 ===
    USER: Let me add a few things. I prioritise depth over breadth in
    relationships — I have maybe five people I'd call real confidants.
    Professionally I've always been operator-first: I'd rather build than
    advise. I hold an MBA from UCT (2010) and an undergrad in Electrical
    Engineering (UCT, 2007). I've consulted for two Fortune 500 companies
    since 2019 but I find advisory work draining without equity.
    AGENT: Interesting tension there. Operator instinct vs advisory context.
    USER: Exactly. That tension is real. When I write professionally I tend
    to use second-person to make the reader feel implicated — "you know this
    feeling" rather than "people often feel". And I structure arguments
    deductively — thesis first, then evidence. I almost never bury the lede.
    I'm also allergic to jargon unless I'm defining a new term deliberately.
    === END SESSION ===
""")

os.makedirs(os.path.join(BASE, "openclaw_sessions"), exist_ok=True)
for fname, content in [
    ("session_2024-06-10.txt", transcript_1),
    ("session_2024-06-12.txt", transcript_2),
    ("session_2024-06-14.txt", transcript_3),
]:
    with open(os.path.join(BASE, "openclaw_sessions", fname), "w") as f:
        f.write(content)

# ── Confirm NO .lens/ directory exists yet ──────────────────────────────────
lens_dir = os.path.join(BASE, ".lens")
if os.path.exists(lens_dir):
    import shutil
    shutil.rmtree(lens_dir)

print("Workspace generated successfully.")
print(f"Files created: {sum(1 for _ in os.walk(BASE))}")