import os
import random
import json
import stat

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# Create the standard openclaw skill directory structure
skill_dir = os.path.join(workspace, ".openclaw", "workspace", "skills", "dev-machine-database")
os.makedirs(skill_dir, exist_ok=True)

# Create the SKILL.md referenced in the skill
skill_md_content = """# 开发机数据库查询技能

## 功能
通过 SSH 连接到开发机 (datax)，查询 MySQL 数据库中的 dw 库

## 触发词
- "去草坪上 dw 库看一下"
- "开发机 MySQL 查询"
- "查询 dw 库的 [表名]"
- "草坪上的 MySQL dw 库"
- "datax 数据库查询"

## 配置信息

### 开发机配置
- **主机名**: `datax`
- **工作目录**: `/mnt/www`
- **数据库类型**: MySQL
- **数据库名**: `dw` (可能有多个：`dw`, `dw库`, `data_warehouse` 等)

### 数据库连接
```bash
# 连接方式
ssh datax "mysql -u [用户] -p[密码] [数据库名] -e 'SQL 语句'"

# 或者直接登录
ssh datax "mysql -h localhost -u [用户] -p[密码]"
```

## 使用示例

### 示例 1：查看表列表
**用户：** "去草坪上 dw 库看一下有哪些表"

**执行：**
```bash
ssh datax "mysql -h localhost -u [用户] -p[密码] dw -e 'show tables;'"
```

**回复：** 表列表

---

### 示例 2：查询用户数据
**用户：** "查看 dw 库的 tr_user 有哪些用户"

**执行：**
```bash
ssh datax "mysql -h localhost -u [用户] -p[密码] dw -e 'select * from tr_user limit 50;'"
```

**回复：** 用户列表表格

---

### 示例 3：查询表结构
**用户：** "tr_user 表结构是什么样的"

**执行：**
```bash
ssh datax "mysql -h localhost -u [用户] -p[密码] dw -e 'desc tr_user;'"
```

**回复：** 表结构详情

---

### 示例 4：统计信息
**用户：** "dw 库的 tr_user 表有多少条数据"

**执行：**
```bash
ssh datax "mysql -h localhost -u [用户] -p[密码] dw -e 'select count(*) from tr_user;'"
```

**回复：** 数据统计

---

## 数据库信息

### 可能的数据库名
| 数据库名 | 说明 |
|----------|------|
| `dw` | 数据仓库主库 |
| `dw库` | 中文别名 |
| `data_warehouse` | 英文全称 |
| `sg_alith_sync_fle_tra` | 泰国项目库 |

### 常见表
| 表名 | 说明 |
|------|------|
| `tr_user` | 用户表 |
| `tr_order` | 订单表 |
| `tr_store` | 门店表 |
| `tr_client` | 客户表 |

---

## 执行流程

1. **接收查询指令**
   - 解析用户意图
   - 提取数据库名、表名、查询条件

2. **构建 SQL 语句**
   - 根据意图生成对应 SQL
   - 添加 LIMIT 限制（默认 50 条）

3. **SSH 执行**
   - 连接到 datax 开发机
   - 执行 MySQL 查询
   - 获取结果

4. **格式化输出**
   - 表格形式展示
   - 添加统计信息
   - 发送到飞书

---

## 安全注意事项

1. **只读操作** - 只执行 SELECT 查询，不执行 INSERT/UPDATE/DELETE
2. **LIMIT 限制** - 默认 LIMIT 50，避免大数据量
3. **密码保护** - MySQL 密码不输出到日志
4. **权限控制** - 只查询授权的数据库和表

---

## 相关文件

- 技能位置：`~/.openclaw/workspace/skills/dev-machine-database/SKILL.md`
- 脚本位置：`~/.openclaw/workspace/skills/dev-machine-database/query_db.py`
- 配置位置：`~/.openclaw/workspace/TOOLS.md` (开发机配置)
"""

with open(os.path.join(skill_dir, "SKILL.md"), "w", encoding="utf-8") as f:
    f.write(skill_md_content)

# Create the query_db.py script referenced in SKILL.md
query_db_py = """#!/usr/bin/env python3
\"\"\"
开发机数据库查询脚本
Usage: python3 query_db.py <table_name> [sql_override]
Connects via SSH to datax and queries the dw database.
\"\"\"
import subprocess
import sys
import json
import os

DATAX_HOST = "datax"
DB_NAME = "dw"
DB_USER = "dwuser"
DB_PASS = "Dw@2024Secure!"
DEFAULT_LIMIT = 50

def run_query(sql, output_file=None):
    cmd = f'ssh {DATAX_HOST} "mysql -h localhost -u {DB_USER} -p{DB_PASS} {DB_NAME} -e \\'{sql}\\' --batch --skip-column-names"'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}", file=sys.stderr)
        sys.exit(1)
    return result.stdout

def get_table_count(table):
    out = run_query(f"SELECT COUNT(*) FROM {table};")
    return int(out.strip())

def get_table_data(table, limit=DEFAULT_LIMIT):
    out = run_query(f"SELECT * FROM {table} LIMIT {limit};")
    return out.strip()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 query_db.py <table_name>")
        sys.exit(1)
    table = sys.argv[1]
    data = get_table_data(table)
    print(data)
"""

