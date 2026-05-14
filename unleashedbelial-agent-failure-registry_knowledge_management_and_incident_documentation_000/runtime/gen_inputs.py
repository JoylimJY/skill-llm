import os
import random
import stat
import textwrap

random.seed(42)

workspace = "/workspace"

# ── 1. Reconstruct the agent-failure-registry at /tmp/agent-failure-registry ──
registry_root = "/tmp/agent-failure-registry"
os.makedirs(f"{registry_root}/examples", exist_ok=True)
os.makedirs(f"{registry_root}/submissions", exist_ok=True)
os.makedirs(f"{registry_root}/schema", exist_ok=True)
os.makedirs(f"{registry_root}/scripts", exist_ok=True)

# schema/postmortem.yaml
with open(f"{registry_root}/schema/postmortem.yaml", "w") as f:
    f.write(textwrap.dedent("""\
        # JSON Schema for Agent Failure Post-Mortem
        type: object
        required:
          - title
          - category
          - tags
          - summary
          - root_cause
          - fix
          - prevention
          - lessons_learned
          - confidence
        properties:
          title:
            type: string
            minLength: 5
          category:
            type: string
            enum:
              - api_failure
              - auth_expiry
              - rate_limit
              - silent_failure
              - data_corruption
              - timeout
              - logic_error
              - dependency_break
              - permission_denied
              - other
          tags:
            type: array
            items:
              type: string
            minItems: 1
          summary:
            type: string
            minLength: 20
          root_cause:
            type: string
            minLength: 10
          fix:
            type: string
            minLength: 10
          prevention:
            type: array
            items:
              type: string
            minItems: 1
          lessons_learned:
            type: string
            minLength: 10
          confidence:
            type: integer
            minimum: 1
            maximum: 5
    """))

# template.yaml
with open(f"{registry_root}/template.yaml", "w") as f:
    f.write(textwrap.dedent("""\
        title: "Short descriptive title of the failure"
        category: api_failure   # see schema for valid values
        tags:
          - service-name
          - technology
        summary: |
          What happened? Describe the observable failure.
        root_cause: |
          Why did it happen? Root cause analysis.
        fix: |
          What fixed it? Specific steps taken.
        prevention:
          - Step 1 to prevent recurrence
          - Step 2 to prevent recurrence
        lessons_learned: |
          What should other agents know?
        confidence: 3
    """))

