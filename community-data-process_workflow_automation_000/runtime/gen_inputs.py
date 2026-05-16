#!/usr/bin/env python3
"""
Generate the sandbox workspace for the community-data-process skill evaluation.
Creates:
  - A realistic Downloads directory with multiple 客户群导出*.xlsx files (decoys + target)
  - An existing BI_社群数据上传表.xlsx with some pre-existing rows
  - The skill scripts at the expected path
  - Various distractor files
"""

import os
import random
import time
import shutil
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows

random.seed(42)

WORKSPACE = Path("/workspace")

# ── helper ────────────────────────────────────────────────────────────────────

def set_file_times(path: Path, ts: float):
    """Set atime and mtime; creation time on Linux = mtime approximation."""
    os.utime(str(path), (ts, ts))


def make_dirs():
    dirs = [
        WORKSPACE / "Downloads",
        WORKSPACE / "home" / "user" / "Documents" / "reports",
        WORKSPACE / "home" / "user" / "Desktop",
        WORKSPACE / "home" / "user" / ".config" / "autostart",
        WORKSPACE / "var" / "log" / "community",
        WORKSPACE / "tmp" / "bi_staging",
        WORKSPACE / "archive" / "2024" / "Q1",
        WORKSPACE / "archive" / "2024" / "Q2",
        WORKSPACE / "scripts" / "legacy",
        Path.home() / ".openclaw" / "workspace-pm" / "skills" / "community-data-process",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)


# ── source file columns ───────────────────────────────────────────────────────
SRC_COLUMNS = [
    "群ID", "群名称", "群主", "群管理员",
    "群人数", "群活跃", "群类型",
    "员工人数", "客户人数", "今日入群", "今日退群", "今日消息",
    "入群时间", "最后发言时间", "群标签"
]

ALL_TAGS = ["温冷一期", "试点店", "标杆店", "普通群", "内部群", "VIP群"]
TARGET_TAGS = {"温冷一期", "试点店"}


def make_source_rows(n_rows=60, seed=0):
    rng = random.Random(seed)
    rows = []
    for i in range(n_rows):
        tag = rng.choice(ALL_TAGS)
        rows.append({
            "群ID": f"GRP{10000 + i}",
            "群名称": f"北汽{'经销商' if i % 2 == 0 else '客户'}群{i:03d}",
            "群主": f"员工{rng.randint(1, 50):03d}",
            "群管理员": f"管理员{rng.randint(1, 10):02d}",
            "群人数": rng.randint(10, 500),
            "群活跃": rng.choice(["活跃", "一般", "沉默"]),
            "群类型": rng.choice(["客户群", "内部群", "经销商群"]),
            "员工人数": rng.randint(1, 20),
            "客户人数": rng.randint(5, 480),
            "今日入群": rng.randint(0, 15),
            "今日退群": rng.randint(0, 5),
            "今日消息": rng.randint(0, 200),
            "入群时间": (datetime(2024, 1, 1) + timedelta(days=rng.randint(0, 365))).strftime("%Y-%m-%d"),
            "最后发言时间": (datetime(2024, 6, 1) + timedelta(days=rng.randint(0, 60))).strftime("%Y-%m-%d %H:%M"),
            "群标签": tag,
        })
    return rows


