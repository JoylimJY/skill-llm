import os
import shutil

# 基础目录
TARGET_DIRS =["agent_skills", "openclaw_skills"]
TRASH_DIR = "quarantine_multimodal_trash"
REVIEW_LOG_FILE = os.path.join(TRASH_DIR, "multimodal_review_log.txt")

# 多模态特征词库 (全部小写)
MULTIMODAL_KEYWORDS =[
    # 🎵 音频/语音类
    "audio", "speech", "voice ", "whisper", "text-to-speech", "speech-to-text",
    "transcribe", "mp3", "wav", "lyrics", "podcast", "elevenlabs",
    # 🎬 视频类
    "video", "mp4", "ffmpeg", "youtube downloader", "video processing",
    # 🖼️ 图像/视觉类 (避开 "image" 单词以防误伤 Docker image)
    "screenshot", "computer vision", "facial recognition", "text-to-image",
    "image generation", "image-to-text", "stable diffusion", "midjourney",
    "dall-e", "ocr", "pixel", "generate image", "process image", "picture", "photo",
    "visual representation", "bounding box"
]

def count_multimodal_triggers(skill_folder):
    """读取 SKILL.md，统计所有多模态关键词出现的次数"""
    skill_md_path = None
    for file in os.listdir(skill_folder):
        if file.lower() == 'skill.md':
            skill_md_path = os.path.join(skill_folder, file)
            break
            
    if not skill_md_path:
        return 0, {}
        
    trigger_details = {}
    total_count = 0
    
    try:
        with open(skill_md_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read().lower()
            # 统计每个特征词的出现次数
            for kw in MULTIMODAL_KEYWORDS:
                count = content.count(kw)
                if count > 0:
                    trigger_details[kw] = count
                    total_count += count
    except Exception as e:
        print(f"无法读取文件 {skill_md_path}: {e}")
        
    return total_count, trigger_details

def main():
    if not os.path.exists(TRASH_DIR):
        os.makedirs(TRASH_DIR)
        
    total_scanned = 0
    kept_skills = 0
    moved_to_trash = 0
    
    print("🚀 开始第二步扫描：剔除多模态技能并生成复核清单...\n")

    # 打开日志文件准备记录
    with open(REVIEW_LOG_FILE, 'w', encoding='utf-8') as log_file:
        log_file.write("=== 多模态技能复核清单 (Multimodal Review Log) ===\n")
        log_file.write("注意：重点排查 '总命中数 = 1' 的技能，可能是误杀。\n\n")
        
        for base_dir in TARGET_DIRS:
            if not os.path.exists(base_dir):
                continue
                
            for category in os.listdir(base_dir):
                category_path = os.path.join(base_dir, category)
                if not os.path.isdir(category_path): continue
                    
                for skill_name in os.listdir(category_path):
                    skill_path = os.path.join(category_path, skill_name)
                    if not os.path.isdir(skill_path): continue
                        
                    total_scanned += 1
                    
                    # 统计命中情况
                    total_hits, details = count_multimodal_triggers(skill_path)
                    
                    if total_hits > 0:
                        # 移动到多模态垃圾桶
                        trash_category_dir = os.path.join(TRASH_DIR, base_dir, category)
                        os.makedirs(trash_category_dir, exist_ok=True)
                        trash_dest = os.path.join(trash_category_dir, skill_name)
                        
                        try:
                            shutil.move(skill_path, trash_dest)
                            print(f"👁️[移至隔离区] {skill_name} (命中 {total_hits} 次)")
                            moved_to_trash += 1
                            
                            # 写入复核日志
                            details_str = ", ".join([f"'{k}': {v}次" for k, v in details.items()])
                            log_line = f"技能: {skill_name}\n路径: {base_dir}/{category}\n总命中数: {total_hits}  |  详细词频: {details_str}\n{'-'*50}\n"
                            log_file.write(log_line)
                            
                        except Exception as e:
                            print(f"⚠️ 移动 {skill_name} 时出错: {e}")
                    else:
                        kept_skills += 1

    print("\n" + "="*50)
    print("📊 第二步扫描统计报告")
    print("="*50)
    print(f"📂 总计复查技能: {total_scanned} 个")
    print(f"✅ 合格保留 (纯文本技能): {kept_skills} 个")
    print(f"🗑️ 隔离移除 (多模态技能): {moved_to_trash} 个")
    print(f"📍 请查看复核清单: ./{REVIEW_LOG_FILE}")
    print("="*50)

if __name__ == "__main__":
    main()