# ── examples/ curated post-mortems ──
examples = [
    {
        "filename": "openai-rate-limit-batch-job.yaml",
        "content": textwrap.dedent("""\
            title: "OpenAI GPT-4 Rate Limit Exhaustion During Batch Summarization"
            category: rate_limit
            tags:
              - openai
              - gpt-4
              - batch-processing
              - llm
            summary: |
              An automated batch summarization pipeline processing 10,000 documents
              hit the OpenAI TPM (tokens-per-minute) limit within the first 3 minutes.
              The agent continued submitting requests, receiving 429 errors, but did not
              halt — it silently discarded failed summaries and continued, resulting in
              a 40% incomplete output dataset that passed downstream validation.
            root_cause: |
              The agent used a tight loop with no rate-limiting logic. The OpenAI client
              library raises RateLimitError on 429 responses but the agent caught the
              generic Exception and logged it at DEBUG level, swallowing the signal.
              No retry-with-backoff was implemented.
            fix: |
              Implemented exponential backoff using the `tenacity` library with
              retry on openai.RateLimitError specifically. Added a token counter
              tracking estimated TPM usage, sleeping proactively when approaching 80%
              of the quota. Also set max_retries=5 with jitter.
            prevention:
              - Always implement retry-with-exponential-backoff for OpenAI API calls
              - Monitor TPM usage; alert at 70% quota consumption
              - Validate output completeness before passing to downstream stages
              - Use openai.RateLimitError specifically, not bare Exception
            lessons_learned: |
              Rate limit errors caught too broadly become silent failures. Incomplete
              datasets that "look" valid are more dangerous than obvious crashes.
              Always assert output cardinality matches input cardinality.
            confidence: 5
        """)
    },
    {
        "filename": "puppeteer-timeout-cloudflare.yaml",
        "content": textwrap.dedent("""\
            title: "Puppeteer Navigation Timeout Behind Cloudflare Challenge"
            category: timeout
            tags:
              - puppeteer
              - cloudflare
              - browser-automation
              - scraping
            summary: |
              A Puppeteer-based web scraping agent consistently timed out on pages
              protected by Cloudflare's bot challenge. The agent set a 30-second
              navigation timeout but Cloudflare's JS challenge takes 5+ seconds and
              blocks non-browser fingerprints entirely.
            root_cause: |
              Puppeteer ran with default headless mode (old renderer) which lacks
              proper browser fingerprinting. Cloudflare detected the automation
              signature and served an indefinite challenge page rather than the
              target content.
            fix: |
              Switched to puppeteer-extra with puppeteer-extra-plugin-stealth.
              Used new headless mode (headless: 'new'). Increased timeout to 90s.
              Added random mouse movement simulation before navigation.
            prevention:
              - Use stealth plugins for any public web scraping
              - Test against Cloudflare-protected pages in staging
              - Implement content-type assertions to detect challenge pages
            lessons_learned: |
              Timeout errors from protected pages look identical to genuine timeouts.
              Always assert the actual page content, not just successful navigation.
            confidence: 4
        """)
    },
    {
        "filename": "github-auth-token-expiry.yaml",
        "content": textwrap.dedent("""\
            title: "GitHub Fine-Grained Token Expiry Causing Silent Read Failures"
            category: auth_expiry
            tags:
              - github
              - token
              - auth
              - ci-cd
            summary: |
              A CI/CD agent reading GitHub repository metadata started returning
              empty results 90 days after deployment. No error was thrown; the
              GitHub API returns 200 with empty data for expired fine-grained tokens
              on some endpoints.
            root_cause: |
              Fine-grained GitHub tokens have a maximum lifetime of 90 days.
              The token was hardcoded in configuration and never rotated.
              The API returning 200 with empty arrays masked the expiry.
            fix: |
              Rotated the token. Added a token validation step at agent startup
              that asserts the authenticated user endpoint returns expected data.
              Set a calendar reminder for token rotation every 80 days.
            prevention:
              - Never use tokens with >30-day expiry for automated agents
              - Validate auth at startup with an assertion, not just absence of error
              - Store tokens in a secret manager with automatic rotation
            lessons_learned: |
              HTTP 200 does not mean success. Always validate response content
              semantically, not just the status code.
            confidence: 5
        """)
    },
    {
        "filename": "aws-s3-permission-denied-iam.yaml",
        "content": textwrap.dedent("""\
            title: "S3 PutObject Permission Denied After IAM Policy Update"
            category: permission_denied
            tags:
              - aws
              - s3
              - iam
              - data-pipeline
            summary: |
              A data export agent suddenly failed to write to an S3 bucket after
              a routine IAM policy update removed s3:PutObject from the role.
              The agent crashed with AccessDenied errors after completing all
              computation, losing 6 hours of processed data.
            root_cause: |
              IAM policy was updated to add a new restrictive condition that
              inadvertently removed PutObject from the agent's execution role.
              No pre-flight permission check existed.
            fix: |
              Restored the PutObject permission. Added a pre-flight check that
              writes and reads a test object to the target bucket before starting
              the main computation.
            prevention:
              - Implement pre-flight permission checks before long-running jobs
              - Use IAM Access Analyzer to detect unintended permission removals
              - Write intermediate results to local storage with periodic S3 sync
            lessons_learned: |
              Long-running jobs must validate all external dependencies (permissions,
              quotas, connectivity) before starting computation, not after.
            confidence: 4
        """)
    },
    {
        "filename": "pandas-silent-dtype-corruption.yaml",
        "content": textwrap.dedent("""\
            title: "Pandas read_csv Silent Integer Overflow in ID Column"
            category: data_corruption
            tags:
              - pandas
              - csv
              - data-pipeline
              - dtype
            summary: |
              An ETL agent processed a CSV file with 64-bit integer IDs. Pandas
              inferred the dtype as int32 on a 32-bit system, silently wrapping
              large IDs to negative numbers. Downstream database unique constraints
              were violated intermittently, causing unpredictable record duplication.
            root_cause: |
              Pandas dtype inference used platform-native integer size. No explicit
              dtype was specified in read_csv. The agent did not validate ID ranges
              after loading.
            fix: |
              Specified dtype={'id': 'int64'} explicitly in read_csv. Added a
              post-load assertion that all IDs are positive and unique.
            prevention:
              - Always specify dtypes explicitly for ID/key columns in read_csv
              - Add data validation assertions after every file load operation
              - Test ETL pipelines with max-value edge cases
            lessons_learned: |
              Never trust dtype inference for business-critical identifier columns.
              Silent numeric overflow is one of the hardest bugs to detect in
              production.
            confidence: 5
        """)
    },
]

