import os
import json
import random

random.seed(42)

workspace = "/workspace"

# Create a realistic project directory structure with distractor files
dirs = [
    "memo-collect/src",
    "memo-collect/dist",
    "memo-collect/tests",
    "memo-collect/node_modules/.cache",
    "memo-collect/node_modules/commander/lib",
    "team-notes/archive",
    "team-notes/drafts",
    "daily-logs/2024-01",
    "daily-logs/2024-02",
    "scripts",
    "config",
]

for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Create the core memo-collect package.json
package_json = {
    "name": "memo-collect",
    "version": "1.0.0",
    "description": "A simple memo-taking skill",
    "main": "dist/index.js",
    "scripts": {
        "build": "tsc",
        "start": "node dist/index.js"
    },
    "dependencies": {}
}
with open(os.path.join(workspace, "memo-collect/package.json"), "w") as f:
    json.dump(package_json, f, indent=2)

# Create tsconfig.json
tsconfig = {
    "compilerOptions": {
        "target": "ES6",
        "module": "commonjs",
        "outDir": "./dist",
        "rootDir": "./src",
        "strict": False,
        "esModuleInterop": True
    },
    "include": ["src/**/*"]
}
with open(os.path.join(workspace, "memo-collect/tsconfig.json"), "w") as f:
    json.dump(tsconfig, f, indent=2)

# Create the TypeScript source file for the memo skill
ts_source = r'''
import * as fs from 'fs';
import * as path from 'path';

const DATA_FILE = path.join(__dirname, '..', 'memos.json');

function loadMemos(): string[] {
    if (!fs.existsSync(DATA_FILE)) {
        return [];
    }
    const raw = fs.readFileSync(DATA_FILE, 'utf-8');
    return JSON.parse(raw);
}

function saveMemos(memos: string[]): void {
    fs.writeFileSync(DATA_FILE, JSON.stringify(memos, null, 2), 'utf-8');
}

const action = process.argv[2];
const content = process.argv[3];

if (action === 'add_memo') {
    const memos = loadMemos();
    memos.push(content);
    saveMemos(memos);
    console.log(`备忘已添加: ${content}`);
} else if (action === 'list_memo') {
    const memos = loadMemos();
    if (memos.length === 0) {
        console.log('暂无备忘记录');
    } else {
        memos.forEach((memo, index) => {
            console.log(`${index + 1}. ${memo}`);
        });
    }
} else if (action === 'delete_memo') {
    const memos = loadMemos();
    const idx = parseInt(content, 10);
    if (isNaN(idx) || idx < 1 || idx > memos.length) {
        console.log('无效的备忘编号');
        process.exit(1);
    }
    const removed = memos.splice(idx - 1, 1);
    saveMemos(memos);
    console.log(`已删除备忘: ${removed[0]}`);
} else {
    console.log('未知操作');
    process.exit(1);
}
'''

with open(os.path.join(workspace, "memo-collect/src/index.ts"), "w") as f:
    f.write(ts_source)

# Create the pre-compiled JavaScript dist/index.js so it works without TypeScript
js_dist = r'''
"use strict";
const fs = require('fs');
const path = require('path');

const DATA_FILE = path.join(__dirname, '..', 'memos.json');

function loadMemos() {
    if (!fs.existsSync(DATA_FILE)) {
        return [];
    }
    const raw = fs.readFileSync(DATA_FILE, 'utf-8');
    return JSON.parse(raw);
}

function saveMemos(memos) {
    fs.writeFileSync(DATA_FILE, JSON.stringify(memos, null, 2), 'utf-8');
}

const action = process.argv[2];
const content = process.argv[3];

if (action === 'add_memo') {
    const memos = loadMemos();
    memos.push(content);
    saveMemos(memos);
    console.log(`备忘已添加: ${content}`);
} else if (action === 'list_memo') {
    const memos = loadMemos();
    if (memos.length === 0) {
        console.log('暂无备忘记录');
    } else {
        memos.forEach((memo, index) => {
            console.log(`${index + 1}. ${memo}`);
        });
    }
} else if (action === 'delete_memo') {
    const memos = loadMemos();
    const idx = parseInt(content, 10);
    if (isNaN(idx) || idx < 1 || idx > memos.length) {
        console.log('无效的备忘编号');
        process.exit(1);
    }
    const removed = memos.splice(idx - 1, 1);
    saveMemos(memos);
    console.log(`已删除备忘: ${removed[0]}`);
} else {
    console.log('未知操作');
    process.exit(1);
}
'''

with open(os.path.join(workspace, "memo-collect/dist/index.js"), "w") as f:
    f.write(js_dist)

# Distractor files to simulate a messy real workspace
distractors = [
    ("team-notes/archive/meeting_2024_01_15.txt", "会议记录：讨论Q1目标，分配任务给各部门负责人。"),
    ("team-notes/archive/meeting_2024_02_03.txt", "会议记录：回顾上月进度，调整排期。"),
    ("team-notes/drafts/weekly_report_draft.txt", "本周工作总结草稿：完成了A、B、C三个功能模块。"),
    ("daily-logs/2024-01/log_jan_10.txt", "今日完成：代码审查3个PR，修复bug #421。"),
    ("daily-logs/2024-01/log_jan_11.txt", "今日完成：部署测试环境，联调接口。"),
    ("daily-logs/2024-02/log_feb_01.txt", "今日完成：需求评审会议，整理用例文档。"),
    ("scripts/backup.sh", "#!/bin/bash\n# backup script placeholder\necho 'backup done'"),
    ("scripts/deploy.sh", "#!/bin/bash\n# deploy script\necho 'deploying...'"),
    ("config/app_config.yaml", "app:\n  name: team-tool\n  version: 2.1.0\n  debug: false"),
    ("config/logging.yaml", "logging:\n  level: INFO\n  format: json\n  output: /var/log/app.log"),
    ("memo-collect/tests/test_memo.txt", "手动测试用例：\n1. 添加备忘测试\n2. 查看备忘测试\n3. 删除备忘测试"),
]

for rel_path, content in distractors:
    full_path = os.path.join(workspace, rel_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

# SKILL.md for the agent to discover
skill_md = """---
name: memo-collect
description: This is a simple skill for note-taking, used to quickly record user notes, and provide users with query, delete, and other capabilities.
---

# Memo Collect Skill

这是一个简单的备忘技能，用于快速记录用户的备忘信息，同时提供给用户查询，删除等能力

## 使用方式

运行：

node dist/index.js <action> <content>

## action 类型

add_memo
添加备忘

示例：
node dist/index.js add_memo "买牛奶"

---

list_memo
查看所有备忘

示例：
node dist/index.js list_memo

---

delete_memo
删除备忘

示例：
node dist/index.js delete_memo 3

---


## Agent 调用规则

如果用户说：

- 记录一下这个内容：XXX
- 帮我将如下信息加入到备忘录：XXX
- 我要记录备忘：XXX

调用：

node dist/index.js add_memo "XXX"

---

如果用户说：

- 查询我已有的备忘
- 查询我的备忘记录
- 查询备忘

调用：

node dist/index.js list_memo

---

如果用户说：

第3条备忘完成了

调用：

node dist/index.js delete_memo 3

---
"""

with open(os.path.join(workspace, "memo-collect/SKILL.md"), "w", encoding="utf-8") as f:
    f.write(skill_md)

print("Workspace generated successfully.")