#!/usr/bin/env python3
"""Office Hub Scheduler - 自动进化与技能缝合

定期检查新技能，自动缝合升级
"""

import sys
import json
import subprocess
import urllib.request
import re
from datetime import datetime

SKILL_DIR = "/Users/lrs/.openclaw/workspace/skills/office-hub"
DATA_DIR = f"{SKILL_DIR}/data"
TASKS_FILE = f"{DATA_DIR}/scheduler_tasks.json"
EVOLUTION_LOG = f"{DATA_DIR}/evolution_log.json"


def ensure_dirs():
    import os
    os.makedirs(DATA_DIR, exist_ok=True)


def load_tasks():
    """加载已注册的任务"""
    try:
        with open(TASKS_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}


def save_tasks(tasks):
    """保存任务列表"""
    ensure_dirs()
    with open(TASKS_FILE, 'w') as f:
        json.dump(tasks, f, indent=2, ensure_ascii=False)


def log_evolution(action, details):
    """记录进化日志"""
    ensure_dirs()
    logs = []
    try:
        with open(EVOLUTION_LOG, 'r') as f:
            logs = json.load(f)
    except:
        pass
    
    logs.append({
        'timestamp': datetime.now().isoformat(),
        'action': action,
        'details': details
    })
    
    # 只保留最近100条
    logs = logs[-100:]
    
    with open(EVOLUTION_LOG, 'w') as f:
        json.dump(logs, f, indent=2, ensure_ascii=False)


