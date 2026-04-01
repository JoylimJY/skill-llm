import os
import re
from collections import Counter

# 目录配置
TARGET_DIRS = ["damaged_agent_skills", "damaged_openclaw_skills"]
REPORT_FILE = "skill_quality_scores.csv"

# 打分权重配置 (总分 100)
# 1. 说明书字数 (Max 30): 字数越多通常代表参数和逻辑越复杂
# 2. 物理代码文件 (Max 30): 包含脚本文件代表是真实工具
# 3. 工具多样性 (Max 20): SKILL.md 中定义的 tool 数量
# 4. 环境规范性 (Max 10): 是否包含 requirements.txt/package.json
# 5. 示例丰富度 (Max 10): 是否包含 'example' 或 'usage' 关键词

def calculate_score(skill_path):
    score = 0
    skill_md_path = None
    script_files = []
    env_files = []
    
    for root, dirs, files in os.walk(skill_path):
        for file in files:
            if file.lower() == 'skill.md':
                skill_md_path = os.path.join(root, file)
            if file.endswith(('.py', '.js', '.sh', '.ts', '.go')):
                script_files.append(file)
            if file in ['requirements.txt', 'package.json', 'Dockerfile', 'Makefile']:
                env_files.append(file)

    if not skill_md_path:
        return 0

    # --- 1. 说明书长度打分 (Max 30) ---
    try:
        with open(skill_md_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            char_count = len(content)
            if char_count > 2000: score += 30
            elif char_count > 1000: score += 20
            elif char_count > 500: score += 10
            elif char_count > 200: score += 5
            
            # --- 3. 工具数量打分 (Max 20) ---
            # 搜索 yaml 中的 '- name:' 数量或 'tools:' 后的列表项
            tool_matches = re.findall(r'-\s*name:', content)
            tool_count = len(tool_matches)
            if tool_count >= 3: score += 20
            elif tool_count >= 1: score += 10
            
            # --- 5. 示例丰富度 (Max 10) ---
            if 'example' in content.lower() or 'usage' in content.lower():
                score += 10
    except:
        pass

    # --- 2. 物理代码文件 (Max 30) ---
    if len(script_files) >= 2: score += 30
    elif len(script_files) == 1: score += 15

    # --- 4. 环境规范性 (Max 10) ---
    if len(env_files) >= 1: score += 10

    return score

def main():
    scores = []
    skill_data = []

    print("📊 正在启动 AI 教材质量评估系统 (Scoring Skills)...")

    for base_dir in TARGET_DIRS:
        if not os.path.exists(base_dir): continue
        for category in os.listdir(base_dir):
            cat_path = os.path.join(base_dir, category)
            if not os.path.isdir(cat_path): continue
            for skill_name in os.listdir(cat_path):
                skill_path = os.path.join(cat_path, skill_name)
                if not os.path.isdir(skill_path): continue
                
                s = calculate_score(skill_path)
                scores.append(s)
                skill_data.append((skill_name, s, f"{base_dir}/{category}"))

    # 按分数降序保存到 CSV 供你后续筛选
    skill_data.sort(key=lambda x: x[1], reverse=True)
    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        f.write("Skill_Name,Score,Path\n")
        for name, s, p in skill_data:
            f.write(f"{name},{s},{p}\n")

    # 统计分布
    distribution = Counter()
    for s in scores:
        # 将分数映射到 1-10, 11-20 ... 91-100
        if s == 0: bin_range = "0 (Invalid)"
        else:
            lower = ((s - 1) // 10) * 10 + 1
            upper = lower + 9
            bin_range = f"{lower:2d}-{upper:3d}"
        distribution[bin_range] += 1

    # 打印分布报告
    print("\n" + "="*50)
    print("📈 技能质量得分分布报告 (Quality Score Distribution)")
    print("="*50)
    print(f"扫描技能总数: {len(scores)} 个\n")

    # 按区间顺序排序
    ranges = [f"{i*10+1:2d}-{i*10+10:3d}" for i in range(10)]
    for r in ranges:
        count = distribution[r]
        pct = (count / len(scores)) * 100 if len(scores) > 0 else 0
        bar = "█" * int(pct / 2)
        print(f" {r} 分区: {count:4d} 个 ({pct:5.1f}%) {bar}")

    print("\n" + "="*50)
    print(f"✅ 详细评分已保存至: {REPORT_FILE}")
    print("💡 建议：优先选择 81-100 分区的技能进行 SFT 轨迹合成。")
    print("="*50)

if __name__ == "__main__":
    main()