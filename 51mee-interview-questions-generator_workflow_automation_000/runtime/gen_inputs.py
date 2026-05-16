import os
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# Create distractor directory structure
dirs = [
    "hr/archives/2023",
    "hr/archives/2024",
    "hr/templates/old",
    "hr/templates/current",
    "recruiting/pipeline/active",
    "recruiting/pipeline/closed",
    "recruiting/assessments",
    "docs/processes",
    "docs/policies",
    "tools/scripts",
    "tools/configs",
    "candidates/processed",
    "candidates/pending",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files
distractors = {
    "hr/archives/2023/interview_summary_q4.txt": "Quarterly interview summary. 47 candidates processed. Avg score: 3.2/5.",
    "hr/archives/2024/headcount_plan.txt": "2024 Headcount: Engineering +12, Design +3, PM +5.",
    "hr/templates/old/generic_questions_v1.txt": "1. Tell me about yourself.\n2. Why do you want this job?\n3. What are your weaknesses?",
    "hr/templates/current/behavioral_bank.txt": "STAR method questions library. Use these as fallback only.",
    "recruiting/pipeline/active/candidates_list.csv": "id,name,stage\n1,Alice,phone_screen\n2,Bob,technical\n3,Charlie,offer",
    "recruiting/pipeline/closed/2024_hires.txt": "Hired: 3 SWE, 1 PM, 2 DevOps",
    "recruiting/assessments/rubric_template.txt": "Score 1-5. 5=Excellent, 3=Meets expectations, 1=Below.",
    "docs/processes/hiring_process.md": "# Hiring Process\n1. Resume screen\n2. Phone interview\n3. Technical assessment\n4. Onsite\n5. Offer",
    "docs/policies/diversity_policy.txt": "We are an equal opportunity employer.",
    "tools/scripts/resume_parser_legacy.py": "# DEPRECATED - do not use\nimport re\n# old parser code",
    "tools/configs/ats_config.json": '{"ats": "Greenhouse", "pipeline_stages": ["sourced","applied","screen","interview","offer"]}',
    "candidates/processed/template_example.json": '{"name": "Jane Doe", "status": "hired", "role": "SRE"}',
}

for path, content in distractors.items():
    full_path = os.path.join(workspace, path)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

# === THE ACTUAL TASK INPUTS ===

# Messy JD file (realistic, somewhat unstructured)
jd_content = """
职位：高级区块链工程师 / Senior Blockchain Engineer
部门：核心协议组
汇报：首席技术官（CTO）
地点：上海 / 远程

=== 关于我们 ===
NexaChain 是一家专注于 Layer-2 扩容解决方案的 Web3 创业公司，
于2022年成立，已完成 A 轮融资（1500万美元）。

=== 岗位职责 ===
* 设计并实现高性能链上协议，使用 Rust 开发 zkRollup 核心模块
* 编写、审计 Solidity 智能合约（ERC-20/ERC-721/自定义协议）
* 参与 DeFi 协议设计：AMM、借贷协议、流动性池
* 优化 EVM 兼容层性能，降低 Gas 成本
* 与密码学团队协作，集成零知识证明（ZKP）方案
* 代码审查、技术文档编写
* 参与链上治理模块开发（DAO、投票合约）

=== 必要技能（Must Have） ===
- Rust 语言：5年以上，熟悉异步编程（tokio/async-std）
- Solidity：3年以上，有主网部署经验
- 以太坊生态：EVM 原理、EIP 标准、主流工具链（Hardhat/Foundry）
- 密码学基础：哈希函数、椭圆曲线、Merkle 树
- 分布式系统：P2P 网络、共识算法（PoS/PBFT）

=== 加分项（Nice to Have） ===
- ZK-SNARK / ZK-STARK 实现经验（circom/snarkjs/halo2）
- MEV/Flashbots 相关经验
- Move 语言或 Substrate 框架
- 有知名 DeFi 协议贡献（Uniswap、Aave、Compound等）
- 发表过密码学或区块链相关学术论文

=== 要求 ===
- 本科及以上，计算机/数学/密码学相关专业
- 至少5年区块链开发经验，有生产级别主网项目
- 英文读写流利（技术文档/代码注释英文优先）
- 能接受 On-call 值班安排

=== 薪资范围 ===
60-100K RMB/月，股票期权另议

=== 面试流程 ===
简历筛选 → 技术电话 → 代码测试（Rust+Solidity） → 技术终面 → HR面
"""

# Messy resume (realistic, has typos, uneven formatting)
resume_content = """
个人信息
========
姓名：李明远
联系方式: liming_yuan@protonmail.com | +86-138-xxxx-8866
GitHub: github.com/lmingyuan_dev  （主要项目见pinned repos）
博客: lmy.hashnode.dev

教育背景
--------
上海交通大学  2014-2018
计算机科学与技术  工学学士
GPA 3.7/4.0

工作经历
---------
【2021.06 - 至今】 高级区块链工程师 @ MetaVault Protocol（DeFi协议，TVL峰值$8亿）
  - 主导 Solidity 智能合约开发：AMM 核心合约重构，Gas 降低约 23%
  - 用 Rust 实现链下撮合引擎（基于tokio异步框架），QPS > 50,000
  - 参与 zkRollup 预研：调研 StarkWare/zkSync 方案，撰写技术选型报告
  - 独立完成 ERC-4626 Vault 合约及配套测试套件（Foundry）
  - 发现并修复一处重入攻击漏洞（Reentrancy），避免潜在损失约$200万
  - 参与 DAO 治理合约设计，集成 Snapshot 链上投票

【2019.03 - 2021.05】 区块链工程师 @ ChainNode Tech（联盟链/企业级区块链方案）
  - 基于 Hyperledger Fabric 开发企业供应链溯源系统（Go/Java）
  - 研究 Cosmos SDK，参与一条公链的早期开发
  - 学习以太坊合约开发，业余时间完成 CryptoZombies 进阶课程

【2018.07 - 2019.02】 后端工程师（实习+转正） @ 某电商公司（保密）
  - 负责订单服务微服务改造，Java Spring Boot
  - 维护 MySQL / Redis 数据层

技术栈
-------
精通: Rust（6年，tokio/serde/ethers-rs）, Solidity（4年主网经验）, Go
熟悉: Python, JavaScript/TypeScript, C++
工具: Foundry, Hardhat, Truffle（旧）, Tenderly, Slither（安全审计）
链/协议: Ethereum, Arbitrum, Optimism, Polygon, BSC
密码学: 了解 ZK-SNARK 原理（读过 bellman 源码），实操过 circom 简单电路
其他: Docker, Kubernetes, AWS基础, Git

项目经历（开源）
---------
1. rust-evm-tracer: 一个轻量 EVM 执行追踪器，GitHub 320 stars
2. solidity-gas-profiler: Foundry 插件，可视化 Gas 消耗热点
3. mini-amm: Uniswap V2 Solidity 实现+测试（学习项目）

自我评价
--------
- 6年区块链一线开发经验，对以太坊生态有深入理解
- 对密码学和零知识证明有浓厚兴趣，在持续学习 halo2
- 喜欢写技术博客分享知识，注重代码可读性和测试覆盖率
- 英文技术文档读写无障碍
"""

with open(os.path.join(workspace, "jd_senior_blockchain_engineer.txt"), "w", encoding="utf-8") as f:
    f.write(jd_content)

with open(os.path.join(workspace, "resume_li_mingyuan.txt"), "w", encoding="utf-8") as f:
    f.write(resume_content)

# A misleading "old output" example to confuse the agent
old_output_example = """{
  "position": "Junior Frontend Developer",
  "candidate": "王小明",
  "questions": {
    "technical": [
      {"id": 1, "question": "What is CSS flexbox?", "level": "easy"}
    ]
  }
}
"""
with open(os.path.join(workspace, "candidates/processed/old_interview_output_example.json"), "w", encoding="utf-8") as f:
    f.write(old_output_example)

# Another misleading schema file
wrong_schema = """{
  "schema_version": "legacy-1.0",
  "interview": {
    "tech_questions": [],
    "soft_questions": [],
    "score_range": "A/B/C/D"
  }
}"""
with open(os.path.join(workspace, "hr/templates/current/wrong_schema_ignore.json"), "w", encoding="utf-8") as f:
    f.write(wrong_schema)

print("Workspace initialized successfully.")
print(f"Files created in {workspace}")