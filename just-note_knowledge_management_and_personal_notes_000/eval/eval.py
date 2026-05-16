import sys
import json
import re
from pathlib import Path

def check(name, passed, detail):
    return {"name": name, "passed": passed, "detail": detail}

def run_eval(workspace: str):
    checks = []
    NOTES = Path("/home/node/.openclaw/workspace/notes")

    # ── CHECK 1: The `crispr-cas9-trial-1.md` note was appended with new content ──
    crispr_note = NOTES / "projects" / "crispr-cas9-trial-1.md"
    try:
        content = crispr_note.read_text(encoding="utf-8")
        original_sections = ["# CRISPR-Cas9 Trial 1", "## Observations"]
        has_originals = all(s in content for s in original_sections)
        # Must have a new section appended AFTER the original content
        # The append must come after the last original line
        obs_pos = content.find("## Observations")
        # Find any new heading after Observations
        new_section_match = re.search(r'\n##\s+\S+', content[obs_pos + len("## Observations"):])
        has_new_section = new_section_match is not None
        checks.append(check(
            "crispr_note_original_preserved",
            has_originals,
            f"Original content preserved: {has_originals}. Found sections: {[s for s in original_sections if s in content]}"
        ))
        checks.append(check(
            "crispr_note_appended_new_section",
            has_new_section,
            f"New ## section appended after original content: {has_new_section}. Snippet: {content[obs_pos:][:200]!r}"
        ))
        # Check that appended content is non-trivial (more than just a heading)
        if new_section_match:
            after_new_section = content[obs_pos + len("## Observations") + new_section_match.start():]
            has_body = len(after_new_section.strip()) > 10
            checks.append(check(
                "crispr_note_append_has_body",
                has_body,
                f"Appended section has body content: {has_body}. Content: {after_new_section[:100]!r}"
            ))
        else:
            checks.append(check(
                "crispr_note_append_has_body",
                False,
                "No new section found, so body check fails."
            ))
    except Exception as e:
        checks.append(check("crispr_note_original_preserved", False, f"Error reading file: {e}"))
        checks.append(check("crispr_note_appended_new_section", False, f"Error reading file: {e}"))
        checks.append(check("crispr_note_append_has_body", False, f"Error reading file: {e}"))

    # ── CHECK 2: A new protein synthesis note exists in projects/ ──
    # Slug must be lowercase, hyphen-separated, no special chars, ends with .md
    new_note_candidates = list((NOTES / "projects").glob("*.md"))
    existing_notes = {
        "genome-sequencer-v2.md",
        "crispr-cas9-trial-1.md",
        "lab-equipment-inventory.md",
        "pcr-optimization.md",
    }
    new_notes = [f for f in new_note_candidates if f.name not in existing_notes]

    has_new_project_note = len(new_notes) > 0
    checks.append(check(
        "new_note_exists_in_projects",
        has_new_project_note,
        f"New note(s) found in projects/: {[f.name for f in new_notes]}"
    ))

    if not new_notes:
        # Try searching all subdirs
        all_new = []
        for subdir in ["ideas", "misc", "daily"]:
            candidates = list((NOTES / subdir).glob("*.md"))
            all_new.extend(candidates)
        checks.append(check("new_note_slug_valid", False, "No new note found in projects/ to validate slug."))
        checks.append(check("new_note_has_frontmatter", False, "No new note found to check frontmatter."))
        checks.append(check("new_note_frontmatter_tags", False, "No new note found."))
        checks.append(check("new_note_frontmatter_created", False, "No new note found."))
        checks.append(check("new_note_has_h1_title", False, "No new note found."))
        checks.append(check("new_note_has_body_content", False, "No new note found."))
    else:
        new_note = new_notes[0]

        # CHECK: Slug format — lowercase, hyphens, no special chars
        slug = new_note.stem  # filename without .md
        slug_valid = bool(re.match(r'^[a-z0-9][a-z0-9\-]*[a-z0-9]$', slug)) or bool(re.match(r'^[a-z0-9]+$', slug))
        no_underscore = '_' not in slug
        no_spaces = ' ' not in slug
        slug_ok = slug_valid and no_underscore and no_spaces
        checks.append(check(
            "new_note_slug_valid",
            slug_ok,
            f"Slug '{slug}': valid={slug_valid}, no_underscore={no_underscore}, no_spaces={no_spaces}"
        ))

        # CHECK: YAML frontmatter present
        try:
            content = new_note.read_text(encoding="utf-8")
            has_frontmatter = content.startswith("---")
            checks.append(check(
                "new_note_has_frontmatter",
                has_frontmatter,
                f"File starts with '---': {has_frontmatter}. First 60 chars: {content[:60]!r}"
            ))

            # CHECK: tags field in frontmatter (array style: tags: [...])
            fm_match = re.search(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
            if fm_match:
                fm_block = fm_match.group(1)
                has_tags = bool(re.search(r'^tags\s*:\s*\[', fm_block, re.MULTILINE))
                checks.append(check(
                    "new_note_frontmatter_tags",
                    has_tags,
                    f"Frontmatter has 'tags: [...]' array: {has_tags}. FM block: {fm_block[:120]!r}"
                ))

                # CHECK: created field in frontmatter with date format
                has_created = bool(re.search(r'^created\s*:\s*\d{4}-\d{2}-\d{2}', fm_block, re.MULTILINE))
                checks.append(check(
                    "new_note_frontmatter_created",
                    has_created,
                    f"Frontmatter has 'created: YYYY-MM-DD': {has_created}. FM block: {fm_block[:120]!r}"
                ))
            else:
                checks.append(check("new_note_frontmatter_tags", False, "Could not parse frontmatter block."))
                checks.append(check("new_note_frontmatter_created", False, "Could not parse frontmatter block."))

            # CHECK: H1 title present
            has_h1 = bool(re.search(r'^#\s+\S+', content, re.MULTILINE))
            checks.append(check(
                "new_note_has_h1_title",
                has_h1,
                f"Note has a '# Title' heading: {has_h1}"
            ))

            # CHECK: Note has non-trivial body content (not just frontmatter + title)
            # Strip frontmatter and title, check remaining text
            body = re.sub(r'^---.*?---\s*', '', content, flags=re.DOTALL)
            body = re.sub(r'^#[^\n]+\n', '', body, flags=re.MULTILINE)
            body_stripped = body.strip()
            has_body = len(body_stripped) > 20
            checks.append(check(
                "new_note_has_body_content",
                has_body,
                f"Note has body content (>20 chars after stripping FM+title): {has_body}. Body preview: {body_stripped[:100]!r}"
            ))

        except Exception as e:
            for cname in ["new_note_has_frontmatter", "new_note_frontmatter_tags",
                          "new_note_frontmatter_created", "new_note_has_h1_title", "new_note_has_body_content"]:
                checks.append(check(cname, False, f"Exception: {e}"))

    # ── CHECK 3: The tag-search was effective — verify `research` tag notes exist ──
    # This is a passive check: we verify that the agent found the right note (crispr)
    # by confirming it was modified and no unrelated notes were corrupted
    try:
        pcr_note = (NOTES / "projects" / "pcr-optimization.md").read_text()
        inventory_note = (NOTES / "projects" / "lab-equipment-inventory.md").read_text()
        distractors_intact = (
            "PCR Optimization" in pcr_note and
            "Lab Equipment Inventory" in inventory_note
        )
        checks.append(check(
            "distractor_notes_not_corrupted",
            distractors_intact,
            f"Non-targeted project notes remain intact: {distractors_intact}"
        ))
    except Exception as e:
        checks.append(check("distractor_notes_not_corrupted", False, f"Exception: {e}"))

    # ── Scoring ──
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 4)
    overall_passed = all(c["passed"] for c in checks)

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/home/node"
    result = run_eval(workspace)
    print(json.dumps(result, indent=2))