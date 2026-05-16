#!/usr/bin/env python3
import os
import random
import json

random.seed(42)

workspace = "/workspace"

# ── helpers ──────────────────────────────────────────────────────────────────
def make_file(path, content=""):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(content)

def make_fake_next_build(base):
    """Simulate a realistic .next folder with several files."""
    os.makedirs(os.path.join(base, ".next", "static", "chunks"), exist_ok=True)
    os.makedirs(os.path.join(base, ".next", "server", "pages"), exist_ok=True)
    os.makedirs(os.path.join(base, ".next", "cache"), exist_ok=True)
    make_file(os.path.join(base, ".next", "BUILD_ID"), "build-" + str(random.randint(10000, 99999)))
    make_file(os.path.join(base, ".next", "build-manifest.json"), json.dumps({"pages": ["/index", "/about"]}))
    make_file(os.path.join(base, ".next", "static", "chunks", "main.js"), "// main chunk\n" + "x" * random.randint(500, 2000))
    make_file(os.path.join(base, ".next", "server", "pages", "index.js"), "// server page\n" + "x" * random.randint(200, 800))
    make_file(os.path.join(base, ".next", "cache", "webpack.cache"), "binary-like-data" * 10)

def make_fake_node_modules(base):
    """Simulate a node_modules folder."""
    os.makedirs(os.path.join(base, "node_modules", "react"), exist_ok=True)
    os.makedirs(os.path.join(base, "node_modules", "next"), exist_ok=True)
    make_file(os.path.join(base, "node_modules", "react", "index.js"), "module.exports = {};")
    make_file(os.path.join(base, "node_modules", "next", "package.json"), json.dumps({"name": "next", "version": "13.0.0"}))

def make_next_project(base, name, has_next_build=True, has_node_modules=True):
    proj = os.path.join(base, name)
    os.makedirs(proj, exist_ok=True)
    make_file(os.path.join(proj, "package.json"), json.dumps({
        "name": name, "version": "1.0.0",
        "scripts": {"build": "next build", "dev": "next dev"},
        "dependencies": {"next": "^13.0.0", "react": "^18.0.0"}
    }, indent=2))
    make_file(os.path.join(proj, "next.config.js"), "/** @type {import('next').NextConfig} */\nmodule.exports = {};")
    os.makedirs(os.path.join(proj, "pages"), exist_ok=True)
    make_file(os.path.join(proj, "pages", "index.tsx"), "export default function Home() { return <div>Hello</div>; }")
    make_file(os.path.join(proj, "pages", "_app.tsx"), "export default function App({ Component, pageProps }) { return <Component {...pageProps} />; }")
    os.makedirs(os.path.join(proj, "public"), exist_ok=True)
    make_file(os.path.join(proj, "public", "favicon.ico"), "fake-icon")
    make_file(os.path.join(proj, "tsconfig.json"), json.dumps({"compilerOptions": {"strict": True}}, indent=2))
    if has_next_build:
        make_fake_next_build(proj)
    if has_node_modules:
        make_fake_node_modules(proj)

# ── STRUCTURE ─────────────────────────────────────────────────────────────────
# /workspace/
#   projects/               <-- agent must scan THIS directory
#     storefront/           <-- Next.js app with .next + node_modules
#     dashboard/            <-- Next.js app with .next + node_modules
#     marketing-site/       <-- Next.js app with .next only (no node_modules yet)
#     api-service/          <-- plain Node.js, has node_modules but NO .next
#     legacy-app/           <-- old Next.js, .next + node_modules
#     shared-ui/            <-- component lib, node_modules only
#     mobile/               <-- React Native, node_modules only
#   vendor/                 <-- DISTRACTOR: a vendor dir, should not be touched
#     some-lib/
#       node_modules/       <-- vendor node_modules (distractor)
#       .next/              <-- vendor .next (distractor - outside projects/)
#   tools/                  <-- DISTRACTOR directory with misc scripts
#   docs/                   <-- DISTRACTOR documentation
#   ci/                     <-- DISTRACTOR CI configs

projects_dir = os.path.join(workspace, "projects")

# Next.js projects with .next builds
make_next_project(projects_dir, "storefront",      has_next_build=True, has_node_modules=True)
make_next_project(projects_dir, "dashboard",       has_next_build=True, has_node_modules=True)
make_next_project(projects_dir, "marketing-site",  has_next_build=True, has_node_modules=False)
make_next_project(projects_dir, "legacy-app",      has_next_build=True, has_node_modules=True)

# Projects WITHOUT .next (should NOT have .next removed by our targeted scan)
make_next_project(projects_dir, "api-service",     has_next_build=False, has_node_modules=True)
make_next_project(projects_dir, "shared-ui",       has_next_build=False, has_node_modules=True)
make_next_project(projects_dir, "mobile",          has_next_build=False, has_node_modules=True)

# ── vendor (distractor - outside projects/) ───────────────────────────────────
vendor_next = os.path.join(workspace, "vendor", "some-lib")
make_fake_next_build(vendor_next)
make_fake_node_modules(vendor_next)
make_file(os.path.join(vendor_next, "package.json"), json.dumps({"name": "some-lib", "version": "0.1.0"}))

# ── tools (distractor) ────────────────────────────────────────────────────────
tools = os.path.join(workspace, "tools")
os.makedirs(tools, exist_ok=True)
make_file(os.path.join(tools, "deploy.sh"), "#!/bin/bash\necho 'deploying...'")
make_file(os.path.join(tools, "seed-db.js"), "console.log('seeding...');")
make_file(os.path.join(tools, "generate-types.ts"), "// auto-generated")

# ── docs (distractor) ─────────────────────────────────────────────────────────
docs = os.path.join(workspace, "docs")
os.makedirs(docs, exist_ok=True)
make_file(os.path.join(docs, "architecture.md"), "# Architecture\nThis is a monorepo...")
make_file(os.path.join(docs, "onboarding.md"), "# Onboarding\nClone the repo and run npm install...")
make_file(os.path.join(docs, "api-spec.yaml"), "openapi: '3.0.0'\ninfo:\n  title: API")

# ── ci (distractor) ───────────────────────────────────────────────────────────
ci = os.path.join(workspace, "ci")
os.makedirs(ci, exist_ok=True)
make_file(os.path.join(ci, "pipeline.yml"), "stages:\n  - build\n  - test\n  - deploy")
make_file(os.path.join(ci, "Dockerfile.ci"), "FROM node:20\nRUN npm ci")
make_file(os.path.join(ci, ".env.example"), "DATABASE_URL=postgres://localhost/mydb\nNEXT_PUBLIC_API_URL=http://localhost:3000")

# ── root-level distractors ────────────────────────────────────────────────────
make_file(os.path.join(workspace, ".gitignore"), "node_modules/\n.next/\n.env\n")
make_file(os.path.join(workspace, "turbo.json"), json.dumps({"$schema": "https://turbo.build/schema.json", "pipeline": {"build": {"outputs": [".next/**"]}}}, indent=2))
make_file(os.path.join(workspace, "package.json"), json.dumps({"name": "monorepo-root", "private": True, "workspaces": ["projects/*"]}, indent=2))

print("Workspace generated successfully.")
print(f"\nDirectory tree under {workspace}:")
for root, dirs, files in os.walk(workspace):
    # skip hidden dirs in display
    dirs[:] = sorted([d for d in dirs if not d.startswith('.')])
    level = root.replace(workspace, '').count(os.sep)
    indent = '  ' * level
    print(f"{indent}{os.path.basename(root)}/")
    sub_indent = '  ' * (level + 1)
    for f in sorted(files):
        print(f"{sub_indent}{f}")