#!/usr/bin/env python3
"""
Markdown TOC Generator

Extracts headings from Markdown files and generates a table of contents.
Supports heading levels # through ######.
"""

import argparse
import re
import sys
from pathlib import Path


def slugify(text: str) -> str:
    """Convert heading text to a URL-friendly anchor slug."""
    # Remove formatting markers
    text = re.sub(r'\*\*|\*|`|~|=|\|', '', text)
    # Convert to lowercase and replace spaces/special chars with hyphens
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'\s+', '-', text)
    return text


def extract_headings(content: str, min_level: int = 1, max_level: int = 6) -> list:
    """
    Extract headings from markdown content.

    Returns list of tuples: (level, text, slug)
    """
    headings = []
    in_code_block = False
    code_fence = None

    lines = content.split('\n')

    for line in lines:
        stripped = line.strip()

        # Track code blocks to skip headings inside them
        if stripped.startswith('```') or stripped.startswith('~~~'):
            if not in_code_block:
                in_code_block = True
                code_fence = stripped[:3]
            elif stripped.startswith(code_fence):
                in_code_block = False
                code_fence = None
            continue

        if in_code_block:
            continue

        # Match ATX headings (# Heading)
        match = re.match(r'^(#{1,6})\s+(.+)$', stripped)
        if match:
            level = len(match.group(1))
            text = match.group(2).strip()

            if min_level <= level <= max_level:
                slug = slugify(text)
                headings.append((level, text, slug))

    return headings


def generate_toc(headings: list, format_type: str = "list") -> str:
    """
    Generate TOC from extracted headings.

    Args:
        headings: List of (level, text, slug) tuples
        format_type: "list" for bullet list, "links" for linked TOC

    Returns:
        Formatted TOC string
    """
    if not headings:
        return ""

    # Track slugs for duplicates
    slug_counts = {}
    lines = []

    for level, text, slug in headings:
        # Handle duplicate slugs
        if slug in slug_counts:
            slug_counts[slug] += 1
            unique_slug = f"{slug}-{slug_counts[slug]}"
        else:
            slug_counts[slug] = 0
            unique_slug = slug

        indent = "  " * (level - 1)

        if format_type == "links":
            lines.append(f"{indent}- [{text}](#{unique_slug})")
        else:
            lines.append(f"{indent}- {text}")

    return '\n'.join(lines)


def process_file(input_path: Path, output_path: Path = None,
                 min_level: int = 1, max_level: int = 6,
                 format_type: str = "list") -> str:
    """
    Process a markdown file and generate TOC.

    Args:
        input_path: Path to input markdown file
        output_path: Path to output file (None for stdout)
        min_level: Minimum heading level to include
        max_level: Maximum heading level to include
        format_type: Output format ("list" or "links")

    Returns:
        Generated TOC string
    """
    content = input_path.read_text(encoding='utf-8')

    headings = extract_headings(content, min_level, max_level)
    toc = generate_toc(headings, format_type)

    if output_path:
        output_path.write_text(toc + '\n', encoding='utf-8')
        print(f"TOC written to: {output_path}")
    else:
        print(toc)

    return toc


def main():
    parser = argparse.ArgumentParser(
        description='Generate Table of Contents from Markdown files'
    )
    parser.add_argument('input', type=Path, help='Input markdown file')
    parser.add_argument('-o', '--output', type=Path,
                        help='Output file (default: stdout)')
    parser.add_argument('--min-level', type=int, default=1,
                        help='Minimum heading level to include (default: 1)')
    parser.add_argument('--max-level', type=int, default=6,
                        help='Maximum heading level to include (default: 6)')
    parser.add_argument('--format', choices=['list', 'links'], default='list',
                        help='Output format: list or links (default: list)')

    args = parser.parse_args()

    if not args.input.exists():
        print(f"Error: File not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    if args.min_level < 1 or args.max_level > 6 or args.min_level > args.max_level:
        print("Error: Invalid heading level range", file=sys.stderr)
        sys.exit(1)

    process_file(
        args.input,
        args.output,
        args.min_level,
        args.max_level,
        args.format
    )


if __name__ == '__main__':
    main()