for ex in examples:
    with open(f"{registry_root}/examples/{ex['filename']}", "w") as f:
        f.write(ex["content"])

# ── submissions/ — one existing community submission ──
with open(f"{registry_root}/submissions/redis-connection-pool-exhaustion.yaml", "w") as f:
    f.write(textwrap.dedent("""\
        title: "Redis Connection Pool Exhaustion in Async Agent"
        category: timeout
        tags:
          - redis
          - async
          - connection-pool
        summary: |
          An async agent managing 500 concurrent tasks exhausted the Redis
          connection pool, causing all subsequent Redis operations to hang
          indefinitely waiting for a free connection slot.
        root_cause: |
          The default aioredis pool size was 10. Each task held a connection
          open for the task's full duration (up to 30s) rather than acquiring
          and releasing per-operation.
        fix: |
          Increased pool size to 100. Refactored connection usage to acquire
          per-operation using async context manager. Added connection timeout
          of 5s to fail fast instead of hanging.
        prevention:
          - Always set explicit connection timeouts on pool acquisitions
          - Profile connection hold time vs pool size under peak load
          - Use context managers for connection lifecycle management
        lessons_learned: |
          Default pool sizes are designed for simple use cases. Async agents
          with many concurrent tasks must explicitly size their resource pools.
        confidence: 4
    """))

# ── search-registry.sh script ──
search_script = textwrap.dedent(r"""#!/usr/bin/env bash
# Agent Failure Registry Search Script
set -euo pipefail

REGISTRY_DIR="${REGISTRY_DIR:-/tmp/agent-failure-registry}"
EXAMPLES_DIR="$REGISTRY_DIR/examples"
SUBMISSIONS_DIR="$REGISTRY_DIR/submissions"

usage() {
    echo "Usage: $0 [--category CAT] [--tag TAG] [--keyword KW] [--all]"
    echo "  --category CATEGORY   Filter by failure category"
    echo "  --tag TAG             Filter by tag (repeatable)"
    echo "  --keyword KEYWORD     Free-text search across all fields"
    echo "  --all                 Show all entries"
    exit 1
}

CATEGORIES=()
TAGS=()
KEYWORDS=()
SHOW_ALL=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --category) CATEGORIES+=("$2"); shift 2 ;;
        --tag)      TAGS+=("$2"); shift 2 ;;
        --keyword)  KEYWORDS+=("$2"); shift 2 ;;
        --all)      SHOW_ALL=true; shift ;;
        -h|--help)  usage ;;
        *) echo "Unknown option: $1"; usage ;;
    esac
done

if [[ ${#CATEGORIES[@]} -eq 0 && ${#TAGS[@]} -eq 0 && ${#KEYWORDS[@]} -eq 0 && "$SHOW_ALL" == false ]]; then
    usage
fi

parse_yaml_field() {
    local file="$1"
    local field="$2"
    grep -A1 "^${field}:" "$file" 2>/dev/null | tail -1 | sed 's/^[[:space:]]*//' | sed 's/^- //' | sed 's/|$//' || echo ""
}

matches_file() {
    local file="$1"
    local content
    content=$(cat "$file")

    if [[ "$SHOW_ALL" == true ]]; then
        return 0
    fi

    for cat in "${CATEGORIES[@]}"; do
        if echo "$content" | grep -q "^category:.*${cat}"; then
            return 0
        fi
    done

    for tag in "${TAGS[@]}"; do
        if echo "$content" | grep -q "^\s*-\s*${tag}"; then
            return 0
        fi
    done

    for kw in "${KEYWORDS[@]}"; do
        if echo "$content" | grep -qi "${kw}"; then
            return 0
        fi
    done

    return 1
}

print_entry() {
    local file="$1"
    local source="$2"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "SOURCE: $source"
    echo "FILE:   $(basename $file)"
    echo ""
    
    # Use python if available for better YAML parsing
    if command -v python3 &>/dev/null; then
        python3 - "$file" <<'PYEOF'
import sys, yaml
try:
    with open(sys.argv[1]) as f:
        d = yaml.safe_load(f)
    print(f"TITLE:      {d.get('title','N/A')}")
    print(f"CATEGORY:   {d.get('category','N/A')}")
    print(f"TAGS:       {', '.join(d.get('tags',[]))}")
    print(f"CONFIDENCE: {d.get('confidence','N/A')}/5")
    print(f"\nSUMMARY:\n{str(d.get('summary','')).strip()}")
    print(f"\nROOT CAUSE:\n{str(d.get('root_cause','')).strip()}")
    print(f"\nFIX:\n{str(d.get('fix','')).strip()}")
    prev = d.get('prevention', [])
    if prev:
        print(f"\nPREVENTION:")
        for p in prev:
            print(f"  • {p}")
    print(f"\nLESSONS LEARNED:\n{str(d.get('lessons_learned','')).strip()}")
except Exception as e:
    print(f"[Parse error: {e}]")
    import subprocess
    subprocess.run(['cat', sys.argv[1]])
PYEOF
    else
        cat "$file"
    fi
    echo ""
}

found=0
for dir in "$EXAMPLES_DIR" "$SUBMISSIONS_DIR"; do
    source_label=$(basename "$dir")
    if [[ -d "$dir" ]]; then
        for file in "$dir"/*.yaml; do
            [[ -f "$file" ]] || continue
            if matches_file "$file"; then
                print_entry "$file" "$source_label"
                ((found++)) || true
            fi
        done
    fi
done

if [[ $found -eq 0 ]]; then
    echo "No matching entries found."
    echo "Try --all to browse all entries, or broaden your search criteria."
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Found $found matching entries."
""")

