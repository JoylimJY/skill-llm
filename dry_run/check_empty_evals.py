import json
import os
import sys
import argparse
import shutil  # 📦 新增：用于移动文件夹
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.sandbox import Sandbox
from src.evaluator import evaluate_in_container

def check_empty_evals(target_dir_path):
    target_dir = Path(target_dir_path)
    if not target_dir.exists():
        print(f"找不到目录: {target_dir}")
        return

    # 📁 新增：定义存放假阳性实例的目标文件夹（和原文件夹同级）
    false_positive_dir = target_dir.parent / f"{target_dir.name}_false_positives"

    sandbox = Sandbox()
    flawed_instances = []
    total_count = 0

    print(f"🔍 开始进行“空载”评测基线检查: {target_dir}\n" + "="*50)

    # 遍历目标文件夹下的所有实例
    for instance_dir in sorted(target_dir.iterdir()):
        if not instance_dir.is_dir() or not (instance_dir / "task.json").exists():
            continue
            
        instance_id = instance_dir.name
        total_count += 1
        print(f"[{total_count}] 正在检查: {instance_id} ...")
        
        container_id = None
        try:
            # 1. 构建镜像 (已注释跳过)
            # 2. 创建空容器
            container_id = sandbox.create(str(instance_dir))
            
            # 3. 直接在空容器里运行 Eval 评测脚本
            result = evaluate_in_container(str(instance_dir), container_id, sandbox)
            
            # 4. 严格检查分数：好代码在空跑时必须得 0 分
            if result.score > 0 or result.passed:
                print(f" ⚠️ 空载得分为: {result.score:.2f} (Passed: {result.passed})")
                
                # 打印具体是哪一项检查“白给”了
                if hasattr(result, 'details') and isinstance(result.details, list):
                    for check in result.details:
                        if isinstance(check, dict) and check.get("passed"):
                            print(f"     - 意外通过: {check.get('name')} -> {check.get('detail')}")
                        elif hasattr(check, 'passed') and check.passed:
                            print(f"     - 意外通过: {check.name} -> {check.detail}")
                            
                # 📝 新增：把有漏洞的实例路径存下来，留到最后移动
                flawed_instances.append({
                    "id": instance_id,
                    "path": instance_dir,  # 记录物理路径
                    "score": result.score,
                    "passed": result.passed
                })
            else:
                print(f" ✅ 评测逻辑严谨 (得分为 0)")

        except Exception as e:
            print(f" ❌ 评测运行出错: {e}")
            
        finally:
            # 5. 销毁容器，保证环境干净
            if container_id:
                try:
                    sandbox.destroy(container_id)
                except Exception:
                    pass

    # ==========================================
    # 🚚 新增：开始批量隔离假阳性实例
    # ==========================================
    print("\n" + "="*50)
    print(f"总计检查: {total_count} 个")
    
    if flawed_instances:
        print(f"🚨 发现 {len(flawed_instances)} 个有假阳性漏洞的实例！准备隔离...")
        
        # 如果隔离文件夹不存在，就创建它
        false_positive_dir.mkdir(parents=True, exist_ok=True)
        print(f"📁 隔离区建立: {false_positive_dir.name}")
        
        for item in flawed_instances:
            src_path = item["path"]
            dest_path = false_positive_dir / item["id"]
            
            try:
                # 核心移动操作：把原文件夹剪切过去
                shutil.move(str(src_path), str(dest_path))
                print(f"  🚚 已移走: {item['id']} (Score: {item['score']})")
            except Exception as e:
                print(f"  ❌ 移动 {item['id']} 失败: {e}")
                
        print(f"\n🎉 隔离完成！所有假阳性实例已从原目录中移除。")
    else:
        print("🎉 完美！所有测试实例在空载状态下均得 0 分，没有发现假阳性。")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="检查实例的 Eval 脚本是否存在漏洞，并自动隔离假阳性实例")
    parser.add_argument("target_dir", type=str, help="需要检查的实例数据文件夹路径")
    
    args = parser.parse_args()
    check_empty_evals(args.target_dir)