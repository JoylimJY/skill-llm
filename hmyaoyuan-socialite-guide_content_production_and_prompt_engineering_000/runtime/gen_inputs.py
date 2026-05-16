import os
import json

WORKSPACE = "/workspace"

# ── Directory structure ──────────────────────────────────────────────────────
dirs = [
    "docs",
    "clients/2026/Q1",
    "clients/2026/Q2",
    "archive/old_briefs",
    "archive/rejected",
    "assets/moodboards",
    "assets/references",
    "internal/brand_guidelines",
    "internal/templates",
    "shoots/upcoming",
    "shoots/completed",
]
for d in dirs:
    os.makedirs(os.path.join(WORKSPACE, d), exist_ok=True)

# ── SKILL.md ─────────────────────────────────────────────────────────────────
skill_md = """\
# Socialite Photography Guide (名媛拍照指南)

## Description
Expert guidance for generating "Socialite Style" (名媛风) images using AI art tools (Nano Banana Pro). Contains professional advice on lighting, composition, poses, makeup, styling, and prompt engineering formulas.

**Activate this skill when:**
- The user wants "Socialite", "High Fashion", "Luxury", "Influencer", or "Magazine" style photos.
- The user mentions specific styles like "Old Money" (老钱风), "French Chic" (法式优雅), "Korean Style" (韩系名媛), "Heiress" (千金风).
- The user needs advice on posing or lighting for a glam shot.

## Resources
The full guide is located in the `docs/` directory relative to this file:
- **Bible**: `docs/nanobanana_pro名媛拍照指南_完整版.md` (Read this first)
- **Styles**: `docs/nanobanana_pro名媛拍照指南_风格定位与场景搭配.md`
- **Tech**: `docs/nanobanana_pro名媛拍照指南_摄影技术篇.md`
- **Beauty**: `docs/nanobanana_pro_妆容造型指导.md`

## Quick Reference (Formulas)

### 1. Style Formulas
- **Relaxed Chic (松弛感)**: `soft natural lighting` + `relaxed pose` + `pastel color palette` + `cozy cafe/home setting`
- **Expensive/Noble (贵气感)**: `golden accents` + `flawless makeup` + `luxury hotel lobby` + `elegant jewelry`
- **Refined Detail (精致感)**: `symmetrical composition` + `detail-focused` + `soft shadows` + `premium fabrics (silk/tweed)`

### 2. Lighting Keywords
- **Golden Hour**: `golden hour lighting`, `warm glow`, `backlight`
- **Studio Glam**: `butterfly lighting` (for face), `Rembrandt lighting` (for mood), `softbox`
- **Cinematic**: `cinematic lighting`, `moody shadows`, `film grain`

### 3. Pose Keywords
- **Standing**: `S-curve pose`, `side profile`, `weight on one leg`, `looking back over shoulder`
- **Sitting**: `crossed legs`, `elegant sitting`, `leaning on armrest`, `holding coffee/champagne`
- **Hands**: `hand touching hair`, `hand on cheek`, `holding bag`

## How to Use
1. **Analyze User Request**: Identify the desired "Socialite Vibe" (e.g., Chill vs. Glitzy).
2. **Consult Docs**: Read the relevant markdown file in `docs/` if you need specific clothing items or makeup terms.
3. **Construct Prompt**: Combine [Quality] + [Subject/Outfit] + [Pose] + [Scene] + [Lighting] + [Style Keywords].
   - *Example*: `masterpiece, best quality, elegant French socialite, wearing silk blouse, sitting at cafe, holding coffee, soft natural lighting, shallow depth of field.`

## Updates
- Based on "OKComputer_未命名会话.zip" uploaded on 2026-02-14.
"""
with open(os.path.join(WORKSPACE, "SKILL.md"), "w", encoding="utf-8") as f:
    f.write(skill_md)

