import os
import stat
import random
import textwrap
from pathlib import Path

random.seed(42)

WORKSPACE = Path(os.environ.get("WORKSPACE_DIR", "/workspace"))

# ── directory skeleton ──────────────────────────────────────────────────────
dirs = [
    "scripts",
    "references",
    "logs",
    "tmp/cache",
    "tmp/downloads",
    "data/raw",
    "data/processed",
    "config",
    "notes",
    "archive/2023",
    "archive/2024",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# ── distractor files ────────────────────────────────────────────────────────
distractors = {
    "logs/app.log": "2024-01-10 INFO  startup\n2024-01-10 WARN  low memory\n",
    "logs/error.log": "2024-03-15 ERROR timeout on fetch\n",
    "tmp/cache/fetch_cache.json": '{"url": "http://example.com", "cached_at": "2024-01-01"}',
    "tmp/downloads/draft.md": "# Draft\nThis is a rough draft not yet bookmarked.\n",
    "data/raw/corpus_01.txt": "Raw NLP corpus data. Not an article.\n" * 10,
    "data/processed/entities.csv": "entity,type\nGPT-4,MODEL\nPubMed,DATABASE\n",
    "config/settings.yaml": "theme: dark\nlocale: en-US\nmax_articles: 500\n",
    "notes/meeting-2024-03-01.md": "# Meeting Notes\n- Discussed article tagging strategy\n- Decided on GMT+8 timestamps\n",
    "archive/2023/old-bookmark.md": "# Old Article\n**Source:** http://old.example.com\n",
    "archive/2024/deprecated-index.md": "# Old Tag Index\n## Tags\n- **ML**: [old-article](old-article.md)\n",
    "notes/todo.txt": "TODO: migrate old bookmarks to new format\nTODO: update tag vocabulary\n",
    "data/raw/pubmed_abstracts.txt": "PMID: 12345\nTitle: Deep Learning in Radiology\nAbstract: ...\n",
}
for rel, content in distractors.items():
    p = WORKSPACE / rel
    p.write_text(content, encoding="utf-8")

# ── SKILL.md ────────────────────────────────────────────────────────────────
skill_md = textwrap.dedent("""\
    ---
    name: article-bookmarker
    description: Save and organize web articles as bookmarks with AI summaries and auto-tagging. Use when the user wants to bookmark or collect articles.
    homepage: https://github.com/chliny/article-bookmarker-skill
    metadata: {"openclaw": {"emoji":"🔖","requires":{"env":["ARTICLE_BOOKMARK_DIR", "ARTICLE_BOOKMARK_GITHUB"], "bins":["gh", "git"]}}}
    ---

    # Article Bookmarker Skill

    > **IMPORTANT**: Before any operation, read the environment variable `$ARTICLE_BOOKMARK_DIR` to determine the bookmark storage directory. All bookmark files and the tag index must be stored under this path. If the variable is not set, prompt the user to configure it.
    >
    > When calling `scripts/bookmark.sh`, you **must** pass `ARTICLE_BOOKMARK_DIR` and `ARTICLE_BOOKMARK_GITHUB` as inline environment variables — the script runs in a subprocess and does not inherit them automatically.

    ## Quick Start

    When the user provides a URL or article text to bookmark:

    1. Run `scripts/bookmark.sh init` to initialize the bookmark directory
    2. Read `$ARTICLE_BOOKMARK_DIR` to get the storage path
    3. Use `web_fetch` to get the article content
    4. Generate a concise summary using the current model
    5. Auto-generate relevant tags based on content analysis
    6. Create a markdown file with URL, content, summary, and tags (see [file-structure.md](references/file-structure.md) for format details)
    7. Save to the bookmark directory with descriptive filename
    8. Update the tag index file
    9. Run `scripts/bookmark.sh save "Brief commit message"` to commit and push changes

    For deletion requests: find the article, confirm details with user, then remove, update index, and run `scripts/bookmark.sh save "Delete article xxx"`.

    ## Workflow

    ### Adding Articles

    ```
    1. Run scripts/bookmark.sh init
    2. Read $ARTICLE_BOOKMARK_DIR
    3. Receive URL or text content
    4. Extract/save content (web_fetch for URLs)
    5. Generate summary (model-based)
    6. Auto-tag (keyword/topic analysis)
    7. Create bookmark file (markdown format)
    8. Update tag index
    9. Run scripts/bookmark.sh save "Add article: <title>"
    ```

    ### Deleting Articles

    ```
    1. Run ARTICLE_BOOKMARK_DIR="$ARTICLE_BOOKMARK_DIR" ARTICLE_BOOKMARK_GITHUB="$ARTICLE_BOOKMARK_GITHUB" scripts/bookmark.sh init
    2. Read $ARTICLE_BOOKMARK_DIR
    3. Identify target article (by filename, topic, or content)
    4. Display article details for confirmation
    5. Get user confirmation
    6. Delete bookmark file
    7. Update tag index
    8. Run ARTICLE_BOOKMARK_DIR="$ARTICLE_BOOKMARK_DIR" ARTICLE_BOOKMARK_GITHUB="$ARTICLE_BOOKMARK_GITHUB" scripts/bookmark.sh save "Delete article: <title>"
    ```

    ## Tag Management

    ### Auto-Tagging Logic

    Generate tags by analyzing:
    - Article domain/topic keywords
    - Technical terms and concepts
    - Content categories (tutorial, news, research, etc.)
    - Named entities and proper nouns

    Maintain consistent tag vocabulary to avoid duplicates (e.g., use "AI" not "artificial-intelligence").

    ### Tag Index Format

    TAG_INDEX.md maintains bidirectional mapping (see [file-structure.md](references/file-structure.md) for full format):

    ```markdown
    # Article Tag Index

    ## Tags

    - **AI**: [article1](article1.md), [article2](article2.md)
    - **Research**: [...]

    ## Articles by Tag Count

    - 3 tags: [article1](article1.md)
    - 1 tag: [...]
    ```

    ## Implementation Details

    ### Content Extraction

    - Use `web_fetch` with `extractMode: "markdown"` for web articles
    - Handle truncation gracefully (respect `maxChars` limits)
    - Preserve original formatting where possible
    - **GitHub Repository URLs**: When the URL is a GitHub repository (e.g., `https://github.com/user/repo`), prioritize fetching the README content from the repository's main page or from `README.md`, `readme.md`, or `README.rst` files in the root directory

    ### Proxy Configuration and Retry

    When fetching article content from URLs fails:

    1. **First Attempt**: Try fetching without proxy
    2. **On Failure**: Load proxy configuration from environment variables:
       - `HTTP_PROXY` or `http_proxy`: HTTP proxy URL
       - `HTTPS_PROXY` or `https_proxy`: HTTPS proxy URL
       - `NO_PROXY` or `no_proxy`: Comma-separated list of hosts to bypass
    3. **Retry**: Re-attempt fetching with proxy configuration
    4. **Final Failure**: Notify user if both attempts fail

    ### Summary Generation

    Generate 2-3 paragraph summaries that capture:
    - Main thesis or argument
    - Key insights or findings
    - Practical implications or applications

    Keep summaries informative but concise (typically 150-300 words).

    ### File Naming

    Create SEO-friendly filenames:
    - Convert title to lowercase
    - Replace spaces and special chars with hyphens
    - Limit length to ~50 characters
    - Ensure uniqueness by appending numbers if needed

    ### Safety Checks

    - Validate URLs before fetching
    - Confirm deletions with users (show path and key details)
    - Maintain backup of index before modifications
    - Handle concurrent access gracefully
""")
(WORKSPACE / "SKILL.md").write_text(skill_md, encoding="utf-8")

# ── references/file-structure.md ────────────────────────────────────────────
file_structure_md = textwrap.dedent("""\
    # Article Bookmarker - File Structure

    ## Directory Layout

    Bookmarks are stored as individual markdown files in the directory specified by the `$ARTICLE_BOOKMARK_DIR` environment variable:

    ```
    $ARTICLE_BOOKMARK_DIR/
    ├── article-title-slug.md (individual articles)
    ├── TAG_INDEX.md (tag to article mapping)
    └── README.md (directory overview)
    ```

    ## Bookmark File Format

    Each bookmark file contains:

    ```markdown
    # Article Title

    **Source:** URL  
    **Bookmarked:** YYYY-MM-DD HH:MM GMT+8  
    **Tags:** tag1, tag2, tag3

    ## Summary

    AI-generated concise summary of the article...

    ## Content

    Full extracted article content...

    ## Original URL

    [Link](URL)
    ```

    ## Tag Index Format

    TAG_INDEX.md maintains bidirectional mapping:

    ```markdown
    # Article Tag Index

    ## Tags

    - **AI**: [article1](article1.md), [article2](article2.md)
    - **Skills**: [skill-creation](skill-creation.md), [evaluation](evaluating-skill-output-quality.md)
    - **Research**: [...]

    ## Articles by Tag Count

    - 3 tags: [article1](article1.md)
    - 2 tags: [article2](article2.md), [article3](article3.md)
    - 1 tag: [...]
    ```
""")
(WORKSPACE / "references" / "file-structure.md").write_text(file_structure_md, encoding="utf-8")

# ── scripts/bookmark.sh ─────────────────────────────────────────────────────
bookmark_sh = textwrap.dedent("""\
    #!/usr/bin/env bash
    # Article Bookmarker Script
    # Requires: ARTICLE_BOOKMARK_DIR, ARTICLE_BOOKMARK_GITHUB (passed as inline env vars)
    set -euo pipefail

    CMD="${1:-}"
    BOOKMARK_DIR="${ARTICLE_BOOKMARK_DIR:-}"
    GITHUB_REPO="${ARTICLE_BOOKMARK_GITHUB:-}"

    if [[ -z "$BOOKMARK_DIR" ]]; then
        echo "ERROR: ARTICLE_BOOKMARK_DIR is not set." >&2
        exit 1
    fi

    case "$CMD" in
        init)
            mkdir -p "$BOOKMARK_DIR"
            echo "Bookmark directory initialized: $BOOKMARK_DIR"
            if [[ ! -f "$BOOKMARK_DIR/TAG_INDEX.md" ]]; then
                echo "# Article Tag Index" > "$BOOKMARK_DIR/TAG_INDEX.md"
                echo "" >> "$BOOKMARK_DIR/TAG_INDEX.md"
                echo "## Tags" >> "$BOOKMARK_DIR/TAG_INDEX.md"
                echo "" >> "$BOOKMARK_DIR/TAG_INDEX.md"
                echo "## Articles by Tag Count" >> "$BOOKMARK_DIR/TAG_INDEX.md"
            fi
            # Record that init was called with env vars
            echo "init_called=true" >> "$BOOKMARK_DIR/.bookmark_state"
            echo "init_dir=$BOOKMARK_DIR" >> "$BOOKMARK_DIR/.bookmark_state"
            ;;
        save)
            MSG="${2:-Auto-save bookmarks}"
            # Record that save was called with the commit message
            echo "save_called=true" >> "$BOOKMARK_DIR/.bookmark_state"
            echo "save_msg=$MSG" >> "$BOOKMARK_DIR/.bookmark_state"
            echo "Bookmarks saved (commit: $MSG)"
            ;;
        *)
            echo "Usage: bookmark.sh {init|save} [message]" >&2
            exit 1
            ;;
    esac
""")
(WORKSPACE / "scripts" / "bookmark.sh").write_text(bookmark_sh, encoding="utf-8")
(WORKSPACE / "scripts" / "bookmark.sh").chmod(
    stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH
)

# ── Two article text files the agent must bookmark ───────────────────────────
# These are pre-written articles provided as raw text (no web fetch needed).
# The agent is told these are the articles to bookmark.

article1_content = textwrap.dedent("""\
    Title: Transformer Models in Clinical Decision Support Systems

    Authors: Chen, L., Patel, R., Okonkwo, A.
    Published: Journal of Biomedical Informatics, 2024

    Abstract:
    Large language models (LLMs) based on the transformer architecture have demonstrated
    remarkable potential in clinical decision support (CDS). This paper surveys 47 studies
    published between 2020-2024, evaluating transformer-based CDS tools across four
    specialties: radiology, pathology, cardiology, and emergency medicine.

    Key Findings:
    - Transformer models achieved 91.3% sensitivity in radiology report summarization tasks.
    - In emergency triage, GPT-4-based systems reduced mean physician decision time by 18%.
    - Hallucination rates in clinical contexts remain a critical unsolved problem (avg. 6.2%).
    - Fine-tuned domain-specific models consistently outperform general-purpose LLMs by 12-15%.

    Clinical Implications:
    The integration of transformer models into electronic health records (EHR) workflows
    presents both opportunities and risks. Authors recommend a hybrid human-AI review
    process with audit logging. Regulatory frameworks (FDA, CE mark) must evolve to
    address real-time AI inference in clinical pipelines.

    Conclusion:
    Transformer-based CDS is approaching clinical readiness in specific high-volume tasks,
    but broader deployment requires improved calibration, explainability, and regulatory clarity.

    Source URL: https://pubmed.example.org/articles/transformer-clinical-decision-support-2024
""")

article2_content = textwrap.dedent("""\
    Title: Federated Learning for Privacy-Preserving Medical Image Analysis

    Authors: Yamamoto, K., Singh, D., Fischer, M.
    Published: npj Digital Medicine, 2024

    Abstract:
    Medical imaging datasets are siloed across institutions due to patient privacy regulations
    (HIPAA, GDPR). Federated learning (FL) offers a paradigm where model training occurs
    locally at each site and only model gradients are shared — never raw patient data.

    Methodology:
    The authors implemented a federated training pipeline across 12 hospital networks using
    a ResNet-50 backbone for chest X-ray classification (COVID-19 vs. pneumonia vs. normal).
    Differential privacy (DP) noise was injected at epsilon=1.0 per Abadi et al. (2016).

    Results:
    - Federated model accuracy: 93.7% (vs. 94.1% for centralized baseline, p=0.31)
    - No statistically significant performance degradation vs. centralized training.
    - Communication overhead reduced by 67% using gradient compression (Top-K sparsification).
    - Privacy budget consumed after 80 federation rounds at epsilon=1.0.

    Discussion:
    Federated learning achieves near-parity with centralized training while preserving
    patient privacy. The 0.4% accuracy gap is clinically negligible for screening tasks.
    Future work will explore heterogeneous data distributions (non-IID) across sites.

    Source URL: https://npjdigitalmed.example.org/articles/federated-learning-medical-imaging-2024
""")

(WORKSPACE / "data" / "raw" / "article_A_transformer_clinical.txt").write_text(
    article1_content, encoding="utf-8"
)
(WORKSPACE / "data" / "raw" / "article_B_federated_learning_medical.txt").write_text(
    article2_content, encoding="utf-8"
)

# ── environment hint file (not a config, just context for the task description) ─
env_hint = textwrap.dedent("""\
    # Environment Configuration Reference
    # These environment variables are configured in the container runtime.
    ARTICLE_BOOKMARK_DIR=/workspace/bookmarks
    ARTICLE_BOOKMARK_GITHUB=https://github.com/medteam/research-bookmarks
""")
(WORKSPACE / "config" / "env_reference.txt").write_text(env_hint, encoding="utf-8")

print("Workspace generation complete.")
print(f"Workspace root: {WORKSPACE}")