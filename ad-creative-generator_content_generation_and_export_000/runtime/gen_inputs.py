import os
import json
import random
import shutil

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# --- Create the ad-creative-generator skill directory ---
skill_dir = os.path.join(workspace, "skills", "ad-creative-generator")
os.makedirs(skill_dir, exist_ok=True)

# --- Generate generate.js (main script) ---
generate_js = r"""
#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const readline = require('readline');

// Load templates
const templates = require('./templates.js');

// Parse command line arguments
function parseArgs() {
    const args = process.argv.slice(2);
    const parsed = {
        product: null,
        categories: null,
        all: false,
        export: null,
        output: null,
        interactive: false
    };

    for (let i = 0; i < args.length; i++) {
        switch (args[i]) {
            case '--product':
                parsed.product = args[++i];
                break;
            case '--categories':
                parsed.categories = args[++i] ? args[++i - 1 + 1].split(',').map(c => c.trim()) : null;
                // re-parse correctly
                parsed.categories = args[i].split(',').map(c => c.trim());
                break;
            case '--all':
                parsed.all = true;
                break;
            case '--export':
                parsed.export = args[++i];
                break;
            case '--output':
                parsed.output = args[++i];
                break;
            case '--interactive':
                parsed.interactive = true;
                break;
        }
    }
    return parsed;
}

function generatePrompts(product, categoryKeys) {
    const prompts = [];
    for (const key of categoryKeys) {
        const category = templates[key];
        if (!category) {
            console.error(`Warning: Unknown category '${key}', skipping.`);
            continue;
        }
        for (const style of category.styles) {
            prompts.push({
                category: category.name,
                style: style.name,
                prompt: style.template.replace(/\{product\}/g, product)
            });
        }
    }
    return prompts;
}

function exportJSON(product, prompts, outputPath) {
    const data = {
        product: product,
        generated_at: new Date().toISOString(),
        prompts: prompts
    };
    const content = JSON.stringify(data, null, 2);
    if (outputPath) {
        fs.writeFileSync(outputPath, content, 'utf8');
        console.log(`JSON exported to: ${outputPath}`);
    } else {
        console.log(content);
    }
    return data;
}

function exportText(product, prompts, outputPath) {
    let content = `Ad Creative Prompts for: ${product}\n`;
    content += `Generated at: ${new Date().toISOString()}\n`;
    content += '='.repeat(60) + '\n\n';
    for (const p of prompts) {
        content += `Category: ${p.category}\n`;
        content += `Style: ${p.style}\n`;
        content += `Prompt: ${p.prompt}\n`;
        content += '-'.repeat(40) + '\n\n';
    }
    if (outputPath) {
        fs.writeFileSync(outputPath, content, 'utf8');
        console.log(`Text exported to: ${outputPath}`);
    } else {
        console.log(content);
    }
    return content;
}

function exportMarkdown(product, prompts, outputPath) {
    let content = `# Ad Creative Prompts: ${product}\n\n`;
    content += `**Generated at:** ${new Date().toISOString()}\n\n`;

    // Group by category
    const grouped = {};
    for (const p of prompts) {
        if (!grouped[p.category]) grouped[p.category] = [];
        grouped[p.category].push(p);
    }

    for (const [cat, items] of Object.entries(grouped)) {
        content += `## ${cat}\n\n`;
        for (const item of items) {
            content += `### ${item.style}\n\n`;
            content += `${item.prompt}\n\n`;
        }
    }

    if (outputPath) {
        fs.writeFileSync(outputPath, content, 'utf8');
        console.log(`Markdown exported to: ${outputPath}`);
    } else {
        console.log(content);
    }
    return content;
}

async function interactiveMode() {
    const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
    const question = (q) => new Promise(resolve => rl.question(q, resolve));

    console.log('\n=== Ad Creative Generator ===\n');
    const product = await question('Enter your product/brand name: ');

    console.log('\nAvailable categories:');
    const catKeys = Object.keys(templates);
    catKeys.forEach((k, i) => console.log(`  ${i + 1}. ${templates[k].name} (${k})`));

    const catInput = await question('\nEnter category keys (comma-separated) or "all": ');
    let selectedKeys;
    if (catInput.trim().toLowerCase() === 'all') {
        selectedKeys = catKeys;
    } else {
        selectedKeys = catInput.split(',').map(c => c.trim());
    }

    const prompts = generatePrompts(product, selectedKeys);

    console.log('\nExport format: json, text, markdown (or press Enter to display):');
    const fmt = await question('Format: ');
    const outFile = await question('Output file (or press Enter to display): ');

    const outputPath = outFile.trim() || null;

    if (fmt.trim() === 'json') {
        exportJSON(product, prompts, outputPath);
    } else if (fmt.trim() === 'markdown') {
        exportMarkdown(product, prompts, outputPath);
    } else {
        exportText(product, prompts, outputPath);
    }

    rl.close();
}

// Main
const args = parseArgs();

if (!args.product && !args.interactive) {
    // Check if stdin is a TTY (interactive)
    if (process.stdin.isTTY) {
        interactiveMode().catch(console.error);
    } else {
        console.error('Error: --product is required in non-interactive mode.');
        process.exit(1);
    }
} else if (args.interactive) {
    interactiveMode().catch(console.error);
} else {
    // Non-interactive mode
    if (!args.product || args.product.trim() === '') {
        console.error('Error: Product name cannot be empty.');
        process.exit(1);
    }

    const allKeys = Object.keys(templates);
    let selectedKeys;

    if (args.all) {
        selectedKeys = allKeys;
    } else if (args.categories && args.categories.length > 0) {
        selectedKeys = args.categories;
    } else {
        selectedKeys = allKeys;
    }

    const prompts = generatePrompts(args.product, selectedKeys);

    if (prompts.length === 0) {
        console.error('Error: No prompts generated. Check your category names.');
        process.exit(1);
    }

    const fmt = args.export || 'text';
    const outputPath = args.output || null;

    if (fmt === 'json') {
        exportJSON(args.product, prompts, outputPath);
    } else if (fmt === 'markdown') {
        exportMarkdown(args.product, prompts, outputPath);
    } else {
        exportText(args.product, prompts, outputPath);
    }
}
"""

