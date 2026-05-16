#!/usr/bin/env node
/**
 * Looking For Someone CLI
 */

const { LookingForSomeone } = require('./index');

const app = new LookingForSomeone();

function main() {
  const args = process.argv.slice(2);
  const command = args[0];

  try {
    switch (command) {
      case 'create':
      case '创建': {
        const info = JSON.parse(args[1] || '{}');
        const result = app.createCase(info);
        console.log(JSON.stringify(result, null, 2));
        break;
      }

      case 'list':
      case '列表': {
        const cases = app.getAllCases();
        console.log(`共 ${cases.length} 个寻人案件:`);
        cases.forEach(c => {
          console.log(`  [${c.status}] ${c.name}，${c.age}岁，失联${c.daysSince}天`);
          console.log(`    最后出现: ${c.lastSeenLocation} (${c.lastSeenDate})`);
          console.log();
        });
        break;
      }

      case 'progress':
      case '进展': {
        const caseId = args[1];
        if (!caseId) {
          console.log('用法: looking-for-someone progress <案件ID>');
          process.exit(1);
        }
        const result = app.getProgress(caseId);
        console.log(JSON.stringify(result, null, 2));
        break;
      }

      case 'clue':
      case '线索': {
        const [caseId, ...contentParts] = args.slice(1);
        const content = contentParts.join(' ');
        if (!caseId || !content) {
          console.log('用法: looking-for-someone clue <案件ID> <线索内容>');
          process.exit(1);
        }
        const result = app.addClue(caseId, {
          type: 'tip',
          content,
          source: 'user'
        });
        console.log(result.message);
        if (result.analysis) {
          console.log('\n分析结果:');
          console.log(`  相关性: ${result.analysis.relevance}`);
          console.log(`  建议: ${result.analysis.actionItems.join('、')}`);
        }
        break;
      }

      case 'poster':
      case '启事': {
        const [caseId, platform = 'general'] = args.slice(1);
        if (!caseId) {
          console.log('用法: looking-for-someone poster <案件ID> [平台]');
          console.log('平台: general, wechat, weibo, douyin, official');
          process.exit(1);
        }
        const result = app.generatePoster(caseId, platform);
        if (result.success) {
          console.log('=== 寻人启事 ===\n');
          console.log(result.content);
          console.log('\n=== 发布建议 ===');
          result.tips.forEach(tip => console.log(`• ${tip}`));
        } else {
          console.log('错误:', result.error);
        }
        break;
      }

      case 'guide':
      case '指南': {
        const guide = app.getSearchGuide();
        console.log('=== 寻人搜索指南 ===\n');
        for (const [key, section] of Object.entries(guide)) {
          console.log(`\n${section.title}`);
          section.items.forEach((item, i) => {
            console.log(`  ${i + 1}. ${item}`);
          });
        }
        break;
      }

      case 'warning':
      case '提醒': {
        console.log('=== 防骗提醒 ===\n');
        app.getScamWarnings().forEach(w => console.log(w));
        break;
      }

      default:
        console.log(`
寻人物助手 - Looking For Someone

用法:
  looking-for-someone create '{"name":"张三","age":30...}'  创建案件
  looking-for-someone list                                    查看所有案件
  looking-for-someone progress <案件ID>                       查看进展
  looking-for-someone clue <案件ID> <线索内容>                添加线索
  looking-for-someone poster <案件ID> [平台]                  生成寻人启事
  looking-for-someone guide                                   搜索指南
  looking-for-someone warning                                 防骗提醒

示例:
  looking-for-someone create '{"name":"张三","age":30,"gender":"男","lastSeenDate":"2024-01-15","lastSeenLocation":"北京市朝阳区"}'
  looking-for-someone poster case_xxx wechat
        `);
    }
  } catch (error) {
    console.error('错误:', error.message);
    process.exit(1);
  }
}

main();
