import os
import json
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# Create deeply nested distractor directory structure
dirs = [
    "clients/active/2024",
    "clients/active/2025",
    "clients/archived/2023",
    "reports/draft",
    "reports/final",
    "templates/bazi",
    "templates/naming",
    "templates/zodiac",
    "data/almanac",
    "data/references",
    "tools/converters",
    "admin/billing",
    "admin/logs",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files
distractor_files = {
    "clients/active/2024/client_zhang_notes.txt": "张总 - 需要八字排盘 - 已完成\n生日: 1975年4月12日\n备注: 喜金水",
    "clients/active/2024/client_liu_report.txt": "刘女士运势报告草稿\n五行偏火\n建议多用水蓝色",
    "clients/active/2025/pending_requests.txt": "待处理客户:\n1. 王建国 - 择日查询\n2. 陈小红 - 生肖配对\n3. 吴磊 - 姓名分析",
    "clients/archived/2023/old_report_template.txt": "旧版报告格式（已弃用）\n格式: 文本段落式",
    "reports/draft/sample_bazi_draft.txt": "样本八字:\n年柱: 壬子\n月柱: 癸亥\n日柱: 甲寅\n时柱: 乙卯\n（此为示例，非真实客户数据）",
    "reports/final/2024_summary.txt": "2024年完成报告统计:\n八字排盘: 47份\n姓名分析: 23份\n择日: 15份",
    "templates/bazi/bazi_template_v2.txt": "八字报告模板v2\n[日期]\n[四柱]\n[五行分布]\n[分析]",
    "templates/naming/naming_guide.txt": "姓名分析指引\n- 需要提供完整姓名\n- 需要各字笔画数\n- 参考五格剖象法",
    "templates/zodiac/zodiac_compat_table.txt": "生肖相合速查\n六合: 子丑 寅亥 卯戌 辰酉 巳申 午未\n三合: 申子辰 寅午戌 巳酉丑 亥卯未",
    "data/almanac/2025_almanac_excerpt.txt": "2025年(乙巳年)黄历摘录\n正月: 初一 宜: 祭祀 忌: 动土\n...",
    "data/references/wuxing_reference.txt": "五行参考资料\n相生: 木火土金水\n相克: 木土水火金\n（注意方向）",
    "data/references/tiangan_dizhi.txt": "天干地支速查\n甲乙=木 丙丁=火 戊己=土 庚辛=金 壬癸=水",
    "tools/converters/lunar_notes.txt": "农历转换注意:\n- 节气换月，非初一\n- 23点后算次日子时",
    "admin/billing/invoice_march.txt": "3月发票记录\n客户A: 排盘服务 ¥500\n客户B: 姓名分析 ¥300",
    "admin/logs/system_log_2025.txt": "系统日志\n2025-01-15: 新增客户档案功能\n2025-02-03: 更新八字算法库",
}

for filepath, content in distractor_files.items():
    full_path = os.path.join(workspace, filepath)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

# THE MAIN TASK INPUT: A client intake form with birth data and proposed name
# The stroke counts are provided (to avoid ambiguity in Chinese character stroke counting)
# Birth: 1988年6月15日 上午10点30分 (solar calendar)
# Name to analyze: 陈思远 (Chen Si Yuan)
# Stroke counts: 陈=7, 思=9, 远=7

client_intake = {
    "client_id": "2025-087",
    "consultant_notes": "新客户，需要完整命理分析报告",
    "personal_info": {
        "surname": "陈",
        "given_name": "思远",
        "birth_year": 1988,
        "birth_month": 6,
        "birth_day": 15,
        "birth_hour": 10,
        "birth_minute": 30,
        "calendar_type": "solar",
        "gender": "male"
    },
    "name_analysis_request": {
        "full_name": "陈思远",
        "surname": "陈",
        "given_name": "思远",
        "stroke_counts": {
            "陈": 7,
            "思": 9,
            "远": 7
        }
    },
    "services_requested": [
        "bazi_reading",
        "five_elements_analysis",
        "name_analysis"
    ],
    "notes": "客户希望了解五行喜忌及姓名是否适合，请给出详细五格数理分析"
}

with open(os.path.join(workspace, "clients/active/2025/client_2025_087_intake.json"), "w", encoding="utf-8") as f:
    json.dump(client_intake, f, ensure_ascii=False, indent=2)

# Add a deliberately confusing/misleading reference file
misleading_ref = """错误参考（已作废）
外格计算旧方法: 总格 - 人格（错误！实际需要+1）
天格旧算法: 直接取姓氏笔画（错误！单姓需+1）
请勿使用此文件中的公式。
"""
with open(os.path.join(workspace, "data/references/DEPRECATED_formula_notes.txt"), "w", encoding="utf-8") as f:
    f.write(misleading_ref)

# Add a partial/wrong bazi example to confuse
wrong_example = """错误八字示例（用于测试）:
1988年6月15日 10:30
错误排法:
年柱: 戊辰 (正确)
月柱: 癸未 (错误! 6月15日应为午月)
日柱: 需要查万年历
时柱: 巳时 (需验证)
"""
with open(os.path.join(workspace, "data/references/bazi_wrong_example.txt"), "w", encoding="utf-8") as f:
    f.write(wrong_example)

print("Workspace initialized successfully.")
print(f"Client intake file created at: clients/active/2025/client_2025_087_intake.json")