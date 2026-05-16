import os
import json
import random

random.seed(42)

BASE = "/workspace"

# Create deeply nested distractor structure
dirs = [
    "design_system/tokens/colors",
    "design_system/tokens/typography",
    "design_system/tokens/spacing",
    "platform_specs/ios",
    "platform_specs/macos",
    "platform_specs/watchos",
    "platform_specs/tvos",
    "platform_specs/visionos",
    "submissions/raw",
    "submissions/reviewed",
    "submissions/archived",
    "brand/logos",
    "brand/guidelines",
    "engineering/swiftui",
    "engineering/uikit",
    "meetings/2024-q3",
    "meetings/2024-q4",
]

for d in dirs:
    os.makedirs(os.path.join(BASE, d), exist_ok=True)

# Distractor files
distractors = [
    ("design_system/tokens/colors/brand_palette.json", json.dumps({
        "primary": "#FF6B35", "secondary": "#004E89", "accent": "#1A936F"
    }, indent=2)),
    ("design_system/tokens/typography/scale.json", json.dumps({
        "base": 16, "ratio": 1.25
    }, indent=2)),
    ("design_system/tokens/spacing/base.txt", "Base unit: 4pt\nNote: legacy system, migrating to 8pt"),
    ("brand/guidelines/voice_tone.md", "# Voice & Tone\nFriendly, informative, concise."),
    ("brand/logos/usage_rules.txt", "Minimum clear space: 24pt around logo."),
    ("engineering/swiftui/examples.swift", "// SwiftUI snippet placeholder"),
    ("engineering/uikit/migration_notes.md", "# Migration Notes\nMoving from UIKit to SwiftUI incrementally."),
    ("meetings/2024-q3/design_review_notes.txt", "Discussed tab bar vs sidebar for iPad. No resolution."),
    ("meetings/2024-q4/accessibility_audit.txt", "Flagged: contrast issues in dark mode on Settings screen."),
    ("submissions/archived/v1_spec.json", json.dumps({"version": "1.0", "status": "archived"}, indent=2)),
    ("submissions/reviewed/approved_components.txt", "Button styles approved: Filled, Tinted, Gray, Plain"),
    ("platform_specs/ios/notes.txt", "iOS team: Using large title nav bar. Tab bar has 4 destinations."),
    ("platform_specs/macos/sidebar_spec.txt", "macOS: Using NSSplitView for sidebar layout."),
]

for path, content in distractors:
    full_path = os.path.join(BASE, path)
    with open(full_path, "w") as f:
        f.write(content)

# THE MAIN PROBLEM: A messy multi-platform design submission with numerous HIG violations
# The agent must identify violations and produce a corrected spec

