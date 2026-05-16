#!/bin/bash
set -e

echo "=== Setting up hex-vetter tool ==="
cd /workspace

# Create hex-vetter directory with necessary files instead of cloning non-existent repo
if [ ! -d "hex-vetter" ]; then
    mkdir -p hex-vetter
fi

cd /workspace/hex-vetter

# Create package.json
cat > package.json << 'EOF'
{
  "name": "hex-vetter",
  "version": "1.0.0",
  "description": "Hex/binary vetting tool for skill packages",
  "main": "vet.js",
  "scripts": {
    "test": "echo \"No tests\""
  },
  "dependencies": {}
}
EOF

# Create vet.js - main vetting tool
cat > vet.js << 'EOF'
#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');

const RISK = {
  LOW: 'LOW',
  MEDIUM: 'MEDIUM',
  HIGH: 'HIGH'
};

function vetFile(filePath) {
  let data;
  try {
    data = fs.readFileSync(filePath);
  } catch (e) {
    return { file: filePath, risk: RISK.LOW, flags: [], error: e.message };
  }

  const flags = [];

  // Check for ELF magic bytes
  if (data.length >= 4 && data[0] === 0x7f && data[1] === 0x45 && data[2] === 0x4c && data[3] === 0x46) {
    flags.push('MAGIC_BYTES');
  }

  // Check for null bytes
  let nullCount = 0;
  for (let i = 0; i < data.length; i++) {
    if (data[i] === 0x00) nullCount++;
  }
  if (nullCount > 0) flags.push('NULL_BYTES');

  // Check for Unicode override characters (U+202E RLO, U+202D LRO)
  const str = data.toString('utf8');
  if (str.includes('\u202e') || str.includes('\u202d')) {
    flags.push('UNICODE_OVERRIDE');
  }

  // Check for control characters (0x01-0x08, 0x0e-0x1f excluding tab/newline/cr)
  for (let i = 0; i < data.length; i++) {
    const b = data[i];
    if ((b >= 0x01 && b <= 0x08) || (b >= 0x0e && b <= 0x1f)) {
      flags.push('CONTROL_CHARS');
      break;
    }
  }

  // Check for high non-ASCII ratio
  let highByteCount = 0;
  for (let i = 0; i < data.length; i++) {
    if (data[i] >= 0x80) highByteCount++;
  }
  if (data.length > 0 && (highByteCount / data.length) > 0.3) {
    flags.push('HIGH_NON_ASCII');
  }

  // Check for suspicious patterns
  const suspiciousPatterns = ['/bin/sh', '/bin/bash', 'execSync', 'child_process'];
  for (const pat of suspiciousPatterns) {
    if (str.includes(pat)) {
      flags.push('SUSPICIOUS_PATTERN');
      break;
    }
  }

  let risk = RISK.LOW;
  if (flags.includes('MAGIC_BYTES') || flags.includes('NULL_BYTES') ||
      flags.includes('UNICODE_OVERRIDE') || flags.includes('SUSPICIOUS_PATTERN')) {
    risk = RISK.HIGH;
  } else if (flags.includes('CONTROL_CHARS') || flags.includes('HIGH_NON_ASCII')) {
    risk = RISK.MEDIUM;
  }

  return { file: filePath, risk, flags };
}

function vetDirectory(dirPath) {
  const results = [];
  const entries = fs.readdirSync(dirPath, { withFileTypes: true });
  for (const entry of entries) {
    const full = path.join(dirPath, entry.name);
    if (entry.isDirectory()) {
      results.push(...vetDirectory(full));
    } else {
      results.push(vetFile(full));
    }
  }
  return results;
}

if (require.main === module) {
  const args = process.argv.slice(2);
  if (args[0] === '--help' || args[0] === '-h') {
    console.log('Usage: node vet.js <file_or_dir>');
    process.exit(0);
  }
  const target = args[0];
  if (!target) {
    console.log('Usage: node vet.js <file_or_dir>');
    process.exit(1);
  }
  const stat = fs.statSync(target);
  let results;
  if (stat.isDirectory()) {
    results = vetDirectory(target);
  } else {
    results = [vetFile(target)];
  }
  console.log(JSON.stringify(results, null, 2));
}

module.exports = { vetFile, vetDirectory, RISK };
EOF

# Create scan_all.js
cat > scan_all.js << 'EOF'
#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const { vetDirectory, RISK } = require('./vet');

const target = process.argv[2] || '/workspace/incoming_skills';
const skillDirs = fs.readdirSync(target, { withFileTypes: true })
  .filter(e => e.isDirectory())
  .map(e => path.join(target, e.name));

const summary = [];
for (const skillDir of skillDirs) {
  const results = vetDirectory(skillDir);
  let overallRisk = RISK.LOW;
  const allFlags = new Set();
  for (const r of results) {
    for (const f of r.flags) allFlags.add(f);
    if (r.risk === RISK.HIGH) overallRisk = RISK.HIGH;
    else if (r.risk === RISK.MEDIUM && overallRisk !== RISK.HIGH) overallRisk = RISK.MEDIUM;
  }
  summary.push({ skill: path.basename(skillDir), risk: overallRisk, flags: [...allFlags], files: results });
}

console.log(JSON.stringify(summary, null, 2));
EOF

# Create verify.js
cat > verify.js << 'EOF'
#!/usr/bin/env node
'use strict';
const { vetFile } = require('./vet');
const target = process.argv[2];
if (!target) { console.error('Usage: node verify.js <file>'); process.exit(1); }
const result = vetFile(target);
console.log(JSON.stringify(result, null, 2));
EOF

# Create starfragment.js
cat > starfragment.js << 'EOF'
#!/usr/bin/env node
'use strict';
// starfragment: integrity checker stub
const fs = require('fs');
const crypto = require('crypto');
const target = process.argv[2];
if (!target) { console.error('Usage: node starfragment.js <file>'); process.exit(1); }
const data = fs.readFileSync(target);
const hash = crypto.createHash('sha256').update(data).digest('hex');
console.log(JSON.stringify({ file: target, sha256: hash }));
EOF

npm install

echo "=== hex-vetter installed ==="
node vet.js --help 2>/dev/null || echo "vet.js ready (no --help flag needed)"

# Verify key scripts exist
for script in vet.js scan_all.js verify.js starfragment.js; do
    if [ -f "/workspace/hex-vetter/$script" ]; then
        echo "  ✓ $script present"
    else
        echo "  ✗ $script MISSING"
    fi
done

echo "=== Workspace ready ==="
ls /workspace/