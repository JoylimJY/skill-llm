#!/usr/bin/env python3
import os
import json
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# ── 1. Create the Cloudflare R2 config at the documented path ──────────────
config_dir = Path.home() / ".config" / "cloudflare"
config_dir.mkdir(parents=True, exist_ok=True)

r2_config = {
    "bucket": "ecommerce-assets-prod",
    "accountId": "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4",
    "publicDomain": "pub-7f3e2d1c9b8a4056.r2.dev",
    "apiToken": "fake-token-for-mock-testing-xyz987"
}

with open(config_dir / "r2.json", "w") as f:
    json.dump(r2_config, f, indent=2)

# ── 2. Create the scripts/ directory with r2-upload.sh (will be overwritten in setup) ──
scripts_dir = workspace / "scripts"
scripts_dir.mkdir(exist_ok=True)

# Placeholder — setup_script will write the real mock script
(scripts_dir / "r2-upload.sh").write_text("#!/bin/bash\necho 'placeholder'\n")

# ── 3. Create the marketing campaign asset directory with realistic files ──
campaign_dir = workspace / "marketing" / "campaign_q4"
campaign_dir.mkdir(parents=True, exist_ok=True)

assets = [
    ("hero_banner.png",       b"\x89PNG\r\n\x1a\n" + b"\x00" * 512),
    ("product_shot_01.jpg",   b"\xff\xd8\xff\xe0" + b"\x00" * 256),
    ("product_shot_02.jpg",   b"\xff\xd8\xff\xe0" + b"\x00" * 300),
    ("promo_video_teaser.mp4",b"\x00\x00\x00\x18ftyp" + b"\x00" * 1024),
    ("email_template.html",   b"<html><body>Q4 Launch</body></html>"),
    ("discount_codes.csv",    b"code,discount\nSAVE10,10\nSAVE20,20\n"),
    ("brand_guidelines.pdf",  b"%PDF-1.4\n" + b"\x00" * 400),
]

for filename, content in assets:
    (campaign_dir / filename).write_bytes(content)

# ── 4. Create distractor directories and files to increase realism ──

# Distractor: an old campaigns folder that should NOT be uploaded
old_campaign = workspace / "marketing" / "campaign_q3"
old_campaign.mkdir(parents=True, exist_ok=True)
for name in ["old_banner.png", "archive_note.txt", "legacy_promo.jpg"]:
    (old_campaign / name).write_bytes(b"\x00" * 128)

# Distractor: general marketing docs
(workspace / "marketing" / "brand_overview.docx").write_bytes(b"\x00" * 200)
(workspace / "marketing" / "2024_roadmap.pptx").write_bytes(b"\x00" * 300)

# Distractor: project root files
(workspace / "README_INTERNAL.md").write_text("# Internal Project Notes\nDo not share.\n")
(workspace / ".gitignore").write_text("node_modules/\n*.log\n")
(workspace / "package.json").write_text(json.dumps({
    "name": "marketing-tools",
    "version": "1.0.0",
    "scripts": {"lint": "eslint ."}
}, indent=2))

# Distractor: a logs folder
logs_dir = workspace / "logs"
logs_dir.mkdir(exist_ok=True)
(logs_dir / "deploy_20231015.log").write_text("Deploy completed.\n")
(logs_dir / "deploy_20231020.log").write_text("Deploy failed: timeout.\n")

# Distractor: a config folder (NOT the real r2 config location)
local_config_dir = workspace / "config"
local_config_dir.mkdir(exist_ok=True)
(local_config_dir / "app_config.yaml").write_text("env: production\ndebug: false\n")
# Decoy r2-like config to trap agents reading from workspace instead of ~/.config
(local_config_dir / "storage.json").write_text(json.dumps({
    "bucket": "WRONG-BUCKET",
    "accountId": "WRONG-ACCOUNT",
    "publicDomain": "WRONG-DOMAIN.example.com",
    "apiToken": "WRONG-TOKEN"
}, indent=2))

# Distractor: src directory
src_dir = workspace / "src"
src_dir.mkdir(exist_ok=True)
(src_dir / "upload_helper.py").write_text(
    "# Legacy uploader - deprecated\nimport boto3\n"
)
(src_dir / "cdn_utils.js").write_text(
    "// CDN helpers\nmodule.exports = {};\n"
)

print("Workspace setup complete.")
print(f"Campaign assets: {list(campaign_dir.iterdir())}")
print(f"R2 config: {config_dir / 'r2.json'}")