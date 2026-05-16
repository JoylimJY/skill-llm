import os
import random
import csv
import textwrap

random.seed(42)

workspace = "/workspace"

# ── 1. Create realistic distractor directory structure ──────────────────────
dirs = [
    "skills/bazi-pan",
    "skills/tarot",
    "skills/numerology",
    "clients/archive/2022",
    "clients/archive/2023",
    "clients/pending",
    "reports/monthly",
    "reports/annual",
    "config",
    "logs",
    "tmp",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# ── 2. Write the real bazi.py script ────────────────────────────────────────
# This is a self-contained Chinese Eight Characters (八字) calculator.
bazi_script = textwrap.dedent(r'''
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
八字排盘脚本
Usage: python3 bazi.py <year> <month> <day> <HH:MM>
All inputs are Lunar calendar dates.
"""
import sys

# ── 天干地支 ──────────────────────────────────────────────────────────────────
TIAN_GAN = ["甲","乙","丙","丁","戊","己","庚","辛","壬","癸"]
DI_ZHI   = ["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"]
SHENG_XIAO = ["鼠","牛","虎","兔","龙","蛇","马","羊","猴","鸡","狗","猪"]

# 五行归属
WU_XING_GAN = {
    "甲":"木","乙":"木","丙":"火","丁":"火","戊":"土",
    "己":"土","庚":"金","辛":"金","壬":"水","癸":"水"
}
WU_XING_ZHI = {
    "子":"水","丑":"土","寅":"木","卯":"木","辰":"土",
    "巳":"火","午":"火","未":"土","申":"金","酉":"金",
    "戌":"土","亥":"水"
}

# 月支对应月份 (农历月 1-12 → 地支索引)
YUE_ZHI = [2,3,4,5,6,7,8,9,10,11,0,1]  # 寅卯辰巳午未申酉戌亥子丑

# 时支 (每2小时一支，子时=0/23时)
def hour_to_dizhi_idx(h):
    # 子(23-1), 丑(1-3), 寅(3-5), 卯(5-7), 辰(7-9), 巳(9-11),
    # 午(11-13), 未(13-15), 申(15-17), 酉(17-19), 戌(19-21), 亥(21-23)
    if h == 23 or h == 0: return 0
    return (h + 1) // 2

def get_ganzhi(idx_60):
    """60甲子中第idx个 (0-based)"""
    return TIAN_GAN[idx_60 % 10] + DI_ZHI[idx_60 % 12]

def year_ganzhi(lunar_year):
    # 甲子年 = 4 AD, offset
    idx = (lunar_year - 4) % 60
    return get_ganzhi(idx)

def month_ganzhi(lunar_year, lunar_month):
    # 月干以年干为基础推算
    # 年干索引
    year_tg_idx = (lunar_year - 4) % 10
    # 月支索引固定：寅(2)为正月
    month_zhi_idx = YUE_ZHI[lunar_month - 1]
    # 月干：甲己年起丙寅，乙庚年起戊寅，丙辛年起庚寅，丁壬年起壬寅，戊癸年起甲寅
    start_tg = [2, 4, 6, 8, 0]  # 丙戊庚壬甲
    month_tg_idx = (start_tg[year_tg_idx % 5] + (lunar_month - 1)) % 10
    return TIAN_GAN[month_tg_idx] + DI_ZHI[month_zhi_idx]

def day_ganzhi(lunar_year, lunar_month, lunar_day):
    # 用简化公式：以1900年1月1日为甲戌日(idx=10)计算
    # 用儒略日差近似（农历直接用一个固定偏移映射）
    # 简化：每年365天，每月30天近似
    base_year = 1900
    days = (lunar_year - base_year) * 365 + (lunar_year - base_year) // 4
    days += (lunar_month - 1) * 30 + (lunar_day - 1)
    idx = (days + 10) % 60  # 甲戌 offset=10
    return get_ganzhi(idx)

def hour_ganzhi(day_ganzhi_str, hour):
    # 时干以日干为基础
    day_tg = day_ganzhi_str[0]
    day_tg_idx = TIAN_GAN.index(day_tg)
    hour_zhi_idx = hour_to_dizhi_idx(hour)
    # 甲己日起甲子，乙庚日起丙子，丙辛日起戊子，丁壬日起庚子，戊癸日起壬子
    start_tg = [0, 2, 4, 6, 8]
    hour_tg_idx = (start_tg[day_tg_idx % 5] + hour_zhi_idx) % 10
    return TIAN_GAN[hour_tg_idx] + DI_ZHI[hour_zhi_idx]

def count_wuxing(pillars):
    counts = {"金":0,"木":0,"水":0,"火":0,"土":0}
    for gz in pillars:
        tg, zhi = gz[0], gz[1]
        counts[WU_XING_GAN[tg]] += 1
        counts[WU_XING_ZHI[zhi]] += 1
    return counts

def assess_rizhu(day_tg, month_zhi, wx_counts):
    """粗略判断日主强弱"""
    day_wx = WU_XING_GAN[day_tg]
    # 得令判断：月支五行与日主同或生日主
    month_wx = WU_XING_ZHI[month_zhi]
    SHENG = {"木":"水","火":"木","土":"火","金":"土","水":"金"}
    de_ling = (month_wx == day_wx) or (SHENG.get(day_wx) == month_wx)
    # 得势：同五行数量
    same_count = wx_counts[day_wx]
    strong = de_ling or same_count >= 4
    return "偏强" if strong else "偏弱"

def suggest_yongshen(day_tg, strength):
    day_wx = WU_XING_GAN[day_tg]
    # 五行生克
    SHENG = {"木":"水","火":"木","土":"火","金":"土","水":"金"}  # X生Y: SHENG[Y]=X
    KE   = {"木":"金","火":"水","土":"木","金":"火","水":"土"}   # X克Y: KE[Y]=X (X被Y克)
    # 印星=生日主之五行，比劫=同日主五行，官杀=克日主之五行，财星=日主所克之五行
    yin_wx   = SHENG[day_wx]          # 印星五行
    bigua_wx = day_wx                 # 比劫
    guansha_wx = KE[day_wx]           # 官杀（克日主）
    # 财星：日主所克
    RIZHU_KE = {"木":"土","火":"金","土":"水","金":"木","水":"火"}
    cai_wx   = RIZHU_KE[day_wx]

    if strength == "偏强":
        yong = [guansha_wx, cai_wx]
        ji   = [yin_wx, bigua_wx]
    else:
        yong = [yin_wx, bigua_wx]
        ji   = [guansha_wx, cai_wx]
    # deduplicate preserving order
    yong = list(dict.fromkeys(yong))
    ji   = list(dict.fromkeys(ji))
    return yong, ji

def dayun_sequence(lunar_year, lunar_month, gender="男"):
    """生成未来10步大运（每步10年）"""
    # 起运年干支：从月柱顺推（阳年男/阴年女顺行，否则逆行）
    year_tg_idx = (lunar_year - 4) % 10
    yang_year = (year_tg_idx % 2 == 0)
    shun = (yang_year and gender == "男") or (not yang_year and gender == "女")

    month_gz = month_ganzhi(lunar_year, lunar_month)
    month_gz_idx = TIAN_GAN.index(month_gz[0]) * 6 + DI_ZHI.index(month_gz[1]) // 2
    # 60甲子序号
    m60 = (TIAN_GAN.index(month_gz[0]) % 10 + DI_ZHI.index(month_gz[1]) % 12)
    # Simpler: use combined index
    tg_i = TIAN_GAN.index(month_gz[0])
    zhi_i = DI_ZHI.index(month_gz[1])

    dayuns = []
    for i in range(1, 9):
        step = i if shun else -i
        new_tg_i = (tg_i + step) % 10
        new_zhi_i = (zhi_i + step) % 12
        dayuns.append(TIAN_GAN[new_tg_i] + DI_ZHI[new_zhi_i])
    return dayuns

def main():
    if len(sys.argv) != 5:
        print("Usage: bazi.py <lunar_year> <lunar_month> <lunar_day> <HH:MM>")
        sys.exit(1)

    year  = int(sys.argv[1])
    month = int(sys.argv[2])
    day   = int(sys.argv[3])
    time_str = sys.argv[4]
    hour  = int(time_str.split(":")[0])

    # ── 计算四柱 ───────────────────────────────────────────────────────────────
    nian_gz  = year_ganzhi(year)
    yue_gz   = month_ganzhi(year, month)
    ri_gz    = day_ganzhi(year, month, day)
    shi_gz   = hour_ganzhi(ri_gz, hour)

    pillars = [nian_gz, yue_gz, ri_gz, shi_gz]

    # 生肖
    sx_idx = (year - 4) % 12
    sx = SHENG_XIAO[sx_idx]

    # 月支生肖
    month_sx = SHENG_XIAO[YUE_ZHI[month-1]]
    day_sx   = SHENG_XIAO[DI_ZHI.index(ri_gz[1])]
    hour_sx  = SHENG_XIAO[DI_ZHI.index(shi_gz[1])]

    # ── 五行统计 ────────────────────────────────────────────────────────────────
    wx = count_wuxing(pillars)

    # ── 日主分析 ────────────────────────────────────────────────────────────────
    ri_tg = ri_gz[0]
    ri_wx = WU_XING_GAN[ri_tg]
    strength = assess_rizhu(ri_tg, yue_gz[1], wx)

    # ── 用神忌神 ────────────────────────────────────────────────────────────────
    yong, ji = suggest_yongshen(ri_tg, strength)

    # ── 大运 ────────────────────────────────────────────────────────────────────
    dayuns = dayun_sequence(year, month, "男")

    # ── 起运岁数(简化：3年) ───────────────────────────────────────────────────
    qi_yun_age = 3 + (month % 4)

    # ── 输出 ────────────────────────────────────────────────────────────────────
    print("📊 八字排盘")
    print()
    print("【基本信息】")
    print(f"出生：{year}年 农历{month}月{day}日 {time_str}")
    print()
    print("【八字】")
    print(f"年柱：{nian_gz}（{sx}）  |  月柱：{yue_gz}（{month_sx}）")
    print(f"日柱：{ri_gz}（{day_sx}）  |  时柱：{shi_gz}（{hour_sx}）")
    print()
    print("【五行分布】")
    print(f"金：{wx['金']}  |  木：{wx['木']}  |  水：{wx['水']}  |  火：{wx['火']}  |  土：{wx['土']}")
    print()
    print("【日主】")
    print(f"{ri_tg}{ri_wx}，生于{yue_gz[1]}月")
    print(f"日主{strength}，{'喜' if strength=='偏弱' else '宜'}{''.join(yong)}{'生扶' if strength=='偏弱' else '泄耗'}")
    print()
    print("【用神建议】")
    print(f"用神：{'、'.join(yong)}")
    print(f"忌神：{'、'.join(ji)}")
    print()
    print("【大运】")
    print(f"{qi_yun_age}岁起运：{'  '.join(dayuns[:8])}")
    print()
    print("---")
    print("※ 八字仅供参考，命理需综合判断 ※")

if __name__ == "__main__":
    main()
''')

with open(os.path.join(workspace, "skills/bazi-pan/bazi.py"), "w", encoding="utf-8") as f:
    f.write(bazi_script)

# ── 3. Write clients.csv ─────────────────────────────────────────────────────
clients = [
    ["name",    "lunar_year", "lunar_month", "lunar_day", "time"],
    ["李明",    "1985",       "3",           "12",        "08:00"],
    ["张晓红",  "1992",       "7",           "28",        "23:00"],
    ["王建国",  "2000",       "11",          "5",         "15:30"],
]

with open(os.path.join(workspace, "clients/pending/clients.csv"), "w",
          encoding="utf-8", newline="") as f:
    writer = csv.writer(f)
    writer.writerows(clients)

# ── 4. Distractor files ───────────────────────────────────────────────────────
distractors = {
    "skills/tarot/tarot.py":          "# tarot card reading stub\n",
    "skills/numerology/numerology.py": "# numerology stub\n",
    "clients/archive/2022/old_clients.csv": "name,dob\n张三,1980-01-01\n",
    "clients/archive/2023/clients_2023.csv": "name,solar_year,solar_month,solar_day\n旧客户,1975,6,15\n",
    "reports/monthly/2024_01.txt":    "Monthly report placeholder\n",
    "reports/annual/2023_summary.txt":"Annual summary placeholder\n",
    "config/app.conf":                "[app]\nname=bazi-service\nversion=1.0\n",
    "config/logging.conf":            "[logging]\nlevel=INFO\n",
    "logs/app.log":                   "2024-01-01 INFO service started\n",
    "tmp/scratch.txt":                "temporary scratch notes\n",
    "tmp/test_run.txt":               "test run output placeholder\n",
}
for rel_path, content in distractors.items():
    full = os.path.join(workspace, rel_path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)

print("Workspace generated successfully.")