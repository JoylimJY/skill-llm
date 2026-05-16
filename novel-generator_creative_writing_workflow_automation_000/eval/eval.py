import sys
import json
import os
import re
from pathlib import Path

workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
ws = Path(workspace)

checks = []

def check(name, condition, detail):
    checks.append({"name": name, "passed": bool(condition), "detail": detail})
    return bool(condition)


# ─────────────────────────────────────────────────────────────────────────────
# CHECK 1: output/提示词.md exists and contains all 8 required dimensions
# ─────────────────────────────────────────────────────────────────────────────
prompt_file = ws / "output" / "提示词.md"
try:
    prompt_content = prompt_file.read_text(encoding="utf-8")
    required_dims = ["题材", "世界观", "主角", "冲突", "爽点", "节奏", "配角", "开篇"]
    found_dims = [d for d in required_dims if d in prompt_content]
    c1 = check(
        "提示词.md: 包含8个自动补全维度关键词",
        len(found_dims) >= 6,
        f"找到维度关键词: {found_dims} ({len(found_dims)}/8)"
    )
    # Check that protagonist name 陈晨 is mentioned
    c1b = check(
        "提示词.md: 包含主角陈晨和系统核心设定",
        "陈晨" in prompt_content and ("系统" in prompt_content or "鉴定" in prompt_content),
        f"陈晨存在: {'陈晨' in prompt_content}, 系统设定存在: {'系统' in prompt_content or '鉴定' in prompt_content}"
    )
    # Check quality checklist items
    has_underdog = any(kw in prompt_content for kw in ["逆袭", "废柴", "起点", "惨"])
    c1c = check(
        "提示词.md: 包含逆袭起点设定（主角足够惨）",
        has_underdog,
        f"逆袭相关关键词存在: {has_underdog}"
    )
except Exception as e:
    check("提示词.md: 文件存在且可读", False, f"错误: {e}")
    check("提示词.md: 包含主角陈晨和系统核心设定", False, "文件不存在")
    check("提示词.md: 包含逆袭起点设定", False, "文件不存在")


# ─────────────────────────────────────────────────────────────────────────────
# CHECK 2: output/大纲.md exists with required structural sections
# ─────────────────────────────────────────────────────────────────────────────
outline_file = ws / "output" / "大纲.md"
try:
    outline_content = outline_file.read_text(encoding="utf-8")
    required_sections = ["基本信息", "力量", "主线", "关键转折"]
    found_sections = [s for s in required_sections if s in outline_content]
    check(
        "大纲.md: 包含必需的结构化章节",
        len(found_sections) >= 3,
        f"找到章节: {found_sections} ({len(found_sections)}/4)"
    )
    # Check for volume/arc planning (第一卷 or 第一章 patterns)
    has_volume = bool(re.search(r'第[一二三]卷|第1-\d+章|第\d+-\d+章', outline_content))
    check(
        "大纲.md: 包含卷章规划（卷名和章节范围）",
        has_volume,
        f"卷章规划存在: {has_volume}"
    )
    # Check 20+ chapter planning
    chapter_nums = re.findall(r'第(\d+)章', outline_content)
    max_ch = max([int(n) for n in chapter_nums], default=0)
    check(
        "大纲.md: 规划达到20章以上",
        max_ch >= 15,
        f"检测到最大章节号: {max_ch}"
    )
except Exception as e:
    check("大纲.md: 文件存在且可读", False, f"错误: {e}")
    check("大纲.md: 包含卷章规划", False, "文件不存在")
    check("大纲.md: 规划达到20章以上", False, "文件不存在")


# ─────────────────────────────────────────────────────────────────────────────
# CHECK 3: Chapter files — naming convention with two-digit zero-padding
# ─────────────────────────────────────────────────────────────────────────────
output_dir = ws / "output"
chapter_files = list(output_dir.glob("第0*.md")) + list(output_dir.glob("第1*.md"))
# Filter to actual chapter files (not 大纲/提示词)
chapter_files = [f for f in chapter_files if re.match(r'第\d{2}章', f.name)]

check(
    "output/: 存在至少2个正确命名的章节文件（第XX章格式）",
    len(chapter_files) >= 2,
    f"找到章节文件: {[f.name for f in chapter_files]}"
)

# Check naming uses underscore separator: 第XX章_章名.md
correctly_named = [f for f in chapter_files if re.match(r'第\d{2}章_.+\.md$', f.name)]
check(
    "章节文件: 使用正确命名格式 第XX章_章名.md（含下划线和章名）",
    len(correctly_named) >= 2,
    f"格式正确的文件: {[f.name for f in correctly_named]}"
)


# ─────────────────────────────────────────────────────────────────────────────
# CHECK 4: Chapter content — mandatory blockquote template fields
# ─────────────────────────────────────────────────────────────────────────────
if chapter_files:
    first_chapter = sorted(chapter_files)[0]
    try:
        ch1_content = first_chapter.read_text(encoding="utf-8")
        required_fields = ["本章概要", "本章爽点", "情绪曲线", "章末钩子"]
        found_fields = [f for f in required_fields if f in ch1_content]
        check(
            "第一章: 包含全部必需的模板字段（概要/爽点/情绪曲线/章末钩子）",
            len(found_fields) >= 4,
            f"找到字段: {found_fields} ({len(found_fields)}/4)"
        )
        # Check actual prose content length (should be 2000+ chars for chapter body)
        # Remove headers/metadata to estimate body length
        body_lines = [l for l in ch1_content.split('\n') if not l.startswith('>') and not l.startswith('#') and l.strip()]
        body_text = ' '.join(body_lines)
        check(
            "第一章: 正文字数充足（去除模板后正文达到合理长度）",
            len(body_text) >= 500,
            f"正文估算字符数: {len(body_text)}"
        )
    except Exception as e:
        check("第一章: 模板字段检查", False, f"错误: {e}")
        check("第一章: 正文字数检查", False, f"错误: {e}")
