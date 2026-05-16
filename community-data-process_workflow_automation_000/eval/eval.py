#!/usr/bin/env python3
"""
Evaluation script for community-data-process skill task.
Usage: python eval.py /workspace
"""

import sys
import json
import traceback
from pathlib import Path
from datetime import datetime

try:
    import pandas as pd
except ImportError:
    print(json.dumps({"passed": False, "score": 0.0, "checks": [
        {"name": "import_pandas", "passed": False, "detail": "pandas not available in eval env"}
    ]}))
    sys.exit(0)

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")
downloads = workspace / "Downloads"
home_downloads = Path.home() / "Downloads"

# Prefer home/Downloads (symlink) if it resolves to workspace/Downloads
if home_downloads.is_symlink() or home_downloads.exists():
    search_dir = home_downloads
else:
    search_dir = downloads

checks = []

# ─── Helper ───────────────────────────────────────────────────────────────────

def find_file(pattern: str) -> Path | None:
    """Search in search_dir for a glob pattern."""
    hits = list(search_dir.glob(pattern))
    if not hits:
        # also try workspace-wide
        hits = list(workspace.rglob(pattern))
    return hits[0] if hits else None


def find_newest_source() -> tuple[Path | None, str]:
    """Return the newest 客户群导出*.xlsx by mtime and its download date."""
    files = list(search_dir.glob("客户群导出*.xlsx"))
    # Exclude cleaned files
    files = [f for f in files if "清理后" not in f.name]
    if not files:
        return None, ""
    newest = max(files, key=lambda p: p.stat().st_mtime)
    dl_date = datetime.fromtimestamp(newest.stat().st_mtime).strftime("%Y-%m-%d")
    return newest, dl_date


def add_check(name: str, passed: bool, detail: str):
    checks.append({"name": name, "passed": passed, "detail": detail})


# ─── Check 0: Newest source file identification ────────────────────────────
try:
    src_path, expected_dl_date = find_newest_source()
    if src_path is None:
        add_check("source_file_exists", False, "No 客户群导出*.xlsx found")
    else:
        add_check("source_file_exists", True,
                  f"Newest source: {src_path.name}, download_date={expected_dl_date}")
except Exception as e:
    add_check("source_file_exists", False, f"Exception: {traceback.format_exc()}")
    src_path, expected_dl_date = None, ""

EXPECTED_DL_DATE = "2025-06-15"

# ─── Check 1: Cleaned output file exists ──────────────────────────────────
try:
    clean_file = find_file("客户群导出_清理后_温冷一期 + 试点店_*.xlsx")
    if clean_file is None:
        add_check("cleaned_file_exists", False, "Cannot find 客户群导出_清理后_温冷一期 + 试点店_YYYYMMDD.xlsx")
    else:
        add_check("cleaned_file_exists", True, f"Found: {clean_file.name}")
except Exception:
    add_check("cleaned_file_exists", False, traceback.format_exc())
    clean_file = None

# ─── Check 2: Cleaned file tag filter ─────────────────────────────────────
SRC_COLS = [
    "群ID", "群名称", "群主", "群管理员",
    "群人数", "群活跃", "群类型",
    "员工人数", "客户人数", "今日入群", "今日退群", "今日消息",
    "入群时间", "最后发言时间", "群标签"
]
TARGET_TAGS = {"温冷一期", "试点店"}

try:
    if clean_file:
        df_clean = pd.read_excel(str(clean_file), header=0)
        # Ensure we have the expected column set
        if "群标签" in df_clean.columns:
            bad_tags = df_clean[~df_clean["群标签"].isin(TARGET_TAGS)]
            if len(bad_tags) > 0:
                add_check("tag_filter_correct", False,
                          f"{len(bad_tags)} rows with disallowed tags: {bad_tags['群标签'].unique().tolist()}")
            elif len(df_clean) == 0:
                add_check("tag_filter_correct", False, "Cleaned file is empty — filter too aggressive?")
            else:
                add_check("tag_filter_correct", True,
                          f"{len(df_clean)} rows, all tags in TARGET_TAGS")
        else:
            add_check("tag_filter_correct", False,
                      f"'群标签' column not found. Columns: {df_clean.columns.tolist()}")
    else:
        add_check("tag_filter_correct", False, "Cleaned file not found, skipping")
except Exception:
    add_check("tag_filter_correct", False, traceback.format_exc())
    df_clean = None

# ─── Check 3: Numeric columns are int ──────────────────────────────────────
NUMERIC_COLS = ["群人数", "员工人数", "客户人数", "今日入群", "今日退群", "今日消息"]
try:
    if clean_file and 'df_clean' in dir() and df_clean is not None:
        bad_cols = []
        for col in NUMERIC_COLS:
            if col in df_clean.columns:
                if not pd.api.types.is_integer_dtype(df_clean[col]):
                    bad_cols.append(f"{col}({df_clean[col].dtype})")
        if bad_cols:
            add_check("numeric_cols_int", False, f"Non-int columns: {bad_cols}")
        else:
            add_check("numeric_cols_int", True, "All 6 numeric columns are integer dtype")
    else:
        add_check("numeric_cols_int", False, "Cleaned file not available")
