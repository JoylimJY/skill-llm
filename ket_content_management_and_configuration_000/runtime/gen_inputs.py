import os
import json
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# ── Deep directory structure with distractor files ──────────────────────────

dirs = [
    "platform/config/legacy",
    "platform/config/drafts",
    "platform/modules/reading",
    "platform/modules/writing",
    "platform/modules/listening",
    "platform/modules/speaking",
    "platform/modules/vocab",
    "platform/tests/unit",
    "platform/tests/integration",
    "docs/internal",
    "docs/archived",
    "scripts/migration",
    "scripts/validators",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# ── WRONG/OUTDATED config files (intentionally incorrect values) ─────────────

# Legacy config with many wrong values - agent must NOT use this
legacy_config = {
    "exam_name": "KET A2 Key",
    "modules": {
        "reading_writing": {
            "duration_minutes": 45,  # WRONG: should be 60
            "weight_percent": 50,
            "parts": {
                "part1": {"type": "multiple_choice", "num_texts": 5, "options_per_question": 3},  # WRONG: 6 texts
                "part2": {"type": "matching", "num_questions": 5, "num_texts": 2},  # WRONG: 7 questions, 3 texts
                "part3": {"type": "reading_comprehension", "num_questions": 5, "options_per_question": 3},
                "part4": {"type": "multiple_choice_cloze", "num_blanks": 5, "options_per_blank": 4},  # WRONG: 6 blanks
                "part5": {"type": "open_cloze", "num_blanks": 5, "words_per_blank": 1},  # WRONG: 6 blanks
                "part6": {"type": "guided_writing", "min_words": 20},  # WRONG: should be 25
                "part7": {"type": "story_writing", "num_images": 3, "min_words": 30}  # WRONG: should be 35
            }
        },
        "listening": {
            "duration_minutes": 25,  # WRONG: should be 30
            "weight_percent": 25,
            "playback_count": 1,  # WRONG: should be 2
            "parts": {
                "part1": {"type": "multiple_choice_image", "num_dialogues": 5, "options_per_question": 3},
                "part2": {"type": "fill_in_blank", "num_blanks": 5},
                "part3": {"type": "multiple_choice_dialogue", "num_questions": 4},  # WRONG: should be 5
                "part4": {"type": "multiple_choice_gist", "num_items": 5, "options_per_question": 3},
                "part5": {"type": "matching", "num_items": 5}
            }
        },
        "speaking": {
            "duration_minutes_per_pair": 8,
            "weight_percent": 25,
            "parts": {
                "part1": {"type": "interview", "duration_minutes": 3},  # WRONG: should be 3-4
                "part2": {"type": "discussion", "duration_minutes": 5}  # WRONG: should be 5-6
            }
        }
    },
    "total_reading_writing_questions": 30,  # WRONG: should be 32
    "total_listening_questions": 20  # WRONG: should be 25
}

with open(os.path.join(workspace, "platform/config/legacy/exam_structure_v1.json"), "w") as f:
    json.dump(legacy_config, f, indent=2)

# Another draft with different wrong values
draft_config = {
    "version": "draft-2.1",
    "writing": {
        "part6_min_words": 30,  # WRONG
        "part6_key_points": 2,  # WRONG: should be 3
        "part7_min_words": 40,  # WRONG
        "part7_images": 3
    },
    "vocab_levels": {
        "pre_a1": 500,   # WRONG: should be ~300
        "a1": 800,       # WRONG: should be ~600
        "a2": 2000       # WRONG: should be ~1500
    },
    "listening_transcription_minutes": 5  # WRONG: should be 6
}

with open(os.path.join(workspace, "platform/config/drafts/module_draft.json"), "w") as f:
    json.dump(draft_config, f, indent=2)

# ── Distractor Python files ──────────────────────────────────────────────────

distractor_py_reading = '''
# Reading module loader - placeholder
# Part 1: short texts with 3 options
# TODO: implement Part 2 matching logic

class ReadingModule:
    def load_part1(self):
        # 5 texts (to be corrected)
        return []

    def load_part2(self):
        # matching: 6 questions (to be corrected)
        return []
'''
with open(os.path.join(workspace, "platform/modules/reading/loader.py"), "w") as f:
    f.write(distractor_py_reading)

distractor_py_writing = '''
# Writing module - word count validator
# WARNING: thresholds below are placeholders, do not use in production

MIN_WORDS_PART6 = 20   # placeholder - check spec doc
MIN_WORDS_PART7 = 30   # placeholder - check spec doc
KEY_POINTS_REQUIRED = 2  # placeholder
'''
with open(os.path.join(workspace, "platform/modules/writing/validator.py"), "w") as f:
    f.write(distractor_py_writing)

distractor_py_listening = '''
# Listening playback controller
# Current setting: plays once per item
# Exam standard may differ - verify with product team

PLAYBACK_COUNT = 1
TRANSCRIPTION_WINDOW_MINUTES = 5
TOTAL_DURATION_MINUTES = 25
'''
with open(os.path.join(workspace, "platform/modules/listening/playback.py"), "w") as f:
    f.write(distractor_py_listening)

distractor_py_vocab = '''
# Vocabulary level thresholds
# These are rough estimates, needs confirmation

VOCAB_PRE_A1 = 200
VOCAB_A1 = 500
VOCAB_A2 = 1200
'''
with open(os.path.join(workspace, "platform/modules/vocab/thresholds.py"), "w") as f:
    f.write(distractor_py_vocab)

# ── Speaking distractor ──────────────────────────────────────────────────────
speaking_notes = """
Speaking Assessment Notes (DRAFT)
===================================
Part 1 (Interview): approximately 2-3 minutes
Part 2 (Discussion): approximately 4-5 minutes
Total pair time: approximately 6-8 minutes

Assessment criteria (tentative):
- Grammar
- Pronunciation
- Interaction

Note: these timings are unconfirmed - check latest Cambridge spec.
"""
with open(os.path.join(workspace, "platform/modules/speaking/assessment_notes.txt"), "w") as f:
    f.write(speaking_notes)

# ── Test stubs ───────────────────────────────────────────────────────────────
test_stub_unit = '''
import unittest
# Unit tests for config validation
# TODO: update expected values once spec is finalized

class TestWritingConfig(unittest.TestCase):
    def test_part6_min_words(self):
        # expected = ???
        pass

    def test_part7_min_words(self):
        # expected = ???
        pass
'''
with open(os.path.join(workspace, "platform/tests/unit/test_config.py"), "w") as f:
    f.write(test_stub_unit)

test_stub_integration = '''
# Integration test scaffold
# Checks that exam modules load with correct parameters

def test_listening_playback():
    """Verify audio plays correct number of times per exam spec."""
    # playback_count = get_playback_count()
    # assert playback_count == ???  # check KET spec
    pass
'''
with open(os.path.join(workspace, "platform/tests/integration/test_listening.py"), "w") as f:
    f.write(test_stub_integration)

# ── Migration scripts ────────────────────────────────────────────────────────
migration_script = '''#!/usr/bin/env python3
"""
Config migration script v1->v2
Migrates legacy exam_structure_v1.json to new format.
WARNING: Values in v1 are known to be incorrect.
Run only after verifying correct values from spec documentation.
"""

import json, sys

def migrate(input_path, output_path):
    with open(input_path) as f:
        old = json.load(f)
    # TODO: apply corrections based on verified spec
    new = old.copy()
    with open(output_path, "w") as f:
        json.dump(new, f, indent=2)

if __name__ == "__main__":
    migrate(sys.argv[1], sys.argv[2])
'''
with open(os.path.join(workspace, "scripts/migration/migrate_v1_to_v2.py"), "w") as f:
    f.write(migration_script)

validator_script = '''#!/usr/bin/env python3
"""Schema validator for exam config files."""
import json, jsonschema, sys

SCHEMA = {
    "type": "object",
    "required": ["exam_config_version", "modules"],
    "properties": {
        "exam_config_version": {"type": "string"},
        "modules": {"type": "object"}
    }
}

def validate(path):
    with open(path) as f:
        data = json.load(f)
    jsonschema.validate(data, SCHEMA)
    print("Schema validation passed.")

if __name__ == "__main__":
    validate(sys.argv[1])
'''
with open(os.path.join(workspace, "scripts/validators/schema_check.py"), "w") as f:
    f.write(validator_script)

# ── Archived docs ────────────────────────────────────────────────────────────
archived_doc = """
[ARCHIVED - DO NOT USE]
Old KET Module Reference (2019)
Reading parts: 1-5, Writing parts: 6-7
Listening parts: 1-5
Speaking parts: 1-2

Old word limits:
- Written response A: minimum 15 words
- Written response B: minimum 25 words
These have since been revised.
"""
with open(os.path.join(workspace, "docs/archived/old_ket_reference.txt"), "w") as f:
    f.write(archived_doc)

internal_doc = """
Internal Platform Notes
========================
The exam configuration system needs a single source-of-truth JSON file.
Currently configs are scattered across legacy/, drafts/, and module code.
Engineering ticket: consolidate into platform/config/exam_config.json

Required sections:
- Module structure (reading/writing, listening, speaking)
- Question counts per part
- Writing word minimums
- Vocabulary level thresholds
- Listening playback settings
- Learner level progression path

All values must come from the authoritative skill documentation (SKILL.md).
"""
with open(os.path.join(workspace, "docs/internal/config_consolidation_notes.txt"), "w") as f:
    f.write(internal_doc)

print("Workspace generated successfully.")
print(f"Files created across {len(dirs)} directories.")