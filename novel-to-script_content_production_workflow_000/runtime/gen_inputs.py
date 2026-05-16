import os
import random

random.seed(42)

# Create a realistic project directory structure
base = "/workspace"

dirs = [
    "projects/凌云传/novels",
    "projects/凌云传/assets/covers",
    "projects/凌云传/assets/bgm",
    "projects/凌云传/production/storyboard",
    "projects/凌云传/production/voiceover",
    "projects/凌云传/drafts",
    "projects/凌云传/references",
    "projects/other_ips/斗破苍穹",
    "projects/other_ips/完美世界",
    "tools/converters",
    "archive/2023",
]

for d in dirs:
    os.makedirs(os.path.join(base, d), exist_ok=True)

# Distractor files
distractor_files = {
    "projects/凌云传/assets/covers/cover_v1.jpg.placeholder": "封面图占位符",
    "projects/凌云传/assets/bgm/battle_theme.mp3.placeholder": "战斗BGM占位符",
    "projects/凌云传/production/storyboard/episode01_rough.txt": "分镜草稿（未完成）\n第一集分镜待定...",
    "projects/凌云传/production/voiceover/casting_notes.txt": "配音演员候选\n主角：待定\n反派：张三",
    "projects/凌云传/drafts/outline_v1.txt": "大纲草稿v1\n第一集：相遇\n第二集：危机\n第三集：反转",
    "projects/凌云传/drafts/outline_v2.txt": "大纲草稿v2（已废弃）\n重新规划中...",
    "projects/凌云传/references/market_research.txt": "市场调研报告\n竖屏短剧月活用户：2亿\n主流时长：3-5分钟/集",
    "projects/other_ips/斗破苍穹/notes.txt": "斗破苍穹改编笔记",
    "projects/other_ips/完美世界/notes.txt": "完美世界改编笔记",
    "tools/converters/legacy_converter.py": "# 旧版转换工具（已弃用）\nprint('deprecated')",
    "archive/2023/old_script_template.txt": "旧版剧本模板（2023年格式，已过期）\n场次：\n人物：\n对白：",
    "projects/凌云传/production/episode_schedule.csv": "集数,主题,状态\n第一集,觉醒,待制作\n第二集,对决,待制作",
}

for path, content in distractor_files.items():
    full_path = os.path.join(base, path)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

# THE MAIN INPUT: The novel file the agent must process
novel_content = """《凌云传》第一章：废材觉醒

时间：午后，烈日当空。
地点：云宗门派大院

    云霄，云宗最年轻的弟子，也是宗门公认的废材。十六岁了，灵根等级仅为一阶，连宗门里最小的孩子都不如。

    这天，云霄像往常一样在柴房劈柴，汗水湿透了他破旧的麻布衣衫。

    "废材，给我滚开！"

    师兄李傲从外面大步走来，身后跟着三四个弟子，个个趾高气扬。李傲是云宗天才弟子，三阶灵根，深受长老们器重。

    他一把将云霄推开，云霄踉跄着撞在柴堆上，木柴哗啦啦散落一地。

    云霄咬紧牙关，没有反驳。他知道反驳没用。

    他心想：总有一天，我会让你们知道，瞧不起我是什么感受。

    就在这时，云霄胸口忽然一阵剧烈的灼烧感，像有什么东西在他体内破壳而出。

    "这是……"

    他低头，只见胸口衣衫下透出一缕金色的光芒。

    【叮！宿主隐藏灵根觉醒——混沌灵根，万法归一，天地第一灵根。系统绑定完成。】

    云霄愣在原地，脑海中浮现出一个声音，冷静而清晰。

    李傲回头，正好看见那缕金光一闪而逝。他眯起眼睛，走近两步。

    "你刚才那是什么？"

    云霄抬起头，眼中第一次出现了一丝异样的神采。他慢慢站起身，拍了拍身上的灰尘。

    "没什么，"他平静地说，"只是……以后的事，还说不准。"

    李傲冷哼一声，转身离去，留下一句话：

    "废材就是废材，三天后的考核，你等着被驱逐出门。"

    云霄看着他们离去的背影，嘴角微微上扬。

    三天后的考核——他倒要看看，到底是谁被驱逐出门。

    夜里，云霄独自坐在柴房，月光透过破旧的窗棂洒进来。

    他在脑海中与系统沟通，了解自己的混沌灵根。系统告诉他：混沌灵根能吸收任何属性的灵气，且转化效率是普通灵根的百倍。这意味着他过去十六年的"废材"，只是因为普通的修炼法门根本无法激活这种特殊灵根。

    云霄想起了父亲。

    【闪回】

    三年前，父亲云天在一次外出任务中失踪，宗门的人说他叛逃了，但云霄从不相信。父亲临走前握着他的手说："霄儿，无论发生什么，记住——忍，是为了更好的爆发。"

    【闪回结束】

    云霄握紧了拳头。

    三天后的考核，就是他的起点。
"""

novel_path = os.path.join(base, "projects/凌云传/novels/凌云传.txt")
with open(novel_path, "w", encoding="utf-8") as f:
    f.write(novel_content)

print("Workspace generated successfully.")
print(f"Novel file: {novel_path}")
print(f"Total distractor files: {len(distractor_files)}")