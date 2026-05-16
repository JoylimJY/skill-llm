import os
import json
import random
import hashlib
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(parents=True, exist_ok=True)

# ── 1. Create deeply nested distractor structure ──────────────────────────────
distractor_dirs = [
    "docs/legacy",
    "docs/drafts",
    "docs/archive/2022",
    "docs/archive/2023",
    "scripts/old",
    "scripts/helpers",
    "config/dev",
    "config/prod",
    "output/tmp",
    "output/exports",
    "assets/images",
    "assets/icons",
    "notes/meeting-notes",
    "notes/backlog",
]
for d in distractor_dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

distractor_files = {
    "docs/legacy/old_presentation.txt": "This is an outdated presentation draft from 2021. Do not use.",
    "docs/drafts/outline_v1.md": "# Draft Outline\n- Intro\n- Main points\n- Conclusion\nNOTE: not finalized",
    "docs/archive/2022/annual_report.txt": "2022 Annual Report - ARCHIVED",
    "docs/archive/2023/q4_summary.txt": "Q4 2023 Summary - See latest version",
    "scripts/old/convert.sh": "#!/bin/bash\n# DEPRECATED: old conversion script\n# Use new workflow instead\npandoc -o output.pptx input.md",
    "scripts/helpers/cleanup.sh": "#!/bin/bash\nrm -rf /tmp/scratch/*",
    "config/dev/settings.json": json.dumps({"env": "dev", "debug": True, "api_url": "http://localhost:8080"}),
    "config/prod/settings.json": json.dumps({"env": "prod", "debug": False, "api_url": "https://api.example.com"}),
    "output/tmp/scratch.txt": "temporary scratch file - ignore",
    "output/exports/old_export.csv": "id,name,value\n1,foo,bar\n2,baz,qux",
    "assets/images/placeholder.txt": "Image assets go here",
    "assets/icons/icon_list.txt": "icon_a.svg\nicon_b.svg\nicon_c.svg",
    "notes/meeting-notes/2024-01-15.md": "# Meeting Notes\n- Discussed Q1 roadmap\n- Assigned action items",
    "notes/backlog/feature_requests.md": "# Feature Backlog\n- Request 1: Better search\n- Request 2: Export to PDF",
    "docs/drafts/style_ideas.txt": "Some style ideas:\n- Use blue color scheme\n- Minimalist fonts\nWARNING: Do not use these - refer to official templates",
}
for fpath, content in distractor_files.items():
    p = workspace / fpath
    p.write_text(content, encoding="utf-8")

# ── 2. Create the SOURCE DOCUMENT the agent must convert to slides ─────────────
source_doc = workspace / "docs" / "microservices_architecture.md"
source_doc.write_text("""# Microservices Architecture Design Document

## Executive Summary

This document describes the microservices architecture adopted by our platform engineering team. 
It covers service decomposition strategy, inter-service communication patterns, deployment topology,
and observability practices.

## Service Decomposition

Our system is decomposed into the following core services:

### User Service
- Manages user accounts, authentication tokens, and profile data
- Exposes REST API on port 8001
- PostgreSQL backend with Redis cache layer
- Deployed as 3 replicas behind a load balancer

### Order Service
- Handles order lifecycle: creation, validation, fulfillment, cancellation
- Event-driven: publishes to Kafka topic `orders.events`
- MongoDB for flexible order schema storage
- Circuit breaker pattern implemented via Resilience4j

### Inventory Service
- Real-time inventory tracking with optimistic locking
- Subscribes to `orders.events` to decrement stock
- Redis sorted sets for fast lookup
- Exposes gRPC API for internal consumption

### Notification Service
- Consumes events from multiple Kafka topics
- Sends email/SMS via pluggable provider adapters
- Stateless, scales horizontally with zero config

## Inter-Service Communication

| Pattern | Use Case | Technology |
|---------|----------|------------|
| Synchronous REST | Client-facing APIs | nginx + HTTP/2 |
| Asynchronous Events | State propagation | Apache Kafka |
| Internal RPC | Low-latency service calls | gRPC + Protobuf |
| Service Mesh | Observability & mTLS | Istio sidecar proxy |

## Deployment Topology

All services run on Kubernetes (EKS):
- Namespace isolation per service
- HPA based on CPU and custom metrics
- Blue-green deployments via Argo Rollouts
- Secrets managed by HashiCorp Vault + External Secrets Operator

## Observability Stack

- **Metrics**: Prometheus scraping + Grafana dashboards
- **Tracing**: OpenTelemetry SDK → Jaeger backend
- **Logging**: Structured JSON logs → Loki → Grafana
- **Alerting**: PagerDuty integration via Alertmanager

## Known Limitations & Future Work

1. Service-to-service discovery still partially uses hard-coded DNS
2. Schema registry for Kafka events needs enforcement
3. Cross-region failover not yet implemented
4. API gateway rate limiting needs tuning

## Conclusion

The microservices architecture enables independent scaling and deployment of each service component.
The team recommends adopting the full service mesh in Q2 and completing schema registry enforcement by Q3.
""", encoding="utf-8")

