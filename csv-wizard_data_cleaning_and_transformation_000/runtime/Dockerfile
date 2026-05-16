FROM python:3.11-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    bash \
    coreutils \
    && rm -rf /var/lib/apt/lists/*

RUN pip install pandas numpy -i https://pypi.tuna.tsinghua.edu.cn/simple

# Create the /clean-csv command as a real executable script
RUN mkdir -p /usr/local/bin

# Write the /clean-csv implementation as a Python script
RUN cat > /usr/local/bin/clean-csv << 'PYEOF'
#!/usr/bin/env python3
import argparse
import sys
import os
import pandas as pd
import numpy as np

def main():
    parser = argparse.ArgumentParser(description='CSV Wizard - Interactive Data Cleaning CLI')
    parser.add_argument('input', help='Input CSV file')
    parser.add_argument('--output', help='Output file path')
    parser.add_argument('--info', action='store_true', help='Show data info')
    parser.add_argument('--preview', type=int, metavar='N', help='Preview N rows')
    parser.add_argument('--fill-missing', choices=['drop','mean','median','mode','constant'], help='Missing value fill strategy')
    parser.add_argument('--fill-value', help='Constant value for fill-missing=constant')
    parser.add_argument('--drop-duplicates', action='store_true', help='Drop duplicate rows')
    parser.add_argument('--standardize-names', action='store_true', help='Standardize column names to snake_case')
    parser.add_argument('--interactive', action='store_true', help='Interactive mode')
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Error: File '{args.input}' not found.", file=sys.stderr)
        sys.exit(1)

    df = pd.read_csv(args.input, encoding='utf-8', skipinitialspace=True)

    # Strip whitespace from string columns
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].str.strip()

    if args.info:
        print(f"Shape: {df.shape}")
        print(f"Columns: {list(df.columns)}")
        print(f"Missing values:\n{df.isnull().sum()}")
        print(f"Dtypes:\n{df.dtypes}")

    if args.preview:
        print(df.head(args.preview).to_string())

    if args.drop_duplicates:
        before = len(df)
        df = df.drop_duplicates()
        after = len(df)
        print(f"Dropped {before - after} duplicate rows.")

    if args.standardize_names:
        def to_snake(name):
            import re
            name = name.strip()
            name = re.sub(r'[\s\-]+', '_', name)
            name = re.sub(r'[^\w]', '', name)
            name = re.sub(r'([A-Z])', r'_\1', name).lower()
            name = re.sub(r'_+', '_', name).strip('_')
            return name
        df.columns = [to_snake(c) for c in df.columns]

    if args.fill_missing:
        strategy = args.fill_missing
        if strategy == 'drop':
            df = df.dropna()
        elif strategy == 'mean':
            for col in df.select_dtypes(include=[np.number]).columns:
                df[col] = df[col].fillna(df[col].mean())
        elif strategy == 'median':
            for col in df.select_dtypes(include=[np.number]).columns:
                df[col] = df[col].fillna(df[col].median())
        elif strategy == 'mode':
            for col in df.columns:
                if df[col].isnull().any():
                    mode_val = df[col].mode()
                    if not mode_val.empty:
                        df[col] = df[col].fillna(mode_val[0])
        elif strategy == 'constant':
            if args.fill_value is None:
                print("Error: --fill-value required with --fill-missing constant", file=sys.stderr)
                sys.exit(1)
            df = df.fillna(args.fill_value)

    if args.output:
        df.to_csv(args.output, index=False, encoding='utf-8')
        print(f"Saved cleaned data to '{args.output}'.")
    elif not args.info and not args.preview:
        print(df.to_csv(index=False))

if __name__ == '__main__':
    main()
PYEOF

RUN chmod +x /usr/local/bin/clean-csv

# Make /clean-csv also work as a slash command by symlinking
RUN ln -s /usr/local/bin/clean-csv /usr/local/bin//clean-csv 2>/dev/null || true

WORKDIR /workspace