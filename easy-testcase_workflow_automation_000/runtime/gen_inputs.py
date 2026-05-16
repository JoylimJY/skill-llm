import os
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# Create deeply nested directory structure with distractor files
dirs = [
    "docs/requirements/v1",
    "docs/requirements/v2",
    "docs/design/ui_mockups",
    "docs/design/flowcharts",
    "src/backend/services",
    "src/backend/models",
    "src/frontend/components",
    "src/frontend/pages",
    "tests/unit",
    "tests/integration",
    "config/env",
    "scripts/deploy",
    "reports/old_testcases",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files
distractors = {
    "docs/requirements/v1/old_prd_draft.txt": """贷款系统旧版PRD（已废弃）
v0.1 初稿，仅供参考。
申请人填写申请表，审批人审批。
注意：此版本已不适用，请参考v2版本。
""",
    "docs/requirements/v2/changelog.md": """# 变更日志
- 2024-01-10: 增加风控节点
- 2024-02-05: 修改金额上限
- 2024-03-01: 新增CFO审批节点
""",
    "docs/design/ui_mockups/login_page.txt": """登录页面设计说明
- 用户名输入框
- 密码输入框（脱敏显示）
- 登录按钮
""",
    "docs/design/flowcharts/old_flow.txt": """旧审批流程图（已废弃）
申请人 -> 部门经理 -> 完成
此流程已被新版本替代。
""",
    "src/backend/services/loan_service.py": """# 贷款服务层（占位）
class LoanService:
    def create_application(self, data):
        pass
    def approve(self, loan_id, approver_id):
        pass
""",
    "src/backend/models/loan.py": """# 数据模型
class LoanApplication:
    id: int
    applicant_name: str
    amount: float
    status: str
""",
    "src/frontend/components/form.vue": """<template>
  <!-- 申请表单组件 -->
</template>
""",
    "src/frontend/pages/dashboard.vue": """<template>
  <!-- 仪表盘页面 -->
</template>
""",
    "tests/unit/test_loan_model.py": """# 单元测试占位
def test_placeholder():
    assert True
""",
    "tests/integration/test_flow.py": """# 集成测试占位
def test_flow_placeholder():
    assert True
""",
    "config/env/dev.yaml": """database:
  host: localhost
  port: 5432
  name: loan_dev
""",
    "config/env/prod.yaml": """database:
  host: db.prod.internal
  port: 5432
  name: loan_prod
""",
    "scripts/deploy/deploy.sh": """#!/bin/bash
echo "Deploying loan system..."
""",
    "reports/old_testcases/legacy_testcases.csv": """ID,Title,Status
TC-001,登录测试,通过
TC-002,提交申请测试,通过
""",
}

for path, content in distractors.items():
    full_path = os.path.join(workspace, path)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

# THE CORE INPUT: A messy, realistic PRD with deliberate ambiguities and conflicts
prd_content = """
# 贷款审批系统 - 需求规格说明书 v2.3

## 项目背景

本系统用于管理企业贷款申请全流程，覆盖从申请人填写申请、多级审批、风控评估到最终放款决策的完整业务链条。

---

## 一、用户角色与权限

| 角色 | 说明 |
|------|------|
| 申请人（Applicant） | 可发起贷款申请、查看自己提交的申请状态、撤回"待审批"状态的申请 |
| 支行经理（BranchManager） | 可查看本支行所有申请、审批（同意/驳回）分配给自己的申请 |
| 风控专员（RiskOfficer） | 可查看全行申请、审批分配给自己的申请；无法看到申请人的身份证号完整信息 |
| 财务总监（CFO） | 仅在申请金额 > 500万时参与审批；可查看所有字段含完整身份证号 |
| 系统管理员（Admin） | 可查看所有申请、可强制终止流程，但不参与审批 |

---

## 二、申请表单字段定义

### 2.1 基本信息模块

| 字段名 | 控件类型 | 必填 | 规则说明 |
|--------|----------|------|----------|
| 申请人姓名 | 文本输入框 | 是 | 2~10个汉字，不允许输入英文、数字、特殊字符 |
| 身份证号 | 文本输入框 | 是 | 标准18位居民身份证格式，末位X大小写均可 |
| 联系电话 | 文本输入框 | 是 | 11位纯数字，必须以1开头 |
| 所属支行 | 下拉选择 | 是 | 从系统预置支行列表选择，不可手动输入 |
| 申请备注 | 文本域 | 否 | 最多500字符，支持中英文及常用标点 |

### 2.2 贷款信息模块

| 字段名 | 控件类型 | 必填 | 规则说明 |
|--------|----------|------|----------|
| 贷款金额 | 数字输入框 | 是 | 整数，最小1万元，最大2000万元，单位：元 |
| 贷款期限 | 下拉选择 | 是 | 枚举值：6个月、12个月、24个月、36个月、60个月 |
| 贷款用途 | 下拉选择 | 是 | 枚举值：经营周转、设备采购、基础建设、其他 |
| 抵押物描述 | 文本域 | 否（当贷款金额 > 100万时必填） | 最多200字符 |
| 企业营业执照编号 | 文本输入框 | 是 | 18位统一社会信用代码格式 |

---

## 三、审批流程定义

### 3.1 流程生命周期（状态机）

```
草稿(Draft) -> 待审批(PendingApproval) -> 支行经理审批(BranchManagerReview)
  -> [金额 <= 500万] 风控审批(RiskReview) -> 审批通过(Approved) -> 放款(Disbursed)
  -> [金额 > 500万] 风控审批(RiskReview) -> CFO审批(CFOReview) -> 审批通过(Approved) -> 放款(Disbursed)

任意节点可驳回(Rejected) 或 申请人可撤回(Withdrawn，仅限PendingApproval状态)
```

### 3.2 驳回规则

- 支行经理驳回：申请返回至"草稿"状态，申请人可修改后重新提交。
- 风控专员驳回：申请返回至"支行经理审批"节点，由支行经理重新审核。（注意：风控驳回后，申请是返回到支行经理节点还是草稿状态，需要确认——PRD另一处写道"所有驳回均返回草稿"，存在冲突。）
- CFO驳回：申请直接进入"已拒绝(Rejected)"终态，不可再提交。

### 3.3 特殊流程规则

- 若支行经理未在3个工作日内审批，系统自动发送催办提醒（邮件+站内信），但不自动流转。
- 申请人撤回后，申请状态变为"已撤回(Withdrawn)"，流程终止，不可再次激活该申请，但可以新建申请。
- 同一申请人同时只能有1个"待审批"或审批中的申请，若已有在途申请则无法提交新申请。（备注：另一处需求说"同一申请人最多可有3个同时在途申请"，与此处冲突。）

---

## 四、页面交互说明

### 4.1 申请表单页

- 用户填写完成后，点击页面右下角"提交审批"按钮。
- 提交前，系统进行前端校验；若校验失败，字段下方显示红色提示文字，按钮保持可点击状态。
- 提交成功后，页面跳转至"我的申请"列表页，列表首行展示新建记录，状态显示为"待审批"。
- 表单支持"保存草稿"功能，点击"保存草稿"按钮后，系统弹出Toast提示"草稿保存成功"，状态为"草稿"。
- 当贷款金额字段值实时变化时，若金额从≤100万变为>100万，"抵押物描述"字段自动从选填变为必填，并在字段标签旁显示红色"*"标记。

### 4.2 审批操作页

- 审批人打开申请详情页，底部显示"同意"和"驳回"两个按钮。
- 点击"驳回"按钮，弹出驳回意见填写框，驳回意见为必填（1~200字符）。
- 驳回意见填写后，点击弹窗内"确认驳回"按钮，完成驳回操作。
- 审批人点击"同意"按钮时，若为最后节点（CFO或风控，视金额而定），显示确认弹窗"确认通过该申请？"，点击确认后状态流转为"审批通过"。
- 重复点击"同意"或"驳回"按钮（防重提交）：第一次点击后按钮变为不可用（灰色禁用态），不可重复提交。

### 4.3 权限隔离

- 申请人只能看到自己提交的申请，不能看到其他申请人的申请列表。
- 风控专员在申请详情页查看时，身份证号显示为"110101********1234"（前6位+****+后4位）。
- CFO可查看完整身份证号。
- 支行经理只能看到本支行的申请，不能跨支行查看。

---

## 五、其他说明

- 系统不支持批量审批，每次只能单笔操作。
- 已放款(Disbursed)的申请不允许任何修改操作。
- 申请备注字段：系统需要校验500字符限制，同时另一处接口文档标注最大长度为255字节（UTF-8编码汉字占3字节），存在冲突，待确认。
"""

prd_path = os.path.join(workspace, "docs/requirements/v2/loan_approval_prd_v2.3.txt")
with open(prd_path, "w", encoding="utf-8") as f:
    f.write(prd_content)

print("Workspace generated successfully.")
print(f"PRD file: {prd_path}")