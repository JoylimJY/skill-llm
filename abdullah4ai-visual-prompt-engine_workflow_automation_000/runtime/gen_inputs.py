#!/usr/bin/env python3
"""
Generates the initial sandbox workspace for the visual-prompt-engine evaluation task.
"""
import os
import json
import random

random.seed(42)

workspace = "/workspace"

# ── Directory structure ──────────────────────────────────────────────────────
dirs = [
    "data",
    "scripts",
    "references",
    "assets/fonts",
    "assets/mockups",
    "assets/brand_guidelines",
    "docs/internal",
    "docs/client_briefs",
    "campaigns/q3_brutalist",
    "campaigns/q2_archive",
    "logs",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# ── Distractor files ─────────────────────────────────────────────────────────
distractors = {
    "assets/fonts/brand_font_spec.txt": "Font: Neue Haas Grotesk, weight 700, tracking -20\n",
    "assets/brand_guidelines/color_palette.txt": "Primary: #1A1A2E\nSecondary: #E94560\nAccent: #0F3460\n",
    "assets/mockups/campaign_brief_q3.txt": "Campaign: Urban Edge\nTarget: Gen-Z, 18-25\nPlatform: Instagram, TikTok\nDeadline: 2024-08-01\n",
    "docs/client_briefs/brutalist_brand_brief.txt": "Client: Neoform Labs\nBrief: Bold, raw, industrial aesthetic. Think exposed grids, heavy typography, high contrast.\n",
    "docs/internal/meeting_notes_2024_07.txt": "Discussed AI image repetition problem. Team frustrated by same palettes.\n",
    "campaigns/q3_brutalist/concept_notes.txt": "Brutalist UI: raw concrete textures, exposed structure, monochrome with neon accents.\n",
    "campaigns/q2_archive/old_prompts.txt": "Prompt 1: A serene landscape at dusk\nPrompt 2: Minimalist workspace with plants\n",
    "logs/scrape_errors.log": "2024-07-01 ERROR: Dribbble WAF blocked request\n2024-07-02 WARN: Rate limit hit, falling back to RSS\n",
    "assets/mockups/shot_reference_notes.txt": "Manually collected 5 brutalist UI shots from Dribbble for Q3 campaign.\n",
    "docs/internal/ai_image_guidelines.txt": "Do not use: beautiful, nice, stunning, gorgeous, amazing\nUse specific design terminology instead.\n",
    "campaigns/q3_brutalist/competitor_analysis.txt": "Competitor A uses pastel gradients. Competitor B: flat design. We need something rawer.\n",
    "data/.gitkeep": "",
}
for path, content in distractors.items():
    with open(os.path.join(workspace, path), "w") as f:
        f.write(content)

# ── scripts/scrape_dribbble.py ───────────────────────────────────────────────
scrape_script = r'''#!/usr/bin/env python3
"""Dribbble reference collector. Supports --method import for manual JSON import."""
import argparse
import json
import sys
import os

def main():
    parser = argparse.ArgumentParser(description="Collect Dribbble visual references")
    parser.add_argument("--output", required=True, help="Output JSON file path")
    parser.add_argument("--count", type=int, default=20, help="Number of shots to collect (live mode)")
    parser.add_argument("--method", choices=["live", "rss", "import"], default="live",
                        help="Collection method: live (browser scrape), rss (RSS feed), import (manual JSON)")
    parser.add_argument("--import-file", help="Path to manually collected shots JSON (required for --method import)")
    args = parser.parse_args()

    os.makedirs(os.path.dirname(args.output) if os.path.dirname(args.output) else ".", exist_ok=True)

    if args.method == "import":
        if not args.import_file:
            print("ERROR: --import-file is required when --method import is used", file=sys.stderr)
            sys.exit(1)
        if not os.path.exists(args.import_file):
            print(f"ERROR: Import file not found: {args.import_file}", file=sys.stderr)
            sys.exit(1)
        with open(args.import_file) as f:
            shots = json.load(f)
        # Validate structure
        required_keys = {"title", "url", "image_url"}
        valid = []
        for shot in shots:
            if isinstance(shot, dict) and required_keys.issubset(shot.keys()):
                valid.append(shot)
            else:
                print(f"WARN: Skipping invalid shot record: {shot}", file=sys.stderr)
        result = {
            "method": "import",
            "count": len(valid),
            "shots": valid
        }
        with open(args.output, "w") as f:
            json.dump(result, f, indent=2)
        print(f"Imported {len(valid)} shots -> {args.output}")

    elif args.method in ("live", "rss"):
        # Simulate WAF block for live/rss in this sandbox
        print("WARN: Live/RSS scraping is blocked in this environment (WAF). Use --method import.", file=sys.stderr)
        # Write empty result so downstream can fail gracefully
        result = {"method": args.method, "count": 0, "shots": [], "error": "WAF_BLOCKED"}
        with open(args.output, "w") as f:
            json.dump(result, f, indent=2)
        sys.exit(0)

if __name__ == "__main__":
    main()
'''

with open(os.path.join(workspace, "scripts/scrape_dribbble.py"), "w") as f:
    f.write(scrape_script)
os.chmod(os.path.join(workspace, "scripts/scrape_dribbble.py"), 0o755)

# ── scripts/style_card.py ────────────────────────────────────────────────────
style_card_script = r'''#!/usr/bin/env python3
"""Converts raw Dribbble references into structured style cards."""
import argparse
import json
import sys
import os
import hashlib

MOOD_MAP = {
    "brutalist": ["raw", "industrial", "confrontational", "bold"],
    "minimal": ["calm", "restrained", "clean", "focused"],
    "playful": ["energetic", "whimsical", "vibrant", "joyful"],
    "dark": ["moody", "atmospheric", "dramatic", "intense"],
    "gradient": ["fluid", "dreamy", "modern", "smooth"],
}

COMPOSITION_MAP = {
    "brutalist": "asymmetric grid with exposed structural elements",
    "minimal": "centered negative space",
    "playful": "dynamic diagonal flow",
    "dark": "low-key with vignette framing",
    "gradient": "full-bleed radial composition",
}

TEXTURE_MAP = {
    "brutalist": ["raw concrete", "exposed grain", "halftone overlay"],
    "minimal": ["matte surface", "micro-texture paper"],
    "playful": ["glossy pop", "flat vector"],
    "dark": ["deep shadow", "velvet matte"],
    "gradient": ["glass morphism", "frosted overlay"],
}

LIGHTING_MAP = {
    "brutalist": "harsh directional side-light, deep shadows",
    "minimal": "diffused ambient light, near-shadowless",
    "playful": "bright even illumination, high saturation",
    "dark": "single-point dramatic backlighting",
    "gradient": "luminous inner glow, rim lighting",
}

DEFAULT_PALETTES = {
    "brutalist": ["#1C1C1C", "#F5F0E8", "#FF2D00", "#FFFFFF"],
    "minimal": ["#F8F8F8", "#222222", "#E0E0E0"],
    "playful": ["#FF6B6B", "#FFE66D", "#4ECDC4", "#45B7D1"],
    "dark": ["#0D0D0D", "#1A1A2E", "#E94560", "#533483"],
    "gradient": ["#667eea", "#764ba2", "#f093fb", "#f5576c"],
}

def detect_style(title: str) -> str:
    title_lower = title.lower()
    for style in MOOD_MAP:
        if style in title_lower:
            return style
    for word, style in [
        ("raw", "brutalist"), ("grid", "brutalist"), ("concrete", "brutalist"), ("exposed", "brutalist"),
        ("clean", "minimal"), ("white", "minimal"), ("simple", "minimal"),
        ("fun", "playful"), ("colorful", "playful"), ("bright", "playful"),
        ("night", "dark"), ("shadow", "dark"), ("noir", "dark"),
        ("glow", "gradient"), ("aurora", "gradient"), ("blur", "gradient"),
    ]:
        if word in title_lower:
            return style
    return "minimal"

def build_style_card(shot: dict, idx: int) -> dict:
    style = detect_style(shot.get("title", ""))
    shot_id = hashlib.md5(shot.get("url", str(idx)).encode()).hexdigest()[:8]
    card = {
        "id": f"card_{shot_id}",
        "source_url": shot.get("url", ""),
        "title": shot.get("title", "Untitled"),
        "palette": DEFAULT_PALETTES.get(style, DEFAULT_PALETTES["minimal"]),
        "composition": COMPOSITION_MAP.get(style, "centered negative space"),
        "typography": "heavy sans-serif, tight tracking, oversized weight" if style == "brutalist" else "geometric sans, balanced weight",
        "mood": MOOD_MAP.get(style, ["clean"]),
        "textures": TEXTURE_MAP.get(style, ["matte surface"]),
        "lighting": LIGHTING_MAP.get(style, "diffused ambient light"),
        "tags": [style, "ui-design", "digital"],
    }
    return card

def main():
    parser = argparse.ArgumentParser(description="Build style cards from Dribbble references")
    subparsers = parser.add_subparsers(dest="command")
    
    build_parser = subparsers.add_parser("build", help="Build style cards from references JSON")
    build_parser.add_argument("--input", required=True, help="Input references JSON")
    build_parser.add_argument("--output", required=True, help="Output style cards JSON")
    
    args = parser.parse_args()
    
    if args.command != "build":
        print("ERROR: Unknown command. Use: style_card.py build --input ... --output ...", file=sys.stderr)
        sys.exit(1)
    
    if not os.path.exists(args.input):
        print(f"ERROR: Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    with open(args.input) as f:
        data = json.load(f)
    
    shots = data.get("shots", [])
    if not shots:
        print("WARN: No shots found in input. Style cards will be empty.", file=sys.stderr)
    
    cards = [build_style_card(shot, i) for i, shot in enumerate(shots)]
    
    output = {
        "version": "1.0",
        "card_count": len(cards),
        "cards": cards
    }
    
    os.makedirs(os.path.dirname(args.output) if os.path.dirname(args.output) else ".", exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(output, f, indent=2)
    
    print(f"Built {len(cards)} style cards -> {args.output}")

if __name__ == "__main__":
    main()
'''

with open(os.path.join(workspace, "scripts/style_card.py"), "w") as f:
    f.write(style_card_script)
os.chmod(os.path.join(workspace, "scripts/style_card.py"), 0o755)

# ── references/prompt-patterns.md ────────────────────────────────────────────
prompt_patterns = """# Prompt Patterns

Use these 12 distinct structures to prevent repetition. Rotate patterns; never use the same pattern as any of the last 5 prompts.

## Pattern 1: Material Study
`[Subject] rendered in [material], [surface_quality] texture, [lighting] illumination, [palette] color range, [composition] framing, [mood] atmosphere`

## Pattern 2: Cinematic Atmosphere (OVERUSED - see history before choosing)
`[Scene] shot on [camera/lens], [lighting] cinematography, [color_grade] palette, [texture_overlay], [mood] emotional register`

## Pattern 3: Graphic Design Abstraction
`[Design_element] as primary visual, [typography_style] letterforms, [composition], [palette], [print_technique] finish, [mood]`

## Pattern 4: Spatial Environment
`[Space_type] interior/exterior, [architectural_style], [material_palette], [light_source] at [time_of_day], [atmospheric_quality], [focal_element]`

## Pattern 5: Typographic Poster
`Editorial poster design, [headline_treatment], [grid_system] layout, [color_blocks], [texture_layer], [design_movement] influence`

## Pattern 6: Product Still Life
`[Product_category] still life, [surface_material], [prop_arrangement], [light_direction] from [angle], [depth_of_field], [palette] tones`

## Pattern 7: Data Visualization Art
`[Data_concept] as visual art, [chart_type] morphed into [organic_form], [palette], [rendering_style], [texture], [mood]`

## Pattern 8: Texture Macro
`Extreme macro of [material], [surface_detail], [light_quality], [color_cast], [depth_cue], tactile [mood]`

## Pattern 9: Motion Freeze Frame
`[Action] frozen mid-motion, [technique: high-speed / long exposure], [motion_blur_style], [palette], [background_treatment], [emotional_quality]`

## Pattern 10: Collage / Mixed Media
`[Subject] as analog collage, [paper_texture] layering, [print_era] halftone, [color_risograph] palette, [composition], [mood]`

## Pattern 11: Isometric World
`Isometric [scene], [pixel/low-poly/detailed] rendering, [palette], [lighting_angle], [scale_contrast], [mood]`

## Pattern 12: Brand Identity Fragment
`[Brand_element] fragment, [scale] crop, [material_rendering], [color_system], [typography_treatment], [layout_tension], [cultural_reference]`
"""

with open(os.path.join(workspace, "references/prompt-patterns.md"), "w") as f:
    f.write(prompt_patterns)

# ── references/visual-vocabulary.md ──────────────────────────────────────────
visual_vocab = """# Visual Vocabulary

Use these precise terms instead of generic adjectives.

## Color
- chroma-shifted, desaturated ochre, duotone wash, split complementary, chromatic aberration, triadic tension
- warm-neutral ground, cold accent, muted earth, electric contrast

## Composition
- bleed-edge, negative space tension, visual weight imbalance, rule-of-thirds offset, brutalist grid, Swiss grid discipline
- asymmetric balance, radial symmetry disrupted, golden ratio crop, dead-zone emphasis

## Lighting
- raking side-light, rembrandt triangle, rim-light halo, hard-shadow graphic, fill-light lifted, bounced ambient
- single-source dramatic, overexposed blow-out, chiaroscuro contrast, neon scatter

## Texture
- micro-grain film, halftone rosette, risograph bleed, screen-print roughness, concrete aggregate, sand-cast surface
- paper tooth, linen weave, glass caustic, frosted diffusion

## Typography (when present)
- condensed grotesque, slab-serif weight, variable axis stretch, optical kerning, tracked display, editorial scale

## Mood / Atmosphere
- confrontational stillness, industrial sublime, restrained tension, kinetic arrested, melancholic warmth, synthetic nostalgia
- raw immediacy, typographic aggression, tactile intimacy
"""

with open(os.path.join(workspace, "references/visual-vocabulary.md"), "w") as f:
    f.write(visual_vocab)

# ── references/style-card-schema.md ──────────────────────────────────────────
schema_doc = """# Style Card Schema

```json
{
  "id": "string - unique card identifier",
  "source_url": "string - original Dribbble shot URL",
  "title": "string - shot title",
  "palette": ["#hex", ...],
  "composition": "string - layout structure description",
  "typography": "string - font style and weight characteristics",
  "mood": ["string", ...],
  "textures": ["string", ...],
  "lighting": "string - light direction and quality",
  "tags": ["string", ...]
}
```

Style cards are stored as an array under the `cards` key in `data/style_cards.json`.
"""

with open(os.path.join(workspace, "references/style-card-schema.md"), "w") as f:
    f.write(schema_doc)

# ── Manual shots import file (pre-collected brutalist UI shots) ───────────────
manual_shots = [
    {
        "title": "Brutalist Grid Dashboard UI",
        "url": "https://dribbble.com/shots/00000001-brutalist-grid-dashboard",
        "image_url": "https://cdn.dribbble.com/shots/00000001.png"
    },
    {
        "title": "Raw Concrete Brand Identity",
        "url": "https://dribbble.com/shots/00000002-raw-concrete-brand",
        "image_url": "https://cdn.dribbble.com/shots/00000002.png"
    },
    {
        "title": "Brutalist Exposed Typography Poster",
        "url": "https://dribbble.com/shots/00000003-brutalist-type-poster",
        "image_url": "https://cdn.dribbble.com/shots/00000003.png"
    },
    {
        "title": "Industrial Dark UI Components",
        "url": "https://dribbble.com/shots/00000004-industrial-dark-ui",
        "image_url": "https://cdn.dribbble.com/shots/00000004.png"
    },
    {
        "title": "Exposed Grid Layout System",
        "url": "https://dribbble.com/shots/00000005-exposed-grid-layout",
        "image_url": "https://cdn.dribbble.com/shots/00000005.png"
    },
]
with open(os.path.join(workspace, "campaigns/q3_brutalist/manual_shots.json"), "w") as f:
    json.dump(manual_shots, f, indent=2)

# ── data/prompt_history.json (pre-populated with 5 "Cinematic Atmosphere" prompts) ──
# This is THE TRAP: all 5 recent prompts use Pattern 2 (Cinematic Atmosphere).
# The agent must detect this and use a DIFFERENT pattern.
prompt_history = {
    "prompts": [
        {
            "id": "ph_001",
            "pattern": "Cinematic Atmosphere",
            "pattern_id": 2,
            "prompt": "Brutalist concrete building shot on 35mm, harsh chiaroscuro cinematography, desaturated ochre palette, halftone overlay, confrontational stillness emotional register",
            "timestamp": "2024-07-01T10:00:00Z"
        },
        {
            "id": "ph_002",
            "pattern": "Cinematic Atmosphere",
            "pattern_id": 2,
            "prompt": "Industrial warehouse interior shot on anamorphic lens, raking side-light cinematography, duotone wash palette, concrete aggregate texture, raw immediacy emotional register",
            "prompt": "Industrial warehouse interior shot on anamorphic lens, raking side-light cinematography, duotone wash palette, micro-grain film texture, industrial sublime emotional register",
            "timestamp": "2024-07-02T11:30:00Z"
        },
        {
            "id": "ph_003",
            "pattern": "Cinematic Atmosphere",
            "pattern_id": 2,
            "prompt": "Raw steel framework shot on medium format, hard-shadow graphic cinematography, cold accent palette, screen-print roughness texture, typographic aggression emotional register",
            "timestamp": "2024-07-03T09:15:00Z"
        },
        {
            "id": "ph_004",
            "pattern": "Cinematic Atmosphere",
            "pattern_id": 2,
            "prompt": "Exposed concrete facade shot on 28mm wide, neon scatter cinematography, chroma-shifted muted earth palette, sand-cast surface texture, kinetic arrested emotional register",
            "timestamp": "2024-07-04T14:00:00Z"
        },
        {
            "id": "ph_005",
            "pattern": "Cinematic Atmosphere",
            "pattern_id": 2,
            "prompt": "Brutalist stairwell shot on 50mm, single-source dramatic cinematography, split complementary palette, paper tooth texture, confrontational stillness emotional register",
            "timestamp": "2024-07-05T16:45:00Z"
        }
    ]
}

with open(os.path.join(workspace, "data/prompt_history.json"), "w") as f:
    json.dump(prompt_history, f, indent=2)

print("Workspace generated successfully.")
print(f"Files created in: {workspace}")