def search_office_skills():
    """搜索办公相关的新技能"""
    print("[搜索] 查找办公类精品技能...")
    
    # 搜索关键词
    keywords = ['office', 'excel', 'word', 'powerpoint', 'document', 'spreadsheet', 'automation']
    found_skills = []
    
    try:
        # 使用 clawhub CLI 搜索
        for kw in keywords:
            result = subprocess.run(
                ['clawhub', 'search', kw],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                # 解析输出
                lines = result.stdout.split('\n')
                for line in lines:
                    if '★' in line or 'stars' in line.lower():
                        found_skills.append({
                            'keyword': kw,
                            'line': line.strip()
                        })
    except Exception as e:
        print(f"[搜索] 异常: {e}")
    
    return found_skills


def check_skill_updates():
    """检查已有技能的更新"""
    print("[检查] 检查办公技能更新...")
    
    # 检查 office-hub 相关目录
    import os
    skill_dirs = [d for d in os.listdir(f"{SKILL_DIR}/../") 
                   if os.path.isdir(f"{SKILL_DIR}/../{d}")]
    
    updates = []
    for skill in skill_dirs:
        if any(k in skill.lower() for k in ['office', 'word', 'excel', 'powerpoint', 'document']):
            skill_path = f"{SKILL_DIR}/../{skill}"
            try:
                mtime = os.path.getmtime(skill_path)
                updates.append({
                    'skill': skill,
                    'last_modified': datetime.fromtimestamp(mtime).isoformat()
                })
            except:
                pass
    
    return updates


def suggest_skill_merge():
    """建议可以合并的技能"""
    print("[分析] 查找可合并的重复技能...")
    
    import os
    skill_dirs = [d for d in os.listdir(f"{SKILL_DIR}/../") 
                   if os.path.isdir(f"{SKILL_DIR}/../{d}")]
    
    # 识别办公相关技能
    office_skills = []
    for skill in skill_dirs:
        skill_lower = skill.lower()
        if any(k in skill_lower for k in ['office', 'word', 'excel', 'powerpoint', 'document', 'spreadsheet', 'pdf', 'markdown']):
            office_skills.append(skill)
    
    return office_skills


def register_evolution_task():
    """注册自动进化任务（每周检查一次）"""
    task_id = "office_evolution"
    tasks = load_tasks()
    
    if task_id in tasks:
        print(f"[已存在] Office进化任务")
        return tasks[task_id]
    
    message = """你是Office技能进化助手。每周自动检查并进化办公技能。

## 第一步：搜索新技能
用 clawhub search office/excel/word 等关键词搜索精品技能。

## 第二步：分析是否需要
- 新技能是否有独特功能？
- 能否缝合到 office-hub？
- 是否与现有功能重复？

## 第三步：执行缝合
如果有值得缝合的功能：
1. 读取新技能的 SKILL.md 和脚本
2. 合并到 office-hub 的对应目录
3. 更新 office-hub/SKILL.md 的致谢部分
4. 记录到进化日志

## 第四步：汇报
输出简短的进化报告：
📋 Office技能进化报告 - YYYY-MM-DD
- 检查技能数: xx
- 发现新功能: xxx
- 已缝合: xxx
- 待观察: xxx

如果没有任何进化，也简单汇报"本周无需进化"。"""
    
    cmd = [
        "openclaw", "cron", "add",
        "--name", "Office技能自动进化",
        "--cron", "0 10 * * 0",  # 每周日上午10点
        "--tz", "Asia/Shanghai",
        "--session", "isolated",
        "--message", message,
        "--deliver",
        "--channel", "feishu"
    ]
    
    print("[注册] Office进化任务（每周检查）...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        tasks[task_id] = "registered"
        save_tasks(tasks)
        print("[成功] 进化任务已注册")
        return True
    else:
        print(f"[失败] {result.stderr[:100]}")
        return False


def register_tips_task():
    """注册办公技巧提醒（每月一次）"""
    task_id = "office_tips"
    tasks = load_tasks()
    
    if task_id in tasks:
        print(f"[已存在] Office技巧提醒")
        return tasks[task_id]
    
    message = """你是Office效率助手。每月分享一个实用办公技巧。

从以下主题选择本月主题：
1. Excel高级公式（INDEX/MATCH/XLOOKUP）
2. Word高效排版（样式+目录+分节）
3. PPT设计技巧（母版+动画）
4. 邮件合并实战
5. Python自动化办公

生成简短教程：
📌 Office技巧分享 - YYYY-MM-DD

### 主题：xxx
### 适用场景：xxx
### 快速步骤：
1. xxx
2. xxx
3. xxx
### 常见错误：xxx

输出后静默退出，不要主动说更多。"""
    
    cmd = [
        "openclaw", "cron", "add",
        "--name", "Office技巧分享",
        "--cron", "0 14 1 * *",  # 每月1日下午2点
        "--tz", "Asia/Shanghai",
        "--session", "isolated",
        "--message", message,
        "--deliver",
        "--channel", "feishu"
    ]
    
    print("[注册] Office技巧提醒（每月1次）...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        tasks[task_id] = "registered"
        save_tasks(tasks)
        print("[成功] 技巧任务已注册")
        return True
    else:
        print(f"[失败] {result.stderr[:100]}")
        return False


def register_all():
    """注册所有进化相关任务"""
    print("=" * 50)
    print("Office Hub Scheduler - 自动进化任务")
    print("=" * 50)
    print()
    
    register_evolution_task()
    register_tips_task()
    
    print()
    print("=" * 50)
    print("注册完成！Office技能会自动进化~")
    print("=" * 50)


def status():
    """查看进化任务状态"""
    tasks = load_tasks()
    
    print("📋 Office Hub 进化任务")
    print("-" * 40)
    print(f"注册的任务数: {len(tasks)}")
    
    if tasks:
        for name, status in tasks.items():
            print(f"  • {name}: {status}")
    
    # 查看进化日志
    try:
        with open(EVOLUTION_LOG, 'r') as f:
            logs = json.load(f)
            recent = logs[-5:] if len(logs) > 5 else logs
            print(f"\n最近进化记录: {len(logs)}条")
            for log in recent:
                print(f"  • {log['timestamp'][:10]} - {log['action']}")
    except:
        print("\n暂无进化记录")


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 scheduler.py [register|status|search]")
        print("  register - 注册所有进化任务")
        print("  status    - 查看进化状态")
        print("  search    - 立即搜索新技能")
        sys.exit(1)
    
    action = sys.argv[1]
    
    if action == "register":
        register_all()
    elif action == "status":
        status()
    elif action == "search":
        print("[立即搜索] 查找办公类技能...")
        skills = search_office_skills()
        print(f"找到 {len(skills)} 个相关技能")
        
        print("\n[分析] 查找可合并的技能...")
        mergeable = suggest_skill_merge()
        print(f"办公相关技能: {mergeable}")
    else:
        print(f"[错误] 未知操作: {action}")


if __name__ == "__main__":
    main()
