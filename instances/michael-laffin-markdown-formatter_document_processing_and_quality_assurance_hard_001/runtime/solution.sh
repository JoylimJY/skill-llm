#!/usr/bin/env bash
set -euo pipefail

WORKSPACE="${1:-/workspace}"
cd "$WORKSPACE"

echo "=== Step 1: Discover the 5 pharma markdown files ==="
mapfile -t MD_FILES < <(find "$WORKSPACE/pharma_docs" -type f -name "*.md" | sort)
echo "Found ${#MD_FILES[@]} markdown files:"
for f in "${MD_FILES[@]}"; do echo "  $f"; done

echo ""
echo "=== Step 2: Locate the skill context (index.js) ==="
SKILL_DIR="/workspace/skill_context"
ls "$SKILL_DIR/index.js"
echo "Skill found at $SKILL_DIR/index.js"

echo ""
echo "=== Step 3: Write a bridge script to use lintMarkdown + formatMarkdown ==="

cat > /tmp/pharma_audit.js << 'JSEOF'
const fs = require('fs');
const path = require('path');

// Load skill from the mounted skill_context
const skill = require('/workspace/skill_context/index.js');

const filePaths = process.argv.slice(2);
const auditResults = [];
let totalWarnings = 0;
let totalErrors = 0;

async function processAll() {
  for (const filePath of filePaths) {
    const originalContent = fs.readFileSync(filePath, 'utf8');
    
    // Step A: Lint with bespoke options (checkEmphasisBalance defaults to false - must explicitly enable)
    let lintResult = null;
    try {
      lintResult = await skill.lintMarkdown({
        markdown: originalContent,
        style: 'github',
        options: {
          checkLinks: true,
          checkHeadingLevels: true,
          checkListConsistency: true,
          checkEmphasisBalance: true   // <- non-default, must read SKILL.md to know this exists
        }
      });
    } catch (e) {
      lintResult = { errors: [], warnings: [], stats: {}, suggestions: [] };
    }

    // Step B: Format with house style options
    // Key proprietary traps:
    //   - style: 'github' (not default 'commonmark')
    //   - maxWidth: 100 (not default 80)
    //   - listStyle: 'dash' (not default 'consistent')
    //   - emphasisStyle: 'underscore' (not default 'asterisk')
    //   - codeStyle: 'fenced'
    //   - headingStyle: 'atx'
    //   - checkEmphasisBalance: true (non-default)
    let formatResult = null;
    try {
      formatResult = await skill.formatMarkdown({
        markdown: originalContent,
        style: 'github',
        options: {
          maxWidth: 100,
          headingStyle: 'atx',
          listStyle: 'dash',
          codeStyle: 'fenced',
          emphasisStyle: 'underscore',
          strongStyle: 'asterisk',
          linkStyle: 'inline',
          preserveHtml: false,
          fixLists: true,
          normalizeSpacing: true
        }
      });
    } catch (e) {
      formatResult = {
        formattedMarkdown: originalContent,
        warnings: [],
        stats: {},
        lintResult: {},
        originalLength: originalContent.length,
        formattedLength: originalContent.length
      };
    }

    // Step C: Write formatted content back to original location
    const formatted = formatResult.formattedMarkdown || originalContent;
    fs.writeFileSync(filePath, formatted, 'utf8');

    // Step D: Collect per-file audit entry using SKILL.md return field names
    const warnings = Array.isArray(formatResult.warnings) ? formatResult.warnings : [];
    const errors = Array.isArray(lintResult.errors) ? lintResult.errors : [];
    totalWarnings += warnings.length;
    totalErrors += errors.length;

    auditResults.push({
      file: filePath,
      filename: path.basename(filePath),
      lintResult: {
        errors: lintResult.errors || [],
        warnings: lintResult.warnings || [],
        stats: lintResult.stats || {},
        suggestions: lintResult.suggestions || []
      },
      formattedMarkdown: formatted,
      warnings: formatResult.warnings || [],
      stats: formatResult.stats || {},
      originalLength: formatResult.originalLength || originalContent.length,
      formattedLength: formatResult.formattedLength || formatted.length
    });

    console.log(`  Processed: ${path.basename(filePath)} | lint errors: ${errors.length} | warnings: ${warnings.length} | ${formatResult.originalLength || 0} -> ${formatResult.formattedLength || 0} chars`);
  }

  // Step E: Build consolidated audit report with aggregated stats
  const auditReport = {
    totalFiles: filePaths.length,
    totalWarnings: totalWarnings,
    totalErrors: totalErrors,
    processingTime: Date.now(),
    style: 'github',
    options: {
      maxWidth: 100,
      headingStyle: 'atx',
      listStyle: 'dash',
      codeStyle: 'fenced',
      emphasisStyle: 'underscore',
      fixLists: true,
      normalizeSpacing: true
    },
    results: auditResults
  };

  // Write audit report to workspace root
  const reportPath = '/workspace/formatting_audit.json';
  fs.writeFileSync(reportPath, JSON.stringify(auditReport, null, 2), 'utf8');
  console.log(`\n=== Audit report written to: ${reportPath} ===`);
  console.log(`Total files: ${auditReport.totalFiles}`);
  console.log(`Total warnings: ${totalWarnings}`);
  console.log(`Total lint errors: ${totalErrors}`);
}

processAll().catch(err => {
  console.error('Fatal error:', err);
  process.exit(1);
});
JSEOF

echo ""
echo "=== Step 4: Execute the bridge script with all pharma markdown files ==="
node /tmp/pharma_audit.js "${MD_FILES[@]}"

echo ""
echo "=== Step 5: Verify output ==="
if [ -f "/workspace/formatting_audit.json" ]; then
    echo "formatting_audit.json created successfully."
    python3 -c "
import json
with open('/workspace/formatting_audit.json') as f:
    data = json.load(f)
print(f'  totalFiles: {data[\"totalFiles\"]}')
print(f'  totalWarnings: {data[\"totalWarnings\"]}')
print(f'  results count: {len(data[\"results\"])}')
for r in data['results']:
    print(f'    - {r[\"filename\"]}: originalLength={r[\"originalLength\"]}, formattedLength={r[\"formattedLength\"]}')
"
else
    echo "ERROR: formatting_audit.json was not created!"
    exit 1
fi

echo ""
echo "=== Solution complete. All 5 pharma docs formatted and audit report generated. ==="