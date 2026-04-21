import json

# This script creates no input files because the prompt specifies a user request only,
# but to illustrate deterministic content, write a dummy file that could represent Shopify customer data

def main():
    customers = [
        {"name": "ShopEase", "employees": 350, "location": "USA", "technologies": ["Shopify"], "catalog_growth": True},
        {"name": "RetailPro", "employees": 450, "location": "USA", "technologies": ["Shopify", "Magento"], "catalog_growth": True},
        {"name": "QuickBuy", "employees": 120, "location": "USA", "technologies": ["Shopify"], "catalog_growth": True},
        {"name": "MegaMart", "employees": 380, "location": "USA", "technologies": ["Shopify"], "catalog_growth": False},
        {"name": "EcomPlus", "employees": 270, "location": "USA", "technologies": ["Shopify"], "catalog_growth": True},
        {"name": "ShopSmart", "employees": 50, "location": "USA", "technologies": ["Shopify"], "catalog_growth": True}
    ]
    with open("shopify_customers.json", "w") as f:
        json.dump(customers, f, indent=2)

if __name__ == "__main__":
    main()
