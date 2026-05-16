import os
import random
import textwrap

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# ── Distractor directory structure ──────────────────────────────────────────
dirs = [
    "archives/2024/Q1",
    "archives/2024/Q2",
    "archives/2024/Q3",
    "drafts/internal",
    "drafts/external",
    "templates/word",
    "templates/pdf",
    "reports/submitted",
    "reports/pending",
    "assets/images",
    "assets/fonts",
    "tools/converters",
    "tools/validators",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# ── Distractor files ─────────────────────────────────────────────────────────
distractors = {
    "archives/2024/Q1/summary.txt": "一季度工作总结（已归档）\n详见附件。",
    "archives/2024/Q2/budget.csv": "部门,预算,实际支出\n行政部,50000,48200\n技术部,80000,79500",
    "archives/2024/Q3/meeting_minutes.txt": "会议纪要\n时间：2024-09-15\n地点：三楼会议室",
    "drafts/internal/note.txt": "内部草稿，勿外传。",
    "drafts/external/proposal_draft.txt": "对外合作方案草稿（待审核）",
    "templates/word/old_template.docx.placeholder": "占位符 - 旧版Word模板",
    "templates/pdf/pdf_guide.txt": "PDF转换说明（已废弃）",
    "reports/submitted/2024_annual.txt": "2024年年报（已提交）",
    "reports/pending/q4_draft.txt": "四季度报告草稿",
    "assets/images/logo_info.txt": "Logo资产说明文件",
    "assets/fonts/font_list.txt": "可用字体列表：宋体、黑体、仿宋、楷体",
    "tools/converters/legacy_converter.py": "# 旧版转换工具（已弃用）\nprint('deprecated')",
    "tools/validators/schema_check.py": "# 文档结构校验工具\npass",
    "drafts/internal/random_notes.md": "# 随机笔记\n- 事项1\n- 事项2\n\n暂无其他内容。",
}
for rel_path, content in distractors.items():
    full_path = os.path.join(workspace, rel_path)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

# ── Main input: the messy weekly report Markdown ─────────────────────────────
# This file is intentionally rich with diverse syntax to test all features.
weekly_report_md = textwrap.dedent("""\
    # 某市行政服务中心第42周工作周报

    ---

    ## 一、本周工作概况

    本周行政服务中心共处理各类事务 **127项**，较上周增长 *8.5%*，整体运行平稳。

    ### 1.1 窗口服务情况

    窗口服务累计接待群众 **892人次**，办结事项 ~~841~~ **867项**，办结率达到 `97.2%`。

    #### 1.1.1 高频事项统计

    1. 不动产登记：234件
    2. 营业执照办理：189件
    3. 社保业务：156件
    4. 公积金查询：98件
    5. 其他事项：190件

    ### 1.2 线上服务情况

    本周线上平台访问量为 **15,320次**，在线申办 *3,241件*，数据如下：

    - 移动端占比：**68%**
    - PC端占比：*29%*
    - 其他终端：~~5%~~（已核实为3%）

    > 注意：线上数据统计截止时间为本周五18:00，部分跨区业务数据尚未完全同步。

    ---

    ## 二、重点工作进展

    ### 2.1 数字化改革专项

    本周完成 `审批流程再造` 方案的第三轮评审，主要修改内容包括：

    ```
    模块一：身份核验流程优化
    - 接入国家政务外网实名认证接口
    - 缩短核验时长至 30秒以内

    模块二：材料预审智能化
    - 引入OCR识别技术
    - 自动比对历史申报记录
    ```

    ### 2.2 投诉与回访工作

    本周共受理群众投诉 **12件**，回访满意率 **96.7%**，详情见下表：

    #### 2.2.1 投诉处理时效

    1. 当日办结：9件
    2. 次日办结：2件
    3. 超时处理：1件（已上报督查部门）

    ---

    ## 三、下周工作计划

    ### 3.1 常规工作

    - 继续保障窗口正常开放，**节假日不休**
    - 开展业务人员 *专项培训* 一次
    - 完成 `Q4季度绩效考核` 数据汇总

    ### 3.2 重点任务

    1. 完成数字化改革专项第四轮评审
    2. 对接省级平台数据接口联调
    3. 组织开展 **"好差评"** 专项整治行动

    > 如有特殊情况，请提前向分管领导报告，不得擅自调整工作安排。

    ---

    ## 四、需协调事项

    #### 4.1 跨部门协作请求

    目前与 **公安局户籍科** 的数据共享协议尚未签署，影响以下业务办理：

    - ~~居住证办理~~（已暂停受理）
    - 户口迁移业务
    - 身份证换领（*部分情形受限*）

    请相关部门 **尽快推进** 协议签署工作，预计影响群众约 `320人`。

    ---

    *本周报由行政服务中心综合协调科整理，如有疑问请联系 [综合协调科](mailto:zhhxk@admin.gov.cn)*
""")

input_path = os.path.join(workspace, "weekly_report_42.md")
with open(input_path, "w", encoding="utf-8") as f:
    f.write(weekly_report_md)

print(f"[gen_inputs] Workspace initialized at {workspace}")
print(f"[gen_inputs] Input file created: {input_path}")
print(f"[gen_inputs] Distractor files created: {len(distractors)}")