---
name: looking-for-someone
description: 帮助用户整理失联人员案件信息、记录线索、生成寻人启事、查看寻人进展，并提供搜索指南与防骗提醒。用于用户明确提到寻人、找失联亲友、生成寻人启事、添加线索、查看案件进展、防诈骗提醒等场景。
---

# Looking For Someone

把这个 skill 当作本地寻人辅助工具，不要把它表述成警方系统、实名数据库或自动联网搜索服务。

## 执行原则

- 先确认目标：创建案件、补充线索、生成启事、查看进展，还是获取搜索建议。
- 优先建议用户尽快报警，尤其是涉及未成年人、老人、精神疾病、自伤风险、失联时间较长等高风险场景。
- 不要承诺已接入官方数据库、监控系统或实时社交平台搜索。
- 不要声称已实现加密、图像比对、身份核验等未实现能力。
- 输出寻人启事时，默认谨慎处理住址、身份证号、银行卡号等敏感信息。

## 可用能力

- 创建和查看本地寻人案件
- 添加线索并给出基础分析
- 生成多平台寻人启事文案
- 查看案件进展和下一步建议
- 提供搜索指南
- 输出防骗提醒

## 运行方式

优先使用 CLI：

```bash
node scripts/cli.js 创建 '<案件JSON>'
node scripts/cli.js 列表
node scripts/cli.js 进展 <案件ID>
node scripts/cli.js 线索 <案件ID> <线索内容>
node scripts/cli.js 启事 <案件ID> [general|wechat|weibo|douyin|official]
node scripts/cli.js 指南
node scripts/cli.js 提醒
```

## 建案输入建议

创建案件时，至少包含：

- name
- age
- gender
- lastSeenDate
- lastSeenLocation

可选字段：

- phone
- birthDate
- idNumber
- height
- clothing
- distinguishingFeatures
- circumstances
- possibleDestinations
- familyContacts

字段说明与推荐流程详见 `references/fields-and-workflows.md`。

## 数据边界

- 当前数据保存在本地目录 `~/.openclaw/skills-data/looking-for-someone/`
- 当前版本使用本地 JSON 文件存储案件
- 当前版本**未实现**字段级加密、图片识别、照片比对、联网抓取、实名核验
- 因此输出时必须避免夸大能力，并提醒用户通过警方和官方渠道核验信息
- 隐私与安全边界详见 `references/privacy-and-boundaries.md`

## 结果表述要求

- 把建议表述为“本地整理结果”或“规则型建议”
- 不要把线索分析说成事实判断
- 对高风险案件，优先建议报警和联系官方机构
- 若数据不完整，先引导补充关键信息再生成启事

## 安全要求

遇到以下情况时，优先提醒风险：

- 有人要求付费才提供线索
- 对方要求先转账、先打保证金、先捐款
- 对方索要身份证、银行卡、验证码
- 对方声称是警方却无法提供可核验身份
- 对方要求下载不明 App、打开屏幕共享、点击陌生链接

必要时直接运行：

```bash
node scripts/cli.js 提醒
```

## 测试

运行最小测试：

```bash
node test.js
```

测试应覆盖：

- 创建案件
- 查看列表
- 添加线索
- 生成启事
- 查看进展
- 防骗提醒
