#!/usr/bin/env bash
set -e

SKILL_ROOT="/workspace/skills/cantian-bazi"

echo "=== Setting up cantian-bazi skill ==="
cd "$SKILL_ROOT"

# Make scripts executable
chmod +x scripts/buildBaziFromSolar.ts
chmod +x scripts/buildBaziFromLunar.ts
chmod +x scripts/getChineseCalendar.ts

# Install npm dependencies (tyme4ts and tsx)
echo "Installing npm dependencies..."
npm install --registry=https://registry.npmmirror.com 2>&1 | tail -5
npm install -D tsx --registry=https://registry.npmmirror.com 2>&1 | tail -5

echo "=== Verifying tyme4ts installation ==="
node -e "import('tyme4ts').then(m => console.log('tyme4ts OK:', Object.keys(m).slice(0,5).join(', '))).catch(e => { console.error('tyme4ts FAILED:', e.message); process.exit(1); })"

echo "=== Setup complete ==="