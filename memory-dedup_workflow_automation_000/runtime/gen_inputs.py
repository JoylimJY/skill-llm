#!/usr/bin/env python3
"""
Generates the messy sandbox workspace for the memory deduplication task.
"""
import os
import random
import textwrap
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# ── 1. Create directory structure with distractor files ───────────────────────
dirs = [
    "skills/memory-dedup",
    "skills/summarizer",
    "skills/planner",
    "memory",
    "logs",
    "config",
    "agents/main",
    "agents/worker",
    "projects/agentawaken",
    "projects/neuroboost",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# Distractor files
distractor_files = {
    "skills/summarizer/summarize.mjs": "// summarize skill placeholder\nexport default function summarize(text) { return text.slice(0, 200); }\n",
    "skills/planner/plan.mjs": "// planner skill\nexport default function plan(goal) { return []; }\n",
    "logs/agent-2026-03-01.log": "INFO agent started\nINFO task completed\nWARN memory limit reached\n",
    "logs/agent-2026-02-28.log": "INFO dedup scheduled\nINFO backup created\n",
    "config/settings.json": '{"model": "gpt-4o", "maxTokens": 8192, "memoryPath": "MEMORY.md"}\n',
    "config/cron.json": '[{"name":"memory-dedup-weekly","cron":"0 2 * * 0","tz":"Asia/Shanghai"}]\n',
    "agents/main/agent.mjs": "// main agent entry\nimport dedup from '../../skills/memory-dedup/dedup.mjs';\n",
    "agents/worker/worker.mjs": "// worker agent\nexport default class Worker {}\n",
    "projects/agentawaken/README.md": "# AgentAwaken\nAutonomous agent platform.\n",
    "projects/neuroboost/package.json": '{"name":"neuroboost","version":"5.0.1"}\n',
    ".openclaw/config.json": '{"workspace": "/workspace", "agent": "main"}\n',
}
Path("/workspace/.openclaw").mkdir(parents=True, exist_ok=True)

for rel_path, content in distractor_files.items():
    fp = workspace / rel_path
    fp.parent.mkdir(parents=True, exist_ok=True)
    fp.write_text(content)

# ── 2. Create the messy MEMORY.md ─────────────────────────────────────────────
# Design:
#  - Group A: 3 nearly-identical entries about AgentAwaken website (>0.8 similarity → 2 should be deleted, 1 kept or merged into 1)
#  - Group B: 2 partial-duplicate entries about NeuroBoost v5.0 (0.5-0.8 similarity → merged)
#  - Group C: 3 fragmented sections about AgentAwaken that should aggregate into one
#  - Group D: unique entries that must be preserved unchanged
#  - Group E: a stale task entry that partially overlaps with a completed one

memory_md = textwrap.dedent("""\
# MEMORY.md — Agent Knowledge Base

## 进行中的任务

### [P0] 优先任务
- [P0] NeuroBoost v5.0 发布待重试
- [P1] AgentAwaken 网站上线
- [P2] 数据管道优化 (deadline: 2026-04-01)
- [P0] NeuroBoost v5.0 发布 ✅ 已发布 (2026-02-26)
- [P1] 日志清理脚本 完成

## 项目

### AgentAwaken
- 代码: /root/.openclaw/workspace/agentawaken
- 主要语言: TypeScript

### AgentAwaken 域名
- agentawaken.xyz 待绑定
- DNS 已配置

### AgentAwaken 部署
- 需要 Vercel
- 构建命令: npm run build

### NeuroBoost
- 版本: v5.0.1
- 发布日期: 2026-02-26
- 仓库: /root/.openclaw/workspace/neuroboost

## 网站开发记录

- AgentAwaken 网站开发中
- AgentAwaken 项目进行中
- AgentAwaken 待部署
- AgentAwaken 网站 正在开发

## 技术栈

- 前端: Next.js 14
- 后端: Node.js 20
- 数据库: PostgreSQL 16
- 部署: Vercel

## 已完成

- NeuroBoost v4.9 发布 ✅ (2026-01-15)
- 支付模块集成 ✅ (2026-02-10)
- CI/CD 流水线 ✅ (2026-02-20)

## 备注

- API 密钥存储在 .env 文件中
- 每周日凌晨 2 点运行自动去重
- 联系人: dev@agentawaken.xyz

## 开发日志

- 2026-02-25: NeuroBoost v5.0 构建失败，重试中
- 2026-02-26: NeuroBoost v5.0 构建成功，已发布
- 2026-03-01: AgentAwaken 域名配置完成
- 2026-03-02: AgentAwaken 网站前端框架搭建完成

## 待办

- AgentAwaken 网站开发
- AgentAwaken 部署到 Vercel
- 更新文档
- 代码审查 (PR #42)

## 环境变量

- DATABASE_URL: postgresql://localhost:5432/prod
- NEXT_PUBLIC_API_URL: https://api.agentawaken.xyz
- NODE_ENV: production
""")

(workspace / "MEMORY.md").write_text(memory_md)

# ── 3. Create the dedup.mjs script ────────────────────────────────────────────
# This is the actual tool referenced in SKILL.md.
# It implements Jaccard similarity with the exact thresholds from the skill doc.
dedup_script = textwrap.dedent("""\
#!/usr/bin/env node
/**
 * Memory Deduplication Tool
 * Implements Jaccard similarity for deduplication of MEMORY.md
 * Thresholds: >0.8 = delete, 0.5-0.8 = merge, <0.5 = keep
 */

import fs from 'fs';
import path from 'path';

const MEMORY_PATH = path.join(process.cwd(), 'MEMORY.md');
const BACKUP_DIR = path.join(process.cwd(), 'memory');
const REPORT_PATH = path.join(process.cwd(), 'memory', 'dedup-report.txt');

const args = process.argv.slice(2);
const DRY_RUN = args.includes('--dry-run');
const BACKUP = args.includes('--backup');

function similarity(text1, text2) {
  const words1 = new Set(text1.toLowerCase().split(/\\s+/).filter(w => w.length > 0));
  const words2 = new Set(text2.toLowerCase().split(/\\s+/).filter(w => w.length > 0));
  const intersection = new Set([...words1].filter(x => words2.has(x)));
  const union = new Set([...words1, ...words2]);
  if (union.size === 0) return 0;
  return intersection.size / union.size;
}

function extractBulletItems(content) {
  const lines = content.split('\\n');
  const items = [];
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const trimmed = line.trim();
    if (trimmed.startsWith('- ')) {
      items.push({ index: i, text: trimmed.slice(2), original: line });
    }
  }
  return items;
}

function dedup(content) {
  const lines = content.split('\\n');
  const items = extractBulletItems(content);
  
  const toDelete = new Set();
  const mergeMap = new Map(); // index -> merged text
  const duplicatesFound = [];
  
  for (let i = 0; i < items.length; i++) {
    if (toDelete.has(items[i].index)) continue;
    const group = [items[i]];
    
    for (let j = i + 1; j < items.length; j++) {
      if (toDelete.has(items[j].index)) continue;
      const sim = similarity(items[i].text, items[j].text);
      
      if (sim > 0.8) {
        // Full duplicate - delete j, keep i
        toDelete.add(items[j].index);
        group.push(items[j]);
      } else if (sim >= 0.5) {
        // Partial duplicate - merge into i, delete j
        const mergedText = mergeTexts(
          mergeMap.get(items[i].index) || items[i].text,
          items[j].text
        );
        mergeMap.set(items[i].index, mergedText);
        toDelete.add(items[j].index);
        group.push(items[j]);
      }
    }
    
    if (group.length > 1) {
      duplicatesFound.push(group);
    }
  }
  
  // Apply changes
  const newLines = [];
  let deletedCount = 0;
  let mergedCount = 0;
  
  for (let i = 0; i < lines.length; i++) {
    if (toDelete.has(i)) {
      deletedCount++;
      continue;
    }
    if (mergeMap.has(i)) {
      const indent = lines[i].match(/^(\\s*)/)[1];
      newLines.push(indent + '- ' + mergeMap.get(i));
      mergedCount++;
    } else {
      newLines.push(lines[i]);
    }
  }
  
  return {
    content: newLines.join('\\n'),
    originalCount: items.length,
    deletedCount,
    mergedCount,
    finalCount: items.length - deletedCount,
    duplicatesFound
  };
}

function mergeTexts(text1, text2) {
  // Combine unique words/phrases, keeping the longer/more informative one as base
  const parts1 = text1.split(/[,，]/);
  const parts2 = text2.split(/[,，]/);
  const merged = new Set([...parts1, ...parts2].map(p => p.trim()).filter(p => p.length > 0));
  return [...merged].join(', ');
}

function generateReport(stats, duplicatesFound) {
  const lines = [
    '=== Memory Deduplication Report ===',
    '',
    '📊 统计:',
    `- 原始条目: ${stats.originalCount}`,
    `- 重复条目: ${stats.deletedCount + stats.mergedCount}`,
    `- 合并条目: ${stats.mergedCount}`,
    `- 删除条目: ${stats.deletedCount}`,
    `- 最终条目: ${stats.finalCount}`,
    '',
    '🔍 发现的重复:',
  ];
  
  duplicatesFound.forEach((group, idx) => {
    lines.push(`${idx + 1}. "${group[0].text.slice(0, 40)}" (${group.length} 次)`);
    lines.push(`   → ${group.length > 2 ? '合并为 1 条' : '保留最新版本'}`);
  });
  
  lines.push('');
  if (!DRY_RUN) {
    lines.push('✅ MEMORY.md 已优化');
  } else {
    lines.push('👁️  预览模式 (--dry-run): 文件未修改');
  }
  
  return lines.join('\\n');
}

// Main
const content = fs.readFileSync(MEMORY_PATH, 'utf-8');
const originalLineCount = content.split('\\n').length;
const originalItems = extractBulletItems(content);

console.log(`读取 MEMORY.md (${originalLineCount} 行, ${originalItems.length} 条目)`);

if (BACKUP && !DRY_RUN) {
  const date = new Date().toISOString().slice(0, 10);
  const backupPath = path.join(BACKUP_DIR, `MEMORY-backup-${date}.md`);
  fs.mkdirSync(BACKUP_DIR, { recursive: true });
  fs.writeFileSync(backupPath, content);
  console.log(`💾 备份保存到: ${backupPath}`);
}

const result = dedup(content);
const report = generateReport({
  originalCount: result.originalCount,
  deletedCount: result.deletedCount,
  mergedCount: result.mergedCount,
  finalCount: result.finalCount
}, result.duplicatesFound);

console.log('');
console.log(report);

if (!DRY_RUN) {
  fs.writeFileSync(MEMORY_PATH, result.content);
  fs.mkdirSync(BACKUP_DIR, { recursive: true });
  fs.writeFileSync(REPORT_PATH, report);
  console.log(`📋 报告保存到: ${REPORT_PATH}`);
}
""")

(workspace / "skills/memory-dedup/dedup.mjs").write_text(dedup_script)

print("Workspace generated successfully.")
print(f"MEMORY.md size: {len(memory_md)} bytes")
print(f"Bullet items in MEMORY.md: {memory_md.count(chr(10) + '- ')}")