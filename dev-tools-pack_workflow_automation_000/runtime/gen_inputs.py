import os
import random
import stat

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# --- Create distractor directory structure ---
dirs = [
    "docs/internal/briefs",
    "docs/internal/reports",
    "docs/public/announcements",
    "src/pipeline/stages",
    "src/pipeline/config",
    "src/utils",
    "assets/templates",
    "assets/icons",
    "output/drafts",
    "output/archive",
    "config/env",
    "scripts/legacy",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# --- Distractor files ---
distractor_files = {
    "docs/internal/reports/q3_metrics.md": "# Q3 Social Metrics\n\nEngagement down 12%.\nReach: 450K\nImpressions: 1.2M\n",
    "docs/public/announcements/v2_release.md": "# Version 2.0 Released\n\nNew features: CI/CD integration, auto-scaling, observability.\n",
    "src/pipeline/stages/fetch.py": "# fetch stage\nimport requests\n\ndef fetch(url): return requests.get(url).text\n",
    "src/pipeline/stages/transform.py": "# transform stage\ndef transform(data): return data.strip().lower()\n",
    "src/pipeline/config/settings.yaml": "pipeline:\n  timeout: 30\n  retries: 3\n  output_format: json\n",
    "src/utils/helpers.py": "def slugify(s): return s.lower().replace(' ', '-')\n",
    "assets/templates/email_template.html": "<html><body><h1>Hello {name}</h1></body></html>\n",
    "assets/icons/logo.svg": "<svg viewBox='0 0 100 100'><circle cx='50' cy='50' r='50'/></svg>\n",
    "config/env/production.env": "ENV=production\nDEBUG=false\nMAX_WORKERS=8\n",
    "config/env/staging.env": "ENV=staging\nDEBUG=true\nMAX_WORKERS=2\n",
    "scripts/legacy/old_thread_maker.sh": "#!/bin/bash\n# DEPRECATED: do not use\necho 'This script is deprecated'\n",
    "output/archive/thread_2023_01.txt": "Old archived thread content from 2023.\n",
    "docs/internal/briefs/product_roadmap.md": (
        "# Product Roadmap Brief - Q4\n\n"
        "Focus areas: Kubernetes orchestration, GitOps workflows, infrastructure-as-code.\n"
        "Key milestones: Helm chart publishing, Terraform module registry, Argo CD integration.\n"
        "Target audience: Platform engineers and SREs.\n"
    ),
}

for path, content in distractor_files.items():
    full_path = os.path.join(workspace, path)
    with open(full_path, "w") as f:
        f.write(content)

# --- THE MAIN INPUT: a technical brief file the agent must process ---
brief_content = """\
# DevOps Automation Technical Brief

## Overview
Modern DevOps automation is transforming how engineering teams ship software.
Infrastructure-as-code, CI/CD pipelines, and container orchestration are now
table stakes for competitive engineering organizations.

## Key Concepts

### Infrastructure as Code (IaC)
- Terraform and Pulumi for cloud resource provisioning
- Declarative configuration eliminates configuration drift
- Version-controlled infrastructure enables rollback and audit trails

### CI/CD Pipelines
- GitHub Actions, GitLab CI, and Jenkins as leading platforms
- Automated testing gates prevent regressions
- Blue-green and canary deployments reduce release risk

### Container Orchestration
- Kubernetes as the de facto orchestration standard
- Helm charts for repeatable application packaging
- Service meshes (Istio, Linkerd) for observability and traffic control

## Business Impact
Organizations adopting full DevOps automation report:
- 60% reduction in deployment failures
- 80% faster mean time to recovery (MTTR)
- 4x increase in deployment frequency

## Conclusion
DevOps automation is not optional for teams that need to move fast and stay reliable.
Investing in the right toolchain and practices pays dividends across the software lifecycle.
"""

brief_path = os.path.join(workspace, "docs/internal/briefs/devops_automation_brief.md")
with open(brief_path, "w") as f:
    f.write(brief_content)

# --- The tweet thread generator script (as provided in SKILL.md) ---
generator_script = r"""#!/bin/bash

# Tweet Thread Generator
# Usage: tweet-thread-generator [text|url|file] [content] [options]

set -e

SOURCE="${1:-}"
CONTENT="${2:-}"

# Parse options
TOPIC=""
LENGTH="auto"
TONE="educational"
FORMAT="thread"

while [[ $# -gt 0 ]]; do
    case $1 in
        --topic|-t)
            TOPIC="$2"
            shift 2
            ;;
        --length|-l)
            LENGTH="$2"
            shift 2
            ;;
        --tone)
            TONE="$2"
            shift 2
            ;;
        --format|-f)
            FORMAT="$2"
            shift 2
            ;;
        *)
            shift
            ;;
    esac
done

# Color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${BLUE}🐦 Tweet Thread Generator${NC}"
echo ""

# Default content if not provided
if [ -z "$CONTENT" ]; then
    CONTENT="$SOURCE"
    SOURCE="text"
fi

case "$SOURCE" in
    text|url|file|interactive)
        echo "📝 Generating thread from: $SOURCE"
        ;;
    *)
        CONTENT="$SOURCE"
        SOURCE="text"
        ;;
esac

# Generate sample thread
cat << 'HEADER'
---

🧵 THREAD: TOPIC_PLACEHOLDER

(n=1)

START_PLACEHOLDER

#Hashtags

---

(n=2)

CONTENT_PLACEHOLDER

#Hashtags

---

(n=3)

MORE_CONTENT_PLACEHOLDER

#Hashtags

---

HEADER

cat << SUMMARY

### 📊 Thread Summary

| Metric | Value |
|--------|-------|
| Tweets | 3 |
| Characters | ~900 |
| Est. Impressions | 5K-10K |
| Engagement Rate | ~3-5% |

### 🏷️ Suggested Hashtags

#TOPIC_PLACEHOLDER #TechTwitter #Programming #Developer

### 💡 Tips for Maximum Engagement

1. 第一个推文最关键 - 用吸引眼球的开头
2. 添加相关图片/视频
3. 在正确时间发布 (工作日 9-11am, 6-8pm)
4. 互动回复增加曝光
5. 固定第一个推文

---

SUMMARY

echo -e "${GREEN}✅ Thread generated!${NC}"
echo ""
echo "📋 Next steps:"
echo "1. 复制上方推文到 Twitter/X"
echo "2. 添加相关图片"
echo "3. 在正确时间发布"
echo "4. 固定第一个推文"
"""

generator_path = os.path.join(workspace, "tweet-thread-generator.sh")
with open(generator_path, "w") as f:
    f.write(generator_script)

os.chmod(generator_path, os.stat(generator_path).st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

# Make the legacy script non-executable to be a real distractor
legacy_path = os.path.join(workspace, "scripts/legacy/old_thread_maker.sh")
os.chmod(legacy_path, 0o644)

print("Workspace initialized.")
print(f"Brief file: {brief_path}")
print(f"Generator script: {generator_path}")