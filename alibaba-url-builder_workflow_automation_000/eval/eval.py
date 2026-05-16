import sys
import json
import re
from pathlib import Path
from urllib.parse import urlparse, parse_qs, unquote_plus

workspace = sys.argv[1]

checks = []
passed_all = True

def find_manifest(workspace):
    matches = list(Path(workspace).rglob("alibaba_url_manifest.json"))
    return matches[0] if matches else None

def record(name, passed, detail):
    checks.append({"name": name, "passed": passed, "detail": detail})
    return passed

# --- Find the output file ---
manifest_path = find_manifest(workspace)
if not manifest_path:
    record("file_exists", False, "alibaba_url_manifest.json not found anywhere in workspace")
    print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
    sys.exit(0)
else:
    record("file_exists", True, f"Found at {manifest_path}")

try:
    with open(manifest_path) as f:
        manifest = json.load(f)
except Exception as e:
    record("file_parseable", False, f"JSON parse error: {e}")
    print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
    sys.exit(0)

record("file_parseable", True, "Valid JSON")

# Helper: find entry by task_id
def get_url(manifest, task_id):
    """Try to find the URL for a given task_id in various manifest structures."""
    # Could be list of objects or dict keyed by task_id
    if isinstance(manifest, list):
        for item in manifest:
            if isinstance(item, dict):
                tid = item.get("task_id") or item.get("id")
                if tid == task_id:
                    return item.get("url") or item.get("URL") or item.get("link")
    elif isinstance(manifest, dict):
        # keyed by task_id
        if task_id in manifest:
            val = manifest[task_id]
            if isinstance(val, str):
                return val
            if isinstance(val, dict):
                return val.get("url") or val.get("URL") or val.get("link")
        # check "tasks" or "results" sub-key
        for subkey in ["tasks", "results", "urls", "entries"]:
            if subkey in manifest and isinstance(manifest[subkey], list):
                for item in manifest[subkey]:
                    if isinstance(item, dict):
                        tid = item.get("task_id") or item.get("id")
                        if tid == task_id:
                            return item.get("url") or item.get("URL") or item.get("link")
    return None

def has_tracking(url):
    return "traffic_type=ags_llm" in url

# ========================
# T1: category_search for "noise cancelling headphones" in Consumer Electronics
# Must have: SearchText with the query, categoryId=201151901, has4Tab=true, tab=product, traffic_type=ags_llm
# ========================
try:
    t1_url = get_url(manifest, "T1")
    if not t1_url:
        record("T1_url_present", False, "No URL found for T1")
    else:
        record("T1_url_present", True, f"URL: {t1_url}")
        # Check tracking param
        ok_tracking = has_tracking(t1_url)
        record("T1_tracking_param", ok_tracking, 
               "traffic_type=ags_llm present" if ok_tracking else "Missing traffic_type=ags_llm")
        
        # Check base domain
        ok_domain = "www.alibaba.com/trade/search" in t1_url
        record("T1_search_endpoint", ok_domain, 
               "Correct search endpoint" if ok_domain else f"Wrong endpoint in {t1_url}")
        
        # Check SearchText contains the query (url-decoded check)
        ok_query = ("noise" in t1_url.lower() and "cancelling" in t1_url.lower() or 
                    "noise+cancelling" in t1_url.lower() or 
                    "noise%2Bcancelling" in t1_url.lower() or
                    "noise-cancelling" in t1_url.lower() or
                    re.search(r'SearchText=.*noise.*cancelling', t1_url, re.IGNORECASE))
        # More permissive - just check that the terms are present in SearchText
        st_match = re.search(r'SearchText=([^&]+)', t1_url, re.IGNORECASE)
        if st_match:
            st_val = unquote_plus(st_match.group(1)).lower()
            ok_query = "noise" in st_val and "cancelling" in st_val
        record("T1_search_text", bool(ok_query), 
               f"SearchText contains 'noise cancelling': {ok_query}")
        
        # Check categoryId=201151901 (Consumer Electronics)
        ok_cat = "categoryId=201151901" in t1_url
        record("T1_category_id", ok_cat, 
               "categoryId=201151901 present" if ok_cat else f"Missing/wrong categoryId in {t1_url}")
        
        # Check has4Tab=true
        ok_4tab = "has4Tab=true" in t1_url
        record("T1_has4tab", ok_4tab, 
               "has4Tab=true present" if ok_4tab else "Missing has4Tab=true")
        
        # Check tab=product
        ok_tab = "tab=product" in t1_url
        record("T1_tab_product", ok_tab, 
               "tab=product present" if ok_tab else "Missing tab=product")
