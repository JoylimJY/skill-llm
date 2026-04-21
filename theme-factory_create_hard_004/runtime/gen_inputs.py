import os

def main():
    # Deterministic markdown slide deck with markers
    content = """
# Q1 Quarterly Results

## Financial Overview

- Revenue growth: 12%
- Operating margin improved

## Product Highlights

- Launched new AI-powered features
- User base expanded by 30%

## Summary

Thank you for your attention.

[MARKER-CORP-INPUT]
"""
    with open("quarterly_results_slides.md", "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == "__main__":
    main()
