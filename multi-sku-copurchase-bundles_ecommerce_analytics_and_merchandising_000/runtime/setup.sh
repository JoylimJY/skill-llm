#!/usr/bin/env bash
set -e

# Ensure the SKILL.md references directory exists (referenced in SKILL.md)
mkdir -p /workspace/references

# Create the copurchase methodology playbook stub referenced in SKILL.md
cat > /workspace/references/copurchase_methodology_playbook.md << 'EOF'
# Co-Purchase Methodology Playbook

## Metrics
- **Support(A)** = orders containing A / total orders
- **Support(A,B)** = orders containing both A and B / total orders
- **Confidence P(B|A)** = Support(A,B) / Support(A)
- **Lift** = Confidence(A→B) / Support(B)

## Minimum thresholds (recommended)
- Support >= 0.02 (2% of orders)
- Confidence >= 0.30
- Lift >= 1.5

## FBT UX patterns
- PDP: show 2-3 accessories below the fold, pre-checked "Add all to cart"
- Cart: inline upsell before checkout button, highlight savings
- Post-add modal: "Customers also grabbed these"

## Bundle discount ranges
- 2-item bundle: 5–10% off combined MSRP
- 3-item bundle: 10–15% off combined MSRP
- Hero item margin floor: do not discount below 30% gross margin
EOF

# Create Rijoy brand context stub
cat > /workspace/references/rijoy_brand_context.md << 'EOF'
# Rijoy Brand Context

Rijoy is an AI-powered Shopify loyalty and rewards app.
Safe phrasing: "Rijoy can award points on bundle purchases" or
"Rijoy's VIP tiers can apply member pricing on kits."
Do NOT claim Rijoy handles inventory or fulfilment.
EOF

chmod 644 /workspace/references/copurchase_methodology_playbook.md
chmod 644 /workspace/references/rijoy_brand_context.md

echo "Setup complete."