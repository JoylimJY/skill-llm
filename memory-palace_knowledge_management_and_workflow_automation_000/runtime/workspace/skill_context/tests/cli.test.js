/**
 * Memory Palace CLI 测试脚本
 * 测试所有 CLI 命令的功能
 */

import { execSync } from 'child_process';
import { randomUUID } from 'crypto';
import { existsSync, rmSync } from 'fs';
import { join } from 'path';

// 测试配置
const CLI_COMMAND = 'node bin/memory-palace.js';
const TEST_WORKSPACE = '/tmp/memory-palace-test-' + Date.now();

// 设置测试环境
process.env.OPENCLAW_WORKSPACE = TEST_WORKSPACE;

console.log('🧪 Memory Palace CLI 测试');
console.log('=========================\n');
console.log(`📁 测试工作区: ${TEST_WORKSPACE}\n`);

let passed = 0;
let failed = 0;

function runCommand(cmd) {
  try {
    const output = execSync(cmd, {
      encoding: 'utf-8',
      env: { ...process.env, OPENCLAW_WORKSPACE: TEST_WORKSPACE }
    });
    return { success: true, output: output.trim() };
  } catch (err) {
    return { success: false, error: err.message, stderr: err.stderr?.trim() };
  }
}

function test(name, fn) {
  process.stdout.write(`Testing: ${name}... `);
  try {
    const result = fn();
    if (result) {
      console.log('✅ PASS');
      passed++;
    } else {
      console.log('❌ FAIL');
      failed++;
    }
  } catch (err) {
    console.log(`❌ FAIL: ${err.message}`);
    failed++;
  }
}

// 测试用例
const tests = [
  // 基础操作
  {
    name: 'write - 写入记忆',
    fn: () => {
      const result = runCommand(`${CLI_COMMAND} write "测试记忆内容" default '["测试"]' 0.5 fact`);
      if (!result.success) return false;
      const data = JSON.parse(result.output);
      return data.id && data.content === '测试记忆内容';
    }
  },
  {
    name: 'list - 列出记忆',
    fn: () => {
      const result = runCommand(`${CLI_COMMAND} list`);
      if (!result.success) return false;
      const data = JSON.parse(result.output);
      return Array.isArray(data);
    }
  },
  {
    name: 'stats - 获取统计',
    fn: () => {
      const result = runCommand(`${CLI_COMMAND} stats`);
      if (!result.success) return false;
      const data = JSON.parse(result.output);
      return data.total !== undefined;
    }
  },
  {
    name: 'search - 搜索记忆',
    fn: () => {
      const result = runCommand(`${CLI_COMMAND} search "测试"`);
      if (!result.success) return false;
      // 搜索可能返回空结果，但应该返回数组
      const data = JSON.parse(result.output);
      return Array.isArray(data);
    }
  },
  {
    name: 'get - 获取单条记忆',
    fn: () => {
      // 先写一条记忆获取 ID
      const writeResult = runCommand(`${CLI_COMMAND} write "获取测试" default '["获取"]' 0.6 fact`);
      if (!writeResult.success) return false;
      const writeData = JSON.parse(writeResult.output);
      const id = writeData.id;
      
      const getResult = runCommand(`${CLI_COMMAND} get ${id}`);
      if (!getResult.success) return false;
      const getData = JSON.parse(getResult.output);
      return getData.content === "获取测试";
    }
  },
  {
    name: 'update - 更新记忆',
    fn: () => {
      // 先写一条记忆
      const writeResult = runCommand(`${CLI_COMMAND} write "原始内容" default '["更新测试"]' 0.5 fact`);
      if (!writeResult.success) return false;
      const writeData = JSON.parse(writeResult.output);
      const id = writeData.id;
      
      // 更新
      const updateResult = runCommand(`${CLI_COMMAND} update ${id} "新内容" '["新标签"]' 0.9`);
      if (!updateResult.success) return false;
      const updateData = JSON.parse(updateResult.output);
      
      // 验证更新
      const getResult = runCommand(`${CLI_COMMAND} get ${id}`);
      const getData = JSON.parse(getResult.output);
      return getData.content === "新内容" && getData.importance === 0.9;
    }
  },
  {
    name: 'delete - 删除记忆',
    fn: () => {
      // 先写一条记忆
      const writeResult = runCommand(`${CLI_COMMAND} write "待删除" default '["删除测试"]' 0.5 fact`);
      if (!writeResult.success) return false;
      const writeData = JSON.parse(writeResult.output);
      const id = writeData.id;
      
      // 删除
      const deleteResult = runCommand(`${CLI_COMMAND} delete ${id}`);
      if (!deleteResult.success) return false;
      
      // 验证删除 - 应该返回 null 或空
      const getResult = runCommand(`${CLI_COMMAND} get ${id}`);
      return getResult.output === 'null' || getResult.output === '';
    }
  },
  // 经验管理
  {
    name: 'record_experience - 记录经验',
    fn: () => {
      const result = runCommand(`${CLI_COMMAND} record_experience "测试经验" "适用场景" "test-source" development`);
      if (!result.success) return false;
      const data = JSON.parse(result.output);
      return data.id && data.content === "测试经验";
    }
  },
  {
    name: 'get_experiences - 获取经验列表',
    fn: () => {
      const result = runCommand(`${CLI_COMMAND} get_experiences`);
      if (!result.success) return false;
      const data = JSON.parse(result.output);
      return Array.isArray(data);
    }
  },
  {
    name: 'verify_experience - 验证经验',
    fn: () => {
      // 先记录一条经验
      const recordResult = runCommand(`${CLI_COMMAND} record_experience "验证测试经验" "验证场景" "verify-source" operations`);
      if (!recordResult.success) return false;
      const recordData = JSON.parse(recordResult.output);
      const id = recordData.id;
      
      // 验证
      const verifyResult = runCommand(`${CLI_COMMAND} verify_experience ${id} true`);
      if (!verifyResult.success) return false;
      const verifyData = JSON.parse(verifyResult.output);
      return verifyData.experienceMeta && verifyData.experienceMeta.verifiedCount >= 1;
    }
  },
  // 帮助命令
  {
    name: 'help - 帮助信息',
    fn: () => {
      const result = runCommand(`${CLI_COMMAND} --help`);
      return result.success && result.output.includes('Memory Palace');
    }
  }
];

// 执行测试
console.log('开始执行测试...\n');

for (const t of tests) {
  test(t.name, t.fn);
}

// 清理测试数据
console.log('\n🧹 清理测试数据...');
if (existsSync(TEST_WORKSPACE)) {
  rmSync(TEST_WORKSPACE, { recursive: true, force: true });
}

// 输出结果
console.log('\n=========================');
console.log(`📊 测试结果: ${passed} 通过, ${failed} 失败`);
console.log('=========================\n');

if (failed > 0) {
  process.exit(1);
} else {
  console.log('🎉 所有测试通过!\n');
  process.exit(0);
}