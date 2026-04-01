import os
import shutil
from collections import Counter

# --- 路径配置 ---
# 注意：现在的源头是 api_pending_skills
SOURCE_DIRS = ["api_pending_skills/agent_skills", "api_pending_skills/openclaw_skills"]
POISON_TRASH = "quarantine_deep_poison" # 最终确认无法运行的毒药区

# --- 沿用高代表性词库 ---
DEEP_AUDIT_KEYWORDS = {
    "SaaS_DEPENDENCY": ["meegle", "clerk", "stripe", "notion", "slack", "discord", "trello", "asana", "jira", "shopify", "zendesk", "intercom", "firebase", "supabase auth", "auth0", "twilio"],
    "NETWORK_ACTION": ["webhook", "callback url", "rest endpoint", "api endpoint", "dns lookup", "fetch from", "synchronize with", "real-time data"],
    "UNSUPPORTED_ENV": ["ios ", "macos ", "xcode", "swiftui", "android studio", "cuda", "gpu required", "sonarqube server", "jenkins master"],
    "CRYPTO_BLOCKCHAIN": ["rpc node", "mainnet", "testnet", "smart contract", "ethereum wallet", "solana api"]
}

def check_poison(skill_path):
    skill_md = None
    for f in os.listdir(skill_path):
        if f.lower() == 'skill.md':
            skill_md = os.path.join(skill_path, f)
            break
    if not skill_md: return None

    try:
        with open(skill_md, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read().lower()
            for label, kws in DEEP_AUDIT_KEYWORDS.items():
                for kw in kws:
                    if f" {kw} " in f" {content} ":
                        return label
    except:
        pass
    return None

def main():
    total_scanned = 0
    moved_count = 0
    stats = Counter()

    print(f"🔍 正在对 api_pending_skills 进行『毒性提取』...\n")

    for base in SOURCE_DIRS:
        if not os.path.exists(base): continue
        
        # 遍历分类 (比如 Coding, DevOps)
        for cat in os.listdir(base):
            cat_path = os.path.join(base, cat)
            if not os.path.isdir(cat_path): continue
            
            # 遍历技能
            for skill in os.listdir(cat_path):
                skill_path = os.path.join(cat_path, skill)
                if not os.path.isdir(skill_path): continue
                
                total_scanned += 1
                label = check_poison(skill_path)
                
                if label:
                    # 如果命中深度毒性关键词，移入真正的“绝症区”
                    # 保持三层结构: quarantine_deep_poison / api_pending_skills / agent_skills / cat / skill
                    dest_path = os.path.join(POISON_TRASH, base, cat, skill)
                    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                    
                    try:
                        shutil.move(skill_path, dest_path)
                        moved_count += 1
                        stats[label] += 1
                    except Exception as e:
                        print(f"⚠️ 移动失败 {skill}: {e}")

    print("\n" + "="*50)
    print(f"📊 待定库 (Pending) 审计报告")
    print("="*50)
    print(f"📂 总计复查待定技能: {total_scanned} 个")
    print(f"🗑️ 确认为『重度毒药』并移走: {moved_count} 个")
    print(f"💎 剩余『轻度 API』技能: {total_scanned - moved_count} 个")
    print("-" * 50)
    print("📈 毒药分布:")
    for l, c in stats.items():
        print(f"   - {l:18}: {c} 个")
    print("="*50)
    print("💡 结论：留在 api_pending_skills 里的技能，是未来最值得 Mock 的高质量资源。")

if __name__ == "__main__":
    main()