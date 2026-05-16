# OpenClaw 相关新闻收集指南

## 每日定时任务使用，由主代理派子代理执行

---

## 方式一：官网 + 社区页面直接抓取（用户侧口碑、案例、KOL评价）

### 原理
OpenClaw 官网首页嵌入了大量用户真实推文，是最好的口碑聚合页。

### 执行方式
使用 web_fetch 访问以下页面，提取 OpenClaw 相关内容：

1. https://openclaw.ai — 官网首页（用户推文、案例展示）
2. https://openclaw.ai/blog — 官方博客（版本更新、生态动态）
3. https://github.com/openclaw/openclaw/releases — 最新版本发布
4. https://clawhub.com — 技能市场最新动态

### 筛选关键词
OpenClaw、clawd、ClawHub、AI Agent、龙虾、🦞

### 关注角度
- 新的用户案例和酷炫玩法
- KOL/名人背书和评价
- 版本更新和新功能
- 生态合作（大厂入场、技能市场）
- 社区文化和 meme

---

## 方式二：新闻聚合工具 + 科技媒体搜索（行业新闻、竞品动态）

### 步骤1：启动 RSSHub 并全量抓取
```bash
~/.openclaw/workspace/services/rsshub-ctl.sh start
sleep 10
python3 ~/.openclaw/workspace/news_fetcher_v2.py --category all --format json --count 10 2>&1
~/.openclaw/workspace/services/rsshub-ctl.sh stop
```

### 步骤2：从全量新闻中筛选相关内容
筛选关键词：OpenClaw、clawd、AI Agent、AI 代理、AI assistant、Claude Code、Codex、Cursor、AI coding agent、智能体、龙虾

### 步骤3：补充科技媒体搜索
用 web_fetch 访问以下搜索页面：
- https://36kr.com/search/articles/OpenClaw
- https://36kr.com/search/articles/AI%20Agent
- https://www.huxiu.com/search?s=AI+Agent
- https://www.huxiu.com/search?s=OpenClaw
- https://sspai.com/search/post/AI%20Agent
- https://www.ifanr.com/?s=AI+Agent
- https://www.ifanr.com/?s=OpenClaw

### 关注角度
- 直接提到 OpenClaw 的报道
- AI Agent 行业趋势和深度分析
- 竞品动态（Claude Code、Codex、Cursor 等）
- 大厂 AI Agent 布局
- 用户使用偏好调查

---

## 输出格式要求

按以下结构整理结果：

### 一、直接提到 OpenClaw 的新闻
每条：标题、来源、链接、核心摘要、为什么值得关注

### 二、用户案例和社区动态
每条：用户/来源、玩法描述、FOMO 点

### 三、AI Agent 行业新闻
每条：标题、来源、链接、与 OpenClaw 的关联

### 四、竞品动态
每条：标题、来源、核心内容

### 五、今日核心信号（一句话总结）