# ── docs/ – full reference files ─────────────────────────────────────────────
bible_md = """\
# Nano Banana Pro 名媛拍照指南 完整版

## 核心理念
名媛风格 = 精致感 × 场景感 × 光线感

## Prompt 构建公式（强制顺序）
[Quality Tags] + [Subject & Outfit] + [Pose] + [Scene/Background] + [Lighting] + [Style Keywords]

### Quality Tags（必须放最前）
- `masterpiece, best quality` — 适用于所有名媛风格
- `ultra-detailed` — 精致感风格必加

### 风格关键词详表
| 风格 | 英文标签 | 核心元素 |
|------|---------|---------|
| 松弛感 (Relaxed Chic) | `relaxed chic`, `effortless elegance` | 自然光, 柔和色调, 慵懒姿态 |
| 贵气感 (Expensive/Noble) | `old money aesthetic`, `haute couture` | 金色点缀, 奢华酒店, 珠宝首饰 |
| 精致感 (Refined Detail) | `refined elegance`, `magazine editorial` | 对称构图, 面料细节, 柔和阴影 |
| 法式优雅 (French Chic) | `French socialite`, `Parisian chic` | 丝绸上衣, 咖啡馆, 随意卷发 |
| 韩系名媛 (Korean Style) | `Korean chic`, `glass skin` | 清透妆容, 奶油色系, 精致配饰 |

## 场景搭配指南
- 松弛感 → 家居、咖啡馆、花园 (cozy cafe, home setting, garden)
- 贵气感 → 五星级酒店大堂、私人游艇、香槟晚宴 (luxury hotel lobby, private yacht)
- 精致感 → 艺术画廊、高级餐厅、精品店 (art gallery, fine dining restaurant)

## 重要提示
- 所有 prompt 必须以 `masterpiece, best quality` 开头
- 风格关键词放在 prompt 最后
- 避免使用模糊词如 "beautiful" 或 "nice"
"""
with open(os.path.join(WORKSPACE, "docs", "nanobanana_pro名媛拍照指南_完整版.md"), "w", encoding="utf-8") as f:
    f.write(bible_md)

styles_md = """\
# 风格定位与场景搭配

## 松弛感 (Relaxed Chic / 松弛感)
**核心感觉**: 不费力的优雅，慵懒而高级
**必用关键词**: `soft natural lighting`, `relaxed pose`, `pastel color palette`, `cozy cafe/home setting`
**服装**: linen shirt, loose trousers, ballet flats
**发型**: messy bun, loose waves
**配件**: minimalist jewelry, canvas tote

## 贵气感 (Expensive/Noble / 贵气感)  
**核心感觉**: 压迫性的精致，令人仰望的高贵
**必用关键词**: `golden accents`, `flawless makeup`, `luxury hotel lobby`, `elegant jewelry`
**服装**: tailored blazer, pencil skirt, pointed heels
**发型**: sleek updo, perfectly set waves
**配件**: statement pearl necklace, structured handbag

## 精致感 (Refined Detail / 精致感)
**核心感觉**: 精工细作，每个细节都完美
**必用关键词**: `symmetrical composition`, `detail-focused`, `soft shadows`, `premium fabrics (silk/tweed)`
**服装**: tweed jacket, silk slip dress, embroidered details
**发型**: polished blowout
**配件**: delicate gold jewelry, classic pumps

## 场景道具搭配速查
| 场景 | 道具 | 适合风格 |
|------|------|---------|
| 咖啡馆 | holding coffee | 松弛感, 法式优雅 |
| 酒店大堂 | holding champagne | 贵气感 |
| 画廊 | hand on cheek | 精致感 |
| 户外花园 | hand touching hair | 松弛感 |
"""
with open(os.path.join(WORKSPACE, "docs", "nanobanana_pro名媛拍照指南_风格定位与场景搭配.md"), "w", encoding="utf-8") as f:
    f.write(styles_md)

