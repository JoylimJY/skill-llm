import os
import sys
import argparse
import shutil
from pathlib import Path

# 导入你现有的环境
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.sandbox import Sandbox
from src.evaluator import evaluate_in_container

def collect_clean_instances(target_dir_path):
    target_dir = Path(target_dir_path)
    # 建立“干净”文件夹
    clean_dir = target_dir.parent / f"{target_dir.name}_verified_clean"
    clean_dir.mkdir(parents=True, exist_ok=True)

    sandbox = Sandbox()
    total_moved = 0

    print(f"🚀 开始提取合格实例 (得分必须为 0): {target_dir}")
    print(f"📦 目标文件夹: {clean_dir}\n" + "="*50)

    # 只遍历还在原目录下的文件夹
    for instance_dir in sorted(target_dir.iterdir()):
        if not instance_dir.is_dir() or not (instance_dir / "task.json").exists():
            continue
            
        instance_id = instance_dir.name
        container_id = None
        
        try:
            print(f"正在核验: {instance_id} ...", end=" ", flush=True)
            
            # 创建容器并评测
            container_id = sandbox.create(str(instance_dir))
            result = evaluate_in_container(str(instance_dir), container_id, sandbox)
            
            # 核心逻辑：只有得分为 0 且 Passed 为 False 的才是我们要的“白纸”
            if result.score == 0 and not result.passed:
                print("✅ 合格！正在搬运...")
                shutil.move(str(instance_dir), str(clean_dir / instance_id))
                total_moved += 1
            else:
                print(f"❌ 不合格 (得分: {result.score})，保留在原位。")

        except Exception as e:
            print(f"⚠️ 报错，保留在原位。 (Error: {str(e)[:50]}...)")
            
        finally:
            if container_id:
                try:
                    sandbox.destroy(container_id)
                except:
                    pass

    print("\n" + "="*50)
    print(f"🎉 提取完成！共搬运了 {total_moved} 个合格实例到 {clean_dir.name}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("target_dir", type=str)
    args = parser.parse_args()
    collect_clean_instances(args.target_dir)