except Exception as e:
    record("T1_exception", False, str(e))

# ========================
# T2: category_search for "foldable electric scooter" in Electric Scooters (categoryId=100006091)
# ========================
try:
    t2_url = get_url(manifest, "T2")
    if not t2_url:
        record("T2_url_present", False, "No URL found for T2")
    else:
        record("T2_url_present", True, f"URL: {t2_url}")
        ok_tracking = has_tracking(t2_url)
        record("T2_tracking_param", ok_tracking, 
               "traffic_type=ags_llm present" if ok_tracking else "Missing traffic_type=ags_llm")
        
        ok_domain = "www.alibaba.com/trade/search" in t2_url
        record("T2_search_endpoint", ok_domain, "Correct endpoint" if ok_domain else "Wrong endpoint")
        
        # SearchText check
        st_match = re.search(r'SearchText=([^&]+)', t2_url, re.IGNORECASE)
        ok_query = False
        if st_match:
            st_val = unquote_plus(st_match.group(1)).lower()
            ok_query = "foldable" in st_val and ("electric" in st_val or "scooter" in st_val)
        record("T2_search_text", ok_query, 
               f"SearchText contains expected terms: {ok_query}")
        
        ok_cat = "categoryId=100006091" in t2_url
        record("T2_category_id", ok_cat, 
               "categoryId=100006091 present" if ok_cat else f"Missing/wrong categoryId: {t2_url}")
except Exception as e:
    record("T2_exception", False, str(e))

# ========================
# T3: Product detail URL
# Title: "Pro-X Noise Cancelling Headphones (Over-Ear, ANC) 2024 Edition!"
# After sanitization (alphanumeric + hyphens, lowercase, spaces→hyphens, remove special chars):
# "Pro-X Noise Cancelling Headphones Over-Ear ANC 2024 Edition" → "pro-x-noise-cancelling-headphones-over-ear-anc-2024-edition"
# product_id: 1600987654321099
# ========================
try:
    t3_url = get_url(manifest, "T3")
    if not t3_url:
        record("T3_url_present", False, "No URL found for T3")
    else:
        record("T3_url_present", True, f"URL: {t3_url}")
        ok_tracking = has_tracking(t3_url)
        record("T3_tracking_param", ok_tracking, 
               "traffic_type=ags_llm present" if ok_tracking else "Missing traffic_type=ags_llm")
        
        ok_domain = "www.alibaba.com/product-detail/" in t3_url
        record("T3_product_detail_endpoint", ok_domain, 
               "Correct product-detail endpoint" if ok_domain else "Wrong endpoint")
        
        # Check product_id present in URL
        ok_pid = "1600987654321099" in t3_url
        record("T3_product_id", ok_pid, 
               "Product ID 1600987654321099 present" if ok_pid else "Missing product ID")
        
        # Extract the slug part
        slug_match = re.search(r'/product-detail/([^_?]+)', t3_url)
        if slug_match:
            slug = slug_match.group(1)
            # Must be lowercase
            ok_lower = slug == slug.lower()
            record("T3_slug_lowercase", ok_lower, 
                   f"Slug is lowercase: '{slug}'" if ok_lower else f"Slug not lowercase: '{slug}'")
            
            # Must not contain parentheses, commas, exclamation marks, or quotes
            ok_no_special = not any(c in slug for c in ['(', ')', ',', '!', '"', "'", ' '])
            record("T3_slug_no_special_chars", ok_no_special, 
                   f"No special chars in slug: '{slug}'" if ok_no_special else f"Special chars found in '{slug}'")
            
            # Must contain key words as hyphen-separated
            ok_key_words = "noise" in slug and "cancelling" in slug and "headphones" in slug
            record("T3_slug_key_words", ok_key_words, 
                   f"Key words in slug: '{slug}'")
        else:
            record("T3_slug_extraction", False, f"Could not extract slug from {t3_url}")