tech_md = """\
# 摄影技术篇

## 光线系统

### 黄金时刻 (Golden Hour)
- 关键词: `golden hour lighting`, `warm glow`, `backlight`
- 适用: 户外场景, 松弛感, 法式优雅
- 时间: 日出后1小时 / 日落前1小时

### 棚拍魅力 (Studio Glam)
- `butterfly lighting` — 专用于面部拍摄, 产生鼻下蝴蝶形阴影, 突出颧骨
- `Rembrandt lighting` — 制造戏剧性情绪光, 一侧脸有三角形光斑
- `softbox` — 柔和均匀的补光
- 适用: 贵气感, 精致感

### 电影感 (Cinematic)
- 关键词: `cinematic lighting`, `moody shadows`, `film grain`
- 适用: 高级感编辑, 艺术风格
- 注意: film grain 与 ultra-detailed 不可同时使用

## 构图技术
- 对称构图 (Symmetrical): 适合精致感 → 使用 `symmetrical composition`
- 黄金比例 (Rule of Thirds): 通用 → `rule of thirds`
- 浅景深 (Shallow DOF): 突出主体 → `shallow depth of field, bokeh background`

## 姿势技术指南

### 站姿
- S形曲线站姿: `S-curve pose` — 最显身材比例
- 侧身: `side profile` — 突出轮廓线条
- 重心偏移: `weight on one leg` — 自然放松感
- 回眸: `looking back over shoulder` — 神秘感

### 坐姿
- 交叉腿: `crossed legs` — 优雅正式
- 优雅坐姿: `elegant sitting` — 通用
- 倚靠扶手: `leaning on armrest` — 慵懒感
- 持物: `holding coffee/champagne` — 场景感

### 手部细节
- 触发: `hand touching hair` — 随性感
- 托腮: `hand on cheek` — 思考/优雅
- 持包: `holding bag` — 时尚感
"""
with open(os.path.join(WORKSPACE, "docs", "nanobanana_pro名媛拍照指南_摄影技术篇.md"), "w", encoding="utf-8") as f:
    f.write(tech_md)

beauty_md = """\
# 妆容造型指导

## 妆容风格对应
| 风格 | 妆容关键词 | 发型关键词 |
|------|-----------|-----------|
| 松弛感 | `natural makeup`, `dewy skin` | `loose waves`, `messy bun` |
| 贵气感 | `flawless makeup`, `bold lip` | `sleek updo`, `perfectly set waves` |
| 精致感 | `polished makeup`, `defined brows` | `polished blowout` |
| 法式优雅 | `French girl makeup`, `red lip` | `effortless waves` |
| 韩系名媛 | `glass skin`, `puppy eye makeup` | `straight silky hair` |

## 造型单品关键词
- 香水: 不在 prompt 中体现（视觉元素）
- 包袋: `structured handbag`, `canvas tote`, `quilted bag`
- 鞋履: `pointed heels`, `ballet flats`, `loafers`
- 珠宝: `statement pearl necklace`, `delicate gold jewelry`, `diamond earrings`

## 肤质表达
- 瓷肌: `porcelain skin`
- 水光肌: `dewy skin`, `glass skin`
- 哑光肌: `matte complexion`
"""
with open(os.path.join(WORKSPACE, "docs", "nanobanana_pro_妆容造型指导.md"), "w", encoding="utf-8") as f:
    f.write(beauty_md)

# ── Client Briefs (the messy inputs the agent must process) ──────────────────
client_briefs = {
    "briefs": [
        {
            "brief_id": "CB-2026-001",
            "client": "Lumière Collective",
            "shoot_title": "Sunday Morning at Home",
            "description": (
                "Client wants a relaxed, effortless vibe. Think Sunday morning, "
                "natural sunlight coming through linen curtains, the subject sipping something warm, "
                "totally at ease. Not too posed, not too glamorous — more like candid luxury. "
                "Subject should be in comfortable but elevated loungewear. "
                "Mood: 'I woke up like this but also I'm rich.'"
            ),
            "desired_output_format": "AI art generation prompt",
            "notes": "Client hates anything that looks 'try-hard' or 'overdone'."
        },
        {
            "brief_id": "CB-2026-002",
            "client": "Sovereign & Co.",
            "shoot_title": "Grand Hotel Gala",
            "description": (
                "This is for a luxury brand campaign. The look must be absolutely commanding — "
                "think old money, inherited wealth, someone who arrived by private jet. "
                "Setting: a grand hotel lobby with marble floors and gilded ceilings. "
                "Subject in a tailored pencil skirt and blazer, standing with full authority. "
                "Jewelry must be prominent. Face must look perfect, like a magazine cover."
            ),
            "desired_output_format": "AI art generation prompt",
            "notes": "The face lighting should create the most flattering, face-sculpting effect possible."
        },
        {
            "brief_id": "CB-2026-003",
            "client": "Maison Éclat",
            "shoot_title": "Tweed & Silk Editorial",
            "description": (
                "High-end editorial shoot focusing on fabric and craftsmanship. "
                "We want every stitch of the tweed jacket to be visible, every fold of the silk to catch light. "
                "Very structured, symmetrical framing. Setting is a high-end art gallery or boutique. "
                "Shadows should be soft, not dramatic. Subject sitting, looking refined."
            ),
            "desired_output_format": "AI art generation prompt",
            "notes": "This is about the clothes, not just the person. Detail is everything."
        }
    ]
}