# Fix the --categories parsing bug in generate.js (clean version)
generate_js_clean = r"""#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const readline = require('readline');

const templates = require('./templates.js');

function parseArgs() {
    const args = process.argv.slice(2);
    const parsed = {
        product: null,
        categories: null,
        all: false,
        export: null,
        output: null,
        interactive: false
    };

    for (let i = 0; i < args.length; i++) {
        if (args[i] === '--product') {
            parsed.product = args[++i];
        } else if (args[i] === '--categories') {
            parsed.categories = args[++i].split(',').map(c => c.trim());
        } else if (args[i] === '--all') {
            parsed.all = true;
        } else if (args[i] === '--export') {
            parsed.export = args[++i];
        } else if (args[i] === '--output') {
            parsed.output = args[++i];
        } else if (args[i] === '--interactive') {
            parsed.interactive = true;
        }
    }
    return parsed;
}

function generatePrompts(product, categoryKeys) {
    const prompts = [];
    for (const key of categoryKeys) {
        const category = templates[key];
        if (!category) {
            console.error(`Warning: Unknown category '${key}', skipping.`);
            continue;
        }
        for (const style of category.styles) {
            prompts.push({
                category: category.name,
                style: style.name,
                prompt: style.template.replace(/\{product\}/g, product)
            });
        }
    }
    return prompts;
}

function exportJSON(product, prompts, outputPath) {
    const data = {
        product: product,
        generated_at: new Date().toISOString(),
        prompts: prompts
    };
    const content = JSON.stringify(data, null, 2);
    if (outputPath) {
        fs.writeFileSync(outputPath, content, 'utf8');
        console.log(`JSON exported to: ${outputPath}`);
    } else {
        console.log(content);
    }
    return data;
}

function exportText(product, prompts, outputPath) {
    let content = `Ad Creative Prompts for: ${product}\n`;
    content += `Generated at: ${new Date().toISOString()}\n`;
    content += '='.repeat(60) + '\n\n';
    for (const p of prompts) {
        content += `Category: ${p.category}\n`;
        content += `Style: ${p.style}\n`;
        content += `Prompt: ${p.prompt}\n`;
        content += '-'.repeat(40) + '\n\n';
    }
    if (outputPath) {
        fs.writeFileSync(outputPath, content, 'utf8');
        console.log(`Text exported to: ${outputPath}`);
    } else {
        console.log(content);
    }
    return content;
}

function exportMarkdown(product, prompts, outputPath) {
    let content = `# Ad Creative Prompts: ${product}\n\n`;
    content += `**Generated at:** ${new Date().toISOString()}\n\n`;

    const grouped = {};
    for (const p of prompts) {
        if (!grouped[p.category]) grouped[p.category] = [];
        grouped[p.category].push(p);
    }

    for (const [cat, items] of Object.entries(grouped)) {
        content += `## ${cat}\n\n`;
        for (const item of items) {
            content += `### ${item.style}\n\n`;
            content += `${item.prompt}\n\n`;
        }
    }

    if (outputPath) {
        fs.writeFileSync(outputPath, content, 'utf8');
        console.log(`Markdown exported to: ${outputPath}`);
    } else {
        console.log(content);
    }
    return content;
}

async function interactiveMode() {
    const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
    const question = (q) => new Promise(resolve => rl.question(q, resolve));

    console.log('\n=== Ad Creative Generator ===\n');
    const product = await question('Enter your product/brand name: ');

    console.log('\nAvailable categories:');
    const catKeys = Object.keys(templates);
    catKeys.forEach((k, i) => console.log(`  ${i + 1}. ${templates[k].name} (${k})`));

    const catInput = await question('\nEnter category keys (comma-separated) or "all": ');
    let selectedKeys;
    if (catInput.trim().toLowerCase() === 'all') {
        selectedKeys = catKeys;
    } else {
        selectedKeys = catInput.split(',').map(c => c.trim());
    }

    const prompts = generatePrompts(product, selectedKeys);

    console.log('\nExport format: json, text, markdown');
    const fmt = await question('Format: ');
    const outFile = await question('Output file (or press Enter to display): ');
    const outputPath = outFile.trim() || null;

    if (fmt.trim() === 'json') {
        exportJSON(product, prompts, outputPath);
    } else if (fmt.trim() === 'markdown') {
        exportMarkdown(product, prompts, outputPath);
    } else {
        exportText(product, prompts, outputPath);
    }

    rl.close();
}

const args = parseArgs();

if (args.interactive || (!args.product && process.stdin.isTTY)) {
    interactiveMode().catch(console.error);
} else if (!args.product) {
    console.error('Error: --product is required in non-interactive mode.');
    process.exit(1);
} else {
    if (!args.product.trim()) {
        console.error('Error: Product name cannot be empty.');
        process.exit(1);
    }

    const allKeys = Object.keys(templates);
    let selectedKeys;

    if (args.all) {
        selectedKeys = allKeys;
    } else if (args.categories && args.categories.length > 0) {
        selectedKeys = args.categories;
    } else {
        selectedKeys = allKeys;
    }

    const prompts = generatePrompts(args.product, selectedKeys);

    if (prompts.length === 0) {
        console.error('Error: No prompts generated. Check your category names.');
        process.exit(1);
    }

    const fmt = args.export || 'text';
    const outputPath = args.output || null;

    if (fmt === 'json') {
        exportJSON(args.product, prompts, outputPath);
    } else if (fmt === 'markdown') {
        exportMarkdown(args.product, prompts, outputPath);
    } else {
        exportText(args.product, prompts, outputPath);
    }
}
"""

