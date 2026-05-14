import os
import random
import json
import textwrap
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# ── directory skeleton ────────────────────────────────────────────────────────
dirs = [
    "genomics_pipeline",
    "genomics_pipeline/parsers",
    "genomics_pipeline/filters",
    "genomics_pipeline/reports",
    "genomics_pipeline/utils",
    "genomics_pipeline/tests",
    "data/raw_vcf",
    "data/processed",
    "docs",
    "scripts",
    "config",
    ".evolution",         # directory exists but log does NOT yet
    ".evolution/variants",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# ── distractor files ──────────────────────────────────────────────────────────
(workspace / "docs" / "architecture.md").write_text(
    "# Genomics Pipeline Architecture\nSee source code for details.\n"
)
(workspace / "docs" / "changelog.txt").write_text(
    "2024-01-10: initial commit\n2024-02-05: added filter stage\n"
)
(workspace / "config" / "pipeline.yaml").write_text(
    "quality_threshold: 30\nmin_depth: 10\nmax_allele_freq: 0.05\n"
)
(workspace / "config" / "logging.yaml").write_text(
    "level: INFO\nformat: '%(asctime)s %(message)s'\n"
)
(workspace / "scripts" / "run_all.sh").write_text(
    "#!/bin/bash\ncd /workspace && python -m pytest genomics_pipeline/tests/ -v\n"
)
(workspace / "data" / "raw_vcf" / "sample_001.vcf").write_text(
    "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\n"
    "chr1\t12345\t.\tA\tT\t45\tPASS\tDP=20\n"
    "chr1\t23456\t.\tG\tC\t15\tLowQual\tDP=5\n"
    "chr2\t34567\t.\tT\tA\t60\tPASS\tDP=35\n"
)
(workspace / "data" / "raw_vcf" / "sample_002.vcf").write_text(
    "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\n"
    "chr3\t5000\t.\tC\tG\t.\tPASS\tDP=12\n"   # missing QUAL — edge case
    "chrX\t9999\t.\tA\tT\t55\tPASS\tDP=22\n"
)
(workspace / "data" / "processed" / ".gitkeep").write_text("")
(workspace / "scripts" / "benchmark.py").write_text(
    "# placeholder benchmark script\nimport sys\nprint('benchmark not implemented')\n"
)

# ── __init__ files ────────────────────────────────────────────────────────────
for pkg in ["genomics_pipeline", "genomics_pipeline/parsers",
            "genomics_pipeline/filters", "genomics_pipeline/reports",
            "genomics_pipeline/utils"]:
    (workspace / pkg / "__init__.py").write_text("")

# ── BROKEN main pipeline code ─────────────────────────────────────────────────
# vcf_parser.py — has a BUG: crashes on missing QUAL field (non-numeric ".")
(workspace / "genomics_pipeline" / "parsers" / "vcf_parser.py").write_text(textwrap.dedent("""\
    \"\"\"VCF file parser for genomics pipeline.\"\"\"


    def parse_vcf_line(line: str) -> dict:
        \"\"\"Parse a single VCF data line into a dict.\"\"\"
        if line.startswith('#'):
            return None
        fields = line.strip().split('\\t')
        return {
            'chrom': fields[0],
            'pos': int(fields[1]),
            'id': fields[2],
            'ref': fields[3],
            'alt': fields[4],
            'qual': float(fields[5]),   # BUG: crashes when QUAL is '.'
            'filter': fields[6],
            'info': fields[7] if len(fields) > 7 else '',
        }


    def parse_vcf_file(filepath: str) -> list:
        \"\"\"Read all variant records from a VCF file.\"\"\"
        records = []
        with open(filepath) as fh:
            for line in fh:
                rec = parse_vcf_line(line)
                if rec is not None:
                    records.append(rec)
        return records
"""))

# quality_filter.py — BUG: filter logic is inverted (keeps LOW quality variants)
(workspace / "genomics_pipeline" / "filters" / "quality_filter.py").write_text(textwrap.dedent("""\
    \"\"\"Quality-based filtering of VCF records.\"\"\"


    def filter_by_quality(records: list, min_qual: float = 30.0) -> list:
        \"\"\"Keep only high-quality variants.\"\"\"
        # BUG: condition is inverted — keeps records BELOW threshold
        return [r for r in records if r['qual'] < min_qual]


    def filter_by_depth(records: list, min_depth: int = 10) -> list:
        \"\"\"Keep only variants with sufficient read depth.\"\"\"
        result = []
        for r in records:
            info = r.get('info', '')
            # BUG: wrong key — 'DP' parsed incorrectly (looks for 'depth=' not 'DP=')
            depth_parts = [p for p in info.split(';') if p.startswith('depth=')]
            if depth_parts:
                depth = int(depth_parts[0].split('=')[1])
                if depth >= min_depth:
                    result.append(r)
        return result
"""))

# stats_reporter.py — BUG: division by zero not handled; also wrong field name
(workspace / "genomics_pipeline" / "reports" / "stats_reporter.py").write_text(textwrap.dedent("""\
    \"\"\"Compute summary statistics for filtered variants.\"\"\"


    def compute_stats(records: list) -> dict:
        \"\"\"Return basic stats dict from a list of variant records.\"\"\"
        if not records:
            # BUG: should return a zero-stats dict, instead raises ZeroDivisionError indirectly
            pass   # falls through to avg_qual computation below

        total = len(records)
        avg_qual = sum(r['qual'] for r in records) / total   # crashes on empty list
        chrom_counts = {}
        for r in records:
            # BUG: uses 'chromosome' instead of 'chrom' key
            chrom = r.get('chromosome', 'unknown')
            chrom_counts[chrom] = chrom_counts.get(chrom, 0) + 1

        return {
            'total_variants': total,
            'avg_quality': round(avg_qual, 2),
            'variants_per_chrom': chrom_counts,
        }
"""))

# pipeline.py — orchestrator (calls all three above)
(workspace / "genomics_pipeline" / "pipeline.py").write_text(textwrap.dedent("""\
    \"\"\"Main pipeline orchestrator.\"\"\"
    from genomics_pipeline.parsers.vcf_parser import parse_vcf_file
    from genomics_pipeline.filters.quality_filter import filter_by_quality, filter_by_depth
    from genomics_pipeline.reports.stats_reporter import compute_stats


    def run_pipeline(vcf_filepath: str, min_qual: float = 30.0, min_depth: int = 10) -> dict:
        \"\"\"End-to-end pipeline: parse → filter → report.\"\"\"
        records = parse_vcf_file(vcf_filepath)
        records = filter_by_quality(records, min_qual)
        records = filter_by_depth(records, min_depth)
        stats = compute_stats(records)
        return stats
"""))

# ── TEST SUITE (10 tests, most fail due to the bugs above) ───────────────────
(workspace / "genomics_pipeline" / "tests" / "__init__.py").write_text("")
(workspace / "genomics_pipeline" / "tests" / "test_vcf_parser.py").write_text(textwrap.dedent("""\
    import pytest
    from genomics_pipeline.parsers.vcf_parser import parse_vcf_line, parse_vcf_file
    import tempfile, os


    def test_parse_normal_line():
        line = "chr1\\t12345\\t.\\tA\\tT\\t45\\tPASS\\tDP=20"
        rec = parse_vcf_line(line)
        assert rec['chrom'] == 'chr1'
        assert rec['pos'] == 12345
        assert rec['qual'] == 45.0


    def test_parse_header_line_returns_none():
        assert parse_vcf_line("#CHROM\\tPOS\\tID\\tREF\\tALT\\tQUAL\\tFILTER\\tINFO") is None


    def test_parse_missing_qual_dot():
        \"\"\"QUAL field is '.' (missing) — must return None for qual, not crash.\"\"\"
        line = "chr3\\t5000\\t.\\tC\\tG\\t.\\tPASS\\tDP=12"
        rec = parse_vcf_line(line)
        assert rec is not None
        assert rec['qual'] is None


    def test_parse_vcf_file_with_missing_qual(tmp_path):
        \"\"\"File with a missing-QUAL line must parse without raising.\"\"\"
        vcf = tmp_path / "test.vcf"
        vcf.write_text(
            "#CHROM\\tPOS\\tID\\tREF\\tALT\\tQUAL\\tFILTER\\tINFO\\n"
            "chr1\\t100\\t.\\tA\\tT\\t.\\tPASS\\tDP=10\\n"
            "chr1\\t200\\t.\\tG\\tC\\t50\\tPASS\\tDP=20\\n"
        )
        records = parse_vcf_file(str(vcf))
        assert len(records) == 2
        assert records[0]['qual'] is None
        assert records[1]['qual'] == 50.0
"""))

(workspace / "genomics_pipeline" / "tests" / "test_quality_filter.py").write_text(textwrap.dedent("""\
    import pytest
    from genomics_pipeline.filters.quality_filter import filter_by_quality, filter_by_depth


    RECORDS = [
        {'chrom': 'chr1', 'pos': 1, 'qual': 45.0, 'filter': 'PASS', 'info': 'DP=20'},
        {'chrom': 'chr1', 'pos': 2, 'qual': 15.0, 'filter': 'LowQual', 'info': 'DP=5'},
        {'chrom': 'chr2', 'pos': 3, 'qual': 60.0, 'filter': 'PASS', 'info': 'DP=35'},
        {'chrom': 'chr2', 'pos': 4, 'qual': None, 'filter': 'PASS', 'info': 'DP=12'},
    ]


    def test_filter_keeps_high_quality():
        result = filter_by_quality(RECORDS, min_qual=30.0)
        quals = [r['qual'] for r in result]
        assert all(q is None or q >= 30.0 for q in quals), f"Got: {quals}"
        assert len(result) == 3  # 45, 60, and None (missing qual = pass through)


    def test_filter_rejects_low_quality():
        result = filter_by_quality(RECORDS, min_qual=30.0)
        assert not any(r['qual'] == 15.0 for r in result)


    def test_filter_by_depth_correct():
        result = filter_by_depth(RECORDS, min_depth=10)
        depths = []
        for r in result:
            info = r.get('info', '')
            dp_parts = [p for p in info.split(';') if p.startswith('DP=')]
            if dp_parts:
                depths.append(int(dp_parts[0].split('=')[1]))
        assert all(d >= 10 for d in depths)
        assert len(result) == 3  # DP=20, DP=35, DP=12 pass; DP=5 fails


    def test_filter_by_depth_excludes_low_depth():
        result = filter_by_depth(RECORDS, min_depth=10)
        for r in result:
            if 'DP=5' in r.get('info', ''):
                pytest.fail("Low depth record should have been filtered out")
"""))

(workspace / "genomics_pipeline" / "tests" / "test_stats_reporter.py").write_text(textwrap.dedent("""\
    import pytest
    from genomics_pipeline.reports.stats_reporter import compute_stats


    GOOD_RECORDS = [
        {'chrom': 'chr1', 'pos': 1, 'qual': 45.0, 'filter': 'PASS', 'info': 'DP=20'},
        {'chrom': 'chr1', 'pos': 2, 'qual': 60.0, 'filter': 'PASS', 'info': 'DP=35'},
        {'chrom': 'chr2', 'pos': 3, 'qual': 50.0, 'filter': 'PASS', 'info': 'DP=25'},
    ]


    def test_compute_stats_basic():
        stats = compute_stats(GOOD_RECORDS)
        assert stats['total_variants'] == 3
        assert stats['avg_quality'] == pytest.approx(51.67, abs=0.1)


    def test_compute_stats_chrom_counts():
        stats = compute_stats(GOOD_RECORDS)
        assert stats['variants_per_chrom']['chr1'] == 2
        assert stats['variants_per_chrom']['chr2'] == 1


    def test_compute_stats_empty_list():
        \"\"\"Empty input must return zero-stats dict, not raise.\"\"\"
        stats = compute_stats([])
        assert stats['total_variants'] == 0
        assert stats['avg_quality'] == 0.0
        assert stats['variants_per_chrom'] == {}
"""))

# ── evolution log skeleton: only baseline entry, no variants yet ──────────────
# Intentionally NOT creating the log — agent must create it properly.
# But we do create a corrupted partial attempt to confuse naive agents:
(workspace / ".evolution" / "NOTES.txt").write_text(
    "Pipeline was initially broken. Need to track improvements here.\n"
    "DO NOT manually edit log.json — use the structured process.\n"
)

print("Workspace generated successfully.")
print("Test count: 10 tests across 3 test files.")
print("Bugs planted: 4 bugs across 3 source files.")