with open(os.path.join(WORKSPACE, "clients/2026/Q1", "client_briefs_q1_2026.json"), "w", encoding="utf-8") as f:
    json.dump(client_briefs, f, indent=2, ensure_ascii=False)

# ── Distractor files ──────────────────────────────────────────────────────────
distractors = {
    "archive/old_briefs/brief_2025_sample.txt": (
        "Old brief from 2025 - DEPRECATED. Do not use these prompt formats.\n"
        "Old format: [subject] [location] [mood] — replaced by new formula in 2026."
    ),
    "archive/rejected/prompt_attempt_v1.txt": (
        "REJECTED by client:\n"
        "beautiful woman standing in hotel, nice lighting, pretty dress.\n"
        "Reason: Too vague, lacks technical specificity, no quality tags."
    ),
    "internal/brand_guidelines/lumiere_brand.txt": (
        "Lumière Collective Brand Guidelines\n"
        "Primary color: #F5F0E8 (warm cream)\n"
        "Secondary: #C9A96E (muted gold)\n"
        "Tone: Warm, approachable, aspirational\n"
        "DO NOT use harsh contrasts or dark moody tones for this client."
    ),
    "internal/brand_guidelines/sovereign_brand.txt": (
        "Sovereign & Co. Brand Guidelines\n"
        "Primary color: #1A1A2E (deep navy)\n"
        "Secondary: #B8960C (antique gold)\n"
        "Tone: Commanding, authoritative, timeless luxury\n"
        "Always convey power and exclusivity."
    ),
    "internal/templates/old_prompt_template.txt": (
        "OUTDATED TEMPLATE — DO NOT USE\n"
        "Template: 'high quality photo of [subject] in [location] with [lighting]'\n"
        "This template was retired in Q4 2025."
    ),
    "assets/moodboards/relaxed_inspo.txt": (
        "Moodboard references for relaxed shoots:\n"
        "- Kinfolk magazine editorial style\n"
        "- Scandinavian minimalism\n"
        "- Natural textures, linen, rattan\n"
        "NOTE: These are visual references only, not prompt keywords."
    ),
    "assets/references/competitor_prompts.txt": (
        "Competitor prompt samples (DO NOT COPY):\n"
        "- '4K photo, gorgeous model, dramatic lighting, luxurious background'\n"
        "- 'stunning woman, fashion shoot, bright lights'\n"
        "These are low-quality prompts our clients have complained about."
    ),
    "shoots/upcoming/schedule_q1.txt": (
        "Q1 2026 Shoot Schedule\n"
        "Jan 15 - CB-2026-001 (Lumière Collective)\n"
        "Feb 03 - CB-2026-002 (Sovereign & Co.)\n"
        "Feb 28 - CB-2026-003 (Maison Éclat)\n"
        "All shoots require AI prompt approval before execution date."
    ),
    "shoots/completed/q4_2025_summary.txt": (
        "Q4 2025 Completed Shoots Summary\n"
        "12 campaigns completed, 3 revisions requested.\n"
        "Main revision reason: incorrect lighting style for target vibe.\n"
        "Lesson learned: Always match lighting to style formula."
    ),
    "clients/2026/Q2/placeholder.txt": (
        "Q2 2026 briefs pending — to be added after Q1 review."
    ),
}

for path, content in distractors.items():
    full_path = os.path.join(WORKSPACE, path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

print("Workspace generated successfully.")
print(f"Files created in: {WORKSPACE}")