with open(os.path.join(skill_dir, "generate.js"), "w") as f:
    f.write(generate_js_clean)

# --- Generate templates.js ---
templates_js = r"""'use strict';

module.exports = {
    minimalist: {
        name: "Minimalist",
        styles: [
            {
                name: "Hand-drawn Minimalist",
                template: "Minimalist creative advertisement with hand-drawn elements, featuring {product} with clean lines, soft pastel accents, negative space emphasizing the product, botanical sketches, elegant typography, white background"
            },
            {
                name: "Geometric Minimalist",
                template: "Geometric minimalist ad for {product}, simple shapes, monochromatic palette, strong negative space, modern sans-serif typography, studio lighting"
            },
            {
                name: "Typography-Only",
                template: "Pure typography advertisement for {product}, bold statement text, minimal color, white space, no imagery, impactful font pairing, print-quality layout"
            }
        ]
    },
    transformation: {
        name: "Product Transformation",
        styles: [
            {
                name: "Translucent Material",
                template: "{product} transformed into translucent paper glass material, soft light filtering through, visible internal layers, delicate texture, ethereal lighting, pastel color gradient background"
            },
            {
                name: "Nature Integration",
                template: "{product} seamlessly merging with natural elements, organic textures bleeding into product form, roots or vines interweaving, golden hour lighting, earthy palette"
            },
            {
                name: "Liquid Sculpture",
                template: "{product} dissolving into or emerging from liquid, high-speed photography style, dramatic splash, studio black background, macro detail, vibrant color contrast"
            }
        ]
    },
    cultural: {
        name: "Cultural/Exotic",
        styles: [
            {
                name: "Moroccan Market",
                template: "{product} in exotic Moroccan market scene, vibrant souk stalls, golden hour lighting, intricate mosaic patterns as background, cultural textiles, authenticity, warm color palette, cinematic composition"
            },
            {
                name: "Japanese Zen",
                template: "{product} in minimalist Japanese zen garden setting, raked gravel, cherry blossoms, wabi-sabi aesthetic, soft morning light, tranquil atmosphere, muted earthy tones"
            },
            {
                name: "Festival Vibrancy",
                template: "{product} integrated into vibrant festival scene, confetti and color powder explosion, joyful crowds, dynamic movement, high saturation, celebratory energy"
            }
        ]
    },
    lifestyle: {
        name: "Lifestyle",
        styles: [
            {
                name: "Morning Ritual",
                template: "{product} as centerpiece of aspirational morning ritual, golden morning light, linen textures, coffee steam, lifestyle magazine aesthetic, warm neutral tones"
            },
            {
                name: "Urban Explorer",
                template: "{product} with urban explorer in city environment, rooftop scene, skyline backdrop, candid documentary style, desaturated tones with single color pop"
            },
            {
                name: "Wellness Journey",
                template: "{product} integrated into wellness lifestyle, yoga or nature setting, soft bokeh, health-conscious consumer vibe, clean airy composition"
            }
        ]
    },
    technology: {
        name: "Technology",
        styles: [
            {
                name: "Holographic Display",
                template: "{product} presented as holographic display, neon grid lines, dark background, light trails, cyber aesthetic, high-tech UI elements surrounding the product"
            },
            {
                name: "Digital Deconstruction",
                template: "{product} deconstructed into floating digital components, circuit patterns, data visualization overlay, deep space background, precision engineering aesthetic"
            },
            {
                name: "AI Neural Art",
                template: "{product} surrounded by AI neural network visualization, glowing synaptic connections, deep purple and cyan palette, futuristic intelligence theme"
            }
        ]
    },
    luxury: {
        name: "Luxury",
        styles: [
            {
                name: "Dark Opulence",
                template: "{product} in dark opulent setting, black marble surfaces, gold accents, dramatic chiaroscuro lighting, velvet textures, exclusive and powerful mood"
            },
            {
                name: "Aerial Elegance",
                template: "{product} photographed from aerial perspective, symmetrical composition, luxury resort or penthouse setting, aspirational wealth aesthetic, muted luxury palette"
            }
        ]
    },
    eco: {
        name: "Eco/Green",
        styles: [
            {
                name: "Forest Immersion",
                template: "{product} immersed in lush forest environment, dappled sunlight through canopy, moss and fern details, sustainable brand messaging, earthy greens and browns"
            },
            {
                name: "Botanical Blueprint",
                template: "{product} with scientific botanical illustration overlay, hand-drawn plant anatomy, cream parchment background, natural ingredient focus, artisan craft aesthetic"
            },
            {
                name: "Zero Waste Story",
                template: "{product} in zero-waste lifestyle scene, compostable packaging highlighted, farmer's market aesthetic, natural textures, transparency and authenticity"
            }
        ]
    },
    seasonal: {
        name: "Seasonal",
        styles: [
            {
                name: "Winter Wonderland",
                template: "{product} in magical winter scene, snow crystals, soft blue-white palette, cozy warmth contrast, holiday gifting context, bokeh lights background"
            },
            {
                name: "Summer Bloom",
                template: "{product} in vibrant summer bloom setting, wildflowers, golden sunshine, carefree energy, saturated warm tones, outdoor festival aesthetic"
            }
        ]
    },
    emotional: {
        name: "Emotional",
        styles: [
            {
                name: "Memory Lane",
                template: "{product} evoking nostalgic memory, vintage film grain, faded warm tones, family or childhood imagery, soft focus, emotional storytelling composition"
            },
            {
                name: "Triumphant Moment",
                template: "{product} associated with personal triumph, dramatic lighting, individual achievement moment, uplifting energy, inspirational color palette"
            }
        ]
    },
    playful: {
        name: "Playful",
        styles: [
            {
                name: "Pop Art Explosion",
                template: "{product} reimagined as pop art, bold Ben-Day dots, primary color palette, comic book speech bubbles, Andy Warhol inspired repetition, high contrast"
            },
            {
                name: "Surreal Dreamscape",
                template: "{product} in surreal dreamscape, floating objects, impossible scale relationships, Dali-inspired landscape, dream logic, vibrant impossible colors"
            },
            {
                name: "Kawaii Characters",
                template: "{product} integrated with kawaii character illustrations, pastel palette, cute anthropomorphic elements, Japanese cute aesthetic, playful typography"
            }
        ]
    }
};
"""

