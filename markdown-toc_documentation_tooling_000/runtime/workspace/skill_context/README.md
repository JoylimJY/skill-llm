# Markdown TOC

Generate a Table of Contents (TOC) from Markdown headings.

## Description

This skill extracts headings from Markdown files and generates a well-formatted table of contents. It supports standard Markdown heading syntax (`#`, `##`, `###`, etc.) and outputs a clean, indented TOC that can be inserted back into your document.

## Usage

```bash
# Generate TOC from a markdown file
python markdown_toc.py <input-file> [options]

# Options:
#   --output, -o    Output file (default: stdout)
#   --min-level     Minimum heading level to include (default: 1)
#   --max-level     Maximum heading level to include (default: 6)
#   --format        Output format: "list" or "links" (default: list)
```

## Examples

```bash
# Basic usage - print TOC to stdout
python markdown_toc.py README.md

# Save TOC to a file
python markdown_toc.py README.md -o toc.md

# Include only level 2-3 headings
python markdown_toc.py README.md --min-level 2 --max-level 3

# Generate TOC with anchor links
python markdown_toc.py README.md --format links
```

## Features

- Extracts headings from `#` to `######` (levels 1-6)
- Supports both bullet list and linked TOC formats
- Configurable heading level filtering
- Handles duplicate headings with unique anchors
- Preserves heading text formatting (bold, italic, code)
- Skips headings inside code blocks

## Output Formats

### List Format (default)
```markdown
- Heading 1
  - Heading 2
    - Heading 3
```

### Links Format
```markdown
- [Heading 1](#heading-1)
  - [Heading 2](#heading-2)
    - [Heading 3](#heading-3)
```
