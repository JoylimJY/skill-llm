import os
import json
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# Clone the real repo structure locally (simulate with realistic file tree)
# We create a realistic Auto_Building_new project skeleton
project_dir = os.path.join(workspace, "Auto_Building_new")

# Core directories
dirs = [
    "config",
    "src/data",
    "src/components",
    "src/pages",
    "src/styles",
    "src/utils",
    "scripts",
    "public/images",
    "public/icons",
    ".github/workflows",
    "tests/unit",
    "tests/e2e",
    "docs",
    "node_modules/.cache",  # distractor
]

for d in dirs:
    os.makedirs(os.path.join(project_dir, d), exist_ok=True)

# --- CORE CONFIG FILE: config/sources.json (CORRUPTED/INCOMPLETE - agent must fix) ---
bad_sources = {
    "primaryCategories": ["健康医疗"],
    "secondaryCategories": {
        "健康医疗": ["政策法规", "临床研究", "医疗器械"]
    },
    "sources": [
        {
            "name": "丁香园",
            "type": "web",
            "url": "https://www.dxy.cn/",
            "enabled": True
        }
    ]
}
with open(os.path.join(project_dir, "config/sources.json"), "w", encoding="utf-8") as f:
    json.dump(bad_sources, f, ensure_ascii=False, indent=2)

# --- CORE TS FILE: src/data/resources.ts (INCOMPLETE - agent must fix) ---
bad_resources_ts = """\
// Auto-generated configuration
export const PRIMARY_CATEGORIES = [
  '健康医疗',
];

export const SECONDARY_CATEGORIES = [
  { label: '政策法规', value: 'policy' },
  { label: '临床研究', value: 'clinical' },
];
"""
with open(os.path.join(project_dir, "src/data/resources.ts"), "w", encoding="utf-8") as f:
    f.write(bad_resources_ts)

# --- DISTRACTOR FILES ---

# package.json
package_json = {
    "name": "auto-building",
    "version": "1.0.0",
    "scripts": {
        "dev": "next dev",
        "build": "next build",
        "start": "next start",
        "daily": "tsx scripts/scrape-all.ts"
    },
    "dependencies": {
        "next": "^14.0.0",
        "react": "^18.0.0",
        "typescript": "^5.0.0"
    }
}
with open(os.path.join(project_dir, "package.json"), "w") as f:
    json.dump(package_json, f, indent=2)

# tsconfig.json distractor
tsconfig = {
    "compilerOptions": {
        "target": "es5",
        "lib": ["dom", "esnext"],
        "strict": True
    }
}
with open(os.path.join(project_dir, "tsconfig.json"), "w") as f:
    json.dump(tsconfig, f, indent=2)

# scripts/scrape-all.ts (distractor - not to be modified)
with open(os.path.join(project_dir, "scripts/scrape-all.ts"), "w") as f:
    f.write("// Core scraping script - DO NOT MODIFY\nexport async function scrapeAll() {}\n")

# scripts/classify.ts (distractor)
with open(os.path.join(project_dir, "scripts/classify.ts"), "w") as f:
    f.write("// Classification script - DO NOT MODIFY\nexport async function classify() {}\n")

# src/data/pending-review.json
with open(os.path.join(project_dir, "src/data/pending-review.json"), "w") as f:
    json.dump([], f)

# src/data/approved-resources.json
with open(os.path.join(project_dir, "src/data/approved-resources.json"), "w") as f:
    json.dump([], f)

# src/components/CategoryNav.tsx (distractor)
with open(os.path.join(project_dir, "src/components/CategoryNav.tsx"), "w") as f:
    f.write("""\
import React from 'react';
import { PRIMARY_CATEGORIES } from '../data/resources';
export const CategoryNav = () => <div>{PRIMARY_CATEGORIES.join(',')}</div>;
""")

# src/pages/index.tsx (distractor)
with open(os.path.join(project_dir, "src/pages/index.tsx"), "w") as f:
    f.write("export default function Home() { return <main>Auto Building</main>; }\n")

# src/pages/admin.tsx (distractor)
with open(os.path.join(project_dir, "src/pages/admin.tsx"), "w") as f:
    f.write("export default function Admin() { return <main>Admin</main>; }\n")

# src/utils/fetcher.ts (distractor)
with open(os.path.join(project_dir, "src/utils/fetcher.ts"), "w") as f:
    f.write("export async function fetchData(url: string) { return fetch(url); }\n")

# src/styles/globals.css (distractor)
with open(os.path.join(project_dir, "src/styles/globals.css"), "w") as f:
    f.write("body { margin: 0; font-family: sans-serif; }\n")

# .github/workflows/daily.yml (distractor)
with open(os.path.join(project_dir, ".github/workflows/daily.yml"), "w") as f:
    f.write("name: Daily Scrape\non:\n  schedule:\n    - cron: '0 2 * * *'\njobs:\n  scrape:\n    runs-on: ubuntu-latest\n")

# tests/unit/sources.test.ts (distractor)
with open(os.path.join(project_dir, "tests/unit/sources.test.ts"), "w") as f:
    f.write("describe('sources', () => { it('loads', () => {}); });\n")

# tests/e2e/homepage.test.ts (distractor)
with open(os.path.join(project_dir, "tests/e2e/homepage.test.ts"), "w") as f:
    f.write("describe('homepage', () => { it('renders', () => {}); });\n")

# docs/architecture.md (distractor)
with open(os.path.join(project_dir, "docs/architecture.md"), "w") as f:
    f.write("# Architecture\n\nSee source code for details.\n")

# Old config backup (distractor / red herring)
old_config = {
    "primaryCategories": ["智能母体"],
    "secondaryCategories": {"智能母体": ["agent", "skill"]},
    "sources": []
}
with open(os.path.join(project_dir, "config/sources.json.bak"), "w") as f:
    json.dump(old_config, f, ensure_ascii=False, indent=2)

# A fake alternate resources file (distractor)
with open(os.path.join(project_dir, "src/data/resources.backup.ts"), "w") as f:
    f.write("// old backup\nexport const PRIMARY_CATEGORIES = ['旧分类'];\n")

print("Workspace initialized successfully.")
print(f"Project directory: {project_dir}")