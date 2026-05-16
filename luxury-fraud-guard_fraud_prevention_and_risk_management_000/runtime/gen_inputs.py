import os
import random

random.seed(42)

BASE = "/workspace"

# --- Directory structure ---
dirs = [
    "store_data/orders/2024_q1",
    "store_data/orders/2024_q2",
    "store_data/customers",
    "store_data/disputes",
    "store_data/inventory",
    "ops/policies",
    "ops/checklists",
    "ops/sops",
    "finance/chargebacks",
    "finance/reports",
    "marketing/campaigns",
    "marketing/loyalty",
    "it/shopify_config",
    "it/integrations",
    "references",
]

for d in dirs:
    os.makedirs(os.path.join(BASE, d), exist_ok=True)

# --- Distractor files ---

# 1. Old order export CSV (messy, partial)
with open(os.path.join(BASE, "store_data/orders/2024_q1/orders_export_jan_mar.csv"), "w") as f:
    f.write("order_id,customer_email,amount,ship_country,bill_country,status\n")
    f.write("1001,john.doe@gmail.com,2400,US,US,fulfilled\n")
    f.write("1002,buyer99@tempmail.com,8750,CA,US,disputed\n")
    f.write("1003,collector@proton.me,1200,US,US,fulfilled\n")
    f.write("1004,watch.fan@yahoo.com,15000,HK,DE,chargeback\n")
    f.write("1005,new_buyer@outlook.com,3200,US,US,review\n")

# 2. Q2 orders
with open(os.path.join(BASE, "store_data/orders/2024_q2/orders_export_apr_jun.csv"), "w") as f:
    f.write("order_id,customer_email,amount,ship_country,bill_country,status\n")
    f.write("2001,vip@clientmail.com,6800,US,US,fulfilled\n")
    f.write("2002,fast_buyer@disposablemail.com,9200,US,US,cancelled\n")
    f.write("2003,rolex.collector@gmail.com,4500,FR,FR,fulfilled\n")
    f.write("2004,agent99@fwd.net,7800,NL,US,chargeback\n")

# 3. Dispute log (partial notes, messy)
with open(os.path.join(BASE, "store_data/disputes/chargeback_notes_2024.txt"), "w") as f:
    f.write("DISPUTE LOG - TimeVault Boutique\n")
    f.write("================================\n")
    f.write("Case #CB-2024-01: Order 1004 - Rolex Submariner $8,750 - Buyer claimed non-receipt.\n")
    f.write("  -> No signature on delivery. No proof. Lost dispute.\n")
    f.write("Case #CB-2024-02: Order 2004 - Omega Seamaster $7,800 - Card holder says unauthorized.\n")
    f.write("  -> Ship address was a freight forwarder in Netherlands. New customer. Lost.\n")
    f.write("Case #CB-2024-03: Order 1002 - Patek Philippe $8,750 - Unauthorized transaction.\n")
    f.write("  -> Temp email used. 3 failed payment attempts before success. No review done.\n")
    f.write("TOTAL LOSS YTD: ~$25,300\n")

# 4. Old (incomplete) fraud checklist
with open(os.path.join(BASE, "ops/checklists/old_fraud_checklist_v1.txt"), "w") as f:
    f.write("DRAFT FRAUD CHECKLIST (v1 - incomplete)\n")
    f.write("- Check if billing matches shipping\n")
    f.write("- Look at email domain\n")
    f.write("- ??? add more steps\n")
    f.write("TODO: get proper system in place\n")

# 5. SOP stub
with open(os.path.join(BASE, "ops/sops/order_review_sop_DRAFT.txt"), "w") as f:
    f.write("ORDER REVIEW SOP - DRAFT (not finalized)\n")
    f.write("Step 1: Someone checks the order\n")
    f.write("Step 2: ??? (ask manager)\n")
    f.write("Step 3: Ship or cancel\n")
    f.write("Last updated: never\n")

# 6. Inventory snapshot
with open(os.path.join(BASE, "store_data/inventory/watch_inventory_june2024.csv"), "w") as f:
    f.write("sku,brand,model,condition,price_usd,in_stock\n")
    f.write("W-001,Rolex,Submariner Date,Excellent,12500,1\n")
    f.write("W-002,Patek Philippe,Nautilus 5711,Good,45000,1\n")
    f.write("W-003,Omega,Speedmaster Pro,Very Good,4800,2\n")
    f.write("W-004,Audemars Piguet,Royal Oak,Fair,18000,1\n")
    f.write("W-005,Cartier,Santos,Good,7200,3\n")

