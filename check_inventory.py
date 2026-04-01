import os

# 定义你想要查看的三个具体“抽屉”
# 脚本会智能检查是 openclaw_skill 还是 openclaw_skills
TARGET_BUCKETS = {
    "Elite Agent": "agent_skills",
    "Elite OpenClaw": "openclaw_skill", # 如果你文件夹叫 openclaw_skills，脚本会自动修正
    "API Pending": "api_pending_skills"
}

def count_valid_skills(folder_path):
    """只统计指定目录下包含 SKILL.md 的文件夹数量"""
    if not os.path.exists(folder_path):
        return 0
    
    count = 0
    # 遍历该目录下的分类目录 (如 Coding, microsoft 等)
    try:
        for category in os.listdir(folder_path):
            cat_path = os.path.join(folder_path, category)
            if not os.path.isdir(cat_path): continue
            
            # 遍历分类下的具体技能
            for skill in os.listdir(cat_path):
                skill_path = os.path.join(cat_path, skill)
                if not os.path.isdir(skill_path): continue
                
                # 检查 SKILL.md 是否存在
                files = [f.lower() for f in os.listdir(skill_path)]
                if 'skill.md' in files:
                    count += 1
    except Exception:
        pass
    return count

def main():
    print("\n" + "="*55)
    print("🎯  Skill-LLM 核心三库资产清点 (严格限定范围)")
    print("="*55)

    grand_total = 0
    results = []

    for label, folder_name in TARGET_BUCKETS.items():
        # 自动兼容单复数拼写
        if not os.path.exists(folder_name):
            alt_name = folder_name + "s" if not folder_name.endswith("s") else folder_name[:-1]
            if os.path.exists(alt_name):
                folder_name = alt_name
        
        count = 0
        if os.path.exists(folder_name):
            # 针对 API Pending 的特殊处理（它内部还有一层子目录）
            if label == "API Pending":
                # 统计内部的 agent_skills 和 openclaw_skills
                for sub in os.listdir(folder_name):
                    sub_path = os.path.join(folder_name, sub)
                    if os.path.isdir(sub_path):
                        count += count_valid_skills(sub_path)
            else:
                # 正常的两层结构
                count = count_valid_skills(folder_name)
        
        grand_total += count
        results.append((label, folder_name, count))

    # 打印结果
    for label, path, num in results:
        status = "✅" if num > 0 else "❌ (空或路径错)"
        print(f"📦 【{label}】")
        print(f"   路径: ./{path:<20} 状态: {status}")
        print(f"   统计: {num} 个有效技能")
        print("-" * 45)

    print(f"\n🔥 核心三库总计: {grand_total} 个精选技能")
    print("="*55)
    print("注：该脚本已排除了底库、垃圾桶及其他无关文件夹。")

if __name__ == "__main__":
    main()