# ── 3. Create references/templates.md (the proprietary template library) ──────
refs_dir = workspace / "references"
refs_dir.mkdir(parents=True, exist_ok=True)

templates_md = refs_dir / "templates.md"
templates_md.write_text("""# PPT Style Templates

This file contains the official pre-approved style templates for presentation generation.
You MUST copy the exact template content (between the `---` markers) when setting style requirements.
Replace placeholders like `[LANGUAGE]` with the appropriate value.

---

## Template: Modern Newspaper

**Applicable Scenarios:** Business reports, economic media, think-tank research  
**Keywords:** Business, Professional, Serious

**Template Prompt (copy exactly):**
```
Style: Modern Newspaper editorial layout. Use a strict black-and-white primary palette with selective red (#D32F2F) accent for headlines and key callouts. Typography: serif headline font (e.g., Times New Roman or Playfair Display) paired with clean sans-serif body text. Layout: multi-column grid resembling broadsheet newspaper. Each slide should have a bold headline bar at top, body content in 2-3 columns, and a thin footer rule with slide number. Data visualizations use monochrome bar/line charts. Output language: [LANGUAGE].
```

---

## Template: Sharp-edged Minimalism

**Applicable Scenarios:** Technical presentations, product introductions, architecture design  
**Keywords:** Technical, Minimalist, Architecture

**Template Prompt (copy exactly):**
```
Style: Sharp-edged minimalism with high-contrast geometric shapes. Primary palette: deep navy (#0A0E2A) background with electric cyan (#00E5FF) and pure white (#FFFFFF) accents. No gradients—use flat, hard-edged shapes only. Typography: monospace or geometric sans-serif (e.g., JetBrains Mono, Space Grotesk) for ALL text including body. Layout: asymmetric grid with strong diagonal cut elements. Diagrams and architecture flows use line-art icons in cyan. Slide titles appear as full-width colored bars. Output language: [LANGUAGE].
```

---

## Template: Yellow × Black Editorial

**Applicable Scenarios:** Fashion magazines, creative proposals  
**Keywords:** Creative, Fashion, Design

**Template Prompt (copy exactly):**
```
Style: Bold yellow (#FFD600) and black (#000000) editorial magazine layout. High-impact typography with oversized display fonts. Layout: magazine-spread style with large image placeholders, pull quotes in yellow highlight boxes, and full-bleed color blocks. Body text uses compact grotesque sans-serif. Strong typographic hierarchy: massive headline → subhead → caption. Output language: [LANGUAGE].
```

---

## Template: Black × Orange Creative

**Applicable Scenarios:** Agency presentations, brand pitches  
**Keywords:** Creative, Energy, Agency

**Template Prompt (copy exactly):**
```
Style: Black (#111111) base with vivid orange (#FF6D00) as the primary accent. Agency portfolio aesthetic: full-bleed dark backgrounds, orange geometric dividers, and large bold section titles. Use card-based layouts for case studies. Photography placeholders use dark overlay with orange tint. Kinetic-feeling layout with offset text blocks. Output language: [LANGUAGE].
```

---

## Template: Neo-Retro Dev

**Applicable Scenarios:** Developer documentation, technical blogs, open-source project presentations  
**Keywords:** Technical, Developer, Retro

**Template Prompt (copy exactly):**
```
Style: Neo-retro developer aesthetic combining terminal/CRT nostalgia with modern flat design. Primary palette: dark charcoal (#1A1A2E) background, phosphor green (#39FF14) for primary accents, amber (#FFC300) for secondary highlights, white for body text. Typography: monospace fonts exclusively (Courier New, Fira Code, or Hack). Layout: terminal-window chrome on content blocks, scan-line texture overlays, blinking cursor decorative elements. Code snippets styled as authentic terminal output. Section dividers use ASCII-art style borders. Output language: [LANGUAGE].
```

---

## Template: Manga Style

**Applicable Scenarios:** Education, fun explainers, training content  
**Keywords:** Education, Fun, Manga

**Template Prompt (copy exactly):**
```
Style: Japanese manga comic-book aesthetic. Panel-based layout mimicking manga page composition. Black ink outlines on white with selective screentone shading. Speech bubbles for key facts. Bold action lines (speed lines) for emphasis. Typography: comic-style fonts for headers, clean rounded sans for body. Output language: [LANGUAGE].
```

---

## Template: Magazine Style

**Applicable Scenarios:** Lifestyle content, female-oriented content  
**Keywords:** Magazine, Fashion, Lifestyle

**Template Prompt (copy exactly):**
```
Style: Premium lifestyle magazine layout. Soft pastel primary palette (blush pink #F8BBD0, cream #FFFDE7, sage green #C8E6C9). Elegant serif typography for headings, light-weight sans-serif for body. Full-bleed hero image on opening slide. Multi-column editorial grid. Pull quotes in italic serif within decorative frames. Subtle watercolor texture backgrounds. Output language: [LANGUAGE].
```

---

## Template: Sports / Athletic

**Applicable Scenarios:** Sports brands, fitness content, high-energy presentations  
**Keywords:** Sports, Fitness, Energy

**Template Prompt (copy exactly):**
```
Style: High-energy sports and athletic visual language. Bold primary palette: team red (#E53935) and white on black (#212121). Dynamic diagonal slash layouts, bold condensed display fonts, and strong motion-blur effects on imagery. Stats and metrics displayed in large scorecard-style blocks. Each slide has an energy bar or progress indicator. Output language: [LANGUAGE].
```

---

## Template: Royal Blue × Red

**Applicable Scenarios:** Art exhibitions, creative projects, watercolor themes  
**Keywords:** Art, Creative, Watercolor

**Template Prompt (copy exactly):**
```
Style: Royal blue (#1A237E) and crimson red (#B71C1C) with artistic watercolor wash textures. Gallery exhibition aesthetic. White space dominant with bold color splash accents. Typography: elegant serif display font for titles, humanist sans for body. Artwork/image placeholders use subtle drop shadows. Layout: centered composition with generous margins. Output language: [LANGUAGE].
```

---

## Template: Pink Street-style

**Applicable Scenarios:** Street culture, streetwear brands, youth content  
**Keywords:** Street, Trendy, Youth

**Template Prompt (copy exactly):**
```
Style: Street fashion and urban culture aesthetic. Hot pink (#FF0080) and black on white. Graffiti-inspired display typography, sticker-style callout boxes, and urban photography overlays. Layered composition with stencil-art elements. Loud, confident typographic hierarchy. Output language: [LANGUAGE].
```

---

## Template: Studio / Mockup / Premium

**Applicable Scenarios:** Product launches, hardware reveals, premium brand presentations  
**Keywords:** Product, Hardware, Premium

**Template Prompt (copy exactly):**
```
Style: Premium studio product presentation. Ultra-clean white (#FFFFFF) and dark slate (#263238) palette. Photorealistic mockup placeholders with soft studio lighting and subtle reflections. Typography: modern geometric sans-serif (SF Pro, Inter, or Helvetica Neue) with precise tracking. Layouts: centered hero product shot with sparse supporting text, feature callouts using thin hairline connectors. Minimalist but premium. Output language: [LANGUAGE].
```

---
""", encoding="utf-8")

