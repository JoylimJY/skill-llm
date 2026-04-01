import os
import shutil

# 目录配置
TRASH_DIR = "quarantine_multimodal_trash"
# 恢复阈值：命中次数 <= 3 的都将被捞回
RESTORE_LIMIT = 3

# 保持与之前相同的多模态特征词库
MULTIMODAL_KEYWORDS =[
    "audio", "speech", "voice ", "whisper", "text-to-speech", "speech-to-text",
    "transcribe", "mp3", "wav", "lyrics", "podcast", "elevenlabs",
    "video", "mp4", "ffmpeg", "youtube downloader", "video processing",
    "screenshot", "computer vision", "facial recognition", "text-to-image",
    "image generation", "image-to-text", "stable diffusion", "midjourney",
    "dall-e", "ocr", "pixel", "generate image", "process image", "picture", "photo",
    "visual representation", "bounding box"
]

def count_multimodal_triggers(skill_folder):
    """重新计算技能目录下的多模态关键词命中数"""
    skill_md_path = None
    for file in os.listdir(skill_folder):
        if file.lower() == 'skill.md':
            skill_md_path = os.path.join(skill_folder, file)
            break
            
    if not skill_md_path:
        return 999  # 如果连说明书都没了，返回一个大数字防止被恢复
        
    total_count = 0
    try:
        with open(skill_md_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read().lower()
            for kw in MULTIMODAL_KEYWORDS:
                total_count += content.count(kw)
    except Exception as e:
        print(f"无法读取文件 {skill_md_path}: {e}")
        return 999
        
    return total_count

def main():
    if not os.path.exists(TRASH_DIR):
        print(f"❌ 找不到垃圾桶目录: {TRASH_DIR}")
        return
        
    rescued_count = 0
    left_in_trash_count = 0
    
    print(f"🚑 开始拯救行动：将命中次数 <= {RESTORE_LIMIT} 的技能恢复原位...\n")

    # 遍历垃圾桶里的基础目录 (如 agent_skills, openclaw_skills)
    for base_dir in os.listdir(TRASH_DIR):
        base_trash_path = os.path.join(TRASH_DIR, base_dir)
        if not os.path.isdir(base_trash_path): continue
            
        # 遍历分类目录 (如 Ai And Llms)
        for category in os.listdir(base_trash_path):
            category_trash_path = os.path.join(base_trash_path, category)
            if not os.path.isdir(category_trash_path): continue
                
            # 遍历具体的技能目录
            for skill_name in os.listdir(category_trash_path):
                skill_trash_path = os.path.join(category_trash_path, skill_name)
                if not os.path.isdir(skill_trash_path): continue
                    
                # 重新计算命中次数
                hits = count_multimodal_triggers(skill_trash_path)
                
                if hits <= RESTORE_LIMIT:
                    # 达到恢复标准，计算原路径
                    original_category_dir = os.path.join(base_dir, category)
                    os.makedirs(original_category_dir, exist_ok=True)
                    original_dest = os.path.join(original_category_dir, skill_name)
                    
                    try:
                        shutil.move(skill_trash_path, original_dest)
                        print(f"✅ [捞回] {skill_name} (仅命中 {hits} 次)")
                        rescued_count += 1
                    except Exception as e:
                        print(f"⚠️ 恢复 {skill_name} 时出错: {e}")
                else:
                    # 依然是危险分子，留在垃圾桶
                    left_in_trash_count += 1

    print("\n" + "="*50)
    print(f"🎉 拯救行动完成！(Threshold: <= {RESTORE_LIMIT})")
    print("="*50)
    print(f"✅ 成功捞回误杀技能: {rescued_count} 个")
    print(f"🗑️ 继续留在隔离区 (真正的多模态): {left_in_trash_count} 个")
    print("="*50)

if __name__ == "__main__":
    main()