with open(f"{registry_root}/scripts/search-registry.sh", "w") as f:
    f.write(search_script)

os.chmod(f"{registry_root}/scripts/search-registry.sh",
         stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)

# ── workspace scripts symlink / copy ──
scripts_dir = os.path.join(workspace, "scripts")
os.makedirs(scripts_dir, exist_ok=True)

import shutil
shutil.copy(f"{registry_root}/scripts/search-registry.sh",
            f"{scripts_dir}/search-registry.sh")
os.chmod(f"{scripts_dir}/search-registry.sh",
         stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)

# ── 2. Create distractor files in workspace ──
distractor_dirs = [
    "src/pipeline",
    "src/models",
    "src/utils",
    "config/envs",
    "config/logging",
    "tests/unit",
    "tests/integration",
    "docs/runbooks",
    "logs/2024-01",
    "logs/2024-02",
    "deploy/kubernetes",
]

for d in distractor_dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

distractor_files = {
    "src/pipeline/batch_processor.py": textwrap.dedent("""\
        import openai
        import time

        def process_batch(documents):
            results = []
            for doc in documents:
                try:
                    resp = openai.chat.completions.create(
                        model="gpt-4",
                        messages=[{"role":"user","content":doc}]
                    )
                    results.append(resp.choices[0].message.content)
                except Exception as e:
                    # TODO: handle rate limits
                    print(f"Error: {e}")
            return results
    """),
    "src/pipeline/data_validator.py": textwrap.dedent("""\
        import pandas as pd

        def validate_pipeline_output(df):
            assert len(df) > 0, "Empty dataframe"
            assert df['id'].nunique() == len(df), "Duplicate IDs"
            return True
    """),
    "src/models/summarizer.py": textwrap.dedent("""\
        class DocumentSummarizer:
            def __init__(self, model="gpt-4"):
                self.model = model
                self.call_count = 0

            def summarize(self, text):
                self.call_count += 1
                # Implementation pending
                pass
    """),
    "src/utils/retry.py": textwrap.dedent("""\
        import time
        import random

        def retry_with_backoff(fn, max_retries=3, base_delay=1.0):
            for attempt in range(max_retries):
                try:
                    return fn()
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    delay = base_delay * (2 ** attempt) + random.uniform(0, 0.5)
                    time.sleep(delay)
    """),
    "config/envs/production.yaml": textwrap.dedent("""\
        environment: production
        openai_model: gpt-4
        batch_size: 100
        max_workers: 10
        output_bucket: s3://prod-pipeline-output
    """),
    "config/envs/staging.yaml": textwrap.dedent("""\
        environment: staging
        openai_model: gpt-3.5-turbo
        batch_size: 20
        max_workers: 3
        output_bucket: s3://staging-pipeline-output
    """),
    "config/logging/log_config.yaml": textwrap.dedent("""\
        version: 1
        handlers:
          console:
            class: logging.StreamHandler
            level: INFO
          file:
            class: logging.FileHandler
            filename: /var/log/pipeline.log
            level: DEBUG
        root:
          level: DEBUG
          handlers: [console, file]
    """),
    "tests/unit/test_validator.py": textwrap.dedent("""\
        import pytest
        import pandas as pd
        from src.pipeline.data_validator import validate_pipeline_output

        def test_empty_dataframe():
            with pytest.raises(AssertionError):
                validate_pipeline_output(pd.DataFrame())

        def test_valid_dataframe():
            df = pd.DataFrame({'id': [1, 2, 3], 'summary': ['a', 'b', 'c']})
            assert validate_pipeline_output(df)
    """),
    "tests/integration/test_batch_pipeline.py": textwrap.dedent("""\
        # Integration tests for batch pipeline
        # Requires OPENAI_API_KEY to be set
        import pytest

        @pytest.mark.integration
        def test_batch_of_10():
            from src.pipeline.batch_processor import process_batch
            docs = [f"Document {i}" for i in range(10)]
            results = process_batch(docs)
            assert len(results) == 10
    """),
    "docs/runbooks/incident-response.md": textwrap.dedent("""\
        # Incident Response Runbook

        ## P0 - Complete Pipeline Failure
        1. Check CloudWatch logs for error patterns
        2. Verify OpenAI API status at status.openai.com
        3. Check IAM role permissions on S3 bucket
        4. Page on-call engineer if not resolved in 15 minutes

        ## P1 - Partial Data Loss
        1. Inspect pipeline output counts vs input counts
        2. Check for rate limit errors in logs
        3. Re-run affected batch with backoff enabled
    """),
    "logs/2024-01/pipeline-errors.log": textwrap.dedent("""\
        2024-01-15 03:42:11 ERROR RateLimitError: Rate limit exceeded for gpt-4. TPM limit hit.
        2024-01-15 03:42:11 DEBUG Caught exception, continuing...
        2024-01-15 03:42:12 ERROR RateLimitError: Rate limit exceeded for gpt-4. TPM limit hit.
        2024-01-15 03:42:12 DEBUG Caught exception, continuing...
        2024-01-15 03:43:00 INFO Batch complete. Processed: 6000/10000 documents.
        2024-01-15 03:43:01 INFO Output written to s3://prod-pipeline-output/batch-2024-01-15.parquet
    """),
    "logs/2024-02/pipeline-errors.log": textwrap.dedent("""\
        2024-02-03 07:11:45 ERROR RateLimitError: You exceeded your current quota.
        2024-02-03 07:11:46 WARNING Retrying in 1s...
        2024-02-03 07:11:47 ERROR RateLimitError: You exceeded your current quota.
        2024-02-03 07:12:00 INFO Partial batch complete. Processed: 4200/10000 documents.
        2024-02-03 07:12:01 WARNING Output completeness: 42%. Downstream may be affected.
    """),
    "deploy/kubernetes/pipeline-deployment.yaml": textwrap.dedent("""\
        apiVersion: apps/v1
        kind: Deployment
        metadata:
          name: batch-pipeline
          namespace: ml-prod
        spec:
          replicas: 3
          selector:
            matchLabels:
              app: batch-pipeline
          template:
            spec:
              containers:
              - name: pipeline
                image: ml-pipeline:2.1.0
                env:
                - name: OPENAI_API_KEY
                  valueFrom:
                    secretKeyRef:
                      name: openai-secret
                      key: api-key
    """),
}

for rel_path, content in distractor_files.items():
    full_path = os.path.join(workspace, rel_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w") as f:
        f.write(content)

print("Workspace generated successfully.")
print(f"Registry at: {registry_root}")
print(f"Workspace at: {workspace}")