else:
    check("第一章: 模板字段检查", False, "无章节文件可检查")
    check("第一章: 正文字数检查", False, "无章节文件可检查")


# ─────────────────────────────────────────────────────────────────────────────
# CHECK 5: .learnings/CHARACTERS.md — populated with actual characters
# ─────────────────────────────────────────────────────────────────────────────
characters_file = ws / ".learnings" / "CHARACTERS.md"
try:
    chars_content = characters_file.read_text(encoding="utf-8")
    # Must contain at least 陈晨 (protagonist) and one other character
    has_protagonist = "陈晨" in chars_content
    has_antagonist = "张浩" in chars_content or "苏璃" in chars_content
    # Must have more content than the stub (stub is ~50 chars)
    is_populated = len(chars_content.strip()) > 100
    check(
        ".learnings/CHARACTERS.md: 已记录主角陈晨和至少一名配角",
        has_protagonist and has_antagonist and is_populated,
        f"包含陈晨: {has_protagonist}, 包含张浩/苏璃: {has_antagonist}, 内容长度: {len(chars_content)}"
    )
except Exception as e:
    check(".learnings/CHARACTERS.md: 角色记录检查", False, f"错误: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# CHECK 6: .learnings/PLOT_POINTS.md — populated with key plot events
# ─────────────────────────────────────────────────────────────────────────────
plot_file = ws / ".learnings" / "PLOT_POINTS.md"
try:
    plot_content = plot_file.read_text(encoding="utf-8")
    is_populated = len(plot_content.strip()) > 100
    # Should mention system acquisition as first key plot point
    has_system_event = any(kw in plot_content for kw in ["系统", "鉴定", "获得", "逐出", "青云宗"])
    check(
        ".learnings/PLOT_POINTS.md: 已记录关键情节（含系统获得等核心事件）",
        is_populated and has_system_event,
        f"已填充: {is_populated}, 含核心事件: {has_system_event}, 内容长度: {len(plot_content)}"
    )
except Exception as e:
    check(".learnings/PLOT_POINTS.md: 情节记录检查", False, f"错误: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# CHECK 7: 人物关系图.md — Mermaid diagram with correct syntax
# ─────────────────────────────────────────────────────────────────────────────
relation_files = list((ws / "output").glob("人物关系图*.md"))
try:
    if not relation_files:
        raise FileNotFoundError("人物关系图.md not found")
    rel_file = relation_files[0]
    rel_content = rel_file.read_text(encoding="utf-8")
    # Must contain a mermaid code block
    has_mermaid_block = "```mermaid" in rel_content
    # Must use graph TD or graph LR (directed graph)
    has_graph_directive = bool(re.search(r'graph\s+(TD|LR|TB|RL)', rel_content))
    # Must contain protagonist 陈晨
    has_protagonist = "陈晨" in rel_content
    # Must have at least 2 relationship arrows (-->)
    arrow_count = rel_content.count("-->")
    check(
        "人物关系图.md: 包含有效的Mermaid代码块（graph TD语法）",
        has_mermaid_block and has_graph_directive,
        f"mermaid块: {has_mermaid_block}, graph指令: {has_graph_directive}"
    )
    check(
        "人物关系图.md: 关系图包含主角陈晨且有≥2个关系箭头",
        has_protagonist and arrow_count >= 2,
        f"陈晨存在: {has_protagonist}, 箭头数量: {arrow_count}"
    )
except FileNotFoundError:
    check("人物关系图.md: 文件存在", False, "文件未找到")
    check("人物关系图.md: 图表内容完整", False, "文件未找到")
except Exception as e:
    check("人物关系图.md: Mermaid语法检查", False, f"错误: {e}")
    check("人物关系图.md: 关系图内容检查", False, f"错误: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# CHECK 8: .learnings/LOCATIONS.md — populated
# ─────────────────────────────────────────────────────────────────────────────
locations_file = ws / ".learnings" / "LOCATIONS.md"
try:
    loc_content = locations_file.read_text(encoding="utf-8")
    is_populated = len(loc_content.strip()) > 100
    has_sect = any(kw in loc_content for kw in ["青云宗", "宗门", "山门", "灵峰"])
    check(
        ".learnings/LOCATIONS.md: 已记录青云宗等出现的地点",
        is_populated and has_sect,
        f"已填充: {is_populated}, 含宗门地点: {has_sect}, 内容长度: {len(loc_content)}"
    )
except Exception as e:
    check(".learnings/LOCATIONS.md: 地点记录检查", False, f"错误: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# FINAL SCORING
# ─────────────────────────────────────────────────────────────────────────────
total = len(checks)
passed_count = sum(1 for c in checks if c["passed"])
score = round(passed_count / total, 3)

output = {
    "passed": passed_count >= int(total * 0.75),
    "score": score,
    "checks": checks
}

print(json.dumps(output, ensure_ascii=False, indent=2))