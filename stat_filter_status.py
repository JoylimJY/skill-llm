import json
import sys
from collections import defaultdict
from pathlib import Path

def main():
    # 默认读取当前目录下的 instances 文件夹，也可以通过命令行参数传入路径
    target_dir = sys.argv[1] if len(sys.argv) > 1 else "instances"
    instances_path = Path(target_dir)

    if not instances_path.exists() or not instances_path.is_dir():
        print(f"❌ 找不到目录: {instances_path.absolute()}")
        return

    # 用于统计数量和记录具体实例名单
    status_counts = defaultdict(int)
    status_lists = defaultdict(list)

    print(f"🔍 正在扫描 '{instances_path}' 目录下的 task.json...\n")

    # 遍历 instances 文件夹下的所有子目录
    for instance_dir in instances_path.iterdir():
        if instance_dir.is_dir():
            task_file = instance_dir / "task.json"
            if task_file.exists():
                try:
                    with open(task_file, "r", encoding="utf-8") as f:
                        task_data = json.load(f)
                        # 获取 filter_status，如果没有该字段则标记为 'missing_field'
                        status = task_data.get("filter_status", "missing_field")
                        
                        status_counts[status] += 1
                        status_lists[status].append(instance_dir.name)
                except json.JSONDecodeError:
                    print(f"⚠️ 警告: {task_file} 不是合法的 JSON 文件，已跳过。")
                except Exception as e:
                    print(f"⚠️ 警告: 读取 {task_file} 时发生错误 - {e}")

    # ================= 打印统计结果 =================

    print("=== 📝 详细名单 ===")
    for status, instances in sorted(status_lists.items()):
        print(f"\n[{status}] (共 {len(instances)} 个):")
        for instance in sorted(instances):
            print(f"  - {instance}")
    print("=== 📊 数量总览 ===")
    total_valid = 0
    for status, count in sorted(status_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"- {status}: {count} 个")
        total_valid += count
    print(f"总计读取有效 task.json: {total_valid} 个\n")
if __name__ == "__main__":
    main()
    