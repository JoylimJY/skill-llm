#!/usr/bin/env python3
"""
Evaluation script for the bioinformatics trash-cli task.

Checks:
1. All tmp/*.bam and tmp/*.sam and tmp/*.txt files have been trashed (not present on disk)
2. All pipeline/logs/*.log files have been trashed (not present on disk)
3. The *.log files are NO LONGER in trash (purged via trash-rm '*.log')
4. The tmp files (*.bam, *.sam, *.txt) ARE still in the trash (not purged)
5. The critical annotation file has been restored to its original location
6. The annotation file content is intact (not empty/corrupted)
"""

import sys
import json
import subprocess
from pathlib import Path

def run(cmd):
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=15
        )
        return result.stdout, result.stderr, result.returncode
    except Exception as e:
        return "", str(e), -1

def main():
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")
    checks = []

    # -------------------------------------------------------------------------
    # CHECK 1: Tmp files are NOT present on disk (they were trashed)
    # -------------------------------------------------------------------------
    tmp_files = [
        "pipeline/tmp/sample_A_sort_temp_001.bam",
        "pipeline/tmp/sample_A_sort_temp_002.bam",
        "pipeline/tmp/sample_B_sort_temp_001.bam",
        "pipeline/tmp/sample_B_sort_temp_002.bam",
        "pipeline/tmp/sample_C_sort_temp_001.bam",
        "pipeline/tmp/merge_intermediary.sam",
        "pipeline/tmp/dedup_metrics.txt",
    ]
    tmp_absent = []
    tmp_present = []
    for f in tmp_files:
        p = workspace / f
        if p.exists():
            tmp_present.append(str(f))
        else:
            tmp_absent.append(str(f))

    check1_passed = len(tmp_present) == 0
    checks.append({
        "name": "tmp_files_removed_from_disk",
        "passed": check1_passed,
        "detail": (
            f"All {len(tmp_files)} tmp files removed from disk." if check1_passed
            else f"Still present on disk: {tmp_present}"
        )
    })

    # -------------------------------------------------------------------------
    # CHECK 2: Log files are NOT present on disk (they were trashed)
    # -------------------------------------------------------------------------
    log_files = [
        "pipeline/logs/alignment_run_001.log",
        "pipeline/logs/alignment_run_002.log",
        "pipeline/logs/variant_call_run_001.log",
        "pipeline/logs/variant_call_run_002.log",
        "pipeline/logs/qc_run_001.log",
    ]
    logs_absent = []
    logs_present = []
    for f in log_files:
        p = workspace / f
        if p.exists():
            logs_present.append(str(f))
        else:
            logs_absent.append(str(f))

    check2_passed = len(logs_present) == 0
    checks.append({
        "name": "log_files_removed_from_disk",
        "passed": check2_passed,
        "detail": (
            f"All {len(log_files)} log files removed from disk." if check2_passed
            else f"Still present on disk: {logs_present}"
        )
    })

    # -------------------------------------------------------------------------
    # CHECK 3: *.log files are NOT in the trash anymore (purged by trash-rm)
    # -------------------------------------------------------------------------
    try:
        stdout, stderr, rc = run("trash-list 2>/dev/null")
        trash_contents = stdout
        log_lines_in_trash = [
            line for line in trash_contents.splitlines()
            if line.strip().endswith('.log')
        ]
        check3_passed = len(log_lines_in_trash) == 0
        checks.append({
            "name": "log_files_purged_from_trash",
            "passed": check3_passed,
            "detail": (
                "No .log files found in trash." if check3_passed
                else f"Found .log files still in trash: {log_lines_in_trash}"
            )
        })
    except Exception as e:
        checks.append({
            "name": "log_files_purged_from_trash",
            "passed": False,
            "detail": f"Exception running trash-list: {e}"
        })

    # -------------------------------------------------------------------------
    # CHECK 4: Tmp files (.bam, .sam, .txt) ARE still in the trash
    # (agent must NOT have purged them, only the .log files)
    # -------------------------------------------------------------------------
    try:
        stdout, stderr, rc = run("trash-list 2>/dev/null")
        trash_contents = stdout
        # Look for at least some of the tmp files in trash
        expected_in_trash_patterns = [
            "sort_temp_001.bam",
            "sort_temp_002.bam",
            "merge_intermediary.sam",
            "dedup_metrics.txt",
        ]
        found_in_trash = []
        for pat in expected_in_trash_patterns:
            if pat in trash_contents:
                found_in_trash.append(pat)

        check4_passed = len(found_in_trash) >= 3
        checks.append({
            "name": "tmp_files_still_in_trash",
            "passed": check4_passed,
            "detail": (
                f"Found {len(found_in_trash)}/{len(expected_in_trash_patterns)} tmp files in trash: {found_in_trash}"
                if check4_passed
                else f"Only {len(found_in_trash)}/{len(expected_in_trash_patterns)} tmp files remain in trash: {found_in_trash}. Possibly over-purged."
            )
        })
    except Exception as e:
        checks.append({
            "name": "tmp_files_still_in_trash",
            "passed": False,
            "detail": f"Exception running trash-list: {e}"
        })

    # -------------------------------------------------------------------------
    # CHECK 5: The critical annotation file is restored to its original location
    # -------------------------------------------------------------------------
    annotation_path = workspace / "pipeline/annotation/final_annotation_report.tsv"
    try:
        check5_passed = annotation_path.exists()
        checks.append({
            "name": "annotation_file_restored_to_disk",
            "passed": check5_passed,
            "detail": (
                f"Critical file found at {annotation_path}" if check5_passed
                else f"Critical file NOT found at {annotation_path}"
            )
        })
    except Exception as e:
        checks.append({
            "name": "annotation_file_restored_to_disk",
            "passed": False,
            "detail": f"Exception checking annotation file: {e}"
        })

    # -------------------------------------------------------------------------
    # CHECK 6: The restored annotation file has correct content
    # -------------------------------------------------------------------------
    try:
        if annotation_path.exists():
            content = annotation_path.read_text()
            required_lines = [
                "gene_id\tchromosome\tstart\tend\tstrand\tannotation",
                "GENE1\tchr1\t1000000\t1001500\t+\tprotein_coding",
                "GENE2\tchr3\t5500000\t5502000\t-\tlncRNA",
                "GENE3\tchr7\t12000000\t12005000\t+\tpseudogene",
            ]
            missing = [line for line in required_lines if line not in content]
            check6_passed = len(missing) == 0
            checks.append({
                "name": "annotation_file_content_intact",
                "passed": check6_passed,
                "detail": (
                    "All 4 required content lines present and intact." if check6_passed
                    else f"Missing content lines: {missing}"
                )
            })
        else:
            checks.append({
                "name": "annotation_file_content_intact",
                "passed": False,
                "detail": "Annotation file does not exist; cannot check content."
            })
    except Exception as e:
        checks.append({
            "name": "annotation_file_content_intact",
            "passed": False,
            "detail": f"Exception reading annotation file: {e}"
        })

    # -------------------------------------------------------------------------
    # CHECK 7: Critical distractor files still intact on disk (no over-deletion)
    # -------------------------------------------------------------------------
    distractor_files = [
        "configs/pipeline.yaml",
        "pipeline/expression/deseq2/deseq2_results.tsv",
        "pipeline/expression/counts/raw_counts.tsv",
        "pipeline/alignment/sample_A/sample_A.bam",
        "pipeline/variant_calling/sample_A/sample_A.vcf",
    ]
    missing_distractors = []
    for f in distractor_files:
        if not (workspace / f).exists():
            missing_distractors.append(f)
    check7_passed = len(missing_distractors) == 0
    checks.append({
        "name": "distractor_files_untouched",
        "passed": check7_passed,
        "detail": (
            "All key pipeline files remain untouched." if check7_passed
            else f"These important files were incorrectly removed: {missing_distractors}"
        )
    })

    # -------------------------------------------------------------------------
    # Scoring
    # -------------------------------------------------------------------------
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 4)
    all_passed = passed_count == total

    output = {
        "passed": all_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()