# ── 4. Create a fake task_brief.txt so the agent knows what to do ─────────────
# (This is the business context, NOT instructions on HOW to use the tool)
task_brief = workspace / "task_brief.txt"
task_brief.write_text("""TASK BRIEF
==========
Project: Platform Engineering Review — Q2 Kickoff
Requester: VP of Engineering

We need to present our microservices architecture to the board next week.
The source document is at: docs/microservices_architecture.md

Please convert this document into a professional PPTX slide deck.
The output file should be named: arch_review.pptx

Once the slide deck is ready, please deliver it via the internal messaging system
to the #platform-eng channel with the message: "Architecture review slides ready for Q2 board presentation"

The slides must reflect our technical, professional brand — this is a developer/architecture audience.
""", encoding="utf-8")

# ── 5. A fake previous attempt (wrong/incomplete) to mislead naive agents ─────
(workspace / "output" / "tmp" / "failed_attempt_notes.txt").write_text(
    "Tried using pandoc but it doesn't produce styled PPTX.\n"
    "Also tried python-pptx directly but couldn't match the style.\n"
    "Need to use the proper tooling. Check scripts in workspace.\n",
    encoding="utf-8"
)

# ── 6. A misleading config file ────────────────────────────────────────────────
(workspace / "config" / "dev" / "ppt_config.json").write_text(
    json.dumps({
        "style": "custom_blue_white",
        "font": "Arial",
        "layout": "standard",
        "WARNING": "This config is NOT for the official PPT generation tool. Do not use."
    }, indent=2),
    encoding="utf-8"
)

print("Workspace initialized successfully.")
print(f"Files created: {sum(1 for _ in workspace.rglob('*') if _.is_file())}")