except Exception:
    add_check("numeric_cols_int", False, traceback.format_exc())

# ─── Check 4: Audit report exists ─────────────────────────────────────────
try:
    report_file = find_file("数据校对报告_*.txt")
    if report_file is None:
        add_check("audit_report_exists", False, "Cannot find 数据校对报告_YYYYMMDD.txt")
    else:
        content = report_file.read_text(encoding="utf-8")
        add_check("audit_report_exists", True, f"Found: {report_file.name}")
except Exception:
    add_check("audit_report_exists", False, traceback.format_exc())
    report_file = None

# ─── Check 5: Audit report contains PASS ──────────────────────────────────
try:
    if report_file:
        content = report_file.read_text(encoding="utf-8")
        if "PASS" in content and "总体结论: PASS" in content:
            add_check("audit_report_pass", True, "Report contains 总体结论: PASS")
        elif "PASS" in content:
            add_check("audit_report_pass", False,
                      "Report has PASS entries but 总体结论 is not PASS")
        else:
            add_check("audit_report_pass", False,
                      f"Report does not contain PASS. Snippet: {content[:300]}")
    else:
        add_check("audit_report_pass", False, "Audit report not found")
except Exception:
    add_check("audit_report_pass", False, traceback.format_exc())

# ─── Check 6: Merged BI file exists ───────────────────────────────────────
try:
    bi_merged = find_file("BI_社群数据上传_已更新_*.xlsx")
    if bi_merged is None:
        add_check("merged_file_exists", False, "Cannot find BI_社群数据上传_已更新_YYYYMMDD.xlsx")
    else:
        add_check("merged_file_exists", True, f"Found: {bi_merged.name}")
except Exception:
    add_check("merged_file_exists", False, traceback.format_exc())
    bi_merged = None

# ─── Check 7: D-column (统计日期) = source file download date ─────────────
# THE KEY PROPRIETARY TRAP: must be 2025-06-15, NOT today
try:
    if bi_merged:
        df_bi = pd.read_excel(str(bi_merged), header=0)
        if "统计日期" not in df_bi.columns:
            add_check("d_col_download_date", False,
                      f"'统计日期' column not found. Columns: {df_bi.columns.tolist()}")
        else:
            # New rows should have 统计日期 = "2025-06-15"
            new_rows = df_bi[df_bi["统计日期"].astype(str).str.strip() == EXPECTED_DL_DATE]
            today_str = datetime.now().strftime("%Y-%m-%d")
            today_rows = df_bi[df_bi["统计日期"].astype(str).str.strip() == today_str]

            if len(new_rows) > 0 and len(today_rows) == 0:
                add_check("d_col_download_date", True,
                          f"Found {len(new_rows)} rows with 统计日期={EXPECTED_DL_DATE} (correct download date). "
                          f"No rows with today={today_str} (correct — script date not used).")
            elif len(new_rows) > 0 and len(today_rows) > 0:
                add_check("d_col_download_date", False,
                          f"Mixed dates: {len(new_rows)} rows with {EXPECTED_DL_DATE}, "
                          f"{len(today_rows)} rows with today={today_str}. Should use file date only.")
            elif len(today_rows) > 0:
                add_check("d_col_download_date", False,
                          f"TRAP TRIGGERED: {len(today_rows)} rows use today's date ({today_str}) "
                          f"instead of file download date ({EXPECTED_DL_DATE}). "
                          f"The D column must use the source file's creation/download date.")
            else:
                unique_dates = df_bi["统计日期"].astype(str).unique().tolist()
                add_check("d_col_download_date", False,
                          f"No rows with expected date {EXPECTED_DL_DATE}. "
                          f"Found dates: {unique_dates}")
    else:
        add_check("d_col_download_date", False, "Merged file not found")
except Exception:
    add_check("d_col_download_date", False, traceback.format_exc())

# ─── Check 8: Column mapping E-S (source A-O → target E-S) ───────────────
BI_COLS_EXPECTED = ["ColA", "ColB", "ColC", "统计日期"] + SRC_COLS  # 19 total
try:
    if bi_merged:
        if 'df_bi' not in dir():
            df_bi = pd.read_excel(str(bi_merged), header=0)
        actual_cols = df_bi.columns.tolist()
        # Check that SRC_COLS appear at positions 4..18 (0-indexed)
        expected_e_to_s = SRC_COLS
        if len(actual_cols) >= 19:
            actual_e_to_s = actual_cols[4:19]
            if actual_e_to_s == expected_e_to_s:
                add_check("column_mapping_e_to_s", True,
                          f"Columns E-S correctly mapped: {actual_e_to_s}")
            else:
                add_check("column_mapping_e_to_s", False,
                          f"E-S columns mismatch. Expected: {expected_e_to_s}, Got: {actual_e_to_s}")
        else:
            add_check("column_mapping_e_to_s", False,
                      f"BI file has only {len(actual_cols)} columns, need 19. Cols: {actual_cols}")
    else:
        add_check("column_mapping_e_to_s", False, "Merged file not found")
