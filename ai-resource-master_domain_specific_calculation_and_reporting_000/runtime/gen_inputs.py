import os
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# Create deeply nested distractor directory structure
dirs = [
    "/workspace/hospital_data/2023/q1",
    "/workspace/hospital_data/2023/q2",
    "/workspace/hospital_data/2023/q3",
    "/workspace/hospital_data/2024/budget",
    "/workspace/hospital_data/2024/procurement",
    "/workspace/infrastructure/network",
    "/workspace/infrastructure/servers/legacy",
    "/workspace/infrastructure/servers/proposed",
    "/workspace/reports/financial",
    "/workspace/reports/operational",
    "/workspace/ai_project/vendors",
    "/workspace/ai_project/specs",
    "/workspace/ai_project/contracts",
    "/workspace/meeting_notes",
    "/workspace/templates",
]
for d in dirs:
    os.makedirs(d, exist_ok=True)

# Distractor files
distractor_files = {
    "workspace/hospital_data/2023/q1/outpatient_stats.csv": (
        "month,count\nJan,450000\nFeb,420000\nMar,480000\n"
    ),
    "workspace/hospital_data/2023/q2/bed_utilization.txt": (
        "Q2床位利用率报告\n平均床位利用率: 87.3%\n实际开放床位: 1200张\n"
    ),
    "workspace/hospital_data/2023/q3/staff_count.json": (
        '{"doctors": 850, "nurses": 2100, "admin": 430}\n'
    ),
    "workspace/hospital_data/2024/budget/it_budget.txt": (
        "2024年IT预算\n硬件采购: 1200万元\n软件授权: 350万元\n运维: 280万元\n"
    ),
    "workspace/hospital_data/2024/procurement/vendor_list.csv": (
        "vendor,category,contract_value\n华为,服务器,800万\nH3C,网络设备,200万\n联想,终端,150万\n"
    ),
    "workspace/infrastructure/network/topology.txt": (
        "核心交换机: 华为CE6870\n接入层: 华为S5735\n带宽: 万兆骨干\n"
    ),
    "workspace/infrastructure/servers/legacy/old_specs.txt": (
        "旧服务器配置\nCPU: Intel Xeon E5-2680 v4\nRAM: 256GB\nStorage: 10TB SAS\n台数: 12\n"
    ),
    "workspace/infrastructure/servers/proposed/gpu_options.txt": (
        "备选GPU方案\n方案A: NVIDIA A100 80GB\n方案B: 华为Atlas 900\n方案C: 待定\n"
    ),
    "workspace/reports/financial/2024_q1_summary.txt": (
        "2024年Q1财务摘要\n医疗收入: 8500万元\n药品收入: 3200万元\n耗材: 1800万元\n"
    ),
    "workspace/reports/operational/kpi_2024.txt": (
        "2024年运营KPI\n门诊满意度: 92.1%\n住院满意度: 95.3%\n平均住院日: 8.2天\n"
    ),
    "workspace/ai_project/vendors/huawei_quote_draft.txt": (
        "华为AI解决方案报价草案\n版本: Draft v0.3\n注意: 此版本待确认，请勿外发\n基础平台费用: 待议\n"
    ),
    "workspace/ai_project/specs/functional_requirements.txt": (
        "AI系统功能需求规格\n1. 支持多模态输入\n2. 响应时间<3秒\n3. 并发用户数>500\n4. 数据安全等级: 三级\n"
    ),
    "workspace/ai_project/contracts/nda_template.txt": (
        "保密协议模板\n甲方: [医院名称]\n乙方: [供应商名称]\n保密期限: 3年\n"
    ),
    "workspace/meeting_notes/2024_03_15_ai_planning.txt": (
        "2024年3月15日AI规划会议纪要\n出席人员: 院长、信息科主任、临床科室代表\n"
        "讨论议题:\n1. AI应用场景梳理\n2. 供应商选型\n3. 实施时间表\n"
        "决议: 启动AI服务器采购论证\n"
    ),
    "workspace/templates/report_header.txt": (
        "报告抬头模板\n[单位名称]大模型应用算力评估报告\n编制日期: YYYY年MM月DD日\n密级: 内部\n"
    ),
}

for fpath, content in distractor_files.items():
    full_path = os.path.join("/", fpath)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

# THE MAIN PROBLEM INPUT FILE - messy, unstructured, with some noise
# Region: 渝北区 (Yubei District, Chongqing)
# Outpatient: 1200万人次/年
# Inpatient: 45万人次/年
# Scenarios requested (with some using custom coverage, some using defaults):
#   1. 病历生成-门诊 (default 100% outpatient)
#   2. 病历生成-住院 (default 100% inpatient)
#   3. 辅助诊断 (default 100% outpatient)
#   4. 病历质控-门诊 (default 100% outpatient)
#   5. 病历质控-住院 (default 100% inpatient)
#   6. 诊疗推荐-门诊 (default 100% outpatient)
#   7. 诊疗推荐-住院 (default 100% inpatient)
#   8. 导医导诊 (CUSTOM: 25% outpatient, not default 30%)
#   9. 患者画像提取 (default 100% outpatient + 100% inpatient)
#  10. 报告解读-专用 (CUSTOM: 8% outpatient, not default 5%)

input_content = """渝北区人民政府卫生健康局
AI大模型应用建设项目 - 需求调研表
（内部工作文件 v1.2，2024年4月）

=========================================
一、基础医疗服务量数据（来源：2023年统计年鉴）
=========================================

  地区名称:  渝北区
  
  年均门诊诊疗人次:   1200  万人次/年
  
  注：包含社区卫生服务中心数据，已扣除重复就诊
  
  年均住院诊疗人次:  45  万人次/年
  
  备注: 以上数据为全区医疗机构汇总口径
  床位总数参考值: 18500张（仅供参考，不参与算力计算）
  平均住院天数: 9.1天（仅供参考）

=========================================
二、拟部署AI大模型应用场景清单
=========================================

以下场景经院方信息科与临床科室联合论证确认，请据此测算算力需求：

  场景1:  病历生成（门诊）
  场景2:  病历生成（住院）
  场景3:  辅助诊断
  场景4:  病历质控-门诊
  场景5:  病历质控-住院
  场景6:  诊疗推荐（门诊）
  场景7:  诊疗推荐（住院）
  场景8:  导医导诊   [覆盖率调整为25%门诊患者，根据实际使用习惯修正]
  场景9:  患者画像提取
  场景10: 报告解读（专用版）  [本地覆盖率: 8%门诊患者，高于行业默认值]

=========================================
三、GPU选型意向
=========================================

  计划采用华为910B3系列显卡（华为一体机方案）

=========================================
四、其他说明
=========================================

  - 如需总算力数据（P值），请一并列出
  - 本次评估按峰值业务量 × 安全冗余系数1.0计算（即不做额外冗余）
  - 联系人: 信息科 张主任  电话: 023-XXXXXXXX
  - 文件编号: YB-AI-2024-007

=========================================
"""

with open("/workspace/ai_project/specs/yubei_ai_requirements.txt", "w", encoding="utf-8") as f:
    f.write(input_content)

print("Workspace generation complete.")
print("Key input file: /workspace/ai_project/specs/yubei_ai_requirements.txt")