def write_xlsx_no_header_style(path: Path, rows, columns):
    """Write xlsx with data starting at row 1 (header row 1, data row 2+)."""
    df = pd.DataFrame(rows, columns=columns)
    with pd.ExcelWriter(str(path), engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Sheet1")


# ── BI target file ─────────────────────────────────────────────────────────────
BI_COLUMNS_TARGET = (
    ["ColA", "ColB", "ColC", "统计日期"] +          # A B C D
    SRC_COLUMNS                                       # E..S
)

def make_bi_target(path: Path):
    """Pre-populate BI file with 20 existing rows from an older export."""
    rng = random.Random(99)
    existing_rows = []
    for i in range(20):
        tag = rng.choice(list(TARGET_TAGS))
        row = {
            "ColA": "",
            "ColB": "",
            "ColC": "",
            "统计日期": "2025-06-01",
            "群ID": f"GRP{20000 + i}",
            "群名称": f"老数据群{i:03d}",
            "群主": f"员工{rng.randint(1, 50):03d}",
            "群管理员": f"管理员{rng.randint(1, 10):02d}",
            "群人数": rng.randint(10, 500),
            "群活跃": rng.choice(["活跃", "一般"]),
            "群类型": "客户群",
            "员工人数": rng.randint(1, 20),
            "客户人数": rng.randint(5, 480),
            "今日入群": rng.randint(0, 15),
            "今日退群": rng.randint(0, 5),
            "今日消息": rng.randint(0, 200),
            "入群时间": "2024-03-15",
            "最后发言时间": "2025-06-01 10:00",
            "群标签": tag,
        }
        existing_rows.append(row)
    df = pd.DataFrame(existing_rows, columns=BI_COLUMNS_TARGET)
    with pd.ExcelWriter(str(path), engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Sheet1")


# ── create source export files ─────────────────────────────────────────────────
def create_export_files(downloads: Path):
    """
    Create 3 客户群导出 files with different 'creation' timestamps.
    The NEWEST by mtime is the one from 2025-06-15 (the target date).
    Two older decoys exist.
    """
    files_info = [
        # (filename_suffix, seed, fake_ts_str, is_target)
        ("20250610", 10, "2025-06-10 09:00:00", False),
        ("20250612", 20, "2025-06-12 14:30:00", False),
        ("20250615", 42, "2025-06-15 08:45:00", True),   # ← newest, THIS is the one
    ]

    target_path = None
    for suffix, seed, ts_str, is_target in files_info:
        fname = downloads / f"客户群导出{suffix}.xlsx"
        rows = make_source_rows(n_rows=60, seed=seed)
        write_xlsx_no_header_style(fname, rows, SRC_COLUMNS)
        # Set file mtime to simulate download date
        ts = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S").timestamp()
        set_file_times(fname, ts)
        if is_target:
            target_path = fname

    return target_path


# ── distractor files ──────────────────────────────────────────────────────────
def create_distractors(workspace: Path):
    distractors = [
        workspace / "Downloads" / "客户群导出备份_旧版.xlsx",
        workspace / "Downloads" / "经销商联系表_2025.xlsx",
        workspace / "Downloads" / "report_draft.xlsx",
        workspace / "home" / "user" / "Documents" / "reports" / "monthly_kpi_june.xlsx",
        workspace / "home" / "user" / "Documents" / "reports" / "bi_upload_test.xlsx",
        workspace / "home" / "user" / "Desktop" / "temp_notes.txt",
        workspace / "archive" / "2024" / "Q1" / "客户群导出_archive_Q1.xlsx",
        workspace / "archive" / "2024" / "Q2" / "客户群导出_archive_Q2.xlsx",
        workspace / "scripts" / "legacy" / "old_merge.py",
        workspace / "var" / "log" / "community" / "run_20250614.log",
        workspace / "tmp" / "bi_staging" / "staging_buffer.xlsx",
    ]

    rng = random.Random(77)
    for p in distractors:
        p.parent.mkdir(parents=True, exist_ok=True)
        if p.suffix == ".xlsx":
            # Write a small random xlsx so it's a real file
            rows = [{"col1": rng.randint(1, 100), "col2": f"data{i}"} for i in range(5)]
            df = pd.DataFrame(rows)
            with pd.ExcelWriter(str(p), engine="openpyxl") as writer:
                df.to_excel(writer, index=False)
        elif p.suffix == ".txt":
            p.write_text("临时笔记：明天开会\n项目进度：70%\n")
        elif p.suffix == ".py":
            p.write_text("# legacy script - do not use\nprint('deprecated')\n")
        elif p.suffix == ".log":
            p.write_text("[2025-06-14 00:55:01] Pipeline started\n[2025-06-14 00:55:45] Done\n")
        # Set old timestamps for distractors
        old_ts = datetime(2025, 5, 1).timestamp()
        set_file_times(p, old_ts)

    # Special: a decoy "BI_社群数据上传表" in wrong location
    decoy_bi = workspace / "tmp" / "bi_staging" / "BI_社群数据上传表_decoy.xlsx"
    rows2 = [{"A": "", "B": "", "C": "", "D": "2025-01-01", "E": "GRP99999"}]
    df2 = pd.DataFrame(rows2)
    with pd.ExcelWriter(str(decoy_bi), engine="openpyxl") as writer:
        df2.to_excel(writer, index=False)


# ── skill scripts ─────────────────────────────────────────────────────────────
SKILL_DIR = Path.home() / ".openclaw" / "workspace-pm" / "skills" / "community-data-process"

RUN_PY = r'''#!/usr/bin/env python3
"""
北汽社群数据导出 — 主控脚本
用法:
  python run.py            # 全流程
  python run.py clean      # 仅清洗
  python run.py audit      # 仅校对
  python run.py merge      # 仅合并
  python run.py verify     # 仅验证
"""
import sys
import os
import glob
import shutil
from pathlib import Path
from datetime import datetime

import pandas as pd

# ── 路径配置 ─────────────────────────────────────────────────────────────────
DOWNLOADS = Path.home() / "Downloads"          # 源文件目录
OUTPUT_DIR = Path.home() / "Downloads"         # 输出目录（与源文件同目录）
BI_TABLE   = Path.home() / "Downloads" / "BI_社群数据上传表.xlsx"

NUMERIC_COLS = ["群人数", "员工人数", "客户人数", "今日入群", "今日退群", "今日消息"]
TARGET_TAGS  = {"温冷一期", "试点店"}

SRC_COLS = [
    "群ID", "群名称", "群主", "群管理员",
    "群人数", "群活跃", "群类型",
    "员工人数", "客户人数", "今日入群", "今日退群", "今日消息",
    "入群时间", "最后发言时间", "群标签"
]
BI_COLS = (
    ["ColA", "ColB", "ColC", "统计日期"] + SRC_COLS
)

EIGHT_METRICS = ["群人数", "员工人数", "客户人数", "今日入群", "今日退群", "今日消息",
                 "群ID", "群名称"]


# ── 工具函数 ─────────────────────────────────────────────────────────────────
def get_latest_export() -> Path:
    """按 mtime 取最新的 客户群导出*.xlsx。"""
    files = list(DOWNLOADS.glob("客户群导出*.xlsx"))
    if not files:
        raise FileNotFoundError("Downloads 目录下找不到 客户群导出*.xlsx")
    return max(files, key=lambda p: p.stat().st_mtime)


def get_download_date(src_path: Path) -> str:
    """返回源文件的下载日期（mtime），格式 YYYY-MM-DD。"""
    ts = src_path.stat().st_mtime
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d")


def today_str() -> str:
    return datetime.now().strftime("%Y%m%d")


# ── Step 1: 清洗 ─────────────────────────────────────────────────────────────
def clean():
    src = get_latest_export()
    print(f"[clean] 源文件: {src}")

    df = pd.read_excel(src, header=0)
    df.columns = SRC_COLS[:len(df.columns)]

    # 筛选
    df = df[df["群标签"].isin(TARGET_TAGS)].copy()
    print(f"[clean] 筛选后行数: {len(df)}")

    # 数字列 → int
    for col in NUMERIC_COLS:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    out_name = f"客户群导出_清理后_温冷一期 + 试点店_{today_str()}.xlsx"
    out_path = OUTPUT_DIR / out_name
    with pd.ExcelWriter(str(out_path), engine="openpyxl") as w:
        df.to_excel(w, index=False, sheet_name="Sheet1")
    print(f"[clean] 输出: {out_path}")
    return src, df, out_path


# ── Step 2: 校对 ─────────────────────────────────────────────────────────────
def audit(src_path=None, cleaned_df=None, cleaned_path=None):
    if src_path is None:
        src_path = get_latest_export()
    if cleaned_df is None:
        pattern = str(OUTPUT_DIR / f"客户群导出_清理后_温冷一期 + 试点店_{today_str()}.xlsx")
        files = glob.glob(pattern)
        if not files:
            raise FileNotFoundError("找不到清理后文件，请先执行 clean")
        cleaned_path = Path(files[0])
        cleaned_df = pd.read_excel(cleaned_path, header=0)
        cleaned_df.columns = SRC_COLS[:len(cleaned_df.columns)]

    # 读取源文件并筛选
    src_df = pd.read_excel(src_path, header=0)
    src_df.columns = SRC_COLS[:len(src_df.columns)]
    src_filtered = src_df[src_df["群标签"].isin(TARGET_TAGS)].copy()
    for col in NUMERIC_COLS:
        src_filtered[col] = pd.to_numeric(src_filtered[col], errors="coerce").fillna(0).astype(int)

    # 读取合并后文件
    bi_pattern = str(OUTPUT_DIR / f"BI_社群数据上传_已更新_{today_str()}.xlsx")
    bi_files = glob.glob(bi_pattern)
    merged_available = len(bi_files) > 0
    if merged_available:
        bi_df = pd.read_excel(bi_files[0], header=0)
        # 取当天新增行（统计日期 = 下载日期）
        dl_date = get_download_date(src_path)
        merged_new = bi_df[bi_df["统计日期"] == dl_date].copy()
        merged_new = merged_new.rename(columns={
            "群ID": "群ID", "群名称": "群名称"
        })
        # 重新对齐列名
        merged_new.columns = bi_df.columns

    report_lines = []
    report_lines.append(f"数据校对报告 — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append(f"源文件: {src_path}")
    report_lines.append(f"源文件筛选后行数: {len(src_filtered)}")
    report_lines.append(f"清理后行数: {len(cleaned_df)}")
    report_lines.append("")

    all_pass = True

    # 行数一致性
    if len(src_filtered) == len(cleaned_df):
        report_lines.append("[PASS] 行数一致")
    else:
        report_lines.append(f"[FAIL] 行数不一致: 源={len(src_filtered)}, 清理后={len(cleaned_df)}")
        all_pass = False

    # 8 指标校对
    for metric in EIGHT_METRICS:
        if metric not in src_filtered.columns or metric not in cleaned_df.columns:
            report_lines.append(f"[SKIP] {metric} 列不存在")
            continue
        s_vals = sorted(src_filtered[metric].tolist())
        c_vals = sorted(cleaned_df[metric].tolist())
        if s_vals == c_vals:
            report_lines.append(f"[PASS] {metric} 一致")
        else:
            report_lines.append(f"[FAIL] {metric} 不一致")
            all_pass = False

    # 空值检查
    null_count = cleaned_df.isnull().sum().sum()
    if null_count == 0:
        report_lines.append("[PASS] 无空值")
    else:
        report_lines.append(f"[FAIL] 存在 {null_count} 个空值")
        all_pass = False

    # 负值检查
    neg_count = 0
    for col in NUMERIC_COLS:
        if col in cleaned_df.columns:
            neg_count += (cleaned_df[col] < 0).sum()
    if neg_count == 0:
        report_lines.append("[PASS] 无负值")
    else:
        report_lines.append(f"[FAIL] 存在 {neg_count} 个负值")
        all_pass = False

    report_lines.append("")
    report_lines.append("总体结论: " + ("PASS" if all_pass else "FAIL"))

    report_name = f"数据校对报告_{today_str()}.txt"
    report_path = OUTPUT_DIR / report_name
    report_path.write_text("\n".join(report_lines), encoding="utf-8")
    print(f"[audit] 报告: {report_path}")
    print(f"[audit] 结论: {'PASS' if all_pass else 'FAIL'}")
    return src_path, cleaned_df, cleaned_path


# ── Step 3: 合并 ─────────────────────────────────────────────────────────────
def merge(src_path=None, cleaned_df=None):
    if src_path is None:
        src_path = get_latest_export()
    if cleaned_df is None:
        pattern = str(OUTPUT_DIR / f"客户群导出_清理后_温冷一期 + 试点店_{today_str()}.xlsx")
        files = glob.glob(pattern)
        if not files:
            raise FileNotFoundError("找不到清理后文件，请先执行 clean")
        cleaned_df = pd.read_excel(files[0], header=0)
        cleaned_df.columns = SRC_COLS[:len(cleaned_df.columns)]

    # 读取现有 BI 表
    if BI_TABLE.exists():
        bi_df = pd.read_excel(str(BI_TABLE), header=0)
    else:
        bi_df = pd.DataFrame(columns=BI_COLS)

    # 统计日期 = 源文件下载日期
    dl_date = get_download_date(src_path)
    print(f"[merge] 统计日期 (源文件下载日期): {dl_date}")

    # 构建新行
    new_rows = []
    for _, row in cleaned_df.iterrows():
        new_row = {col: "" for col in BI_COLS}
        new_row["统计日期"] = dl_date
        for src_col in SRC_COLS:
            if src_col in cleaned_df.columns:
                new_row[src_col] = row[src_col]
        new_rows.append(new_row)

    new_df = pd.DataFrame(new_rows, columns=BI_COLS)
    merged = pd.concat([bi_df, new_df], ignore_index=True)

    out_name = f"BI_社群数据上传_已更新_{today_str()}.xlsx"
    out_path = OUTPUT_DIR / out_name
    with pd.ExcelWriter(str(out_path), engine="openpyxl") as w:
        merged.to_excel(w, index=False, sheet_name="Sheet1")
    print(f"[merge] 输出: {out_path}")
    return out_path, merged


# ── Step 4: 验证 ─────────────────────────────────────────────────────────────
def verify():
    today = today_str()
    issues = []

    # 检查输出文件存在
    clean_files = list(OUTPUT_DIR.glob(f"客户群导出_清理后_温冷一期 + 试点店_{today}.xlsx"))
    bi_files    = list(OUTPUT_DIR.glob(f"BI_社群数据上传_已更新_{today}.xlsx"))
    report_files= list(OUTPUT_DIR.glob(f"数据校对报告_{today}.txt"))

    if not clean_files:  issues.append("缺少清理后文件")
    if not bi_files:     issues.append("缺少合并后文件")
    if not report_files: issues.append("缺少校对报告")

    if bi_files:
        bi_df = pd.read_excel(str(bi_files[0]), header=0)
        src   = get_latest_export()
        dl_date = get_download_date(src)
        new_rows = bi_df[bi_df["统计日期"] == dl_date]
        if len(new_rows) == 0:
            issues.append(f"合并后文件中找不到统计日期={dl_date} 的记录")
        abc_cols = ["ColA", "ColB", "ColC"]
        for col in abc_cols:
            if col in bi_df.columns:
                non_empty = bi_df[col].dropna().astype(str).str.strip().ne("").sum()
                if non_empty > 0:
                    issues.append(f"{col} 列不应有值")

    if issues:
        print("[verify] FAIL:")
        for iss in issues:
            print(f"  - {iss}")
    else:
        print("[verify] PASS — 所有检查通过")


# ── 入口 ─────────────────────────────────────────────────────────────────────
def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"

    if cmd == "clean":
        clean()
    elif cmd == "audit":
        audit()
    elif cmd == "merge":
        merge()
    elif cmd == "verify":
        verify()
    else:  # all
        src, cleaned_df, cleaned_path = clean()
        src, cleaned_df, cleaned_path = audit(src, cleaned_df, cleaned_path)
        out_path, merged = merge(src, cleaned_df)
        verify()
        print("[all] 全流程完成")


if __name__ == "__main__":
    main()
'''


def create_skill_scripts():
    run_py = SKILL_DIR / "run.py"
    run_py.write_text(RUN_PY, encoding="utf-8")
    run_py.chmod(0o755)

    # Also write a minimal SKILL.md in the skill dir
    skill_md = SKILL_DIR / "SKILL.md"
    skill_md.write_text(
        "# community-data-process\n"
        "See ~/.openclaw/workspace-pm/skills/community-data-process/run.py\n",
        encoding="utf-8"
    )


# ── BI source table ───────────────────────────────────────────────────────────
def create_bi_source_table(downloads: Path):
    bi_path = downloads / "BI_社群数据上传表.xlsx"
    make_bi_target(bi_path)
    # Set old timestamp so it doesn't interfere
    old_ts = datetime(2025, 6, 1, 12, 0, 0).timestamp()
    set_file_times(bi_path, old_ts)
    return bi_path


# ── main ──────────────────────────────────────────────────────────────────────
def main():
    make_dirs()
    downloads = WORKSPACE / "Downloads"

    # Symlink ~/Downloads → /workspace/Downloads for the skill scripts
    home_downloads = Path.home() / "Downloads"
    if not home_downloads.exists():
        home_downloads.symlink_to(downloads)

    # Create export source files (the agent should pick newest = 20250615)
    target_src = create_export_files(downloads)
    print(f"Target source file: {target_src} | mtime={datetime.fromtimestamp(target_src.stat().st_mtime)}")

    # Create BI upload table (pre-populated)
    bi_path = create_bi_source_table(downloads)
    print(f"BI table: {bi_path}")

    # Distractor files
    create_distractors(WORKSPACE)

    # Create skill scripts
    create_skill_scripts()

    print("Workspace generated successfully.")
    print(f"Downloads contents: {sorted(str(p) for p in downloads.iterdir())}")


if __name__ == "__main__":
    main()