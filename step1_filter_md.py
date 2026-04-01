import os
import shutil

# 配置你需要扫描的基础目录
TARGET_DIRS =["agent_skills", "openclaw_skills"]
TRASH_DIR = "quarantine_trash"

def check_skill_md_exists(skill_folder):
    """检查文件夹内是否包含 SKILL.md (忽略大小写)"""
    try:
        # 遍历技能文件夹下的所有文件
        for file in os.listdir(skill_folder):
            if file.lower() == 'skill.md':
                return True
    except Exception as e:
        print(f"无法读取目录 {skill_folder}: {e}")
    return False

def main():
    # 确保隔离垃圾桶目录存在
    if not os.path.exists(TRASH_DIR):
        os.makedirs(TRASH_DIR)
        
    total_scanned = 0
    kept_skills = 0
    moved_to_trash = 0
    
    print("🚀 开始第一步扫描：仅检查 SKILL.md 的存在性...\n")

    for base_dir in TARGET_DIRS:
        if not os.path.exists(base_dir):
            print(f"⚠️ 找不到基础目录: {base_dir}，跳过。")
            continue
            
        # 第一层：组织/分类目录 (例如 tinybirdco, Ai And Llms)
        for category in os.listdir(base_dir):
            category_path = os.path.join(base_dir, category)
            
            # 跳过非文件夹（比如 .DS_Store 等隐藏文件）
            if not os.path.isdir(category_path):
                continue
                
            # 第二层：具体的技能目录 (例如 tinybird-best-practices)
            for skill_name in os.listdir(category_path):
                skill_path = os.path.join(category_path, skill_name)
                
                if not os.path.isdir(skill_path):
                    continue
                    
                total_scanned += 1
                
                # 核心逻辑：检查 SKILL.md
                if check_skill_md_exists(skill_path):
                    kept_skills += 1
                else:
                    # 如果没有，移动到隔离垃圾桶
                    # 为了防止重名冲突，在垃圾桶里保持原有目录结构
                    trash_category_dir = os.path.join(TRASH_DIR, base_dir, category)
                    os.makedirs(trash_category_dir, exist_ok=True)
                    
                    trash_dest = os.path.join(trash_category_dir, skill_name)
                    
                    try:
                        shutil.move(skill_path, trash_dest)
                        print(f"❌ [缺失 SKILL.md] 已隔离: {base_dir}/{category}/{skill_name}")
                        moved_to_trash += 1
                    except Exception as e:
                        print(f"⚠️ 移动 {skill_name} 时出错: {e}")

    # 打印最终统计信息
    print("\n" + "="*45)
    print("📊 第一步扫描统计报告 (Step 1 Report)")
    print("="*45)
    print(f"📂 总计扫描技能: {total_scanned} 个")
    print(f"✅ 合格保留 (含说明书): {kept_skills} 个")
    print(f"🗑️ 隔离移除 (无说明书): {moved_to_trash} 个")
    print(f"📍 隔离区路径: ./{TRASH_DIR}/")
    print("="*45)

if __name__ == "__main__":
    main()