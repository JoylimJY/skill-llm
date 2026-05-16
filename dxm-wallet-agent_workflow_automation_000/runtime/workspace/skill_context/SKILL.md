---
name: dxm-agent-wallet
description: 度小满支付钱包 Skill，处理 SP 服务余额不足/未购买场景：获取商品信息、生成支付二维码并通过飞书发送给用户
---

# 度小满支付钱包 Skill (dxm-agent-wallet)

本 Skill 负责处理所有 SP 服务的**余额不足 / 未购买**场景，统一完成商品信息查询、二维码生成、飞书消息推送和引导话术。

**脚本路径**: `scripts/qrcode.js`（相对于本 skill 目录）

---

## 触发条件

当任意 SP 服务调用返回以下情况时，由调用方 Skill 转交本 Skill 处理：

- 返回 `error: "FORBIDDEN"`
- 返回 `detail` 字段包含"未购买"

> 本 Skill 也可被用户直接触发：「查看充值套餐」「我要充值」「怎么付款」

---

## 输入参数

调用本 Skill 时，调用方需提供：

| 参数 | 说明 | 示例 |
|------|------|------|
| `cliCommand` | 用于查询商品详情的完整命令 | `node scripts/sp-weather-cli.js queryPurchaseDetail` |
| `sender_id` | 当前飞书用户的 open_id | `ou_xxxxxxxx` |

---

## 工作流程

### 第一步：获取商品信息和充值地址

运行调用方提供的 `cliCommand`：

```bash
# 示例（由调用方传入）
node /path/to/sp-weather-cli.js queryPurchaseDetail
```

从返回的 `data` 中提取：
- 商品名称、价格、描述等展示信息
- `payUrl`：充值支付链接

---

### 第二步：生成支付二维码

```bash
node scripts/qrcode.js --save "<payUrl>" 2>&1
```

从命令输出中提取 `fp` 字段，即二维码图片的本地文件路径。

---

### 第三步：通过飞书发送二维码图片

使用 `tools` 工具将二维码图片发送给当前用户：

```javascript
// 发送给当前私聊的用户
tools.message({
  action: "send",
  channel: "feishu",
  target: "${sender_id}",  // 动态获取发送者的 open_id
  message: "充值二维码",
  filePath: fp
})
```

---

### 第四步：输出商品信息并引导用户

1. 将商品信息（名称、价格、描述、套餐内容等）整理后展示给用户
2. 告知用户：

> 「余额不足，请使用微信扫描上方二维码付费后重试」

---

## 调用示例（其他 Skill 如何引入）

在其他 Skill 的 SKILL.md 中，当遇到 `error: "FORBIDDEN"` 时写法如下：

```
- **当返回 `error: "FORBIDDEN"` 或 `detail` 包含"未购买"时**：
  转交 `dxm-agent-wallet` Skill 处理，传入：
  - cliCommand: `node scripts/<xxx>-cli.js queryPurchaseDetail`
  - sender_id: 当前飞书用户 open_id
```

---

## 故障排查

| 现象 | 处理 |
|------|------|
| 二维码图片发送失败 | 检查 `fp` 路径是否有效；确认 qrcode.js 正常执行 |
| `payUrl` 为空 | queryPurchaseDetail 返回异常，告知用户联系客服 |
| 飞书消息发送失败 | 确认 `sender_id` 正确；检查 tools.message 权限 |
