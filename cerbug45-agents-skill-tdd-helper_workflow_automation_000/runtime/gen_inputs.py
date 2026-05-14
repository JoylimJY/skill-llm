import os
import random
import textwrap

random.seed(42)

BASE = "/workspace"

# --- Directory structure ---
dirs = [
    "pipeline",
    "pipeline/utils",
    "pipeline/io",
    "pipeline/deprecated",
    "data/raw",
    "data/processed",
    "docs",
    "configs",
    "scripts",
    "archive",
    "archive/v1",
    "archive/v2",
]
for d in dirs:
    os.makedirs(os.path.join(BASE, d), exist_ok=True)

# --- Distractor files ---

# 1. Old deprecated GC counter (wrong logic, do not use)
with open(os.path.join(BASE, "pipeline/deprecated/gc_counter_old.py"), "w") as f:
    f.write(textwrap.dedent("""\
        # DEPRECATED - do not use
        def gc_content(seq):
            return len([b for b in seq if b in 'GC']) / max(1, len(seq)) * 100
    """))

# 2. Utility: file reader stub
with open(os.path.join(BASE, "pipeline/utils/file_utils.py"), "w") as f:
    f.write(textwrap.dedent("""\
        def read_lines(path):
            with open(path) as fh:
                return fh.readlines()
    """))

# 3. Distractor config
with open(os.path.join(BASE, "configs/pipeline_config.json"), "w") as f:
    f.write('{"version": "2.1.0", "output_dir": "data/processed", "threads": 4}\n')

# 4. Archive v1 script
with open(os.path.join(BASE, "archive/v1/run_pipeline.sh"), "w") as f:
    f.write("#!/bin/bash\npython old_main.py --input data/raw/sequences.fa\n")

# 5. Archive v2 script
with open(os.path.join(BASE, "archive/v2/run_pipeline.sh"), "w") as f:
    f.write("#!/bin/bash\npython main_v2.py --input data/raw/sequences.fa\n")

# 6. Docs placeholder
with open(os.path.join(BASE, "docs/pipeline_overview.md"), "w") as f:
    f.write("# Pipeline Overview\nThis pipeline processes genomic sequences.\n")

# 7. Distractor io module
with open(os.path.join(BASE, "pipeline/io/fasta_reader.py"), "w") as f:
    f.write(textwrap.dedent("""\
        def parse_fasta(path):
            records = {}
            current = None
            with open(path) as fh:
                for line in fh:
                    line = line.strip()
                    if line.startswith('>'):
                        current = line[1:]
                        records[current] = ''
                    elif current:
                        records[current] += line
            return records
    """))

# 8. Distractor requirements file (no pytest/ruff listed, agent must install anyway)
with open(os.path.join(BASE, "requirements.txt"), "w") as f:
    f.write("biopython==1.83\n")

# 9. Dummy test placeholder that is intentionally EMPTY (will cause tdd.py to fail if used as-is)
os.makedirs(os.path.join(BASE, "tests"), exist_ok=True)
with open(os.path.join(BASE, "tests/.gitkeep"), "w") as f:
    f.write("")

# 10. Distractor main that does NOT produce correct output
with open(os.path.join(BASE, "pipeline/deprecated/main_broken.py"), "w") as f:
    f.write(textwrap.dedent("""\
        # Broken main - do not use
        import csv
        def run():
            with open('data/processed/gc_results.csv', 'w') as f:
                writer = csv.writer(f)
                writer.writerow(['sequence_id', 'gc_content'])
                writer.writerow(['seq1', 'WRONG'])
        if __name__ == '__main__':
            run()
    """))

# 11. tdd.py (the skill tool - already present per instructions but generated here for workspace completeness)
with open(os.path.join(BASE, "tdd.py"), "w") as f:
    f.write(textwrap.dedent("""\
        import argparse, subprocess, sys, os

        parser = argparse.ArgumentParser()
        parser.add_argument('--tests', default='tests', help='Path to tests (dir or file)')
        parser.add_argument('--run', required=True, help='Command to run after tests pass')
        args = parser.parse_args()

        TEST_CMD = os.getenv('TEST_CMD') or f"pytest {args.tests}" if os.path.isdir(args.tests) else f"pytest {args.tests}"

        print(f"Running tests: {TEST_CMD}")
        res = subprocess.run(TEST_CMD, shell=True)
        if res.returncode != 0:
            print("Tests failed or missing. Aborting run.")
            sys.exit(res.returncode or 1)

        if os.getenv('WARN_AS_ERROR') == '1':
            lint = os.getenv('LINT_CMD') or "ruff ."
            print(f"Running lint: {lint}")
            lint_res = subprocess.run(lint, shell=True)
            if lint_res.returncode != 0:
                print("Lint/warnings failed. Aborting run.")
                sys.exit(lint_res.returncode or 1)

        print("Tests green. Running target...")
        run_res = subprocess.run(args.run, shell=True)
        sys.exit(run_res.returncode)
    """))

# 12. The raw FASTA-like input data (messy: mixed case, blank lines, windows-style line endings mixed in)
fasta_content = (
    ">seq_alpha\r\n"
    "ATGCGCATTAGCGCGCTATTTACGCGCGATATCGCG\n"
    "\n"
    ">seq_beta\n"
    "atgcatgcATGCATGCatgcATGC\n"
    ">seq_gamma\r\n"
    "AAAATTTTCCCCGGGG\n"
    "\n"
    ">seq_delta\n"
    "GCGCGCGCGCGCGCGCGCGC\n"
    ">seq_epsilon\n"
    "ATATATAT\n"
)
with open(os.path.join(BASE, "data/raw/sequences.fa"), "w") as f:
    f.write(fasta_content)

# 13. scripts/ distractor
with open(os.path.join(BASE, "scripts/upload_results.sh"), "w") as f:
    f.write("#!/bin/bash\necho 'Uploading results... (stub)'\n")

# 14. Another distractor in pipeline/
with open(os.path.join(BASE, "pipeline/normalizer.py"), "w") as f:
    f.write(textwrap.dedent("""\
        def normalize(seq):
            return seq.upper().strip()
    """))

print("Workspace generated.")