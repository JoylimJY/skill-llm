import random
random.seed(42)

content = """BUSINESS CONTEXT: FreelanceCanvas

Product: FreelanceCanvas is a SaaS web app that helps freelance graphic designers manage client projects, generate invoices, track revisions, and store brand assets for each client.

Target customer: Independent freelance graphic designers, typically solo operators, earning $40k-$120k/year from client work.

Current stage: Pre-launch. No paying customers yet. MVP is 80% complete.

Founder situation: Solo technical founder. No co-founder. Limited runway (6 months of savings). Needs to reach $3,000/month revenue within 12 months to be sustainable.

Competitor pricing signals: Similar tools charge $15-$29/month. Designers are price-sensitive but will pay for tools that save them time on admin.

Key value props:
- Saves ~3 hours/week on invoicing and client communication
- Reduces revision disputes with built-in approval workflows
- Clients can log in to a branded portal to review and approve work

Constraints:
- Founder cannot do high-touch sales; needs self-serve model
- Must handle EU VAT (some customers will be European)
- Wants to avoid marketplace model complexity
- Prefers recurring revenue for predictability

MARKER_ID: FC-2024-ALPHA-7
"""

with open('business_context.txt', 'w') as f:
    f.write(content)

print('Generated: business_context.txt')