except Exception:
    add_check("column_mapping_e_to_s", False, traceback.format_exc())

# ─── Check 9: A-C columns are blank ───────────────────────────────────────
try:
    if bi_merged:
        if 'df_bi' not in dir():
            df_bi = pd.read_excel(str(bi_merged), header=0)
        abc_cols = ["ColA", "ColB", "ColC"]
        bad = []
        for col in abc_cols:
            if col in df_bi.columns:
                non_empty = df_bi[col].dropna().astype(str).str.strip().ne("").sum()
                if non_empty > 0:
                    bad.append(f"{col}: {non_empty} non-empty values")
        if bad:
            add_check("abc_cols_blank", False, f"A-C columns not blank: {bad}")
        else:
            add_check("abc_cols_blank", True, "Columns A-C (ColA/ColB/ColC) are all blank ✓")
    else:
        add_check("abc_cols_blank", False, "Merged file not found")
except Exception:
    add_check("abc_cols_blank", False, traceback.format_exc())

# ─── Check 10: Incremental merge (old rows preserved) ─────────────────────
try:
    if bi_merged:
        if 'df_bi' not in dir():
            df_bi = pd.read_excel(str(bi_merged), header=0)
        # Original BI had 20 rows with 统计日期=2025-06-01
        old_rows = df_bi[df_bi["统计日期"].astype(str).str.strip() == "2025-06-01"]
        if len(old_rows) >= 20:
            add_check("incremental_merge", True,
                      f"Old rows preserved: {len(old_rows)} rows with 统计日期=2025-06-01")
        elif len(old_rows) > 0:
            add_check("incremental_merge", False,
                      f"Only {len(old_rows)}/20 old rows preserved (expected 20)")
        else:
            add_check("incremental_merge", False,
                      "Old rows (统计日期=2025-06-01) not found — incremental merge failed")
    else:
        add_check("incremental_merge", False, "Merged file not found")
except Exception:
    add_check("incremental_merge", False, traceback.format_exc())

# ─── Check 11: New rows count matches cleaned rows ─────────────────────────
try:
    if bi_merged and clean_file:
        if 'df_bi' not in dir():
            df_bi = pd.read_excel(str(bi_merged), header=0)
        if 'df_clean' not in dir() or df_clean is None:
            df_clean = pd.read_excel(str(clean_file), header=0)
        new_rows_bi = df_bi[df_bi["统计日期"].astype(str).str.strip() == EXPECTED_DL_DATE]
        n_clean = len(df_clean)
        n_new = len(new_rows_bi)
        if n_clean == n_new and n_clean > 0:
            add_check("new_rows_count_matches", True,
                      f"New rows in BI ({n_new}) == cleaned rows ({n_clean}) ✓")
        else:
            add_check("new_rows_count_matches", False,
                      f"New rows in BI ({n_new}) ≠ cleaned rows ({n_clean})")
    else:
        add_check("new_rows_count_matches", False, "Merged or cleaned file not found")
except Exception:
    add_check("new_rows_count_matches", False, traceback.format_exc())

# ─── Scoring ──────────────────────────────────────────────────────────────
# Weights for each check
WEIGHTS = {
    "source_file_exists":        0.04,
    "cleaned_file_exists":       0.07,
    "tag_filter_correct":        0.10,
    "numeric_cols_int":          0.07,
    "audit_report_exists":       0.05,
    "audit_report_pass":         0.07,
    "merged_file_exists":        0.07,
    "d_col_download_date":       0.20,  # THE KEY TRAP
    "column_mapping_e_to_s":     0.13,
    "abc_cols_blank":            0.08,
    "incremental_merge":         0.07,
    "new_rows_count_matches":    0.05,
}

total_weight = sum(WEIGHTS.values())
score = 0.0
for ch in checks:
    w = WEIGHTS.get(ch["name"], 0.0)
    if ch["passed"]:
        score += w

score = round(score / total_weight, 4)
passed = score >= 0.75 and all(
    c["passed"] for c in checks
    if c["name"] in ("d_col_download_date", "tag_filter_correct",
                     "column_mapping_e_to_s", "incremental_merge")
)

result = {
    "passed": passed,
    "score": score,
    "checks": checks,
}
print(json.dumps(result, ensure_ascii=False, indent=2))