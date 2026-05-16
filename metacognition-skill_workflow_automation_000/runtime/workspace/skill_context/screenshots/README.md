# 截图准备指南

## 需要准备的截图

### 1. self-state-example.png - SELF_STATE.md 自我状态示例

**内容建议：**
- SELF_STATE.md 文件内容截图
- 显示完整的模板结构
- 包含：当前状态、最近行动、待办承诺、自我反思、羁绊记录
- 清晰的 Markdown 格式

**尺寸：** 1920x1080 或 1280x720

---

### 2. four-questions.png - 元认知核心四问

**内容建议：**
- 显示四个核心问题
- 可以用文本编辑器或终端显示
- 包含问题和示例回答
- 清晰的排版

**尺寸：** 1920x1080 或 1280x720

---

## 截图方法

### 方法 1：查看模板文件截图

```bash
# 查看 SELF_STATE.md 模板
cat templates/SELF_STATE.md

# 查看 HEARTBEAT.md 模板
cat templates/HEARTBEAT.md

# 截图（根据你的系统）
# macOS: Cmd + Shift + 4
# Windows: Win + Shift + S
# Linux: Flameshot 或系统截图工具
```

### 方法 2：使用文本编辑器

1. 用 VSCode 或其他编辑器打开模板文件
2. 调整字体大小和主题
3. 截图

---

## 完成后

将截图文件放入 `screenshots/` 目录：

```
/home/node/.openclaw/workspace/skills/metacognition-skill/screenshots/
├── self-state-example.png
└── four-questions.png
```

然后在 clawhub.json 中确认路径正确。

---

## 临时方案

如果暂时无法截图，可以：
1. 先发布（截图在 clawhub.json 中是可选的）
2. 后续补充截图并更新
