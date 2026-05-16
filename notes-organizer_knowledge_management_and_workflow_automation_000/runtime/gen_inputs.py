import os
import random

random.seed(42)

workspace = "/workspace"
notes_dir = os.path.join(workspace, "dev_notes")
os.makedirs(notes_dir, exist_ok=True)

# Create a flat, messy collection of markdown notes covering multiple topics
notes = {
    "react_hooks.md": """# React Hooks 入门

React Hooks 是 React 16.8 引入的新特性，允许在函数组件中使用状态和其他 React 特性。

## 常用 Hooks

- `useState`: 状态管理
- `useEffect`: 副作用处理
- `useContext`: 上下文访问
- `useReducer`: 复杂状态管理

Hooks 让我们可以在不写 class 的情况下使用更多的 React 特性。
""",

    "vue3_composition.md": """# Vue 3 Composition API

Composition API 是 Vue 3 中引入的新特性，提供了更灵活的代码组织方式。

## 核心概念

- `setup()` 函数
- `ref` 和 `reactive`
- `computed` 和 `watch`
- 生命周期钩子

与 React Hooks 类似，Composition API 解决了大型组件难以维护的问题。
""",

    "css_flexbox.md": """# CSS Flexbox 布局

Flexbox 是一种现代 CSS 布局模型，用于在容器中排列元素。

## 主要属性

- `display: flex`
- `flex-direction`
- `justify-content`
- `align-items`

配合 CSS Grid 使用，可以实现复杂的响应式布局。
""",

    "css_grid.md": """# CSS Grid 布局

CSS Grid 是二维布局系统，比 Flexbox 更强大。

## 核心概念

- `grid-template-columns`
- `grid-template-rows`
- `grid-gap`
- `grid-area`

CSS Grid 和 Flexbox 经常配合使用完成页面布局。
""",

    "nodejs_express.md": """# Node.js Express 框架

Express 是最流行的 Node.js Web 框架，用于构建 RESTful API。

## 快速开始

```javascript
const express = require('express');
const app = express();
app.get('/', (req, res) => res.send('Hello World'));
app.listen(3000);
```

Express 常与 MongoDB 或 PostgreSQL 配合使用构建后端服务。
""",

    "python_fastapi.md": """# Python FastAPI 框架

FastAPI 是现代、高性能的 Python Web 框架，基于标准 Python 类型提示。

## 特点

- 自动生成 OpenAPI 文档
- 基于 Pydantic 的数据验证
- 异步支持
- 高性能（接近 NodeJS 和 Go）

FastAPI 适合构建微服务和 REST API，可以与 SQLAlchemy 配合使用。
""",

    "mysql_basics.md": """# MySQL 基础

MySQL 是最流行的关系型数据库之一。

## 基本操作

- DDL: CREATE, ALTER, DROP
- DML: INSERT, UPDATE, DELETE, SELECT
- 索引优化
- 事务管理

MySQL 常与 Python FastAPI 或 Node.js Express 配合使用。
""",

    "redis_cache.md": """# Redis 缓存

Redis 是高性能的内存数据库，常用作缓存层。

## 使用场景

- 会话存储
- 缓存数据库查询结果
- 消息队列
- 分布式锁

Redis 通常部署在 MySQL 或 PostgreSQL 前面作为缓存层。
""",

    "docker_basics.md": """# Docker 基础

Docker 是容器化技术，用于打包、分发和运行应用。

## 核心概念

- Image（镜像）
- Container（容器）
- Dockerfile
- Docker Compose

Docker 与 Kubernetes 配合可以实现容器编排。
""",

    "kubernetes_intro.md": """# Kubernetes 入门

Kubernetes（K8s）是容器编排平台，用于自动化部署、扩展和管理容器应用。

## 核心组件

- Pod
- Deployment
- Service
- ConfigMap

K8s 通常与 Docker 配合使用，是现代云原生应用的基础。
""",

    "git_workflow.md": """# Git 工作流

Git 是分布式版本控制系统，常用工作流包括 Git Flow 和 GitHub Flow。

## Git Flow

- main/master 分支
- develop 分支
- feature 分支
- hotfix 分支

良好的 Git 工作流配合 CI/CD 工具可以提高团队协作效率。
""",

    "sorting_algorithms.md": """# 排序算法

常见排序算法的时间复杂度和实现。

## 常用排序

- 冒泡排序: O(n²)
- 快速排序: O(n log n)
- 归并排序: O(n log n)
- 堆排序: O(n log n)

理解排序算法对于编写高性能代码和通过算法面试至关重要。
""",

    "binary_search.md": """# 二分搜索

二分搜索是在有序数组中查找元素的高效算法，时间复杂度 O(log n)。

## 实现要点

- 确保数组已排序
- 正确处理边界条件
- 防止整数溢出

二分搜索是许多排序算法和数据结构（如平衡树）的基础。
""",

    "design_patterns.md": """# 设计模式

设计模式是软件开发中常见问题的可重用解决方案。

## 三大类型

- 创建型：Singleton, Factory, Builder
- 结构型：Adapter, Decorator, Proxy
- 行为型：Observer, Strategy, Command

理解设计模式有助于编写可维护、可扩展的代码。
""",

    "typescript_basics.md": """# TypeScript 基础

TypeScript 是 JavaScript 的超集，添加了静态类型系统。

## 核心特性

- 类型注解
- 接口（Interface）
- 泛型（Generics）
- 枚举（Enum）

TypeScript 与 React 或 Vue 3 配合使用，可以大大提升前端开发的可维护性。
""",
}

# Write all notes flat into the dev_notes directory (messy, unorganized)
for filename, content in notes.items():
    filepath = os.path.join(notes_dir, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

# Also create a couple of stray files in sub-paths to simulate real mess
os.makedirs(os.path.join(notes_dir, "temp"), exist_ok=True)
with open(os.path.join(notes_dir, "temp", "scratch.md"), 'w', encoding='utf-8') as f:
    f.write("# Scratch\n\nTemporary notes, can be deleted.\n")

with open(os.path.join(notes_dir, "temp", "todo.md"), 'w', encoding='utf-8') as f:
    f.write("# TODO\n\n- [ ] Review React hooks\n- [ ] Study K8s\n")

with open(os.path.join(notes_dir, ".gitignore"), 'w', encoding='utf-8') as f:
    f.write("*.tmp\n*.log\n")

print(f"Created {len(notes)} notes in {notes_dir}")
print("Directory structure:")
for root, dirs, files in os.walk(notes_dir):
    level = root.replace(notes_dir, '').count(os.sep)
    indent = ' ' * 2 * level
    print(f'{indent}{os.path.basename(root)}/')
    subindent = ' ' * 2 * (level + 1)
    for file in files:
        print(f'{subindent}{file}')