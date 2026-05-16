# news-aggregator — 指定主体新闻收集

## Skill 描述（description）

触发场景：
- 用户说「搜集 XX 新闻」「帮我看看 XX 最近动态」「收集 XX 相关资讯」「XX 最新消息」「XX 有什么新进展」等
- 定时任务触发新闻收集（cron 场景，通常配合 config/openclaw.yaml）

本 skill 不依赖本地脚本、不执行 exec 命令，全程仅使用 `web_fetch` 和子代理并发抓取。

---

## 执行流程

### Step 0：解析 Target（主体名称）

**优先级从高到低：**

1. **对话输入优先**：从用户最新一条消息中提取主体名称。
   - 示例：「帮我看看 Cursor 最近动态」→ target = `Cursor`
   - 示例：「字节跳动新闻」→ target = `字节跳动`

2. **读取 config 文件**：若对话中未指定主体，尝试读取本 skill 目录下的 `config/openclaw.yaml`（或用户自定义的 yaml 文件）。
   - 读取字段：`target.name`、`target.keywords`、`target.official_urls`

3. **无法确定时**：直接回复用户，请求指定主体名称，不继续执行。

---

### Step 1：推导关键词

从 target 名称生成搜索关键词列表（keywords）：

- 将 `target.name` 本身作为第一个关键词
- 若 config 中有 `keywords` 列表，合并进来（去重）
- 若没有 config，主代理自行推导 2-3 个合理关键词，规则：
  - 英文产品名 → 加常见缩写/全称（如 "Cursor" → ["Cursor", "Cursor IDE"]）
  - 中文公司名 → 加英文名/品牌名（如 "字节跳动" → ["字节跳动", "ByteDance", "抖音"]）
  - 品牌名 → 加主要产品线（如 "OpenAI" → ["OpenAI", "ChatGPT", "GPT-4"]）

---

### Step 2：两路子代理并发执行

**同时**启动以下两路抓取任务（可并发，不需要等待彼此）：

---

#### 路线 A：官网 + 社区抓取

目标：获取第一手官方信息和用户社区声音。

**若 config 中有 `official_urls`：**
- 逐一用 `web_fetch` 抓取这些 URL
- 筛选与 keywords 相关的内容

**若无 config（自动推断）：**
- 尝试以下 URL 模式（`{name}` 替换为主体名称的英文/拼音）：
  - `https://{name}.com/blog`（官方博客）
  - `https://{name}.com/releases`（如能推断）
  - `https://github.com/{name}/{name}/releases`（GitHub releases，如能推断）
  - `https://{name}.com`（官网首页）
- 抓取失败（404/超时）的 URL 跳过，不报错

**关注内容：**
- 产品版本更新、新功能发布
- 官方公告、里程碑
- 用户案例、合作动态
- KOL / 社区评价（如能获取）

---

#### 路线 B：科技媒体搜索

目标：获取科技媒体报道和行业背景。

**固定媒体站点（写死）：**

```
https://36kr.com/search/articles/{keyword}
https://www.huxiu.com/search?s={keyword}
https://sspai.com/search/post/{keyword}
https://www.ifanr.com/?s={keyword}
```

**执行方式：**
1. 用 keywords 中的每个词逐一替换 `{keyword}`，用 `web_fetch` 抓取搜索结果页
2. 提取标题、链接、摘要（抓取失败的跳过）
3. 额外补充行业大词搜索，固定抓取以下 URL（用于获取行业背景）：
   - `https://36kr.com/search/articles/AI%20Agent`
   - `https://36kr.com/search/articles/智能体`
   - `https://www.huxiu.com/search?s=AI+Agent`

**关注内容：**
- 对 target 的直接报道
- 行业趋势、市场动态
- 竞品动态（同赛道其他产品/公司）

---

### Step 3：合并结果，按格式输出

两路子代理完成后，合并所有抓取内容，去重，按以下格式输出：

```markdown
## 🦞 [主体名称] 新闻简报 · [YYYY-MM-DD]

### 一、直接提到 [主体名称] 的新闻
- **[标题]**
  - 来源：[媒体名] | [链接]
  - 摘要：[2-3句核心内容]
  - 为什么值得关注：[1句话]

### 二、用户案例和社区动态
- **[用户/社区/来源]**
  - 玩法描述：[具体用法或场景]
  - 亮点：[1句话]

### 三、行业新闻
- **[标题]**
  - 来源：[媒体名] | [链接]
  - 与 [主体名称] 的关联：[1-2句]

### 四、竞品动态
- **[标题]**
  - 来源：[媒体名]
  - 核心内容：[2-3句]

### 五、今日核心信号（一句话总结）
> [对今日信息的最重要判断，1-2句]
```

**若某类别无内容，写：「暂无相关内容」**

---

## 注意事项

- **不执行任何本地命令**：所有数据均来自 `web_fetch`
- **不读写本地文件**：除读取 config/openclaw.yaml 外，不做任何文件系统操作
- **容错处理**：任何单个 URL 抓取失败（网络超时、404 等），跳过该 URL，不中断整体流程
- **内容筛选**：抓取到的内容较多时，优先保留：时间最新、与 keywords 最相关、信息量最大的条目
- **时效性**：若能判断文章发布时间，优先展示最近 7 天内的内容；若无法判断，展示搜索结果前几条

---

## 示例对话

**用户**：帮我搜一下 Cursor 的最新动态

**执行过程**：
1. target = `Cursor`，推导 keywords = `["Cursor", "Cursor IDE", "AI coding"]`
2. 路线 A：抓取 `https://cursor.com/blog`、`https://cursor.com`
3. 路线 B：抓取 36kr/虎嗅/少数派/爱范儿各 keyword 搜索页
4. 合并输出简报

---

**用户**：（cron 定时触发，无对话内容）

**执行过程**：
1. 无对话输入 → 读取 config/openclaw.yaml
2. target = `OpenClaw`，keywords = `["OpenClaw", "clawd", "ClawHub", "龙虾"]`
3. 路线 A：抓取 config 中的 official_urls
4. 路线 B：搜索媒体站点
5. 合并输出简报
