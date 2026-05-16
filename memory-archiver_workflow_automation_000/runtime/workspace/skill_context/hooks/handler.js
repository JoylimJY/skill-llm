/**
 * Auto Memory Search Hook
 * 
 * 事件：message:received
 * 功能：检测用户消息类型，自动搜索相关记忆并注入上下文
 */

import { exec } from 'child_process';
import { promisify } from 'util';
import * as path from 'path';
import * as fs from 'fs';

const execAsync = promisify(exec);

/**
 * 检测消息类型
 */
function detectMessageType(message) {
  const lowerMsg = message.toLowerCase();
  
  // 疑问类型
  if (/怎么 | 如何 | 为什么 | 什么 | 哪里 | 何时 | 谁 | 哪个 | whether|what|how|why|where|when|who/.test(lowerMsg)) {
    return '疑问';
  }
  
  // 修复类型
  if (/修复|bug|错误 | 问题 | 故障 | 解决|repair|fix|error|issue|debug/.test(lowerMsg)) {
    return '修复';
  }
  
  // 规范类型
  if (/规范 | 规则 | 标准 | 要求 | 必须 | 应该 |spec|standard|rule|require/.test(lowerMsg)) {
    return '规范';
  }
  
  // 特征类型
  if (/特征 | 特点 | 特性 | 特色 |feature|characteristic/.test(lowerMsg)) {
    return '特征';
  }
  
  // 配置类型
  if (/配置 | 设置 | 安装 | 部署 | 环境 |config|setup|install|deploy|environment/.test(lowerMsg)) {
    return '配置';
  }
  
  // 命令类型
  if (/命令 | 指令 | 脚本 | 用法 |example|command|script|usage/.test(lowerMsg)) {
    return '命令';
  }
  
  // 技术类型
  if (/\b(css|html|php|javascript|node|npm|tailwind|vite|thinkphp)\b/i.test(lowerMsg)) {
    return '技术';
  }
  
  return null;
}

/**
 * 提取关键词
 */
function extractKeywords(message) {
  // 提取英文单词
  const enKeywords = message.match(/[A-Za-z0-9_]{2,}/g) || [];
  
  // 提取中文词语（简化：按空格分隔）
  const cnKeywords = message
    .split(/[\s,，.。!?！？;；:：]+/)
    .filter(w => w.length >= 2 && /[\u4e00-\u9fa5]/.test(w));
  
  // 合并并去重，取前 5 个
  const all = [...new Set([...enKeywords, ...cnKeywords])];
  return all.slice(0, 5);
}

/**
 * 搜索记忆
 */
async function searchMemory(message) {
  const homeDir = process.env.HOME || '/root';
  const workspaceDir = path.join(homeDir, '.openclaw', 'workspace');
  // 优先使用技能目录内的脚本，回退到工作区 scripts 目录
  const skillScriptPath = path.join(workspaceDir, 'skills', 'memory-archiver', 'scripts', 'auto-memory-search.sh');
  const fallbackScriptPath = path.join(workspaceDir, 'scripts', 'auto-memory-search.sh');
  const scriptPath = fs.existsSync(skillScriptPath) ? skillScriptPath : fallbackScriptPath;
  
  // 检查脚本是否存在
  if (!fs.existsSync(scriptPath)) {
    console.log('[AutoMemorySearch] 脚本不存在:', scriptPath);
    return null;
  }
  
  try {
    // 执行搜索脚本
    const escapedMessage = message.replace(/"/g, '\\"');
    const { stdout } = await execAsync(`bash "${scriptPath}" "${escapedMessage}"`);
    return stdout.trim() || null;
  } catch (error) {
    console.log('[AutoMemorySearch] 搜索失败:', error.message);
    return null;
  }
}

/**
 * Hook 主函数
 */
const handler = async (event) => {
  console.log(`[AutoMemorySearch] Event received: type=${event.type}, action=${event.action}`);
  
  // 只处理消息事件
  if (event.type !== 'message' || event.action !== 'received') {
    return;
  }
  
  // 新版 API: event.context.content
  const userMessage = event.context?.content || event.message?.text || '';
  
  if (!userMessage) {
    console.log('[AutoMemorySearch] No message content found');
    return;
  }
  
  console.log(`[AutoMemorySearch] Message: ${userMessage.substring(0, 80)}...`);
  
  // 跳过系统消息/cron
  if (userMessage.startsWith('System:') || userMessage.includes('记忆及时写入检查') || userMessage.includes('工作进度检查')) {
    console.log('[AutoMemorySearch] Skipping system/cron message');
    return;
  }
  
  // 1. 检测消息类型
  const msgType = detectMessageType(userMessage);
  
  if (!msgType) {
    console.log('[AutoMemorySearch] No matching type, skipping');
    return;
  }
  
  console.log(`[AutoMemorySearch] 检测到消息类型：${msgType}`);
  
  // 2. 提取关键词
  const keywords = extractKeywords(userMessage);
  console.log(`[AutoMemorySearch] 关键词：${keywords.join(', ')}`);
  
  // 3. 搜索记忆
  const searchResults = await searchMemory(userMessage);
  
  if (!searchResults) {
    console.log('[AutoMemorySearch] 未找到相关记忆');
    return;
  }
  
  // 4. 注入结果 - 通过 event.messages 推送
  const memoryNote = `📚 相关记忆:\n${searchResults}`;
  event.messages.push(memoryNote);
  console.log('[AutoMemorySearch] 记忆已通过 event.messages 注入');
};

export default handler;
