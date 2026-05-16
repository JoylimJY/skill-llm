import sys
import json
import os
from pathlib import Path

def evaluate(workspace: str):
    checks = []
    total_score = 0.0

    # ── Helper ──────────────────────────────────────────────────────────
    def add_check(name, passed, detail, weight=1.0):
        checks.append({"name": name, "passed": passed, "detail": detail})
        return weight if passed else 0.0

    # ════════════════════════════════════════════════════════════════════
    # CHECK 1: Cleaned CSV exists in outputs/ and uses utf-8-sig encoding
    # ════════════════════════════════════════════════════════════════════
    cleaned_csv = None
    output_dir = Path("/mnt/user-data/outputs")
    csv_candidates = list(output_dir.rglob("*.csv"))
    # Also search workspace
    csv_candidates += list(Path(workspace).rglob("*.csv"))
    # Filter out the original input
    csv_candidates = [p for p in csv_candidates if "pharmacy_dispense_2024.csv" != p.name or "outputs" in str(p)]
    
    cleaned_csv_path = None
    for p in csv_candidates:
        if "outputs" in str(p) or "clean" in p.name.lower() or "processed" in p.name.lower() or "cleaned" in p.name.lower():
            cleaned_csv_path = p
            break
    # Fallback: any CSV in outputs
    if cleaned_csv_path is None:
        out_csvs = list(output_dir.rglob("*.csv"))
        if out_csvs:
            cleaned_csv_path = out_csvs[0]

    if cleaned_csv_path is None:
        total_score += add_check("cleaned_csv_exists", False,
            "No cleaned CSV found in /mnt/user-data/outputs/", 1.5)
    else:
        total_score += add_check("cleaned_csv_exists", True,
            f"Found cleaned CSV at {cleaned_csv_path}", 1.5)

        # Check utf-8-sig encoding (BOM marker)
        try:
            with open(cleaned_csv_path, "rb") as f:
                bom = f.read(3)
            is_utf8_sig = bom == b'\xef\xbb\xbf'
            total_score += add_check("utf8_sig_encoding", is_utf8_sig,
                f"BOM bytes: {bom.hex()} — {'utf-8-sig detected' if is_utf8_sig else 'utf-8-sig NOT used (must use utf-8-sig for Excel compatibility)'}", 1.5)
        except Exception as e:
            total_score += add_check("utf8_sig_encoding", False, f"Error reading file bytes: {e}", 1.5)

        # Check duplicates removed
        try:
            import pandas as pd
            df = pd.read_csv(cleaned_csv_path, encoding="utf-8-sig")
            original_rows = 315  # 300 + 15 duplicates
            # After dedup, should be <= 300
            dup_removed = len(df) <= 305  # allow some tolerance
            total_score += add_check("duplicates_removed", dup_removed,
                f"Cleaned CSV has {len(df)} rows. Expected ≤305 after removing 15 duplicates.", 1.0)
        except Exception as e:
            try:
                df = pd.read_csv(cleaned_csv_path, encoding="utf-8")
                dup_removed = len(df) <= 305
                total_score += add_check("duplicates_removed", dup_removed,
                    f"Cleaned CSV has {len(df)} rows (read as utf-8). Expected ≤305.", 1.0)
            except Exception as e2:
                total_score += add_check("duplicates_removed", False, f"Could not read CSV: {e2}", 1.0)

        # Check date standardization
        try:
            import pandas as pd
            try:
                df = pd.read_csv(cleaned_csv_path, encoding="utf-8-sig")
            except:
                df = pd.read_csv(cleaned_csv_path, encoding="utf-8")
            
            date_col = None
            for col in df.columns:
                if "日期" in col or "date" in col.lower():
                    date_col = col
                    break
            
            if date_col:
                sample = df[date_col].dropna().head(50).astype(str)
                # Check no Chinese date format remains
                has_chinese_date = sample.str.contains("年|月|日").any()
                has_us_date = sample.str.match(r'^\d{2}/\d{2}/\d{4}$').any()
                dates_standardized = not has_chinese_date and not has_us_date
                total_score += add_check("date_format_standardized", dates_standardized,
                    f"Date column '{date_col}' standardization: chinese_dates_remain={has_chinese_date}, us_format_remain={has_us_date}", 1.0)
            else:
                total_score += add_check("date_format_standardized", False,
                    "No date column found in cleaned CSV", 1.0)
        except Exception as e:
            total_score += add_check("date_format_standardized", False, f"Error: {e}", 1.0)

        # Check currency format cleaned (总金额 should be numeric)
        try:
            import pandas as pd
            try:
                df = pd.read_csv(cleaned_csv_path, encoding="utf-8-sig")
            except:
                df = pd.read_csv(cleaned_csv_path, encoding="utf-8")
            
            amount_col = None
            for col in df.columns:
                if "金额" in col or "amount" in col.lower() or "price" in col.lower():
                    amount_col = col
                    break
            
            if amount_col:
                # Check if column is numeric or can be converted
                col_data = df[amount_col].dropna()
                # Remove rows with N/A string
                col_data = col_data[col_data.astype(str) != "N/A"]
                try:
                    numeric_vals = pd.to_numeric(col_data, errors="coerce")
                    pct_numeric = numeric_vals.notna().mean()
                    has_yuan_symbol = col_data.astype(str).str.contains("¥").any()
                    currency_cleaned = pct_numeric >= 0.85 and not has_yuan_symbol
                    total_score += add_check("currency_format_cleaned", currency_cleaned,
                        f"Column '{amount_col}': {pct_numeric:.1%} numeric, yuan_symbol_remains={has_yuan_symbol}", 1.0)
                except Exception as e:
                    total_score += add_check("currency_format_cleaned", False, f"Numeric check error: {e}", 1.0)
            else:
                total_score += add_check("currency_format_cleaned", False,
                    "No amount/金额 column found in cleaned CSV", 1.0)
        except Exception as e:
            total_score += add_check("currency_format_cleaned", False, f"Error: {e}", 1.0)

    # ════════════════════════════════════════════════════════════════════
    # CHECK 2: Analysis report exists with required 5-section structure
    # ════════════════════════════════════════════════════════════════════
    report_path = None
    # Search for .md, .txt files in outputs and workspace
    report_candidates = list(output_dir.rglob("*.md")) + list(output_dir.rglob("*.txt"))
    report_candidates += list(Path(workspace).rglob("*.md")) + list(Path(workspace).rglob("*.txt"))
    # Exclude distractor files
    report_candidates = [p for p in report_candidates
                         if not any(x in str(p) for x in ["archive", "logs", "config", "scripts", "temp"])
                         and "error.log" not in p.name and "access" not in p.name]
    
    for p in report_candidates:
        try:
            content = p.read_text(encoding="utf-8", errors="ignore")
            if "数据分析报告" in content or "数据概况" in content:
                report_path = p
                break
        except:
            pass

    if report_path is None:
        total_score += add_check("report_exists", False,
            "No analysis report (.md or .txt) with '数据分析报告' found in outputs", 1.5)
        # Zero score for all sub-checks
        for section in ["数据概况", "数据质量", "核心发现", "处理流程说明", "后续建议"]:
            total_score += add_check(f"report_section_{section}", False,
                f"Report not found, cannot check section '{section}'", 0.5)
    else:
        total_score += add_check("report_exists", True,
            f"Report found at {report_path}", 1.5)

        try:
            report_content = report_path.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            report_content = ""
            total_score += add_check("report_readable", False, f"Cannot read report: {e}", 0.5)

        # Check all 5 required sections
        required_sections = ["数据概况", "数据质量", "核心发现", "处理流程说明", "后续建议"]
        for section in required_sections:
            found = section in report_content
            total_score += add_check(f"report_section_{section}", found,
                f"Section '### {section}' {'found' if found else 'MISSING'} in report", 0.5)

        # Check report mentions negative amounts / returns issue
        mentions_negative = any(kw in report_content for kw in ["负值", "退款", "负金额", "negative"])
        total_score += add_check("report_mentions_negatives", mentions_negative,
            "Report should mention negative amount rows (returns/refunds)", 0.5)

        # Check report mentions data quality issues with counts
        import re
        has_numbers = bool(re.search(r'\d+', report_content))
        mentions_quality = any(kw in report_content for kw in ["重复", "缺失", "duplicate", "missing", "N/A"])
        total_score += add_check("report_mentions_quality_with_data", has_numbers and mentions_quality,
            "Report should mention quality issues (duplicates/missing) with numeric evidence", 0.5)

        # Check processing log documents before/after row counts
        has_row_counts = bool(re.search(r'(行|rows?|记录)[^\n]*\d+', report_content, re.IGNORECASE))
        total_score += add_check("report_has_row_counts", has_row_counts,
            "Report/processing log should document row counts (before/after cleaning)", 0.5)

        # Check business-language interpretation (not just raw numbers)
        business_lang_keywords = ["说明", "建议", "表明", "意味", "原因", "因为", "反映", "导致"]
        has_business_lang = any(kw in report_content for kw in business_lang_keywords)
        total_score += add_check("report_uses_business_language", has_business_lang,
            "Report should use business-language interpretations, not just raw statistics", 0.5)

    # ════════════════════════════════════════════════════════════════════
    # CHECK 3: Input file encoding handled correctly (GBK → read properly)
    # ════════════════════════════════════════════════════════════════════
    # If the cleaned CSV exists and has Chinese content, encoding was handled
    if cleaned_csv_path:
        try:
            import pandas as pd
            try:
                df_check = pd.read_csv(cleaned_csv_path, encoding="utf-8-sig")
            except:
                df_check = pd.read_csv(cleaned_csv_path, encoding="utf-8")
            
            # Check Chinese text is properly preserved (not garbled)
            sample_text = df_check.to_string()
            has_chinese = bool(re.search(r'[\u4e00-\u9fff]', sample_text))
            total_score += add_check("encoding_handled_correctly", has_chinese,
                f"Cleaned CSV contains Chinese characters: {has_chinese}. Input was GBK-encoded.", 1.0)
        except Exception as e:
            total_score += add_check("encoding_handled_correctly", False,
                f"Could not verify Chinese encoding in output: {e}", 1.0)
    else:
        total_score += add_check("encoding_handled_correctly", False,
            "No cleaned CSV to verify encoding handling", 1.0)

    # ════════════════════════════════════════════════════════════════════
    # Final scoring
    # ════════════════════════════════════════════════════════════════════
    max_score = 14.5  # sum of all weights
    normalized = round(min(total_score / max_score, 1.0), 4)
    passed = normalized >= 0.60

    return {
        "passed": passed,
        "score": normalized,
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))