with open(os.path.join(skill_dir, "templates.js"), "w") as f:
    f.write(templates_js)

# --- Create SKILL.md in the skill directory ---
# (Already exists as part of the skill, but we create a reference copy)
skill_md_content = """# Ad Creative Generator Skill
See the main SKILL.md for full documentation.
"""
with open(os.path.join(skill_dir, "README.md"), "w") as f:
    f.write(skill_md_content)

# --- Create distractor files to test contextual awareness ---

# Marketing team's old notes
old_notes_dir = os.path.join(workspace, "marketing", "campaign_notes")
os.makedirs(old_notes_dir, exist_ok=True)

with open(os.path.join(old_notes_dir, "q4_2024_brief.txt"), "w") as f:
    f.write("Q4 Campaign Ideas\n- Holiday promotions\n- End of year sale\n- Focus on gifting\nProduct: VitaGlow Face Oil\n")

with open(os.path.join(old_notes_dir, "competitor_analysis.csv"), "w") as f:
    f.write("Competitor,Style,Channel\nBrandX,Minimalist,Instagram\nBrandY,Eco,Pinterest\nBrandZ,Luxury,Print\n")

# Old JSON output (malformed / outdated schema - distractor)
old_output_dir = os.path.join(workspace, "marketing", "old_outputs")
os.makedirs(old_output_dir, exist_ok=True)

