#!/usr/bin/env bash
set -euo pipefail

WORKSPACE="${1:-/workspace}"
cd "$WORKSPACE"

echo "=== Step 1: Locate all 5 legacy markdown files ==="
mapfile -t MD_FILES < <(find "$WORKSPACE/docs/legacy" "$WORKSPACE/docs/current/reference" -type f -name "*.md" | sort)
echo "Found ${#MD_FILES[@]} markdown files:"
for f in "${MD_FILES[@]}"; do echo "  $f"; done

echo ""
echo "=== Step 2: Locate the skill ==="
SKILL_DIR="$WORKSPACE/skill_context"
echo "Skill directory: $SKILL_DIR"
ls "$SKILL_DIR/index.js"

echo ""
echo "=== Step 3: Write a Node.js bridge script ==="
cat > /tmp/audit_and_format.js << 'JSEOF'
const fs = require('fs');
const path = require('path');

// Load the skill from workspace
const skillPath = process.argv[2];
const outputPath = process.argv[3];
const filePaths = process.argv.slice(4);

// Import the skill tools
const skill = require(skillPath);

async function main() {
    const { formatMarkdown, lintMarkdown } = skill;
    
    if (!formatMarkdown || !lintMarkdown) {
        throw new Error(`Required functions not found. Available: ${Object.keys(skill).join(', ')}`);
    }

    const results = [];

    for (const filePath of filePaths) {
        console.log(`Processing: ${filePath}`);
        
        // Read the raw messy content
        const rawContent = fs.readFileSync(filePath, 'utf8');
        const originalLength = rawContent.length;

        // Step 1: Lint first with emphasis balance check (non-default: checkEmphasisBalance=true)
        let lintResult;
        try {
            lintResult = await lintMarkdown({
                markdown: rawContent,
                style: 'commonmark',
                options: {
                    checkLinks: true,
                    checkHeadingLevels: true,
                    checkListConsistency: true,
                    checkEmphasisBalance: true   // NON-DEFAULT: must read SKILL.md to know this exists
                }
            });
        } catch (e) {
            console.error(`Lint error for ${filePath}: ${e.message}`);
            lintResult = { errors: [], warnings: [], suggestions: [] };
        }

        const lintErrorCount = Array.isArray(lintResult.errors) ? lintResult.errors.length : 0;

        // Step 2: Format with strict CommonMark house style
        // KEY PROPRIETARY PARAMS: emphasisStyle='underscore', strongStyle='underline'
        // These differ from defaults (default emphasisStyle='asterisk', strongStyle='asterisk')
        let formatResult;
        try {
            formatResult = await formatMarkdown({
                markdown: rawContent,
                style: 'commonmark',   // NOT 'github' - must read docs to know the difference
                options: {
                    headingStyle: 'atx',            // Convert setext to ATX
                    listStyle: 'dash',              // Only dash markers, no * or +
                    codeStyle: 'fenced',            // Fenced code blocks
                    emphasisStyle: 'underscore',    // _italic_ not *italic* - NON-DEFAULT
                    strongStyle: 'underline',       // __bold__ not **bold** - NON-DEFAULT
                    linkStyle: 'inline',
                    fixLists: true,                 // Fix inconsistent list markers
                    normalizeSpacing: true,         // Fix spacing
                    maxWidth: 80
                }
            });
        } catch (e) {
            console.error(`Format error for ${filePath}: ${e.message}`);
            // Graceful degradation
            formatResult = {
                formattedMarkdown: rawContent,
                warnings: [],
                stats: {},
                originalLength: originalLength,
                formattedLength: rawContent.length
            };
        }

        const formattedContent = formatResult.formattedMarkdown || rawContent;
        const formattedLength = formatResult.formattedLength || formattedContent.length;
        const warnings = formatResult.warnings || [];

        // Step 3: Write formatted content back to original file
        fs.writeFileSync(filePath, formattedContent, 'utf8');
        console.log(`  Written back to: ${filePath}`);

        // Collect result entry for the audit report
        results.push({
            file: filePath,
            formattedMarkdown: formattedContent,
            originalLength: originalLength,
            formattedLength: formattedLength,
            warnings: warnings,
            lintErrors: lintErrorCount,
            lintSuggestions: Array.isArray(lintResult.suggestions) ? lintResult.suggestions.length : 0,
            style: 'commonmark',
            options: {
                emphasisStyle: 'underscore',
                strongStyle: 'underline',
                listStyle: 'dash',
                headingStyle: 'atx',
                codeStyle: 'fenced'
            }
        });
    }

    // Step 4: Write the formatting_audit.json report
    const report = {
        generatedAt: new Date().toISOString(),
        style: 'commonmark',
        totalFiles: results.length,
        totalWarnings: results.reduce((sum, r) => sum + (Array.isArray(r.warnings) ? r.warnings.length : 0), 0),
        totalLintErrors: results.reduce((sum, r) => sum + (r.lintErrors || 0), 0),
        results: results
    };

    fs.writeFileSync(outputPath, JSON.stringify(report, null, 2), 'utf8');
    console.log(`\nAudit report written to: ${outputPath}`);
    console.log(`Processed ${results.length} files.`);
    console.log(`Total lint errors found: ${report.totalLintErrors}`);
    console.log(`Total warnings: ${report.totalWarnings}`);
}

main().catch(err => {
    console.error('Fatal error:', err);
    process.exit(1);
});
JSEOF

echo ""
echo "=== Step 4: Execute the bridge script ==="
SKILL_INDEX="$SKILL_DIR/index.js"
OUTPUT_PATH="$WORKSPACE/formatting_audit.json"

node /tmp/audit_and_format.js "$SKILL_INDEX" "$OUTPUT_PATH" "${MD_FILES[@]}"

echo ""
echo "=== Step 5: Verify output ==="
if [ -f "$OUTPUT_PATH" ]; then
    echo "formatting_audit.json created successfully."
    echo "File size: $(wc -c < "$OUTPUT_PATH") bytes"
    # Show summary without full content
    node -e "
        const r = require('$OUTPUT_PATH');
        console.log('Total files:', r.totalFiles);
        console.log('Total warnings:', r.totalWarnings);
        console.log('Total lint errors:', r.totalLintErrors);
        r.results.forEach(res => {
            console.log('  -', res.file, '| orig:', res.originalLength, '| fmt:', res.formattedLength, '| lintErrors:', res.lintErrors);
        });
    "
else
    echo "ERROR: formatting_audit.json was not created!"
    exit 1
fi

echo ""
echo "=== Solution complete ==="