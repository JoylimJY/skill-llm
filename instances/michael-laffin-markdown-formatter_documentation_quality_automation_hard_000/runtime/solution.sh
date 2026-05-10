#!/usr/bin/env bash
set -euo pipefail

WORKSPACE="${1:-/workspace}"
cd "$WORKSPACE"

echo "=== Step 1: Discover all markdown files under docs/ ==="
mapfile -t MD_FILES < <(find "$WORKSPACE/docs" -type f -name "*.md" | sort)
echo "Found ${#MD_FILES[@]} markdown files:"
for f in "${MD_FILES[@]}"; do echo "  $f"; done

echo ""
echo "=== Step 2: Locate the skill ==="
SKILL_INDEX=$(find /workspace/skill_context -name "index.js" | head -n 1)
SKILL_DIR=$(dirname "$SKILL_INDEX")
echo "Skill found at: $SKILL_DIR"

echo ""
echo "=== Step 3: Write Node.js bridge script ==="
cat > /tmp/audit_and_format.js << 'JSEOF'
const fs = require('fs');
const path = require('path');

// Load skill from workspace
const skillDir = process.argv[2];
const skill = require(skillDir);

const files = process.argv.slice(3);

async function main() {
  const auditResults = [];
  const formattedFiles = [];
  let totalWarnings = 0;
  let filesWithLintErrors = 0;

  // Phase 1: Lint all files to find which have errors
  console.error(`Phase 1: Linting ${files.length} files...`);
  for (const filePath of files) {
    let content;
    try {
      content = fs.readFileSync(filePath, 'utf8');
    } catch (e) {
      console.error(`  Skipping (read error): ${filePath}`);
      continue;
    }

    let lintResult;
    try {
      lintResult = await skill.lintMarkdown({
        markdown: content,
        style: 'github',
        options: {
          checkHeadingLevels: true,
          checkListConsistency: true,
          checkLinks: false,
          checkEmphasisBalance: false
        }
      });
    } catch (e) {
      console.error(`  Lint error on ${filePath}: ${e.message}`);
      lintResult = { errors: [], warnings: [] };
    }

    const errorCount = Array.isArray(lintResult.errors) ? lintResult.errors.length : 0;
    const hasErrors = errorCount > 0;
    if (hasErrors) filesWithLintErrors++;

    auditResults.push({
      filePath,
      content,
      hasErrors,
      errorCount
    });

    console.error(`  ${path.basename(filePath)}: ${errorCount} lint errors`);
  }

  // Phase 2: Format files that have lint errors
  console.error(`\nPhase 2: Formatting ${filesWithLintErrors} files with errors...`);
  for (const audit of auditResults) {
    if (!audit.hasErrors) {
      console.error(`  Skipping (no errors): ${path.basename(audit.filePath)}`);
      continue;
    }

    const originalLength = audit.content.length;
    let formatResult;
    try {
      formatResult = await skill.formatMarkdown({
        markdown: audit.content,
        style: 'github',
        options: {
          listStyle: 'dash',
          emphasisStyle: 'asterisk',
          headingStyle: 'atx',
          codeStyle: 'fenced',
          fixLists: true,
          normalizeSpacing: true,
          maxWidth: 100
        }
      });
    } catch (e) {
      console.error(`  Format error on ${audit.filePath}: ${e.message}`);
      continue;
    }

    const formattedContent = formatResult.formattedMarkdown;
    const formattedLength = formattedContent ? formattedContent.length : originalLength;
    const warningCount = Array.isArray(formatResult.warnings) ? formatResult.warnings.length : 0;
    totalWarnings += warningCount;

    // Overwrite original file in-place
    try {
      fs.writeFileSync(audit.filePath, formattedContent, 'utf8');
      console.error(`  Formatted: ${path.basename(audit.filePath)} (${originalLength} -> ${formattedLength} chars, ${warningCount} warnings)`);
    } catch (e) {
      console.error(`  Write error on ${audit.filePath}: ${e.message}`);
    }

    formattedFiles.push({
      file: audit.filePath,
      warnings: warningCount,
      original_length: originalLength,
      formatted_length: formattedLength
    });
  }

  // Phase 3: Build the report
  const report = {
    total_files_audited: files.length,
    files_with_lint_errors: filesWithLintErrors,
    style_used: 'github',
    total_warnings: totalWarnings,
    formatted_files: formattedFiles
  };

  // Write report to stdout for the shell script to capture
  process.stdout.write(JSON.stringify(report, null, 2) + '\n');
}

main().catch(e => {
  console.error('Fatal error:', e.message);
  process.exit(1);
});
JSEOF

echo "Bridge script written to /tmp/audit_and_format.js"

echo ""
echo "=== Step 4: Execute audit and formatting ==="
node /tmp/audit_and_format.js "$SKILL_DIR" "${MD_FILES[@]}" > "$WORKSPACE/formatting_report.json"

echo ""
echo "=== Step 5: Verify output ==="
echo "Contents of formatting_report.json:"
cat "$WORKSPACE/formatting_report.json" | python3 -m json.tool

echo ""
echo "=== Done! ==="
echo "Report saved to: $WORKSPACE/formatting_report.json"
echo "Original markdown files have been overwritten with formatted versions."