import os
import json
import textwrap
from pathlib import Path

WORKSPACE = Path("/workspace")

# ── directory structure ──────────────────────────────────────────────────────
dirs = [
    "scripts",
    "scripts/utils",
    "references",
    "output",
    "output/archive",
    "logs",
    "docs/internal",
    "docs/specs",
    "tests",
    "tests/fixtures",
    "data/raw",
    "data/processed",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# ── SKILL.md ─────────────────────────────────────────────────────────────────
(WORKSPACE / "SKILL.md").write_text(textwrap.dedent("""\
    ---
    name: langextract-search
    description: 集成智谱搜索、DuckDuckGo 搜索和多模型结构化提取的完整工作流。
    license: Apache-2.0
    ---

    # LangExtract Search Skill

    集成智谱搜索 + DuckDuckGo 搜索 + 多模型结构化提取的完整工作流。

    ## 功能特性

    - 🔍 **智谱 AI 搜索**: 使用智谱 zai-sdk 进行网络搜索
    - 🌐 **DuckDuckGo 搜索**: 备用搜索引擎（支持多后端：Bing/Google/Brave 等）
    - 📝 **多模型提取**: 支持 OpenAI 通用协议
    - 🔄 **完整工作流**: 搜索 → 提取 → 保存，一键完成
    - ⚙️ **灵活配置**: 支持时间过滤、地区设置、代理等高级参数

    ## 前置条件

    1. Python 3.8+
    2. **ddgs**（DuckDuckGo 搜索库）
    3. **requests**（HTTP 请求库）
    4. 可选：配置 langextract 处理模型

    ## 安装

    ```bash
    pip install requests ddgs langextract
    ```

    参考 `conf.json.example` 配置模型

    ### 首次使用交互选择

    如果未在 `openclaw.json` 中配置 `baseUrl`，首次运行时会自动提示选择套餐类型，选择结果保存到项目 `conf.json` 文件中。

    ## 快速开始

    ```bash
    cd scripts
    python search.py "搜索关键词" --verbose
    ```

    ## 使用方法

    ### 基本用法

    ```bash
    python search.py "搜索关键词"
    ```

    ### 验证输入输出（详细模式）

    ```bash
    python search.py "搜索关键词" --verbose
    ```

    ### 保存完整 JSON

    ```bash
    python search.py "搜索关键词" --save-json
    ```

    ### 自定义 DuckDuckGo 结果数量

    ```bash
    python search.py "搜索关键词" --ddg-max-results 30
    ```

    ### 所有选项

    ```bash
    python search.py --help
    ```

    ## 搜索配置

    搜索参数通过 `conf.json` 配置。默认配置开箱即用，无需额外设置。

    ### 默认配置（自动应用）

    | 搜索引擎   | 默认结果数 | 时间过滤 | 其他            |
    | ---------- | ---------- | -------- | --------------- |
    | 智谱搜索   | 15 条      | 不限     | search_pro 引擎 |
    | DuckDuckGo | 20 条      | 不限     | 自动选择后端    |

    ### 自定义配置

    当默认配置不满足需求时（如需要时间过滤、地区设置、代理等），请参阅 **[references/search-params.md](references/search-params.md)** 获取完整参数说明。

    常见自定义场景：

    - 搜索最近一周/一月的内容：设置 `timelimit: "week"` 或 `"month"`
    - 限定搜索地区：设置 `region: "cn-zh"` 或 `"us-en"`
    - 使用代理访问：设置 `proxy: "http://127.0.0.1:7890"`
    - 切换搜索后端：设置 `backend: "google"` 或 `"bing,google"`

    ## 更多信息

    工作流详细说明、输出文件格式和故障排除，请参阅 **[references/workflow-details.md](references/workflow-details.md)**。
"""))

# ── references/search-params.md ──────────────────────────────────────────────
(WORKSPACE / "references" / "search-params.md").write_text(textwrap.dedent("""\
    # 搜索参数配置详解

    本文档详细说明 `conf.json` 中搜索相关的配置参数。当默认配置无法满足需求时，参考此文档进行自定义配置。

    ## 智谱 AI 搜索配置 (zhipu_search)

    ### 基础配置

    | 参数 | 类型 | 默认值 | 必填 | 说明 |
    |------|------|--------|------|------|
    | `enabled` | boolean | `true` | 否 | 是否启用智谱搜索 |
    | `apiKey` | string | - | 是 | API Key（支持环境变量名或实际密钥） |

    ### 搜索引擎 (search_engine)

    | 值 | 说明 | 特点 |
    |----|------|------|
    | `search_std` | 智谱基础版搜索引擎 | 支持全部参数 |
    | `search_pro` | 智谱高阶版搜索引擎（默认） | 支持全部参数，效果更好 |
    | `search_pro_sogou` | 搜狗搜索 | count 仅支持 10/20/30/40/50 |
    | `search_pro_quark` | 夸克搜索 | 仅支持 timelimit、content_size |

    ### 结果数量 (count)

    - **类型**: number
    - **范围**: 1-50
    - **默认值**: 15
    - **说明**: 返回搜索结果的数量。数量越大，消耗的 token 越多。

    ### 时间过滤 (timelimit)

    统一格式，自动映射到智谱原生格式：

    | 配置值 | 智谱原生值 | 说明 |
    |--------|-----------|------|
    | `day` | `oneDay` | 一天内 |
    | `week` | `oneWeek` | 一周内 |
    | `month` | `oneMonth` | 一个月内 |
    | `year` | `oneYear` | 一年内 |
    | `null` | `noLimit` | 不限时间（默认） |

    ### 内容长度 (content_size)

    | 值 | 说明 |
    |----|------|
    | `medium` | 返回摘要信息，满足基础推理需求 |
    | `high` | 最大化上下文，信息量大，适合需要细节的场景（默认） |

    ### 域名过滤 (search_domain_filter)

    - **类型**: string | null
    - **默认值**: null
    - **示例**: `"www.example.com"`
    - **说明**: 限定搜索结果只来自指定域名，null 表示不限制

    ---

    ## DuckDuckGo 搜索配置 (duckduckgo_search)

    ### 基础配置

    | 参数 | 类型 | 默认值 | 说明 |
    |------|------|--------|------|
    | `enabled` | boolean | `true` | 是否启用 DuckDuckGo 搜索 |
    | `maxResults` | number | `20` | 返回结果数量 |
    | `timeout` | number | `10` | 请求超时（秒） |

    ### 地区代码 (region)

    | 代码 | 地区 |
    |------|------|
    | `cn-zh` | 中国 |
    | `us-en` | 美国 |
    | `uk-en` | 英国 |
    | `jp-jp` | 日本 |
    | `kr-kr` | 韩国 |
    | `de-de` | 德国 |
    | `fr-fr` | 法国 |
    | `ru-ru` | 俄罗斯 |
    | `wt-wt` | 无地区限制（默认） |

    ### 安全搜索 (safesearch)

    | 值 | 说明 |
    |----|------|
    | `on` | 严格过滤成人内容 |
    | `moderate` | 适度过滤（默认） |
    | `off` | 不过滤 |

    ### 时间过滤 (timelimit)

    统一格式，自动映射到 DDGS 原生格式：

    | 配置值 | DDGS 原生值 | 说明 |
    |--------|------------|------|
    | `day` | `d` | 一天内 |
    | `week` | `w` | 一周内 |
    | `month` | `m` | 一个月内 |
    | `year` | `y` | 一年内 |
    | `null` | `None` | 不限时间（默认） |

    ### 搜索后端 (backend)

    | 值 | 说明 |
    |----|------|
    | `auto` | 自动选择最佳引擎（默认） |
    | `bing` | 使用 Bing 搜索 |
    | `google` | 使用 Google 搜索 |
    | `duckduckgo` | 使用 DuckDuckGo 搜索 |
    | `brave` | 使用 Brave 搜索 |
    | `yandex` | 使用 Yandex 搜索 |
    | `yahoo` | 使用 Yahoo 搜索 |
    | `wikipedia` | 使用 Wikipedia |

    可组合多个后端：`"bing,google,duckduckgo"`

    ### 代理设置 (proxy)

    - **类型**: string | null
    - **默认值**: null
    - **示例**:
      - `"http://127.0.0.1:7890"` - HTTP 代理
      - `"socks5://127.0.0.1:1080"` - SOCKS5 代理
      - `"tb"` - Tor Browser（等同于 `socks5://127.0.0.1:9150`）

    ---

    ## DuckDuckGo 搜索运算符

    在搜索查询中可以使用以下运算符：

    | 运算符 | 示例 | 说明 |
    |--------|------|------|
    | 空格 | `cats dogs` | OR 搜索 |
    | 引号 | `"cats and dogs"` | 精确匹配 |
    | `-` | `cats -dogs` | 排除词 |
    | `+` | `cats +dogs` | 强调词 |
    | `filetype:` | `cats filetype:pdf` | 文件类型（pdf/doc/xls/ppt/html） |
    | `site:` | `dogs site:example.com` | 指定站点 |
    | `-site:` | `cats -site:example.com` | 排除站点 |
    | `intitle:` | `intitle:dogs` | 标题包含 |
    | `inurl:` | `inurl:cats` | URL 包含 |

    ---

    ## 配置示例

    ### 最小配置（使用默认值）

    ```json
    {
      "zhipu_search": {
        "enabled": true,
        "apiKey": "YOUR_API_KEY"
      },
      "duckduckgo_search": {
        "enabled": true
      }
    }
    ```

    ### 完整配置

    ```json
    {
      "zhipu_search": {
        "enabled": true,
        "apiKey": "ZHIPU_SEARCH_API_KEY",
        "search_engine": "search_pro",
        "count": 15,
        "timelimit": null,
        "content_size": "high",
        "search_domain_filter": null
      },
      "duckduckgo_search": {
        "enabled": true,
        "maxResults": 20,
        "region": "wt-wt",
        "safesearch": "moderate",
        "timelimit": null,
        "backend": "auto",
        "proxy": null,
        "timeout": 10
      }
    }
    ```

    ### 只搜索最近一周的中文结果

    ```json
    {
      "zhipu_search": {
        "enabled": true,
        "apiKey": "YOUR_API_KEY",
        "timelimit": "week"
      },
      "duckduckgo_search": {
        "enabled": true,
        "region": "cn-zh",
        "timelimit": "week"
      }
    }
    ```

    ### 使用代理访问

    ```json
    {
      "duckduckgo_search": {
        "enabled": true,
        "proxy": "http://127.0.0.1:7890",
        "timeout": 30
      }
    }
    ```
"""))

# ── references/workflow-details.md ───────────────────────────────────────────
(WORKSPACE / "references" / "workflow-details.md").write_text(textwrap.dedent("""\
    # 工作流详细说明

    本文档详细说明搜索工作流的各个步骤、输出文件格式和故障排除方法。

    ## 工作流说明

    ### 步骤 1: 智谱 AI 搜索

    **工具**: `zai-sdk` (智谱 AI 官方 Python SDK)

    **输入**:
    - 搜索查询
    - 搜索引擎（search_pro/search_std/search_pro_sogou/search_pro_quark）
    - 最大结果数（1-50，默认 15）
    - 时间过滤（day/week/month/year/null）
    - 内容长度（medium/high）

    **输出**:
    - 搜索结果列表，每条包含：
      - title: 网页标题
      - link: 网页 URL
      - content: 内容摘要
      - media: 来源媒体
      - publish_date: 发布日期

    ### 步骤 2: DuckDuckGo 搜索

    **工具**: `ddgs` (Python 元搜索库)

    **输入**:
    - 搜索查询
    - 最大结果数（默认 20，可配置）
    - 地区代码（cn-zh/us-en/wt-wt 等）
    - 安全搜索级别（on/moderate/off）
    - 时间过滤（day/week/month/year）
    - 搜索后端（auto/bing/google/duckduckgo 等）

    **输出**:
    - 搜索结果列表，每条包含：
      - title: 网页标题
      - href: 网页 URL
      - body: 网页摘要

    ### 步骤 3: LangExtract 结构化提取

    **工具**: [langextract](https://github.com/google/langextract)（Google LLM 结构化提取库）

    **后端模型**: 可配置，默认 `doubao-seed-2-0-code`（火山引擎 ARK）

    **输入**:
    - 搜索结果合并内容（智谱 + DuckDuckGo）

    **输出**:
    - 结构化信息，包含：
      1. 主要内容摘要
      2. 关键点列表（3-5个）
      3. 相关事实或数据
      4. 来源或参考信息

    ---

    ## 输出文件

    运行后会在 `output/` 目录生成：

    | 文件名 | 说明 |
    |--------|------|
    | `zhipu_search_result_YYYYMMDD_HHMMSS.md` | 智谱 AI 搜索结果 |
    | `duckduckgo_search_result_YYYYMMDD_HHMMSS.md` | DuckDuckGo 搜索结果 |
    | `extracted_info_YYYYMMDD_HHMMSS.md` | 提取的结构化信息 |
    | `workflow_summary_YYYYMMDD_HHMMSS.md` | 工作流摘要 |
    | `full_results_YYYYMMDD_HHMMSS.json` | 完整 JSON 结果（需 `--save-json`） |

    ---

    ## 故障排除

    ### 智谱搜索失败

    - 检查 API Key 是否有效
    - 确认 `conf.json` 中 `zhipu_search.apiKey` 配置正确
    - 检查网络是否能访问 `open.bigmodel.cn`

    ### DuckDuckGo 搜索失败

    - 确保已安装 `ddgs` 库：`pip install ddgs`
    - 检查网络连接
    - 尝试配置代理：参阅 [search-params.md](search-params.md#代理设置-proxy)
    - 尝试切换搜索后端：设置 `backend: "bing"` 或 `"google"`

    ### 搜索结果为空

    - 尝试使用更通用的关键词
    - 检查时间过滤是否过于严格
    - 尝试切换搜索引擎或后端

    ### 提取失败

    - 检查 API Key 是否有效
    - 确认模型可访问
    - 查看 `--verbose` 输出了解详细错误
    - 确认 `~/.openclaw/openclaw.json` 配置正确
    - 检查搜索结果是否过长导致超出模型上下文限制
"""))

# ── conf.json.example  (intentionally partial / misleading) ──────────────────
# This is a CORRUPTED example that uses wrong field names and native values
# instead of the unified format — the agent must NOT just copy this.
corrupt_example = {
    "_comment": "EXAMPLE ONLY - DO NOT USE DIRECTLY. Field names and values may be outdated.",
    "zhipu_search": {
        "enabled": True,
        "apiKey": "YOUR_ZHIPU_API_KEY_HERE",
        "search_engine": "search_pro",
        "count": 25,                   # WRONG: 25 is not valid for search_pro_sogou
        "timelimit": "oneMonth",       # WRONG: should use unified "month" not native "oneMonth"
        "content_size": "high",
        "search_domain_filter": None
    },
    "duckduckgo_search": {
        "enabled": True,
        "maxResults": 20,
        "region": "wt-wt",
        "safesearch": "moderate",
        "timelimit": "m",              # WRONG: should use unified "month" not native "m"
        "backend": "bing",             # WRONG: should be "bing,google" for multi-backend
        "proxy": None,
        "timeout": 10
    }
}
(WORKSPACE / "conf.json.example").write_text(
    json.dumps(corrupt_example, indent=2, ensure_ascii=False)
)

# ── distractor files ──────────────────────────────────────────────────────────
(WORKSPACE / "scripts" / "search.py").write_text(textwrap.dedent("""\
    #!/usr/bin/env python3
    # search.py - Main search workflow script (placeholder)
    # Reads conf.json for configuration
    import sys
    import json
    from pathlib import Path

    def main():
        conf_path = Path(__file__).parent.parent / "conf.json"
        if not conf_path.exists():
            print("ERROR: conf.json not found", file=sys.stderr)
            sys.exit(1)
        with open(conf_path) as f:
            conf = json.load(f)
        print("Configuration loaded successfully.")
        print(f"Zhipu engine: {conf.get('zhipu_search', {}).get('search_engine')}")
        print(f"DDG backend: {conf.get('duckduckgo_search', {}).get('backend')}")

    if __name__ == "__main__":
        main()
"""))

(WORKSPACE / "scripts" / "utils" / "helpers.py").write_text(
    "# Utility helpers for search workflow\n"
)

(WORKSPACE / "scripts" / "utils" / "formatters.py").write_text(
    "# Output formatting utilities\ndef format_results(results): return results\n"
)

(WORKSPACE / "logs" / "search_20240101_120000.log").write_text(
    "2024-01-01 12:00:00 INFO Search completed successfully\n"
    "2024-01-01 12:00:01 INFO Results saved to output/\n"
)

(WORKSPACE / "logs" / "error_20240115.log").write_text(
    "2024-01-15 09:30:00 ERROR API key invalid\n"
    "2024-01-15 09:30:01 ERROR zhipu search failed\n"
)

(WORKSPACE / "docs" / "internal" / "project_brief.md").write_text(textwrap.dedent("""\
    # Project Brief: Competitive Intelligence Automation

    ## Objective
    Automate weekly search briefings for the consumer electronics market intelligence team.

    ## Requirements
    - Search must be restricted to the past month to surface recent trends only
    - Use Sogou engine for Zhipu AI search (better Chinese market coverage)
    - Return exactly 20 results from Zhipu AI (standard batch size)
    - Use compact summaries to reduce token costs
    - DuckDuckGo should target Chinese-language results
    - DuckDuckGo should use both Bing AND Google as fallback backends
    - DuckDuckGo should return up to 25 results
    - No domain filter on Zhipu AI search
    - Both search engines should be enabled

    ## Deployment
    The configuration file `conf.json` must be placed at the root of the workspace.
    The Zhipu API key to use is: ZHIPU_SEARCH_API_KEY (environment variable name)
"""))

(WORKSPACE / "docs" / "specs" / "timelimit_spec.txt").write_text(textwrap.dedent("""\
    INTERNAL SPEC - Timelimit values (DEPRECATED - DO NOT USE)
    ============================================================
    Old format (native):
      Zhipu: oneDay, oneWeek, oneMonth, oneYear, noLimit
      DDG:   d, w, m, y

    New format (unified - use this in conf.json):
      Use: day, week, month, year, null

    Note: The system automatically maps unified values to native formats.
    ALWAYS use unified format strings in conf.json.
"""))

(WORKSPACE / "tests" / "fixtures" / "sample_response.json").write_text(
    json.dumps({"results": [{"title": "Sample", "link": "http://example.com", "content": "..."}]}, indent=2)
)

(WORKSPACE / "tests" / "test_config.py").write_text(textwrap.dedent("""\
    # Test configuration loading
    import json
    from pathlib import Path

    def test_conf_exists():
        assert Path('conf.json').exists()
"""))

(WORKSPACE / "data" / "raw" / "queries.txt").write_text(
    "smartphone market 2024\n消费电子市场趋势\niPhone vs Samsung\n折叠屏手机\n"
)

(WORKSPACE / "data" / "processed" / "market_summary.txt").write_text(
    "Consumer electronics market summary Q4 2024\n(processed output placeholder)\n"
)

(WORKSPACE / "output" / "archive" / "old_results.md").write_text(
    "# Old Search Results (Archived)\nThese results are from a previous run.\n"
)

# Deliberately place a conf.json with wrong values to be REPLACED by the agent
wrong_conf = {
    "zhipu_search": {
        "enabled": True,
        "apiKey": "PLACEHOLDER",
        "search_engine": "search_pro",
        "count": 15,
        "timelimit": None,
        "content_size": "high"
    },
    "duckduckgo_search": {
        "enabled": True,
        "maxResults": 20,
        "timelimit": None,
        "backend": "auto"
    }
}
# NOTE: We do NOT place a conf.json — agent must create it from scratch
# (the above wrong_conf is just illustrative — not written to disk)

print("Workspace generated successfully.")
print(f"Files created in: {WORKSPACE}")