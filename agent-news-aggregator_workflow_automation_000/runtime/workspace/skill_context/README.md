# news-aggregator

> 让 OpenClaw 帮你持续追踪任意主体（产品、公司、人物）的最新新闻与行业动态，一句话触发，结构化输出。

---

## 这是什么

`news-aggregator` 是一个 OpenClaw AgentSkill，通过多路并发抓取官网、科技媒体（36kr、虎嗅、少数派、爱范儿）等公开页面，将指定主体的最新动态整合为结构化简报。

**特点：**
- 🗣️ 自然语言触发，无需记命令
- 🔍 官网 + 科技媒体双路并发抓取
- 📋 固定输出格式，方便阅读或转发
- ⚙️ 支持 yaml 配置文件，适合定时任务
- 🔒 纯 web_fetch，不执行本地命令，安全透明

---

## 安装方式

### 方式一：通过 ClawHub 安装（推荐）

```bash
npx clawhub@latest install news-aggregator
```

安装完成后，skill 会出现在你的 OpenClaw skills 目录下。

### 方式二：手动复制

将本目录复制到你的 OpenClaw skills 目录：

```
~/.openclaw/workspace/skills/news-aggregator/
```

确保目录结构如下：

```
news-aggregator/
├── SKILL.md
├── config/
│   └── openclaw.yaml
└── README.md
```

---

## 使用方式

### 1. 自然语言触发（最简单）

直接在 OpenClaw 对话中说：

```
帮我搜一下 Cursor 的最新动态
```

```
字节跳动最近有什么新闻？
```

```
收集一下 OpenAI 的相关资讯
```

OpenClaw 会自动识别主体名称，推导关键词，并发抓取后输出结构化简报。

---

### 2. 定时任务（配合 cron）

首先修改 `config/openclaw.yaml`，填入你想关注的主体：

```yaml
target:
  name: "Cursor"
  keywords:
    - "Cursor"
    - "Cursor IDE"
    - "AI coding"
  official_urls:
    - https://cursor.com/blog
    - https://cursor.com/changelog
```

然后在 OpenClaw 中创建定时任务（示例，每天早上 9 点）：

```
帮我每天早上 9 点自动收集一次 config/openclaw.yaml 里配置的主体新闻，发到飞书
```

或通过 cron 配置直接触发 news-aggregator skill。

---

### 3. 自定义 config 文件示例

`config/openclaw.yaml` 完整字段说明：

```yaml
target:
  name: "主体名称"          # 必填，用于输出标题和推导关键词
  keywords:                  # 可选，额外关键词，会与 name 合并搜索
    - "关键词1"
    - "关键词2"
  official_urls:             # 可选，官网/博客/GitHub releases 等直接抓取的 URL
    - https://example.com/blog
    - https://github.com/example/releases
```

- `name` 是唯一必填字段
- 不填 `keywords` 时，agent 会自动推导 2-3 个相关关键词
- 不填 `official_urls` 时，agent 会尝试推断官网地址

---

## 输出格式

每次执行后输出如下结构化简报：

```
## 🦞 [主体名称] 新闻简报 · [日期]

### 一、直接提到 [主体名称] 的新闻
标题、来源、链接、核心摘要、为什么值得关注

### 二、用户案例和社区动态
用户/来源、玩法描述、亮点

### 三、行业新闻
标题、来源、链接、与主体的关联

### 四、竞品动态
标题、来源、核心内容

### 五、今日核心信号（一句话总结）
对当日信息的最重要判断
```

若某类别无内容，会注明「暂无相关内容」。

---

## 数据来源

| 类型 | 来源 |
|------|------|
| 官网/博客 | 由 config 指定或自动推断 |
| 科技媒体 | 36kr、虎嗅、少数派、爱范儿 |
| 行业背景 | 36kr / 虎嗅 AI Agent 相关搜索 |

---

## 安全说明

- ✅ **不含任何个人信息**：无用户名、账号、路径、API key 等私人数据
- ✅ **不执行本地命令**：SKILL.md 中无任何 exec/bash 指令
- ✅ **不操作文件系统**：除读取 config 配置外，不读写任何本地文件
- ✅ **所有 URL 均为公开页面**：仅访问可公开访问的网址
- ✅ **只读操作**：不向任何第三方写入数据

---

## License

MIT

---

## Contributing

欢迎提 Issue 和 PR！如果你有想加入的数据源、输出格式建议，或发现 URL 失效，欢迎反馈。
