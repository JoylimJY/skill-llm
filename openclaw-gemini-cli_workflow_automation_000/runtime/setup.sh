#!/bin/bash
set -e

WORKSPACE=/workspace

# Make helper scripts executable
chmod +x "$WORKSPACE/scripts/gemini_json.sh"
chmod +x "$WORKSPACE/scripts/gemini_review.sh"

# ─── Install the mock `gemini` binary ───────────────────────────────────────
# This mock simulates the real Gemini CLI behavior deterministically.
# It responds to exact flag patterns documented in SKILL.md.

cat > /usr/local/bin/gemini << 'GEMINI_MOCK_EOF'
#!/bin/bash
# Mock Gemini CLI — deterministic responses for sandbox testing

PROMPT=""
MODEL=""
SHOW_HELP=false

# Parse arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    --help|-h)
      SHOW_HELP=true
      shift
      ;;
    -p)
      shift
      PROMPT="$1"
      shift
      ;;
    --model|-m)
      shift
      MODEL="$1"
      shift
      ;;
    *)
      shift
      ;;
  esac
done

# --help output (mirrors real gemini CLI structure)
if $SHOW_HELP; then
  cat << 'HELP_EOF'
Gemini CLI - AI assistant for your terminal

Usage:
  gemini [flags]

Flags:
  -p, --prompt string     Prompt to send to the model
  -m, --model string      Model to use (default: gemini-2.0-flash)
                          Available: gemini-2.0-flash, gemini-1.5-pro, gemini-1.5-flash
  -h, --help              Show this help message

Examples:
  gemini -p "hello"
  gemini -p "your prompt" -m gemini-1.5-pro
  cat file.txt | gemini -p "review this"

Note: FileKeychain fallback active (keytar not installed). This is non-fatal.
HELP_EOF
  exit 0
fi

# Read from stdin if available (pipe support)
STDIN_CONTENT=""
if [ ! -t 0 ]; then
  STDIN_CONTENT=$(cat)
fi

# Combine prompt and stdin
FULL_INPUT="${PROMPT} ${STDIN_CONTENT}"

# ── Response routing based on prompt content ────────────────────────────────

# Smoke test
if echo "$FULL_INPUT" | grep -qi "^hello$\|^hello\b" && [ -z "$STDIN_CONTENT" ]; then
  echo "Hello! I'm ready to help. (FileKeychain fallback active — non-fatal)"
  exit 0
fi

# JSON site spec request (must contain "Return only valid JSON" AND site spec keys)
if echo "$FULL_INPUT" | grep -q "Return only valid JSON" && \
   echo "$FULL_INPUT" | grep -qi "stack\|pages\|components\|seo_keywords\|copy_style\|risks"; then
  cat << 'JSON_EOF'
{"stack":"Next.js","pages":[{"path":"/","title":"ホーム","sections":["hero","pain_points","benefits","cta","faq"]},{"path":"/features","title":"機能紹介","sections":["overview","details"]},{"path":"/pricing","title":"料金","sections":["plans","cta"]}],"components":["Header","HeroSection","PainPoints","BenefitCards","PricingTable","Footer","CTAButton"],"copy_style":"energetic_trustworthy_conversion_focused","seo_keywords":["Instagramアナリティクス","インスタ分析","店舗向けSNS","日本 中小企業 Instagram","インスタグラム運用改善"],"risks":["low_brand_awareness","price_sensitivity_SMB","instagram_api_changes","localization_quality"]}
JSON_EOF
  exit 0
fi

# Review request (file content piped in OR review keyword present)
if echo "$FULL_INPUT" | grep -qi "review\|issues\|bullet\|identify"; then
  cat << 'REVIEW_EOF'
• ISSUE: Heading uses lowercase — should be title-cased and emotionally compelling for Japanese SMB audience
• ISSUE: Copy is vague ("it's good") — lacks concrete value proposition and trust signals
• ISSUE: No call-to-action with urgency — conversion rate will suffer without clear CTA button
• ISSUE: Missing pain-point framing — users need to see their problem articulated before solution
• ISSUE: No SEO structure — h1/h2 hierarchy not optimized for target keywords
• FIX: Rewrite hero headline to lead with outcome: "Instagram運用を自動化し、来店数を増やす"
• FIX: Add social proof section (testimonials, client logos) above CTA
• FIX: Replace generic contact text with specific CTA: "14日間無料で試す →"
• FIX: Add structured FAQ section for conversion optimization
• COMPONENT: Split into HeroSection, PainPoints, BenefitCards, and CTASection components
REVIEW_EOF
  exit 0
fi

# Model-specific acknowledgment
if [ -n "$MODEL" ]; then
  echo "Using model: $MODEL"
fi

# Default fallback
echo "I can help with that. Please provide a more specific prompt for best results."
exit 0
GEMINI_MOCK_EOF

chmod +x /usr/local/bin/gemini

# Verify mock works
echo "=== Verifying mock gemini CLI ==="
gemini --help | head -5
gemini -p "hello"
echo "=== Mock gemini CLI ready ==="