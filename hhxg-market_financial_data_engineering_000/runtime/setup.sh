#!/bin/bash
set -e

# Install the hhxg-market skill into the expected path
SKILL_TARGET="$HOME/.claude/skills/hhxg-market"
mkdir -p "$SKILL_TARGET/scripts"
mkdir -p "$SKILL_TARGET/references"

# Clone or copy the skill scripts into place
# Since the skill scripts are embedded in the SKILL.md, we recreate them here

cat > "$SKILL_TARGET/scripts/_common.py" << 'PYEOF'
"""共用工具：HTTP 请求 + 本地缓存 + schema 检查。"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request

BASE_URL = "https://hhxg.top/static/data"
CACHE_DIR = os.path.expanduser("~/.cache/hhxg-market")
SUPPORTED_SCHEMA = 3
HEADERS = {
    "User-Agent": "hhxg-skill/1.0",
    "X-Skill-Client": "clawhub",
}


def fetch_json(path, cache_name=None):
    url = "%s/%s" % (BASE_URL, path)
    cache_file = os.path.join(CACHE_DIR, cache_name) if cache_name else None

    last_err = None
    for attempt in range(2):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            if cache_file:
                _save_cache(cache_file, data)
            return data, False
        except urllib.error.HTTPError as e:
            if e.code == 404:
                raise RuntimeError(
                    "数据接口不存在 (404)，请升级技能：\n"
                    "  cd ~/.claude/skills/hhxg-market && git pull"
                )
            raise RuntimeError("服务端错误 HTTP %s，请稍后重试" % e.code)
        except json.JSONDecodeError:
            raise RuntimeError("数据格式异常，服务端可能在维护，请稍后重试")
        except urllib.error.URLError as e:
            last_err = e
            if attempt == 0:
                time.sleep(1)

    if cache_file:
        cached = _load_cache(cache_file)
        if cached:
            return cached, True
    raise RuntimeError(
        "网络不可用，且无本地缓存。请稍后重试或直接访问 https://hhxg.top"
    )


def check_schema(data):
    meta = data.get("meta", {})
    ver = meta.get("schema_version", SUPPORTED_SCHEMA)
    if ver > SUPPORTED_SCHEMA:
        print(
            "WARNING: 数据格式已更新 (v%s)，当前技能支持 v%s，建议升级：\n"
            "  cd ~/.claude/skills/hhxg-market && git pull\n" % (ver, SUPPORTED_SCHEMA),
            file=sys.stderr,
        )


def print_cache_hint(from_cache, date_str):
    if from_cache:
        print(
            "NOTE: 网络不可用，以下为本地缓存数据（%s）\n" % date_str,
            file=sys.stderr,
        )


def run_main(sections, default="all"):
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    flags = {a for a in sys.argv[1:] if a.startswith("-")}
    use_json = "--json" in flags

    section = args[0] if args else default
    if section not in sections:
        print("未知板块: %s" % section)
        print("可选: %s" % ", ".join(sections))
        sys.exit(1)

    return section, args[1:], use_json


def _save_cache(path, data):
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
    except OSError:
        pass


def _load_cache(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None
PYEOF

cat > "$SKILL_TARGET/scripts/fetch_snapshot.py" << 'PYEOF'
#!/usr/bin/env python3
from __future__ import annotations
import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import fetch_json, check_schema, print_cache_hint


def fetch():
    return fetch_json("assistant/skill_snapshot.json", "last.json")


def fmt_market(data):
    m = data.get("market")
    if not m:
        return "暂无市场数据"
    comp = data.get("comparison", {})
    yd = comp.get("yesterday", {}) if comp else {}
    today_si = m.get("sentiment_index", "?")
    yd_si = yd.get("sentiment_index")
    si_diff = ""
    if yd_si is not None and isinstance(today_si, (int, float)):
        diff = round(today_si - yd_si, 1)
        sign = "+" if diff > 0 else ""
        si_diff = "，昨 %s%%，%s%s%%" % (yd_si, sign, diff)
    today_lu = m.get("limit_up", "?")
    yd_lu = yd.get("limit_up")
    lu_diff = ""
    if yd_lu is not None and isinstance(today_lu, int):
        diff = today_lu - yd_lu
        sign = "+" if diff > 0 else ""
        lu_diff = "（昨%s，%s%s）" % (yd_lu, sign, diff)
    today_fr = m.get("fried", "?")
    yd_fr = yd.get("fried")
    fr_diff = ""
    if yd_fr is not None and isinstance(today_fr, int):
        diff = today_fr - yd_fr
        sign = "+" if diff > 0 else ""
        fr_diff = "（昨%s，%s%s）" % (yd_fr, sign, diff)
    lines = [
        "# 市场赚钱效应 — %s" % data.get("date", ""),
        "",
        "赚钱效应指数: **%s%%** (%s)%s" % (today_si, m.get("sentiment_label", "?"), si_diff),
        "涨停 %s%s | 炸板 %s%s | 跌停 %s" % (
            today_lu, lu_diff, today_fr, fr_diff, m.get("limit_down", "?")
        ),
    ]
    return "\n".join(lines)


def fmt_themes(data):
    themes = data.get("hot_themes", [])
    if not themes:
        return "暂无热门题材数据"
    lines = ["# 热门题材 — %s" % data.get("date", ""), ""]
    for i, t in enumerate(themes, 1):
        lines.append("%d. %s" % (i, t.get("name", "")))
    return "\n".join(lines)


def fmt_ladder(data):
    ld = data.get("ladder_detail")
    if not ld:
        return "暂无连板数据"
    ladder = data.get("ladder", {})
    lines = ["# 连板天梯 — %s" % data.get("date", "")]
    return "\n".join(lines)


def fmt_hotmoney(data):
    hm = data.get("hotmoney")
    if not hm:
        return "暂无游资数据"
    return "# 游资龙虎榜\n龙虎榜总净买入: **%s 亿**" % hm.get("total_net_yi", "?")


def fmt_sectors(data):
    sectors = data.get("sectors", [])
    if not sectors:
        return "暂无行业资金数据"
    return "# 行业资金流向"


def fmt_news(data):
    macro = data.get("macro_news", [])
    if not macro:
        return "暂无新闻数据"
    return "# 宏观新闻"


def fmt_ai_summary(data):
    ai = data.get("ai_summary")
    if not ai:
        return ""
    if isinstance(ai, str):
        return "> %s" % ai
    if not isinstance(ai, dict):
        return ""
    lines = []
    headline = ai.get("market_state", "")
    if headline:
        lines.append("> **%s**" % headline)
    return "\n".join(lines)


def fmt_comparison(data):
    comp = data.get("comparison")
    if not comp:
        return ""
    return "## 较昨日变化"


def fmt_signals(data):
    sig = data.get("signals_count")
    if not sig:
        return ""
    return "## 量化工具"


def fmt_snapshot(data):
    parts = ["# 恢恢量化 · %s" % data.get("date", ""), ""]
    summary = fmt_ai_summary(data)
    if summary:
        parts.append(summary)
    return "\n".join(parts)


SECTIONS = {
    "all": fmt_snapshot,
    "summary": fmt_ai_summary,
    "market": fmt_market,
    "themes": fmt_themes,
    "ladder": fmt_ladder,
    "hotmoney": fmt_hotmoney,
    "sectors": fmt_sectors,
    "news": fmt_news,
    "comparison": fmt_comparison,
    "signals": fmt_signals,
}


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    flags = {a for a in sys.argv[1:] if a.startswith("-")}
    use_json = "--json" in flags

    section = args[0] if args else "all"
    if section not in SECTIONS:
        print("未知板块: %s" % section)
        print("可选: %s" % ", ".join(SECTIONS))
        sys.exit(1)

    try:
        data, from_cache = fetch()
    except RuntimeError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)

    check_schema(data)
    print_cache_hint(from_cache, data.get("date", ""))

    data_date = data.get("date", "")
    today = datetime.now().strftime("%Y-%m-%d")
    if data_date and data_date != today:
        print(
            "NOTE: 以下为 %s 的数据（最近交易日）。"
            "每个交易日盘后约 20:00 更新，今日数据尚未发布。\n" % data_date,
            file=sys.stderr,
        )

    if use_json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(SECTIONS[section](data))


if __name__ == "__main__":
    main()
PYEOF

cat > "$SKILL_TARGET/scripts/margin.py" << 'PYEOF'
#!/usr/bin/env python3
from __future__ import annotations
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import fetch_json, print_cache_hint, run_main


def _fetch():
    return fetch_json("assistant/recent_margin_7d.json", "margin_7d.json")


def fmt_overview(data):
    mkt = data.get("market", {})
    win = data.get("window", {})
    lines = [
        "# 融资融券市场总览（近 7 个交易日）",
        "",
        "区间: %s ~ %s" % (win.get("start", "?"), win.get("end", "?")),
    ]
    delta_rz = mkt.get("delta_rzye_yi", 0)
    delta_rq = mkt.get("delta_rqye_yi", 0)
    sign_rz = "+" if delta_rz > 0 else ""
    sign_rq = "+" if delta_rq > 0 else ""
    lines.append("7 日融资变化: **%s%.1f 亿**" % (sign_rz, delta_rz))
    lines.append("7 日融券变化: **%s%.1f 亿**" % (sign_rq, delta_rq))
    return "\n".join(lines)


def fmt_top(data):
    top = data.get("top", {})
    lines = ["# 融资净买入/净卖出 TOP", ""]
    inc = top.get("increase_rzye", [])
    if inc:
        lines.append("## 融资净买入 TOP")
        for s in inc[:10]:
            lines.append("- %s: +%.1f亿 (+%.1f%%)" % (
                s.get("name", ""), s.get("delta_rzye_yi", 0), s.get("delta_pct", 0)
            ))
    return "\n".join(lines)


def fmt_all(data):
    return fmt_overview(data) + "\n\n---\n\n" + fmt_top(data)


SECTIONS = {"all": fmt_all, "overview": fmt_overview, "top": fmt_top}


def main():
    section, _, use_json = run_main(SECTIONS)
    try:
        data, cached = _fetch()
    except RuntimeError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)
    print_cache_hint(cached, data.get("window", {}).get("end", ""))
    if use_json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(SECTIONS[section](data))


if __name__ == "__main__":
    main()
PYEOF

cat > "$SKILL_TARGET/scripts/calendar.py" << 'PYEOF'
#!/usr/bin/env python3
from __future__ import annotations
import json
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import fetch_json, print_cache_hint, run_main

YEAR = datetime.now().strftime("%Y")


def _this_week():
    today = datetime.now().date()
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)
    return monday.isoformat(), sunday.isoformat()


def _fetch_trading_days():
    data, cached = fetch_json(
        "calendar/trading_days_%s.json" % YEAR, "trading_days.json"
    )
    return data, cached


def _fetch_events(kind, month):
    if kind == "delivery":
        path = "calendar/delivery_%s.json" % YEAR
    else:
        path = "calendar/%s_%s.json" % (kind, month.replace("-", ""))
    return fetch_json(path, "%s_%s.json" % (kind, month or YEAR))


def fmt_trading(data, args):
    if not args:
        target = datetime.now().strftime("%Y-%m-%d")
    else:
        target = args[0]
    days = data if isinstance(data, list) else data.get("days", data)
    is_trading = target in days
    if is_trading:
        return "%s 是交易日" % target
    nxt = ""
    for d in sorted(days):
        if d > target:
            nxt = d
            break
    hint = "，下一个交易日是 %s" % nxt if nxt else ""
    return "%s 不是交易日（休市）%s" % (target, hint)


def fmt_events(events, title):
    if not events:
        return "暂无%s数据" % title
    lines = ["# %s" % title, ""]
    prev_date = ""
    for e in events:
        date = e.get("date", "")
        label = e.get("label", "")
        desc = e.get("description", "")
        if date == prev_date:
            lines.append("- ↳ %s — %s" % (label, desc))
        else:
            lines.append("- **%s** %s — %s" % (date, label, desc))
        prev_date = date
    return "\n".join(lines)


def fmt_week(trading_days, all_events):
    mon, sun = _this_week()
    today = datetime.now().strftime("%Y-%m-%d")
    week_td = [d for d in trading_days if mon <= d <= sun]
    is_today_trading = today in trading_days
    lines = [
        "# 本周 A 股日历（%s ~ %s）" % (mon, sun),
        "",
        "今天 %s %s交易日" % (today, "是" if is_today_trading else "不是"),
        "本周交易日: %s" % ", ".join(week_td) if week_td else "本周无交易日",
    ]
    return "\n".join(lines)


SECTIONS = {"week": "week", "trading": "trading", "unlock": "unlock", "earnings": "earnings", "delivery": "delivery"}


def main():
    section, extra_args, use_json = run_main(SECTIONS, default="week")

    if section == "trading":
        data, cached = _fetch_trading_days()
        print_cache_hint(cached, YEAR)
        if use_json:
            print(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            print(fmt_trading(data, extra_args))

    elif section in ("unlock", "earnings"):
        month = extra_args[0] if extra_args else datetime.now().strftime("%Y-%m")
        data, cached = _fetch_events(section, month)
        print_cache_hint(cached, month)
        if use_json:
            print(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            events = data.get("events", []) if isinstance(data, dict) else data
            title = "限售解禁 — %s" % month if section == "unlock" else "业绩预告 — %s" % month
            print(fmt_events(events, title))

    elif section == "delivery":
        data, cached = _fetch_events("delivery", "")
        print_cache_hint(cached, YEAR)
        if use_json:
            print(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            events = data.get("events", []) if isinstance(data, dict) else data
            print(fmt_events(events, "期货/期权交割日 — %s" % YEAR))

    elif section == "week":
        td_data, cached1 = _fetch_trading_days()
        trading_days = td_data if isinstance(td_data, list) else []
        mon, sun = _this_week()
        months = {mon[:7], sun[:7]}
        all_events = []
        for month in sorted(months):
            for kind in ("unlock", "earnings"):
                try:
                    edata, _ = _fetch_events(kind, month)
                    evts = edata.get("events", []) if isinstance(edata, dict) else []
                    all_events.extend(evts)
                except RuntimeError:
                    pass
        try:
            edata, _ = _fetch_events("delivery", "")
            evts = edata.get("events", []) if isinstance(edata, dict) else []
            all_events.extend(evts)
        except RuntimeError:
            pass
        print_cache_hint(cached1, mon[:7])
        if use_json:
            print(json.dumps({"trading_days": trading_days, "events": all_events}, ensure_ascii=False, indent=2))
        else:
            print(fmt_week(trading_days, all_events))


if __name__ == "__main__":
    main()
PYEOF

cat > "$SKILL_TARGET/scripts/news.py" << 'PYEOF'
#!/usr/bin/env python3
from __future__ import annotations
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import fetch_json, print_cache_hint


def _fetch():
    return fetch_json("news/n0.json", "news_latest.json")


def fmt_news(items, limit=20):
    if not items:
        return "暂无快讯数据"
    lines = ["# 财经快讯（最新 %d 条）" % min(limit, len(items)), ""]
    current_date = ""
    for n in items[:limit]:
        t = n.get("t", "")
        cat = n.get("cat", "")
        title = n.get("title", "")
        date_part = t.split("T")[0] if "T" in t else ""
        if date_part != current_date:
            current_date = date_part
            lines.append("## %s" % date_part)
        time_part = t.split("T")[1][:5] if "T" in t else t
        tag = "[%s]" % cat if cat else ""
        lines.append("- `%s` %s %s" % (time_part, tag, title))
    return "\n".join(lines)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    flags = {a for a in sys.argv[1:] if a.startswith("-")}
    use_json = "--json" in flags
    limit = 20
    if args:
        try:
            limit = int(args[0])
        except ValueError:
            pass
    try:
        data, cached = _fetch()
    except RuntimeError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)
    items = data if isinstance(data, list) else data.get("items", [])
    print_cache_hint(cached, "")
    if use_json:
        print(json.dumps(items[:limit], ensure_ascii=False, indent=2))
    else:
        print(fmt_news(items, limit))


if __name__ == "__main__":
    main()
PYEOF

chmod +x "$SKILL_TARGET/scripts/"*.py

# Also create the openclaw path as alternative
mkdir -p "$HOME/.openclaw/skills/hhxg-market/scripts"
cp -r "$SKILL_TARGET/scripts/"* "$HOME/.openclaw/skills/hhxg-market/scripts/"

echo "Skill installed at $SKILL_TARGET"
echo "Verifying skill location..."
SKILL_DIR="$(dirname "$(find ~/.claude/skills ~/.openclaw/skills -name _common.py -path '*/hhxg-market/*' 2>/dev/null | head -1)")"
echo "SKILL_DIR=$SKILL_DIR"