FROM python:3.11-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple \
    pytest

# Create the skill directory and install the markdown_toc skill
RUN mkdir -p /root/.openclaw/skills/markdown-toc

# Write the markdown_toc.py skill script
RUN cat > /root/.openclaw/skills/markdown-toc/markdown_toc.py << 'SKILL_EOF'
#!/usr/bin/env python3
"""Generate a Table of Contents from Markdown headings."""

import re
import sys
import argparse
from pathlib import Path


def slugify(text):
    """Convert heading text to a URL-friendly anchor slug."""
    # Remove markdown formatting
    text = re.sub(r'[*_`]', '', text)
    # Lowercase
    text = text.lower()
    # Replace spaces and special chars with hyphens
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'-+', '-', text)
    text = text.strip('-')
    return text


def extract_headings(content, min_level=1, max_level=6):
    """Extract headings from markdown content, skipping code blocks."""
    headings = []
    in_code_block = False
    
    for line in content.split('\n'):
        # Toggle code block state
        if line.strip().startswith('```') or line.strip().startswith('~~~'):
            in_code_block = not in_code_block
            continue
        
        if in_code_block:
            continue
        
        # Match ATX headings
        match = re.match(r'^(#{1,6})\s+(.+?)(?:\s+#+\s*)?$', line)
        if match:
            level = len(match.group(1))
            text = match.group(2).strip()
            if min_level <= level <= max_level:
                headings.append((level, text))
    
    return headings


def generate_toc(headings, fmt='list'):
    """Generate TOC from list of (level, text) tuples."""
    if not headings:
        return ''
    
    lines = []
    anchor_counts = {}
    
    # Find base level for indentation
    base_level = min(level for level, _ in headings)
    
    for level, text in headings:
        indent = '  ' * (level - base_level)
        
        if fmt == 'links':
            slug = slugify(text)
            # Handle duplicates
            if slug in anchor_counts:
                anchor_counts[slug] += 1
                anchor = f'{slug}-{anchor_counts[slug]}'
            else:
                anchor_counts[slug] = 0
                anchor = slug
            lines.append(f'{indent}- [{text}](#{anchor})')
        else:
            lines.append(f'{indent}- {text}')
    
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description='Generate Table of Contents from Markdown')
    parser.add_argument('input_file', help='Input Markdown file')
    parser.add_argument('--output', '-o', help='Output file (default: stdout)')
    parser.add_argument('--min-level', type=int, default=1, help='Minimum heading level (default: 1)')
    parser.add_argument('--max-level', type=int, default=6, help='Maximum heading level (default: 6)')
    parser.add_argument('--format', dest='fmt', choices=['list', 'links'], default='list',
                        help='Output format: list or links (default: list)')
    
    args = parser.parse_args()
    
    input_path = Path(args.input_file)
    if not input_path.exists():
        print(f'Error: File not found: {args.input_file}', file=sys.stderr)
        sys.exit(1)
    
    content = input_path.read_text(encoding='utf-8')
    headings = extract_headings(content, args.min_level, args.max_level)
    toc = generate_toc(headings, args.fmt)
    
    if args.output:
        Path(args.output).write_text(toc + '\n', encoding='utf-8')
    else:
        print(toc)


if __name__ == '__main__':
    main()
SKILL_EOF

RUN chmod +x /root/.openclaw/skills/markdown-toc/markdown_toc.py