except Exception as e:
    record("T3_exception", False, str(e))

# ========================
# T4: Product detail URL
# Title: 'Smart LED TV 55" 4K Ultra HD -- Wall Mount Ready'
# After sanitization: remove ", special chars; spaces→hyphens; lowercase
# "smart-led-tv-55-4k-ultra-hd--wall-mount-ready" (double hyphens acceptable) or "smart-led-tv-55-4k-ultra-hd-wall-mount-ready"
# product_id: 62000123456789
# ========================
try:
    t4_url = get_url(manifest, "T4")
    if not t4_url:
        record("T4_url_present", False, "No URL found for T4")
    else:
        record("T4_url_present", True, f"URL: {t4_url}")
        ok_tracking = has_tracking(t4_url)
        record("T4_tracking_param", ok_tracking, 
               "traffic_type=ags_llm present" if ok_tracking else "Missing traffic_type=ags_llm")
        
        ok_domain = "www.alibaba.com/product-detail/" in t4_url
        record("T4_product_detail_endpoint", ok_domain, "Correct endpoint" if ok_domain else "Wrong endpoint")
        
        ok_pid = "62000123456789" in t4_url
        record("T4_product_id", ok_pid, 
               "Product ID 62000123456789 present" if ok_pid else "Missing product ID")
        
        slug_match = re.search(r'/product-detail/([^_?]+)', t4_url)
        if slug_match:
            slug = slug_match.group(1)
            ok_lower = slug == slug.lower()
            record("T4_slug_lowercase", ok_lower, f"Slug lowercase check: '{slug}'")
            
            # No quotes or special chars
            ok_no_special = not any(c in slug for c in ['"', "'", ' ', '!', '(', ')'])
            record("T4_slug_no_special_chars", ok_no_special, 
                   f"No special chars in '{slug}'" if ok_no_special else f"Special chars in '{slug}'")
            
            ok_key_words = "smart" in slug and ("led" in slug or "tv" in slug) and "4k" in slug
            record("T4_slug_key_words", ok_key_words, f"Key words in slug: '{slug}'")
        else:
            record("T4_slug_extraction", False, f"Could not extract slug from {t4_url}")
except Exception as e:
    record("T4_exception", False, str(e))

# ========================
# T5: Supplier profile URL for subdomain 'shenzhen-innovatech'
# Pattern: https://shenzhen-innovatech.en.alibaba.com/company_profile.html?traffic_type=ags_llm
# ========================
try:
    t5_url = get_url(manifest, "T5")
    if not t5_url:
        record("T5_url_present", False, "No URL found for T5")
    else:
        record("T5_url_present", True, f"URL: {t5_url}")
        ok_tracking = has_tracking(t5_url)
        record("T5_tracking_param", ok_tracking, 
               "traffic_type=ags_llm present" if ok_tracking else "Missing traffic_type=ags_llm")
        
        ok_pattern = "shenzhen-innovatech.en.alibaba.com/company_profile.html" in t5_url
        record("T5_supplier_profile_pattern", ok_pattern, 
               "Correct supplier profile URL pattern" if ok_pattern else f"Wrong pattern: {t5_url}")
        
        ok_https = t5_url.startswith("https://")
        record("T5_https", ok_https, "Uses HTTPS" if ok_https else "Missing HTTPS")
except Exception as e:
    record("T5_exception", False, str(e))

