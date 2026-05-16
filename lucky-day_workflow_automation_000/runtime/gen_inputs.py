import os
import stat
from pathlib import Path

WORKSPACE = Path("/workspace")
WORKSPACE.mkdir(parents=True, exist_ok=True)

# ── distractor directory structure ──────────────────────────────────────────
dirs = [
    "agency/clients/zhang_family",
    "agency/clients/li_family",
    "agency/templates/contracts",
    "agency/templates/invitations",
    "agency/finance/invoices",
    "agency/finance/receipts",
    "agency/staff/schedules",
    "agency/venues/lotus_hall",
    "agency/venues/phoenix_banquet",
    "agency/tools",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# distractor files
distractor_files = {
    "agency/clients/zhang_family/contact.txt": (
        "姓名：张伟\n电话：138-0000-1234\n婚期意向：春季\n"
    ),
    "agency/clients/zhang_family/budget.csv": (
        "项目,金额\n婚宴,88000\n摄影,15000\n花艺,8000\n"
    ),
    "agency/clients/li_family/contact.txt": (
        "姓名：李晓梅\n属相：马\n电话：139-9876-5432\n婚期意向：尽快\n"
    ),
    "agency/clients/li_family/notes.txt": (
        "新娘属马，需回避冲马日期\n新郎属相：龙\n"
        "婚宴地点：莲花大厅\n备注：希望三个推荐日期\n"
    ),
    "agency/clients/li_family/checklist.md": (
        "# 婚礼筹备清单\n- [ ] 择吉选日\n- [ ] 预订酒店\n- [ ] 发请柬\n- [ ] 试妆\n"
    ),
    "agency/templates/contracts/standard_contract.txt": (
        "甲方：__\n乙方：喜庆文化策划公司\n服务内容：婚礼策划全程服务\n"
    ),
    "agency/templates/invitations/template_v2.txt": (
        "敬邀阁下莅临__先生与__小姐的婚礼\n时间：____年__月__日\n地点：____\n"
    ),
    "agency/finance/invoices/INV-2024-001.txt": (
        "发票号：INV-2024-001\n客户：王先生\n金额：¥12,000\n"
    ),
    "agency/finance/receipts/REC-2024-001.txt": (
        "收据号：REC-2024-001\n日期：2024-06-01\n金额：¥5,000\n"
    ),
    "agency/staff/schedules/june_schedule.txt": (
        "员工排班表 - 6月\n张经理：周一至周五\n王助理：全周\n"
    ),
    "agency/venues/lotus_hall/capacity.txt": (
        "莲花大厅\n容纳人数：300人\n每桌：10人\n最低消费：¥80,000\n"
    ),
    "agency/venues/phoenix_banquet/capacity.txt": (
        "凤凰宴会厅\n容纳人数：500人\n每桌：10人\n最低消费：¥120,000\n"
    ),
    "agency/tools/README_internal.txt": (
        "内部工具说明\n本目录存放策划工具脚本\n使用前请联系技术部\n"
    ),
}

for rel_path, content in distractor_files.items():
    fpath = WORKSPACE / rel_path
    fpath.write_text(content, encoding="utf-8")

# ── THE KEY TOOL: lucky.py ──────────────────────────────────────────────────
# This is the bespoke script referenced in SKILL.md
lucky_py = r'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
择吉选日工具 - lucky.py
用法:
    python3 lucky.py <事项> [属相]
例:
    python3 lucky.py 嫁娶
    python3 lucky.py 嫁娶 马
"""
import sys
import hashlib
from datetime import date, timedelta

# 十天干 十二地支
TIANGAN = ["甲","乙","丙","丁","戊","己","庚","辛","壬","癸"]
DIZHI   = ["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"]

# 属相 -> 地支
SHUXIANG_TO_DIZHI = {
    "鼠":"子","牛":"丑","虎":"寅","兔":"卯","龙":"辰","蛇":"巳",
    "马":"午","羊":"未","猴":"申","鸡":"酉","狗":"戌","猪":"亥"
}
DIZHI_TO_SHUXIANG = {v:k for k,v in SHUXIANG_TO_DIZHI.items()}

# 六冲关系 (地支相冲)
LIUCHONG = {
    "子":"午","午":"子","丑":"未","未":"丑",
    "寅":"申","申":"寅","卯":"酉","酉":"卯",
    "辰":"戌","戌":"辰","巳":"亥","亥":"巳"
}

# 事项 -> 宜项映射
YI_MAP = {
    "嫁娶": ["嫁娶","订盟","纳采","祭祀"],
    "开业": ["开市","交易","立券","挂匾","祭祀"],
    "搬家": ["移徙","入宅","安床","祭祀"],
    "动土": ["动土","起基","定磉","破土"],
    "订盟": ["订盟","纳采","盟誓","祭祀"],
    "祭祀": ["祭祀","斋醮","解除"],
}
JI_MAP = {
    "嫁娶": ["安葬","动土","破土"],
    "开业": ["动土","安葬","破土"],
    "搬家": ["动土","破土","安葬"],
    "动土": ["嫁娶","安葬","入宅"],
    "订盟": ["动土","安葬","破土"],
    "祭祀": ["嫁娶","开市","动土"],
}

JISHEN_POOL = [
    ["天德","月德","贵人"],
    ["天恩","福生","玉堂"],
    ["月恩","三合","天喜"],
    ["天德合","月德合","五合"],
    ["贵人","天官","福星"],
    ["月空","解神","除神"],
    ["天马","驿马","喜神"],
]

def get_ganzhi(offset_from_epoch):
    """从一个固定历元推算干支"""
    # 历元: 2024-01-01 = 甲辰年 甲子日(日序=0)
    tg_idx = offset_from_epoch % 10
    dz_idx = offset_from_epoch % 12
    return TIANGAN[tg_idx] + DIZHI[dz_idx]

def pseudo_random(seed_str, n):
    """基于字符串种子的确定性伪随机，返回 0..n-1"""
    h = int(hashlib.md5(seed_str.encode()).hexdigest(), 16)
    return h % n

def get_day_info(d, shishi):
    """为指定日期生成当天的宜忌冲煞吉神信息"""
    epoch = date(2024, 1, 1)
    offset = (d - epoch).days

    ganzhi = get_ganzhi(offset)
    dizhi_day = ganzhi[1]  # 日支

    # 宜：基础宜事 + 可能追加
    yi_base = list(YI_MAP.get(shishi, ["祭祀"]))
    extra_yi = ["沐浴","理发","求医","纳财","开光","安香","挂匾","立券"]
    seed_yi = f"{d.isoformat()}_yi"
    extra_count = pseudo_random(seed_yi + "cnt", 3)
    added = set()
    for i in range(extra_count):
        idx = pseudo_random(seed_yi + str(i), len(extra_yi))
        added.add(extra_yi[idx])
    yi_list = yi_base + list(added)

    # 忌：当日忌事（可能包含或不包含冲突项）
    ji_base = list(JI_MAP.get(shishi, ["安葬"]))
    extra_ji = ["出行","词讼","开渠","置产","移柩"]
    seed_ji = f"{d.isoformat()}_ji"
    extra_count_ji = pseudo_random(seed_ji + "cnt", 2)
    ji_added = set()
    for i in range(extra_count_ji):
        idx = pseudo_random(seed_ji + str(i), len(extra_ji))
        ji_added.add(extra_ji[idx])
    ji_list = ji_base + list(ji_added)

    # 冲煞
    chong_dizhi = LIUCHONG.get(dizhi_day, "子")
    chong_shuxiang = DIZHI_TO_SHUXIANG.get(chong_dizhi, "鼠")
    chong_ganzhi_seed = f"{d.isoformat()}_chong"
    chong_tg_idx = pseudo_random(chong_ganzhi_seed, 10)
    chong_gz = TIANGAN[chong_tg_idx] + chong_dizhi
    chong_str = f"冲{chong_shuxiang}（{chong_gz}）"

    # 吉神
    seed_js = f"{d.isoformat()}_js"
    pool_idx = pseudo_random(seed_js, len(JISHEN_POOL))
    jishen = JISHEN_POOL[pool_idx]

    return {
        "date": d,
        "ganzhi": ganzhi,
        "yi": yi_list,
        "ji": ji_list,
        "chong_dizhi": chong_dizhi,
        "chong_shuxiang": chong_shuxiang,
        "chong_str": chong_str,
        "jishen": jishen,
    }

def is_good_day(info, shishi, shuxiang=None):
    """判断是否为吉日"""
    yi_needed = YI_MAP.get(shishi, [])
    ji_bad    = JI_MAP.get(shishi, [])
    # 宜中必须含所求事项
    if not any(y in info["yi"] for y in yi_needed):
        return False
    # 忌中不能含主要冲突
    if ji_bad and ji_bad[0] in info["ji"]:
        pass  # 允许，但降分
    # 冲属相
    if shuxiang and info["chong_shuxiang"] == shuxiang:
        return False
    return True

def find_lucky_days(shishi, shuxiang=None, start=None, max_results=3):
    if start is None:
        start = date.today()
    results = []
    d = start
    checked = 0
    while len(results) < max_results and checked < 180:
        info = get_day_info(d, shishi)
        if is_good_day(info, shishi, shuxiang):
            results.append(info)
        d += timedelta(days=1)
        checked += 1
    return results

WEEKDAY_CN = ["周一","周二","周三","周四","周五","周六","周日"]

def format_output(shishi, shuxiang, days):
    medals = ["🥇","🥈","🥉"]
    lines = []
    lines.append("🗓️ 择吉选日")
    lines.append("")
    lines.append(f"【需求】：{shishi}")
    if shuxiang:
        lines.append(f"【您的属相】：{shuxiang}")
    lines.append("")
    lines.append("【推荐吉日】")
    for i, info in enumerate(days):
        d = info["date"]
        weekday = WEEKDAY_CN[d.weekday()]
        medal = medals[i] if i < len(medals) else f"第{i+1}选"
        lines.append(f"{medal} {d.year}年{d.month}月{d.day}日（{weekday}）")
        lines.append(f"   干支：{info['ganzhi']}")
        lines.append(f"   宜：{'、'.join(info['yi'])}")
        chong_note = info["chong_str"]
        if shuxiang:
            if info["chong_shuxiang"] == shuxiang:
                chong_note += f" - 忌（冲{shuxiang}）"
            else:
                chong_note += f" - 不冲{shuxiang}"
        lines.append(f"   冲煞：{chong_note}")
        lines.append(f"   吉神：{'、'.join(info['jishen'])}")
        lines.append("")
    lines.append("【建议】")
    if days:
        d0 = days[0]["date"]
        lines.append(f"首选 {d0.month} 月 {d0.day} 日，忌神较少，吉神汇聚")
    if len(days) > 1:
        d1 = days[1]["date"]
        lines.append(f"次选 {d1.month} 月 {d1.day} 日")
    lines.append("")
    lines.append("---")
    lines.append("※ 黄历仅供参考 ※")
    return "\n".join(lines)

def main():
    if len(sys.argv) < 2:
        print("用法: python3 lucky.py <事项> [属相]")
        sys.exit(1)
    shishi  = sys.argv[1]
    shuxiang = sys.argv[2] if len(sys.argv) >= 3 else None
    days = find_lucky_days(shishi, shuxiang)
    print(format_output(shishi, shuxiang, days))

if __name__ == "__main__":
    main()
'''

tool_path = WORKSPACE / "agency/tools/lucky.py"
tool_path.write_text(lucky_py, encoding="utf-8")
tool_path.chmod(tool_path.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

# ── task brief for the agent (business context only) ────────────────────────
brief = """李晓梅婚礼策划档案
===================
客户：李晓梅
需求：嫁娶择吉
属相：马
要求：请为李晓梅出具一份正式的"择吉选日报告"
输出文件名：lucky_report.txt
"""
(WORKSPACE / "agency/clients/li_family/task_brief.txt").write_text(brief, encoding="utf-8")

print("Workspace generated at /workspace")
print("Files created:")
for f in sorted(WORKSPACE.rglob("*")):
    if f.is_file():
        print(f"  {f.relative_to(WORKSPACE)}")