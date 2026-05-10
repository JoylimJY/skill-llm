import json
from pathlib import Path
from collections import Counter

def main():
    instances_dir = Path("instances-openclaw-Browser-fix")
    if not instances_dir.exists():
        print("❌ 找不到 instances 目录")
        return

    # 统计容器
    success_stats = Counter()
    failed_count = 0
    total_unsolvable_at_start = 0

    results = []

    for task_dir in instances_dir.iterdir():
        if not task_dir.is_dir(): continue
        
        task_json_path = task_dir / "task.json"
        if not task_json_path.exists(): continue
        
        try:
            with open(task_json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            status = data.get("filter_status")
            attempts = data.get("repair_attempts", 0)
            
            # 判断逻辑：
            # 1. 只有原本是 unsolvable 的才会计入（通过 repair_attempts 是否存在判断）
            if attempts > 0:
                total_unsolvable_at_start += 1
                
                if status == "kept":
                    # 修复成功
                    success_stats[attempts] += 1
                    results.append(f"✅ [成功] {task_dir.name}: 花费 {attempts} 轮")
                else:
                    # 仍然是 unsolvable 或其他状态，但尝试过
                    failed_count += 1
                    results.append(f"❌ [失败] {task_dir.name}: 尝试 {attempts} 轮后放弃")
        except Exception as e:
            print(f"读取 {task_dir.name} 出错: {e}")

    # 打印报表
    print("\n" + "="*40)
    print("        🛠️  修复任务进度统计报表")
    print("="*40)
    print(f"总计尝试修复的任务数: {total_unsolvable_at_start}")
    print("-" * 40)
    
    total_fixed = sum(success_stats.values())
    print(f"🎉 修复成功总数: {total_fixed}")
    for i in range(1, 4):
        count = success_stats[i]
        percent = (count / total_fixed * 100) if total_fixed > 0 else 0
        print(f"   第 {i} 轮修复成功: {count} 个 ({percent:.1f}%)")
    
    print("-" * 40)
    print(f"💀 修复失败总数: {failed_count}")
    
    success_rate = (total_fixed / total_unsolvable_at_start * 100) if total_unsolvable_at_start > 0 else 0
    print(f"\n整体修复成功率: {success_rate:.2f}%")
    print("="*40 + "\n")

    # 如果你想看明细，可以取消下面这行的注释
    # print("\n".join(results))

if __name__ == "__main__":
    main()