# ========================
# T6: Supplier product search for 'audiopromax' with query 'wireless earbuds'
# Pattern: https://audiopromax.en.alibaba.com/search/product?SearchText=wireless+earbuds&traffic_type=ags_llm
# ========================
try:
    t6_url = get_url(manifest, "T6")
    if not t6_url:
        record("T6_url_present", False, "No URL found for T6")
    else:
        record("T6_url_present", True, f"URL: {t6_url}")
        ok_tracking = has_tracking(t6_url)
        record("T6_tracking_param", ok_tracking, 
               "traffic_type=ags_llm present" if ok_tracking else "Missing traffic_type=ags_llm")
        
        ok_subdomain = "audiopromax.en.alibaba.com" in t6_url
        record("T6_supplier_subdomain", ok_subdomain, 
               "Correct supplier subdomain" if ok_subdomain else f"Wrong subdomain in {t6_url}")
        
        ok_search_path = "/search/product" in t6_url
        record("T6_search_product_path", ok_search_path, 
               "/search/product path present" if ok_search_path else f"Missing /search/product in {t6_url}")
        
        st_match = re.search(r'SearchText=([^&]+)', t6_url, re.IGNORECASE)
        ok_query = False
        if st_match:
            st_val = unquote_plus(st_match.group(1)).lower()
            ok_query = "wireless" in st_val and "earbuds" in st_val
        record("T6_search_text", ok_query, f"SearchText contains 'wireless earbuds': {ok_query}")
except Exception as e:
    record("T6_exception", False, str(e))

# ========================
# T7: AI Mode URL
# Must be: https://aimode.alibaba.com/?traffic_type=ags_llm
# ========================
try:
    t7_url = get_url(manifest, "T7")
    if not t7_url:
        record("T7_url_present", False, "No URL found for T7")
    else:
        record("T7_url_present", True, f"URL: {t7_url}")
        ok_tracking = has_tracking(t7_url)
        record("T7_tracking_param", ok_tracking, 
               "traffic_type=ags_llm present" if ok_tracking else "Missing traffic_type=ags_llm")
        
        ok_aimode = "aimode.alibaba.com" in t7_url
        record("T7_aimode_domain", ok_aimode, 
               "Correct aimode.alibaba.com domain" if ok_aimode else f"Wrong domain: {t7_url}")
except Exception as e:
    record("T7_exception", False, str(e))

# ========================
# T8: Top Ranking URL
# Must be: https://sale.alibaba.com/p/dviiav4th/index.html?traffic_type=ags_llm
# ========================
try:
    t8_url = get_url(manifest, "T8")
    if not t8_url:
        record("T8_url_present", False, "No URL found for T8")
    else:
        record("T8_url_present", True, f"URL: {t8_url}")
        ok_tracking = has_tracking(t8_url)
        record("T8_tracking_param", ok_tracking, 
               "traffic_type=ags_llm present" if ok_tracking else "Missing traffic_type=ags_llm")
        
        ok_top_ranking = "sale.alibaba.com/p/dviiav4th/index.html" in t8_url
        record("T8_top_ranking_url", ok_top_ranking, 
               "Correct top ranking URL path" if ok_top_ranking else f"Wrong URL: {t8_url}")
except Exception as e:
    record("T8_exception", False, str(e))

# ========================
# T9: RFQ URL
# Must be: https://rfq.alibaba.com/rfq/profession.htm?traffic_type=ags_llm
# ========================
try:
    t9_url = get_url(manifest, "T9")
    if not t9_url:
        record("T9_url_present", False, "No URL found for T9")
    else:
        record("T9_url_present", True, f"URL: {t9_url}")
        ok_tracking = has_tracking(t9_url)
        record("T9_tracking_param", ok_tracking, 
               "traffic_type=ags_llm present" if ok_tracking else "Missing traffic_type=ags_llm")
        
        ok_rfq = "rfq.alibaba.com/rfq/profession.htm" in t9_url
        record("T9_rfq_url", ok_rfq, 
               "Correct RFQ URL" if ok_rfq else f"Wrong RFQ URL: {t9_url}")
except Exception as e:
    record("T9_exception", False, str(e))

# ========================
# Compute final score
# ========================
total = len(checks)
passed_count = sum(1 for c in checks if c["passed"])
score = round(passed_count / total, 3) if total > 0 else 0.0
final_passed = score >= 0.80  # 80% threshold to pass

print(json.dumps({
    "passed": final_passed,
    "score": score,
    "checks": checks
}, indent=2))