with open(os.path.join(old_output_dir, "draft_ads.json"), "w") as f:
    old_data = {
        "brand": "VitaGlow",  # Wrong schema field name
        "date": "2024-11-01",  # Wrong field name
        "ads": [  # Wrong field name
            {"type": "minimalist", "text": "Some old draft text..."}
        ]
    }
    json.dump(old_data, f, indent=2)

# Product research files
research_dir = os.path.join(workspace, "product", "research")
os.makedirs(research_dir, exist_ok=True)

with open(os.path.join(research_dir, "vitaglow_ingredients.txt"), "w") as f:
    f.write("VitaGlow Botanical Face Oil\nKey ingredients: Rosehip, Sea Buckthorn, Jojoba\nTarget: 25-45 year old women\nUSP: 100% organic, cold-pressed\n")

with open(os.path.join(research_dir, "market_sizing.json"), "w") as f:
    json.dump({"market_size_usd": 15000000000, "cagr": 0.072, "segment": "organic_skincare"}, f)

# Social media planning files
social_dir = os.path.join(workspace, "marketing", "social_media")
os.makedirs(social_dir, exist_ok=True)

with open(os.path.join(social_dir, "instagram_calendar.csv"), "w") as f:
    f.write("Date,Post Type,Caption,Status\n2025-02-01,Product,TBD,Draft\n2025-02-08,Lifestyle,TBD,Draft\n")

