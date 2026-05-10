import os
import json
import shutil
import argparse
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="根据 task.json 状态分离 unsolvable 实例到同级目录")
    parser.add_argument("source_dir", help="原始实例目录的路径 (例如: instance/instances_openclaw_skills)")
    parser.add_argument("--action", choices=['move', 'copy'], default='move', 
                        help="移动(move)还是复制(copy)？默认为 move")

    args = parser.parse_args()

    source_path = Path(args.source_dir).resolve() # 获取绝对路径

    if not source_path.exists():
        print(f"❌ 错误: 找不到原始实例目录 {source_path}")
        return

    # --- 计算同级目录名称 ---
    parent_dir = source_path.parent
    base_name = source_path.name
    
    # 定义新的存放目录
    unsolvable_dir = parent_dir / f"{base_name}_unsolvable"
    unsolvable_dir.mkdir(parents=True, exist_ok=True)

    stats = {'processed': 0, 'not_unsolvable': 0, 'no_task_json': 0, 'error': 0}

    print("\n" + "="*60)
    print(f"🧹 目标目录: {parent_dir}")
    print(f"📁 原始区: {base_name}")
    print(f"📁 隔离区 (UNSOLVABLE): {unsolvable_dir.name}")
    print("="*60)

    # 遍历源目录下的所有子文件夹
    for instance_path in source_path.iterdir():
        if not instance_path.is_dir():
            continue
            
        task_json_path = instance_path / "task.json"
        instance_name = instance_path.name
        
        if not task_json_path.exists():
            stats['no_task_json'] += 1
            continue

        try:
            with open(task_json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            status = data.get("filter_status")
            
            if status == "unsolvable":
                dest_folder = unsolvable_dir / instance_name
                
                if args.action == 'move':
                    shutil.move(str(instance_path), str(dest_folder))
                    print(f"🚚 [移动] {instance_name}")
                else:
                    shutil.copytree(str(instance_path), str(dest_folder), dirs_exist_ok=True)
                    print(f"📋 [复制] {instance_name}")
                stats['processed'] += 1
            else:
                stats['not_unsolvable'] += 1
                
        except Exception as e:
            print(f"⚠️ [错误] 处理 {instance_name} 时发生异常: {e}")
            stats['error'] += 1

    print("\n" + "="*60)
    print("✅ 分离工作完成！")
    print(f"📦 移入 _unsolvable 目录: {stats['processed']} 个")
    print(f"🌟 留在原目录 (非 unsolvable): {stats['not_unsolvable']} 个")
    if stats['no_task_json'] > 0:
        print(f"⏭️  跳过 (无 task.json): {stats['no_task_json']} 个")
    if stats['error'] > 0:
        print(f"❌ 读取错误: {stats['error']} 个")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()