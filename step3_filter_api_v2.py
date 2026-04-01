import os
import shutil
from collections import Counter

TARGET_DIRS =[ "openclaw_skills","agent_skills"]
PENDING_DIR = "quarantine_api_pending"
REVIEW_LOG_FILE = os.path.join(PENDING_DIR, "api_review_log.txt")

# 💎 精心优化的 API/鉴权 特征词库 (全部小写)
# 核心原则：绝对不单独使用 "api" 或 "token" 这两个词，以防误杀纯本地工具。
API_KEYWORDS =[
    # 1. 强鉴权与密钥 (Auth & Keys - 高致死率)
    "api_key", "api key", "apikey", 
    "access_token", "access token", 
    "secret_key", "secret key", 
    "bearer token", "oauth", 
    "client_secret", "client id", 
    "jwt token", "personal access token",
    "login required", "authentication required",
    
    # 2. 强网络端点 (Network & Endpoints)
    "webhook", "endpoint", "graphql", "rest api", "http request", 
    "https://api.", "api.github.com",
    
    # 3. 典型商业云服务凭证 (Cloud/SaaS Credentials)
    "aws credentials", "aws_access_key", "aws_secret_access_key",
    "azure_tenant_id", "gcp credentials", "stripe api", "twilio api"
]

def count_api_triggers(skill_folder):
    """读取 SKILL.md，统计所有外部依赖关键词出现的次数"""
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
            for kw in API_KEYWORDS:
                count = content.count(kw)
                if count > 0:
                    trigger_details[kw] = count
                    total_count += count
    except Exception as e:
        print(f"无法读取文件 {skill_md_path}: {e}")
        
    return total_count, trigger_details

def main():
    if not os.path.exists(PENDING_DIR):
        os.makedirs(PENDING_DIR)
        
    total_scanned = 0
    kept_skills = 0
    moved_to_pending = 0
    
    # 用于统计分布的计数器
    trigger_distribution = Counter()
    one_hit_keywords = Counter()
    
    print("🚀 开始第三步扫描：隔离 API 依赖技能，并进行命中分布分析...\n")

    with open(REVIEW_LOG_FILE, 'w', encoding='utf-8') as log_file:
        log_file.write("=== API 与外部依赖 复核清单 (API/Network Review Log) ===\n")
        log_file.write("注意：重点排查 '总命中数 = 1' 的技能，可能是文档里的随口一提导致误杀。\n\n")
        
        for base_dir in TARGET_DIRS:
            if not os.path.exists(base_dir): continue
                
            for category in os.listdir(base_dir):
                category_path = os.path.join(base_dir, category)
                if not os.path.isdir(category_path): continue
                    
                for skill_name in os.listdir(category_path):
                    skill_path = os.path.join(category_path, skill_name)
                    if not os.path.isdir(skill_path): continue
                        
                    total_scanned += 1
                    
                    # 获取命中统计
                    total_hits, details = count_api_triggers(skill_path)
                    
                    if total_hits > 0:
                        # 记录分布数据
                        trigger_distribution[total_hits] += 1
                        if total_hits == 1:
                            # 找出是哪个词导致了这唯一的 1 次击杀
                            kw = list(details.keys())[0]
                            one_hit_keywords[kw] += 1

                        # 移动到待定区
                        pending_category_dir = os.path.join(PENDING_DIR, base_dir, category)
                        os.makedirs(pending_category_dir, exist_ok=True)
                        pending_dest = os.path.join(pending_category_dir, skill_name)
                        
                        try:
                            shutil.move(skill_path, pending_dest)
                            moved_to_pending += 1
                            
                            # 写入复核日志
                            details_str = ", ".join([f"'{k}': {v}次" for k, v in details.items()])
                            log_line = f"技能: {skill_name}\n路径: {base_dir}/{category}\n总命中数: {total_hits}  |  详细词频: {details_str}\n{'-'*50}\n"
                            log_file.write(log_line)
                            
                        except Exception as e:
                            print(f"⚠️ 移动 {skill_name} 时出错: {e}")
                    else:
                        kept_skills += 1

    # ================= 打印深度分析报告 =================
    print("\n" + "="*50)
    print("📊 第三步：API 隔离扫描报告 & 命中分布分析")
    print("="*50)
    print(f"📂 总计复查技能: {total_scanned} 个")
    print(f"✅ 合格保留 (纯本地工具): {kept_skills} 个")
    print(f"📦 移至待定区 (需 Mock): {moved_to_pending} 个")
    print(f"📍 复核清单已保存至: ./{REVIEW_LOG_FILE}")
    print("-" * 50)
    
    if moved_to_pending > 0:
        print("📈 【隔离触发次数分布】")
        for hits in sorted(trigger_distribution.keys()):
            count = trigger_distribution[hits]
            pct = (count / moved_to_pending) * 100
            print(f"   命中 {hits:2d} 次的技能数: {count:4d} 个 ({pct:5.1f}%)")
            
        print("-" * 50)
        print("🔍 【1次误杀嫌疑词 Top 5】(重点排查)")
        for kw, count in one_hit_keywords.most_common(5):
            print(f"   ⚠️ '{kw}': 导致了 {count} 次单次击杀")
    print("="*50)

if __name__ == "__main__":
    main()