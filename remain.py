import os

# 基础目录
TARGET_DIRS = ["agent_skills", "openclaw_skills"]

def main():
    total_skills = 0
    inventory = {}

    for base_dir in TARGET_DIRS:
        if not os.path.exists(base_dir):
            continue
            
        inventory[base_dir] = {"total": 0, "categories": {}}
        
        # 遍历分类目录
        for category in os.listdir(base_dir):
            category_path = os.path.join(base_dir, category)
            if not os.path.isdir(category_path): 
                continue
                
            skill_count = 0
            # 遍历具体的技能目录
            for skill_name in os.listdir(category_path):
                skill_path = os.path.join(category_path, skill_name)
                if os.path.isdir(skill_path):
                    skill_count += 1
            
            if skill_count > 0:
                inventory[base_dir]["categories"][category] = skill_count
                inventory[base_dir]["total"] += skill_count
                total_skills += skill_count

    # 打印统计报告
    print("\n" + "="*50)
    print("📊 当前保留技能盘点报告 (Remaining Skills Inventory)")
    print("="*50)
    print(f"🔥 总计可用技能: {total_skills} 个\n")

    for base_dir, data in inventory.items():
        print(f"📂 【{base_dir}】: 共 {data['total']} 个")
        
        # 按数量降序排序分类
        sorted_categories = sorted(data["categories"].items(), key=lambda x: x[1], reverse=True)
        
        for category, count in sorted_categories:
            # 计算该分类占该大库的百分比
            pct = (count / data['total']) * 100 if data['total'] > 0 else 0
            print(f"   ├── {category}: {count} 个 ({pct:.1f}%)")
        print()
        
    print("="*50)

if __name__ == "__main__":
    main()