# 7. Finance chargeback report
with open(os.path.join(BASE, "finance/chargebacks/chargeback_tracker_2024.csv"), "w") as f:
    f.write("month,num_chargebacks,total_loss_usd,chargeback_rate_pct\n")
    f.write("Jan,1,8750,1.8\n")
    f.write("Feb,0,0,0\n")
    f.write("Mar,1,7800,1.5\n")
    f.write("Apr,2,8750,2.1\n")
    f.write("May,0,0,0\n")
    f.write("Jun,1,0,0.4\n")

# 8. Finance revenue report
with open(os.path.join(BASE, "finance/reports/monthly_revenue_2024.csv"), "w") as f:
    f.write("month,gross_revenue_usd,num_orders,avg_order_value\n")
    f.write("Jan,48000,6,8000\n")
    f.write("Feb,32000,4,8000\n")
    f.write("Mar,51000,7,7286\n")
    f.write("Apr,42000,5,8400\n")
    f.write("May,38000,5,7600\n")
    f.write("Jun,29000,4,7250\n")

# 9. Marketing loyalty notes (distractor)
with open(os.path.join(BASE, "marketing/loyalty/loyalty_program_notes.txt"), "w") as f:
    f.write("Loyalty Program Ideas - TimeVault Boutique\n")
    f.write("- Reward repeat buyers with early access to new inventory\n")
    f.write("- VIP tier for customers who have spent >$10,000 lifetime\n")
    f.write("- Consider using an AI platform for retention\n")
    f.write("- Need to figure out how to identify trusted buyers vs new risky ones\n")

# 10. Shopify config notes (distractor)
with open(os.path.join(BASE, "it/shopify_config/shopify_settings_notes.txt"), "w") as f:
    f.write("Shopify Store Config Notes\n")
    f.write("- Using Shopify Payments\n")
    f.write("- No third-party fraud app installed\n")
    f.write("- Manual review: currently not set up\n")
    f.write("- Shopify built-in fraud analysis: enabled but not acted upon\n")

# 11. IT integrations (distractor)
with open(os.path.join(BASE, "it/integrations/third_party_apps.txt"), "w") as f:
    f.write("Third-party app evaluation\n")
    f.write("Evaluated: Signifyd, NoFraud, Kount\n")
    f.write("Decision: deferred - cost concern\n")
    f.write("Alternative: build internal checklist\n")

# 12. Marketing campaigns (distractor)
with open(os.path.join(BASE, "marketing/campaigns/email_campaign_q3_plan.txt"), "w") as f:
    f.write("Q3 Email Campaign Plan\n")
    f.write("- Welcome series for new subscribers\n")
    f.write("- Re-engagement for lapsed buyers (>6 months no purchase)\n")
    f.write("- Authentication certificate campaign for recent buyers\n")

# 13. ops/policies placeholder
with open(os.path.join(BASE, "ops/policies/return_policy_v2.txt"), "w") as f:
    f.write("RETURN POLICY v2\n")
    f.write("All sales final on pre-owned watches unless defect found within 3 days of receipt.\n")
    f.write("No return on watches shipped internationally.\n")

# 14. Customer data sample
with open(os.path.join(BASE, "store_data/customers/vip_customer_list.csv"), "w") as f:
    f.write("customer_id,email,total_spend_usd,num_orders,vip_status\n")
    f.write("C-001,collector@proton.me,18400,4,VIP\n")
    f.write("C-002,watch.enthusiast@gmail.com,12000,3,VIP\n")
    f.write("C-003,vip@clientmail.com,6800,1,Standard\n")

# 15. A partial internal memo
with open(os.path.join(BASE, "ops/sops/internal_memo_fraud_concern.txt"), "w") as f:
    f.write("INTERNAL MEMO\n")
    f.write("TO: Operations Team\n")
    f.write("FROM: Owner\n")
    f.write("DATE: 2024-07-01\n\n")
    f.write("We lost another $8,000 last month to a chargeback. Buyer ordered a Rolex Submariner,\n")
    f.write("used a shipping address we've never seen, and the email looked fake. We shipped it same day.\n")
    f.write("We NEED a proper system. No more same-day fulfillment on large orders without some kind of check.\n")
    f.write("Please figure this out - I'm tired of losing money on this.\n")
    f.write("\n- Marcus (Owner)\n")

print("Workspace generated successfully.")