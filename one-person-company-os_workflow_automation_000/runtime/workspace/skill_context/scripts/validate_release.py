#!/usr/bin/env python3
"""Run local release validation for One Person Company OS."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = ROOT / "scripts"
RELEASE_ASSETS_DIR = ROOT / "release" / "assets"


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )


def assert_exists(path: Path) -> None:
    if not path.is_file():
        raise FileNotFoundError(f"expected file not found: {path}")


def assert_contains(text: str, *snippets: str) -> None:
    for snippet in snippets:
        if snippet not in text:
            raise AssertionError(f"expected snippet not found: {snippet}")


def read_docx_text(path: Path) -> str:
    with zipfile.ZipFile(path) as archive:
        document = archive.read("word/document.xml").decode("utf-8")
    return document


def validate_python_compatibility_logic() -> None:
    from common import build_agent_action, is_python_version_supported
    from ensure_python_runtime import build_install_plan

    if not is_python_version_supported((3, 7, 0)):
        raise AssertionError("Python 3.7 should be supported")
    if is_python_version_supported((3, 6, 15)):
        raise AssertionError("Python 3.6 should not be supported")

    switch_action = build_agent_action(
        current_supported=False,
        compatible_runtime={"executable": "/opt/python3.11/bin/python3.11", "version": (3, 11, 9)},
        writable=True,
    )
    assert_contains(switch_action, "OpenClaw", "/opt/python3.11/bin/python3.11", "重跑脚本")

    install_action = build_agent_action(
        current_supported=False,
        compatible_runtime=None,
        writable=True,
    )
    assert_contains(install_action, "OpenClaw", "安装兼容解释器", "手动落盘")

    mac_plan = build_install_plan(
        target_version="3.11",
        system_name="darwin",
        available_commands={"brew"},
    )
    if not mac_plan["supported"] or mac_plan["installer"] != "Homebrew":
        raise AssertionError("expected Homebrew install plan for macOS")

    apt_plan = build_install_plan(
        target_version="3.11",
        system_name="linux",
        os_release={"ID": "ubuntu", "PRETTY_NAME": "Ubuntu 24.04"},
        available_commands={"apt-get"},
    )
    if not apt_plan["supported"] or apt_plan["installer"] != "apt-get":
        raise AssertionError("expected apt-get install plan for Ubuntu")

    win_plan = build_install_plan(
        target_version="3.11",
        system_name="windows",
        available_commands={"winget"},
    )
    if not win_plan["supported"] or win_plan["installer"] != "winget":
        raise AssertionError("expected winget install plan for Windows")


def validate_workspace_scripts() -> None:
    with tempfile.TemporaryDirectory(prefix="opc-validate-") as tmp_dir:
        workspace = Path(tmp_dir)

        ensure_runtime = run(str(SCRIPTS_DIR / "ensure_python_runtime.py"))
        assert_contains(
            ensure_runtime.stdout,
            "Step 5/5 核对结果、说明变化并给出回报 [验证与回报]",
            "Python 兼容状态",
            "安装方案",
            "执行结果",
        )
        print(ensure_runtime.stdout.strip())

        preflight = run(str(SCRIPTS_DIR / "preflight_check.py"), "--mode", "创建公司", "--company-dir", str(workspace / "北辰实验室"))
        assert_contains(
            preflight.stdout,
            "Step 5/5 核对结果、说明变化并给出回报 [验证与回报]",
            "用户导航版:",
            "三层导航条:",
            "本次范围:",
            "回合仪表盘:",
            "审计版:",
            "保存状态:",
            "运行状态:",
            "模式 A：脚本执行",
            "python_supported",
            "兼容目标",
            "恢复脚本",
            "智能体建议动作",
        )
        print(preflight.stdout.strip())

        init = run(
            str(SCRIPTS_DIR / "init_business.py"),
            "北辰实验室",
            "--path",
            str(workspace),
            "--product-name",
            "北辰助手",
            "--stage",
            "构建期",
            "--target-user",
            "独立开发者",
            "--core-problem",
            "还没有一个真正能持续推进产品和成交的一人公司系统",
            "--product-pitch",
            "一个帮助独立开发者把产品做出来并卖出去的一人公司控制系统",
        )
        assert_contains(
            init.stdout,
            "Step 5/5 核对结果、说明变化并给出回报 [验证与回报]",
            "本次变化:",
            "查看与改进:",
            "保存解释:",
            "运行解释:",
            "文件名:",
            "00-经营总盘.md",
        )
        print(init.stdout.strip())

        company_dir = workspace / "北辰实验室"
        assert_exists(company_dir / "00-经营总盘.md")
        assert_exists(company_dir / "01-创始人约束.md")
        assert_exists(company_dir / "02-价值承诺与报价.md")
        assert_exists(company_dir / "03-机会与成交管道.md")
        assert_exists(company_dir / "04-产品与上线状态.md")
        assert_exists(company_dir / "05-客户交付与回款.md")
        assert_exists(company_dir / "06-现金流与经营健康.md")
        assert_exists(company_dir / "07-资产与自动化.md")
        assert_exists(company_dir / "08-风险与关键决策.md")
        assert_exists(company_dir / "09-本周唯一主目标.md")
        assert_exists(company_dir / "10-今日最短动作.md")
        assert_exists(company_dir / "11-协作记忆.md")
        assert_exists(company_dir / "12-会话交接.md")
        assert_exists(company_dir / "角色智能体" / "角色清单.md")
        assert_exists(company_dir / "sales" / "01-成交动作清单.md")
        assert_exists(company_dir / "product" / "01-MVP与上线清单.md")
        assert_exists(company_dir / "delivery" / "01-客户交付追踪.md")
        assert_exists(company_dir / "delivery" / "02-交付目录总览.md")
        assert_exists(company_dir / "产物" / "01-实际交付" / "01-实际产出总表.docx")
        assert_exists(company_dir / "产物" / "02-软件与代码" / "01-代码与功能交付清单.docx")
        assert_exists(company_dir / "产物" / "02-软件与代码" / "02-测试与验收记录.docx")
        assert_exists(company_dir / "产物" / "03-非软件与业务" / "01-非软件交付清单.docx")
        assert_exists(company_dir / "自动化" / "当前状态.json")
        if (company_dir / "产物" / "产品").exists() or (company_dir / "产物" / "增长").exists() or (company_dir / "产物" / "运营").exists():
            raise AssertionError("legacy unnumbered artifact directories should not be created")
        artifact_md_files = list((company_dir / "产物").rglob("*.md"))
        if artifact_md_files:
            raise AssertionError(f"expected only docx files under artifacts, found markdown: {artifact_md_files}")
        assert_contains(
            read_docx_text(company_dir / "产物" / "01-实际交付" / "01-实际产出总表.docx"),
            "实际产出总表",
            "起始版",
        )
        assert_contains(
            (company_dir / "00-经营总盘.md").read_text(encoding="utf-8"),
            "当前结论",
            "闭环健康",
        )
        assert_contains(
            (company_dir / "04-产品与上线状态.md").read_text(encoding="utf-8"),
            "产品与上线状态",
            "当前状态",
        )

        focus_update = run(
            str(SCRIPTS_DIR / "update_focus.py"),
            str(company_dir),
            "--primary-goal",
            "把 MVP 推到可演示并拿到第一批对话",
            "--primary-bottleneck",
            "价值表达和产品演示都还不够可卖",
            "--primary-arena",
            "product",
            "--today-action",
            "先补 homepage hero 的价值表达和 CTA 路径",
            "--week-outcome",
            "拿到可演示的首版首页与注册入口",
        )
        assert_contains(focus_update.stdout, "Step 5/5 核对结果、说明变化并给出回报 [验证与回报]", "更新主焦点", "00-经营总盘.md")
        print(focus_update.stdout.strip())

        product_update = run(
            str(SCRIPTS_DIR / "advance_product.py"),
            str(company_dir),
            "--state",
            "prototype",
            "--current-version",
            "v0.1 hero",
            "--core-capability",
            "首页首屏价值表达",
            "--core-capability",
            "注册 CTA 路径",
            "--current-gap",
            "首屏证明点不够强",
            "--launch-blocker",
            "还没有对外可演示链接",
            "--repository",
            "workspace/北辰实验室",
        )
        assert_contains(product_update.stdout, "Step 5/5 核对结果、说明变化并给出回报 [验证与回报]", "推进产品与上线", "04-产品与上线状态.md")
        print(product_update.stdout.strip())

        pipeline_update = run(
            str(SCRIPTS_DIR / "advance_pipeline.py"),
            str(company_dir),
            "--talking",
            "3",
            "--proposal",
            "1",
            "--next-revenue-action",
            "把首版 demo 发给 3 位独立开发者并约反馈",
            "--opportunity-name",
            "首批独立开发者用户",
            "--opportunity-stage",
            "talking",
            "--opportunity-next-action",
            "约一次 20 分钟看 demo 的通话",
        )
        assert_contains(pipeline_update.stdout, "Step 5/5 核对结果、说明变化并给出回报 [验证与回报]", "推进成交管道", "03-机会与成交管道.md")
        print(pipeline_update.stdout.strip())

        artifact_docs = run(
            str(SCRIPTS_DIR / "generate_artifact_document.py"),
            str(company_dir),
            "--title",
            "首页首屏规范",
            "--artifact-type",
            "产品规范",
            "--category",
            "software",
            "--summary",
            "明确首页首屏的价值主张、结构和 CTA 路径。",
            "--scope-in",
            "首页首屏信息结构",
            "--scope-in",
            "CTA 与注册入口说明",
            "--scope-out",
            "完整站点视觉系统",
            "--deliverable",
            "首页首屏正式交付文档",
            "--deliverable",
            "首页首屏代码与界面交付记录",
            "--software-output",
            "首页首屏组件代码",
            "--software-output",
            "CTA 路径配置",
            "--evidence",
            "workspace/北辰实验室/产物/02-软件与代码/待补充",
            "--change",
            "本次补齐了正式交付文档结构",
            "--decision",
            "先收敛价值主张再扩展视觉探索",
            "--risk",
            "用户价值表达仍需继续校准",
        )
        assert_contains(
            artifact_docs.stdout,
            "Step 5/5 核对结果、说明变化并给出回报 [验证与回报]",
            "生成正式交付文档",
            "已生成正式 DOCX",
            ".docx",
        )
        print(artifact_docs.stdout.strip())
        generated_docx = company_dir / "产物" / "02-软件与代码" / "03-首页首屏规范.docx"
        assert_exists(generated_docx)
        assert_contains(read_docx_text(generated_docx), "首页首屏规范", "实际软件与代码产出", "证据与验收路径", "交付就绪版")
        assert_contains(
            (company_dir / "delivery" / "02-交付目录总览.md").read_text(encoding="utf-8"),
            "03-首页首屏规范.docx",
            "文档成熟度: 交付就绪版",
        )

        delivery_update = run(
            str(SCRIPTS_DIR / "advance_delivery.py"),
            str(company_dir),
            "--active-customers",
            "1",
            "--delivery-status",
            "首位试用客户已进入 onboarding",
            "--blocking-issue",
            "缺少标准化开通说明",
            "--next-delivery-action",
            "补 onboarding 引导和反馈回收",
            "--receivable",
            "2999",
        )
        assert_contains(delivery_update.stdout, "Step 5/5 核对结果、说明变化并给出回报 [验证与回报]", "推进交付与回款", "05-客户交付与回款.md")
        print(delivery_update.stdout.strip())

        cash_update = run(
            str(SCRIPTS_DIR / "update_cash.py"),
            str(company_dir),
            "--cash-in",
            "2999",
            "--cash-out",
            "500",
            "--receivable",
            "2999",
            "--monthly-target",
            "10000",
            "--runway-note",
            "当前仍需优先盯住回款和下一个成交动作",
        )
        assert_contains(cash_update.stdout, "Step 5/5 核对结果、说明变化并给出回报 [验证与回报]", "更新现金状态", "06-现金流与经营健康.md")
        print(cash_update.stdout.strip())

        asset_record = run(str(SCRIPTS_DIR / "record_asset.py"), str(company_dir), "--kind", "templates", "--item", "首位试用客户 onboarding 话术")
        assert_contains(asset_record.stdout, "Step 5/5 核对结果、说明变化并给出回报 [验证与回报]", "记录资产沉淀", "07-资产与自动化.md")
        print(asset_record.stdout.strip())

        deploy_artifact = run(
            str(SCRIPTS_DIR / "generate_artifact_document.py"),
            str(company_dir),
            "--title",
            "部署与回滚清单",
            "--artifact-type",
            "部署清单",
            "--category",
            "ops",
            "--summary",
            "明确首版产品演示环境的部署入口、配置项、回滚方式和验证步骤。",
            "--deployment-item",
            "演示环境部署步骤",
            "--deployment-item",
            "关键环境变量检查",
            "--deployment-item",
            "回滚触发条件与回退流程",
            "--evidence",
            "workspace/北辰实验室/ops/01-上线检查清单.md",
            "--risk",
            "部署说明与实际入口可能仍需继续校准",
        )
        assert_contains(deploy_artifact.stdout, "生成正式交付文档", "部署与回滚清单", ".docx")
        print(deploy_artifact.stdout.strip())

        production_artifact = run(
            str(SCRIPTS_DIR / "generate_artifact_document.py"),
            str(company_dir),
            "--title",
            "生产观测与告警清单",
            "--artifact-type",
            "生产运维清单",
            "--category",
            "ops",
            "--summary",
            "明确首版产品上线后的监控、告警、值守与故障观察要点。",
            "--production-item",
            "关键成功事件监控",
            "--production-item",
            "错误告警与升级路径",
            "--production-item",
            "试用与回款转化观察项",
            "--evidence",
            "workspace/北辰实验室/06-现金流与经营健康.md",
            "--risk",
            "告警口径仍需结合真实上线环境继续细化",
        )
        assert_contains(production_artifact.stdout, "生成正式交付文档", "生产观测与告警清单", ".docx")
        print(production_artifact.stdout.strip())

        checkpoint = run(str(SCRIPTS_DIR / "checkpoint_save.py"), str(company_dir), "--reason", "准备结束当前会话，保存一次可恢复检查点", "--note", "验证 checkpoint save 能力")
        assert_contains(checkpoint.stdout, "Step 5/5 核对结果、说明变化并给出回报 [验证与回报]", "保存检查点", "记录/检查点")
        print(checkpoint.stdout.strip())

        single_brief = run(
            str(SCRIPTS_DIR / "build_agent_brief.py"),
            "--stage",
            "构建期",
            "--role",
            "engineer-tech-lead",
            "--company-name",
            "北辰实验室",
            "--objective",
            "把首屏需求落实成可交付路径",
            "--current-round",
            "完成首页首屏",
            "--round-goal",
            "完成首页首屏结构与注册入口",
            "--current-bottleneck",
            "前端结构还未收敛",
            "--next-shortest-action",
            "先拆出首屏组件和 CTA 路径",
            "--output-format",
            "json",
        )
        packet = json.loads(single_brief.stdout)
        if packet["role_id"] != "engineer-tech-lead":
            raise ValueError("unexpected role id in single brief validation")
        if packet["stage_id"] != "build":
            raise ValueError("unexpected stage in single brief validation")
        assert_contains(
            single_brief.stderr,
            "Step 5/5 核对结果、说明变化并给出回报 [验证与回报]",
            "模式 C：纯对话推进",
            "当前内容仅输出到标准输出，未指定 --output-dir",
        )

        output_dir = company_dir / "角色智能体"
        stage_briefs = run(
            str(SCRIPTS_DIR / "build_agent_brief.py"),
            "--stage",
            "上线期",
            "--all-default-roles",
            "--company-name",
            "北辰实验室",
            "--objective",
            "启动上线期的第一个回合",
            "--current-round",
            "准备首轮外部测试",
            "--round-goal",
            "整理测试入口、反馈表单和告知文案",
            "--current-bottleneck",
            "反馈入口还没打通",
            "--next-shortest-action",
            "先确认首轮测试表单字段",
            "--output-dir",
            str(output_dir),
        )
        assert_contains(stage_briefs.stdout, "总控台.md", "增长负责人.md")
        assert_contains(stage_briefs.stdout, "运维保障.md", "用户运营.md")
        assert_contains(stage_briefs.stderr, "Step 5/5 核对结果、说明变化并给出回报 [验证与回报]", "模式 A：脚本执行", "保存状态:")
        print(stage_briefs.stdout.strip())
        assert_exists(output_dir / "总控台.md")
        assert_exists(output_dir / "增长负责人.md")
        assert_exists(output_dir / "运维保障.md")
        assert_exists(output_dir / "用户运营.md")
        assert_exists(company_dir / "产物" / "04-部署与生产" / "01-部署与回滚清单.docx")
        assert_exists(company_dir / "产物" / "04-部署与生产" / "02-生产观测与告警清单.docx")
        assert_exists(next((company_dir / "记录" / "检查点").glob("*-检查点.md")))

        english_preflight = run(
            str(SCRIPTS_DIR / "preflight_check.py"),
            "--mode",
            "create-company",
            "--language",
            "en-US",
        )
        assert_contains(
            english_preflight.stdout,
            "User Navigation View:",
            "Three-Layer Navigation:",
            "Runtime Explanation:",
            "Mode A: Script Execution",
        )
        print(english_preflight.stdout.strip())

        english_init = run(
            str(SCRIPTS_DIR / "init_business.py"),
            "North Star Lab",
            "--path",
            str(workspace),
            "--product-name",
            "North Star Assistant",
            "--stage",
            "build",
            "--language",
            "en-US",
        )
        assert_contains(
            english_init.stdout,
            "User Navigation View:",
            "Current Mode: Create Company",
            "Current Stage: Build",
            "Current Artifact: Operating dashboard",
        )
        print(english_init.stdout.strip())

        english_company_dir = workspace / "North Star Lab"
        assert_exists(english_company_dir / "00-经营总盘.md")
        assert_contains((english_company_dir / "00-经营总盘.md").read_text(encoding="utf-8"), "Operating Dashboard", "Current Read")
        assert_contains((english_company_dir / "角色智能体" / "工程负责人.md").read_text(encoding="utf-8"), "Engineering Lead", "Outputs")

        english_artifact = run(
            str(SCRIPTS_DIR / "generate_artifact_document.py"),
            str(english_company_dir),
            "--title",
            "Homepage Hero Spec",
            "--artifact-type",
            "software",
            "--category",
            "software",
            "--summary",
            "Define the homepage value proposition and CTA.",
        )
        assert_contains(
            english_artifact.stdout,
            "Generate Formal Deliverable Document",
            "Generated a formal DOCX",
            "Mode A: Script Execution",
        )
        english_generated_docx = english_company_dir / "产物" / "02-软件与代码" / "03-Homepage-Hero-Spec.docx"
        assert_exists(english_generated_docx)
        assert_contains(read_docx_text(english_generated_docx), "Homepage Hero Spec", "Evidence And Acceptance Paths", "Delivery-Ready")

        english_brief = run(
            str(SCRIPTS_DIR / "build_agent_brief.py"),
            "--stage",
            "build",
            "--role",
            "engineer-tech-lead",
            "--language",
            "en-US",
            "--company-name",
            "North Star Lab",
            "--objective",
            "Ship the homepage hero section",
            "--current-round",
            "Homepage Hero",
            "--round-goal",
            "Implement the homepage hero path",
            "--current-bottleneck",
            "Copy and CTA hierarchy are not aligned yet",
            "--next-shortest-action",
            "Draft the hero copy and CTA structure",
        )
        assert_contains(english_brief.stdout, "Role Brief:", "Engineering Lead", "Continuation Context")
        assert_contains(english_brief.stderr, "Build Agent Brief", "Mode C: Chat-Only Progression")

        english_runtime = run(
            str(SCRIPTS_DIR / "ensure_python_runtime.py"),
            "--language",
            "en-US",
        )
        assert_contains(
            english_runtime.stdout,
            "Python Compatibility Status",
            "Install Plan",
            "Execution Result",
        )
        print(english_runtime.stdout.strip())


def validate_svg_assets() -> None:
    for path in sorted(RELEASE_ASSETS_DIR.glob("*.svg")):
        ET.parse(path)
        print(f"OK {path.relative_to(ROOT)}")


def main() -> int:
    validate_python_compatibility_logic()
    validate_workspace_scripts()
    validate_svg_assets()
    print("Release validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