with open(os.path.join(skill_dir, "query_db.py"), "w") as f:
    f.write(query_db_py)
os.chmod(os.path.join(skill_dir, "query_db.py"), 0o755)

# Create TOOLS.md with connection config
tools_dir = os.path.join(workspace, ".openclaw", "workspace")
tools_md = """# TOOLS.md - 工具配置

## 开发机配置

### datax 开发机
- **主机**: datax (SSH别名，见 ~/.ssh/config)
- **用户**: devuser
- **工作目录**: /mnt/www
- **MySQL 用户**: dwuser
- **MySQL 密码**: Dw@2024Secure!
- **目标数据库**: dw

### SSH 配置参考
```
Host datax
    HostName localhost
    User devuser
    Port 2222
    StrictHostKeyChecking no
```

## 数据库说明
主要操作 dw 数据库，包含以下核心表：
- tr_user: 用户主数据
- tr_order: 订单流水
- tr_store: 门店信息
- tr_client: 客户档案
"""

with open(os.path.join(tools_dir, "TOOLS.md"), "w", encoding="utf-8") as f:
    f.write(tools_md)

# Create distractor files to test contextual awareness
distractor_dirs = [
    os.path.join(workspace, "projects", "retail_analytics"),
    os.path.join(workspace, "projects", "data_pipeline"),
    os.path.join(workspace, "logs", "query_logs"),
    os.path.join(workspace, "config", "database"),
    os.path.join(workspace, "reports", "old"),
    os.path.join(workspace, "scripts", "etl"),
    os.path.join(workspace, ".openclaw", "workspace", "skills", "feishu-notify"),
    os.path.join(workspace, ".openclaw", "workspace", "skills", "file-manager"),
]

for d in distractor_dirs:
    os.makedirs(d, exist_ok=True)

# Distractor 1: Old query report (wrong format, agent should NOT just copy this)
old_report = {
    "generated_at": "2024-01-15",
    "database": "data_warehouse",  # WRONG db name - distractor
    "tables": {
        "users": {"count": 999, "sample": []},  # Wrong table name
        "orders": {"count": 888, "sample": []}   # Wrong table name
    }
}
with open(os.path.join(workspace, "reports", "old", "db_report_2024.json"), "w") as f:
    json.dump(old_report, f, indent=2)

# Distractor 2: Wrong connection config
wrong_config = {
    "host": "192.168.1.100",  # Wrong - should be datax
    "port": 3306,
    "database": "warehouse_prod",  # Wrong database
    "user": "admin"
}
with open(os.path.join(workspace, "config", "database", "prod_config.json"), "w") as f:
    json.dump(wrong_config, f, indent=2)

# Distractor 3: ETL scripts
with open(os.path.join(workspace, "scripts", "etl", "sync_data.sh"), "w") as f:
    f.write("""#!/bin/bash
# Old ETL sync script - connects to staging
mysql -h staging-db -u etluser -petlpass staging_dw -e 'SELECT * FROM users LIMIT 100;'
""")

# Distractor 4: Log files with noise
for i in range(5):
    with open(os.path.join(workspace, "logs", "query_logs", f"query_{i:04d}.log"), "w") as f:
        f.write(f"[2024-{i+1:02d}-01] Query executed on data_warehouse db\n")
        f.write(f"Table: users, rows: {random.randint(100, 9999)}\n")

# Distractor 5: Feishu skill (unrelated)
feishu_skill = """# 飞书通知技能
发送消息到飞书群组
"""
with open(os.path.join(workspace, ".openclaw", "workspace", "skills", "feishu-notify", "SKILL.md"), "w", encoding="utf-8") as f:
    f.write(feishu_skill)

# Distractor 6: file-manager skill
with open(os.path.join(workspace, ".openclaw", "workspace", "skills", "file-manager", "SKILL.md"), "w", encoding="utf-8") as f:
    f.write("# 文件管理技能\n管理开发机文件系统\n")

# Distractor 7: Retail analytics data (red herring)
with open(os.path.join(workspace, "projects", "retail_analytics", "schema.sql"), "w") as f:
    f.write("""-- Old schema, deprecated
CREATE TABLE customer (id INT, name VARCHAR(100));
CREATE TABLE sale (id INT, amount DECIMAL(10,2));
""")

# Distractor 8: Pipeline config
with open(os.path.join(workspace, "projects", "data_pipeline", "pipeline.yaml"), "w") as f:
    f.write("""pipeline:
  source: sg_alith_sync_fle_tra
  destination: s3://data-lake/
  schedule: daily
""")

# Distractor 9: Another wrong report template
with open(os.path.join(workspace, "reports", "old", "template.json"), "w") as f:
    json.dump({"template": True, "tables": [], "database": "???"}, f)

# Distractor 10: README in retail analytics (misleading)
with open(os.path.join(workspace, "projects", "retail_analytics", "notes.txt"), "w") as f:
    f.write("Note: Use tr_user, tr_order tables from the main DW. Connect via devdb host.\n")

print("Workspace generated successfully.")
print(f"Skill directory: {skill_dir}")
print(f"Workspace root: {workspace}")