with open(os.path.join(social_dir, "hashtag_research.txt"), "w") as f:
    f.write("#OrganicSkincare #FaceOil #CleanBeauty #VitaGlow #NaturalGlow\n")

# Budget tracking
finance_dir = os.path.join(workspace, "finance", "ad_budget")
os.makedirs(finance_dir, exist_ok=True)

with open(os.path.join(finance_dir, "q1_2025_budget.csv"), "w") as f:
    f.write("Channel,Budget_USD,Allocated,Remaining\nInstagram,50000,20000,30000\nPrint,15000,0,15000\nDigital,35000,10000,25000\n")

# Brand assets directory (empty/placeholder)
brand_dir = os.path.join(workspace, "brand", "assets")
os.makedirs(brand_dir, exist_ok=True)

with open(os.path.join(brand_dir, "brand_guidelines_summary.txt"), "w") as f:
    f.write("VitaGlow Brand Colors: Forest Green (#2D5A27), Cream (#F5F0E8), Gold (#C9A84C)\nFonts: Playfair Display (headings), Lato (body)\nTone: Clean, natural, sophisticated\n")

# Agency communication directory
agency_dir = os.path.join(workspace, "agency", "briefs")
os.makedirs(agency_dir, exist_ok=True)

with open(os.path.join(agency_dir, "spring_launch_request.txt"), "w") as f:
    f.write("""Agency Brief Request - VitaGlow Botanical Face Oil Spring Launch

We need creative concepts for the upcoming Spring 2025 campaign.
The creative team needs both structured data for our content pipeline
AND a formatted document for the creative team's reference.

For the pipeline integration: we specifically need ONLY eco/green and minimalist
style concepts exported as structured data (ads_pipeline.json).

For the creative brief document: we need ALL creative styles documented
in a formatted reference file (creative_brief_all.md).

Product name to use: VitaGlow Botanical Face Oil

Please use the ad creative generation tooling available in the skills directory.
""")

# Partial/incorrect previous attempt by a junior marketer (distractor)
attempts_dir = os.path.join(workspace, "agency", "previous_attempts")
os.makedirs(attempts_dir, exist_ok=True)

with open(os.path.join(attempts_dir, "failed_attempt_notes.txt"), "w") as f:
    f.write("Tried running the script manually but couldn't figure out the flags.\n"
            "Tried: node generate.js --format json --product 'VitaGlow'\n"
            "Got errors. Also tried --category instead of --categories.\n"
            "Not sure how to export to file vs stdout.\n")

# Config files (distractors)
config_dir = os.path.join(workspace, "config")
os.makedirs(config_dir, exist_ok=True)

with open(os.path.join(config_dir, "env.example"), "w") as f:
    f.write("# Environment variables\nNODE_ENV=production\nLOG_LEVEL=info\n")

with open(os.path.join(config_dir, "package.json"), "w") as f:
    json.dump({"name": "vitaglow-marketing", "version": "1.0.0", "description": "Marketing tools"}, f, indent=2)

print("Workspace setup complete.")
print(f"Created skill at: {skill_dir}")
print(f"Created distractor files in: marketing/, product/, finance/, brand/, agency/, config/")