raw_submission = {
    "app_name": "StreamFlow",
    "version": "3.2",
    "submission_date": "2024-11-15",
    "submitted_by": "Platform Design Team",
    "platforms": {
        "ios": {
            "typography": {
                "system_font": "SF Pro",
                "body_size_pt": 17,
                "supports_dynamic_type": False,
                "text_styles_used": ["Body", "Headline", "Title1", "Footnote"]
            },
            "navigation": {
                "pattern": "tab_bar",
                "tab_count": 7,
                "tab_labels": ["Home", "Discover", "Library", "Downloads", "Profile", "Settings", "Help"],
                "position": "bottom"
            },
            "layout": {
                "grid_base_pt": 6,
                "iphone_margin_pt": 12,
                "ipad_margin_pt": 20,
                "minimum_touch_target_pt": 44
            },
            "components": {
                "primary_button_style": "filled",
                "sheet_detents": ["medium", "large"],
                "list_style": "inset_grouped",
                "swipe_actions": True
            },
            "accessibility": {
                "voiceover_labels": True,
                "wcag_contrast_ratio_normal_text": 3.5,
                "reduce_motion_support": True,
                "dynamic_type_max_tested": "AX3"
            },
            "dark_mode": {
                "supported": True,
                "uses_semantic_colors": False,
                "avoids_pure_black": True
            },
            "animation": {
                "screen_transition_duration_s": 0.25,
                "sheet_presentation_duration_s": 0.6,
                "button_press_duration_s": 0.15
            }
        },
        "macos": {
            "typography": {
                "system_font": "SF Pro",
                "supports_dynamic_type": True
            },
            "navigation": {
                "pattern": "sidebar_splitview",
                "sidebar_collapsible": True
            },
            "layout": {
                "grid_base_pt": 8,
                "window_margin_pt": 20,
                "minimum_window_width_pt": 480,
                "minimum_window_height_pt": 320
            },
            "toolbar": {
                "customizable": True,
                "shows_icon_and_text": True
            },
            "keyboard_shortcuts": {
                "new": "cmd+n",
                "save": "cmd+s",
                "quit": "cmd+q",
                "preferences": "cmd+comma"
            },
            "accessibility": {
                "voiceover_labels": True,
                "full_keyboard_access": True,
                "wcag_contrast_ratio_normal_text": 4.5
            },
            "dark_mode": {
                "supported": True,
                "uses_semantic_colors": True
            }
        },
        "watchos": {
            "typography": {
                "system_font": "SF Pro",
                "uses_rounded_variant": False
            },
            "layout": {
                "content_edge_to_edge": True,
                "scroll_direction": "vertical"
            },
            "navigation": {
                "pattern": "list_based",
                "uses_digital_crown": True
            },
            "complications": {
                "supported_styles": ["circular", "rectangular"],
                "tappable": True
            },
            "always_on_display": {
                "supported": True,
                "simplified_ui": True
            },
            "accessibility": {
                "voiceover_labels": True,
                "wcag_contrast_ratio_normal_text": 4.5
            }
        },
        "tvos": {
            "typography": {
                "system_font": "SF Pro",
                "minimum_title_size_pt": 48
            },
            "navigation": {
                "pattern": "tab_bar",
                "tab_count": 4,
                "position": "bottom",
                "focus_engine": True
            },
            "layout": {
                "minimum_touch_target_pt": 150,
                "grid_layout": True,
                "parallax_effects": True
            },
            "interaction": {
                "siri_remote": True,
                "directional_navigation": True,
                "haptic_feedback": False
            },
            "accessibility": {
                "voiceover_labels": True,
                "wcag_contrast_ratio_normal_text": 4.5
            }
        },
        "visionos": {
            "typography": {
                "system_font": "SF Pro"
            },
            "windows": {
                "type": "floating",
                "uses_glass_material": True,
                "supports_3d_depth": True
            },
            "interaction": {
                "primary_gesture": "gaze_and_pinch",
                "voice_commands": True,
                "immersion_modes": ["windowed", "full_immersion"]
            },
            "accessibility": {
                "voiceover_labels": True,
                "wcag_contrast_ratio_normal_text": 4.5
            }
        }
    }
}

raw_path = os.path.join(BASE, "submissions/raw/streamflow_design_spec_v3.2.json")
with open(raw_path, "w") as f:
    json.dump(raw_submission, f, indent=2)

# Also create a design_violations_reference stub (distractor, not the answer)
stub = {
    "note": "This file is a placeholder. The compliance report must be generated by reviewing the raw spec.",
    "hint": "Check all platforms for compliance issues."
}
with open(os.path.join(BASE, "submissions/reviewed/compliance_stub.json"), "w") as f:
    json.dump(stub, f, indent=2)

# A changelog for context
changelog = """# StreamFlow Design Spec Changelog

## v3.2 (2024-11-15)
- Added visionOS platform support
- Updated watchOS complications
- Revised iOS navigation structure (added more tabs)
- tvOS layout updates

## v3.1 (2024-09-01)
- macOS sidebar improvements
- Dark mode color token updates

## v3.0 (2024-06-15)
- Initial multi-platform spec
"""
with open(os.path.join(BASE, "submissions/raw/CHANGELOG.md"), "w") as f:
    f.write(changelog)

print("Workspace generated successfully.")
print(f"Raw spec: {raw_path}")