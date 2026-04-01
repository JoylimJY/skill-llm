import os
import shutil

# 配置
AGENT_ROOT = "agent_skills"
OPENCLAW_ROOT = "openclaw_skill" 
TRASH_DIR = "quarantine_low_priority"

# 1. Agent Skills 垃圾档 (基于作者/组织名)
AGENT_TRASH_LIST = [
    # --- 原有的 ---
    "coreyhaines31", "deanpeters", "garrytan", "typefully", 
    "Shpigford", "phuryn", "fal-ai-community", "replicate",
    
    # --- 新追加的：视觉/动画类 (纯文本模型无法评估) ---
    "greensock",       # GSAP 动画库。模型看不见动画效果，无法 eval。
    "remotion-dev",    # 用代码写视频。属于多模态，直接砍掉。
    "figma",           # 设计工具。强视觉依赖，文本模型无法操作。
    "efremidze",       # 大多是 iOS UI 动画库（如 VisualEffectView）。
    
    # --- 新追加的：移动端/架构不匹配 (Linux Docker 跑不通) ---
    "expo",            # React Native 框架。需要真机或模拟器，Docker 极难跑通。
    "callstackincubator", # 也是 React Native 相关的移动端开发工具。
    
    # --- 新追加的：软技能/纯话术/SaaS 依赖 ---
    "muratcankoylan",  # 主要是 GPT 角色扮演和 Prompt 技巧，无硬核代码。
    "makenotion",      # 强依赖 Notion OAuth 认证和 SaaS 环境。
    "sanjay3290",      # 经查大多是通用的 Prompt 指南。
    "pawełhuryn",      # 产品管理 (PM) 技能，只有文档建议。
    "gokapso"          # 营销与 AI 话术类。
]

# 2. OpenClaw 垃圾档 (完整 1星 & 2星 & 多模态 & iOS)
OPENCLAW_TRASH_LIST = [
    # --- 1星 & 多模态 (文本模型无法处理) ---
    "Image And Video Generation", 
    "Speech And Transcription",
    "Media And Streaming",
    "Apple Apps And Services",
    "Smart Home And Iot",
    "Transportation",
    "Shopping And E Commerce",
    "Personal Development",
    "Marketing And Sales",
    "Calendar And Scheduling",
    
    # --- 2星 & 低价值 (需OAuth/主观/冷门) ---
    "Communication",
    "Gaming",
    "Health And Fitness",
    "Notes And Pkm",
    "Productivity And Tasks",
    "Moltbook",
    "Social Media",
    
    # --- 架构不兼容 ---
    "Ios And Macos Development"
]

def main():
    if not os.path.exists(TRASH_DIR):
        os.makedirs(TRASH_DIR)
    
    moved_count = 0

    print("🚀 启动修正版最终筛选 (Text-Only Focused)...")

    # --- 处理 Agent Skills ---
    if os.path.exists(AGENT_ROOT):
        trash_agent_path = os.path.join(TRASH_DIR, AGENT_ROOT)
        os.makedirs(trash_agent_path, exist_ok=True)
        
        for folder in os.listdir(AGENT_ROOT):
            if folder in AGENT_TRASH_LIST:
                src = os.path.join(AGENT_ROOT, folder)
                dst = os.path.join(trash_agent_path, folder)
                if os.path.exists(src):
                    shutil.move(src, dst)
                    print(f"🗑️ [Agent] 已隔离: {folder}")
                    moved_count += 1

    # --- 处理 OpenClaw Skills ---
    if os.path.exists(OPENCLAW_ROOT):
        trash_openclaw_path = os.path.join(TRASH_DIR, OPENCLAW_ROOT)
        os.makedirs(trash_openclaw_path, exist_ok=True)
        
        # 获取当前目录下所有的文件夹
        current_folders = [f for f in os.listdir(OPENCLAW_ROOT) if os.path.isdir(os.path.join(OPENCLAW_ROOT, f))]
        
        for folder in current_folders:
            # 匹配逻辑：如果文件夹名在我们的垃圾名单中
            match_found = False
            for target in OPENCLAW_TRASH_LIST:
                if folder.lower().strip() == target.lower().strip():
                    match_found = True
                    break
            
            if match_found:
                src = os.path.join(OPENCLAW_ROOT, folder)
                dst = os.path.join(trash_openclaw_path, folder)
                try:
                    shutil.move(src, dst)
                    print(f"🗑️ [OpenClaw] 已隔离: {folder}")
                    moved_count += 1
                except Exception as e:
                    print(f"⚠️ 移动 {folder} 失败: {e}")

    print("\n" + "="*50)
    print(f"✅ 修正筛选完成！")
    print(f"📦 本次共隔离分类/作者: {moved_count} 个")
    print(f"📍 所有的 1-2 星及多模态干扰项已移至: ./{TRASH_DIR}/")
    print("="*50)

if __name__ == "__main__":
    main()