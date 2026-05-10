import os
import shutil
import argparse
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="根据修复报告将失败实例分离到同级目录")
    parser.add_argument("report_file", help="修复报告的路径")
    parser.add_argument("source_dir", help="原始实例目录的路径")
    parser.add_argument("--action", choices=['move', 'copy'], default='move', 
                        help="移动(move)还是复制(copy)？默认为 move")

    args = parser.parse_args()

    report_path = Path(args.report_file)
    source_path = Path(args.source_dir).resolve() # 获取绝对路径方便计算

    if not report_path.exists():
        print(f"❌ 错误: 找不到报告文件 {report_path}")
        return
    if not source_path.exists():
        print(f"❌ 错误: 找不到原始实例目录 {source_path}")
        return

    # --- 核心逻辑：自动计算同级目录名称 ---
    parent_dir = source_path.parent
    base_name = source_path.name
    
    # 定义新的存放目录
    failed_dir = parent_dir / f"{base_name}_fail"
    build_failed_dir = parent_dir / f"{base_name}_buildfail"
    
    failed_dir.mkdir(parents=True, exist_ok=True)
    build_failed_dir.mkdir(parents=True, exist_ok=True)

    stats = {'processed': 0, 'not_found': 0, 'kept': 0}

    print("\n" + "="*60)
    print(f"🧹 目标目录: {parent_dir}")
    print(f"📁 隔离区1 (FAILED): {failed_dir.name}")
    print(f"📁 隔离区2 (BUILD_FAILED): {build_failed_dir.name}")
    print("="*60)

    with open(report_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or any(line.startswith(s) for s in ["===", "---", "Timestamp", "Model", "Summary"]):
                continue

            if ":" in line:
                parts = line.split(":", 1)
                instance_name = parts[0].strip()
                status = parts[1].strip()

                if status in ["FAILED", "BUILD_FAILED"]:
                    src_folder = source_path / instance_name
                    
                    if status == "FAILED":
                        dest_folder = failed_dir / instance_name
                    else:
                        dest_folder = build_failed_dir / instance_name

                    if src_folder.exists() and src_folder.is_dir():
                        if args.action == 'move':
                            shutil.move(str(src_folder), str(dest_folder))
                            print(f"🚚 [移动] {status} -> {instance_name}")
                        else:
                            shutil.copytree(str(src_folder), str(dest_folder), dirs_exist_ok=True)
                            print(f"📋 [复制] {status} -> {instance_name}")
                        stats['processed'] += 1
                    else:
                        print(f"⚠️ [跳过] 找不到原文件夹: {instance_name}")
                        stats['not_found'] += 1
                        
                elif status in ["FIXED", "SKIPPED"]:
                    stats['kept'] += 1

    print("\n" + "="*60)
    print("✅ 分离工作完成！")
    print(f"🌟 留在原目录 ({base_name}): {stats['kept']} 个")
    print(f"📦 移入 _fail 目录: {sum(1 for x in failed_dir.iterdir() if x.is_dir()) if failed_dir.exists() else 0} 个")
    print(f"📦 移入 _buildfail 目录: {sum(1 for x in build_failed_dir.iterdir() if x.is_dir()) if build_failed_dir.exists() else 0} 个")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()