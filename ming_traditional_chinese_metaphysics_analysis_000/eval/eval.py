import sys
import json
import os
from pathlib import Path

def evaluate(workspace_dir):
    checks = []
    total_score = 0.0

    # ─── Locate output file ───────────────────────────────────────────────────
    report_files = list(Path(workspace_dir).rglob("destiny_report_2025_087.json"))
    if not report_files:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "output_file_exists", "passed": False,
                        "detail": "destiny_report_2025_087.json not found anywhere in workspace"}]
        }

    report_path = report_files[0]
    try:
        with open(report_path, "r", encoding="utf-8") as f:
            report = json.load(f)
    except Exception as e:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "output_file_parseable", "passed": False,
                        "detail": f"Could not parse JSON: {e}"}]
        }

    checks.append({"name": "output_file_exists", "passed": True, "detail": str(report_path)})
    total_score += 0.05

    # ─── CHECK 1: 年柱 (Year Pillar) ─────────────────────────────────────────
    # 1988 = 戊辰年
    # 1984=甲子, 1985=乙丑, 1986=丙寅, 1987=丁卯, 1988=戊辰
    # Heavenly stem: 戊 (Earth yang), Earthly branch: 辰 (Earth, Dragon)
    try:
        bazi = report.get("bazi", report.get("八字", {}))
        year_pillar = str(bazi.get("year_pillar", bazi.get("年柱", ""))).strip()
        year_ok = "戊" in year_pillar and "辰" in year_pillar
        checks.append({
            "name": "year_pillar_correct",
            "passed": year_ok,
            "detail": f"Expected 戊辰, got: '{year_pillar}'"
        })
        if year_ok:
            total_score += 0.10
    except Exception as e:
        checks.append({"name": "year_pillar_correct", "passed": False, "detail": str(e)})

    # ─── CHECK 2: 月柱 (Month Pillar) ────────────────────────────────────────
    # 1988年6月15日 (solar): June 15 is after 芒种 (Grain in Ear, ~June 6), so it's 午月
    # 1988 is a 戊年 (Earth Heavenly Stem, index 4 in 甲乙丙丁戊...)
    # 午月 (5th month in the cycle for 戊年):
    # 戊年/癸年: 寅月=丙寅, 卯=丁卯, 辰=戊辰, 巳=己巳, 午=庚午...
    # Month stem formula: year_stem_idx * 2 + month_branch_idx (mod 10)
    # 戊 is index 4 (0-based: 甲0乙1丙2丁3戊4)
    # 午 is the 7th branch (0-based: 子0丑1寅2卯3辰4巳5午6)
    # Month stem = (4*2 + 2 + 6) % 10 = (8+2+6)%10 = 16%10 = 6 → 庚 (index 6: 甲0乙1丙2丁3戊4己5庚6)
    # So 月柱 = 庚午
    try:
        month_pillar = str(bazi.get("month_pillar", bazi.get("月柱", ""))).strip()
        month_ok = "庚" in month_pillar and "午" in month_pillar
        checks.append({
            "name": "month_pillar_correct",
            "passed": month_ok,
            "detail": f"Expected 庚午, got: '{month_pillar}'"
        })
        if month_ok:
            total_score += 0.10
    except Exception as e:
        checks.append({"name": "month_pillar_correct", "passed": False, "detail": str(e)})

    # ─── CHECK 3: 时柱 (Hour Pillar) ─────────────────────────────────────────
    # 10:30 falls in 巳时 (09:00-11:00) per the SKILL.md time table
    # Day stem must be determined for hour stem calculation
    # The hour branch is 巳 - this is the critical SKILL.md table lookup
    try:
        hour_pillar = str(bazi.get("hour_pillar", bazi.get("时柱", ""))).strip()
        hour_branch_ok = "巳" in hour_pillar
        checks.append({
            "name": "hour_pillar_branch_correct",
            "passed": hour_branch_ok,
            "detail": f"Expected 巳 in hour pillar (10:30 = 巳时 per SKILL.md table), got: '{hour_pillar}'"
        })
        if hour_branch_ok:
            total_score += 0.10
    except Exception as e:
        checks.append({"name": "hour_pillar_branch_correct", "passed": False, "detail": str(e)})

    # ─── CHECK 4: 五行分布 (Five Elements Distribution) ──────────────────────
    # 八字: 戊辰 庚午 [日柱] [时柱含巳]
    # Stems: 戊=土, 庚=金, 日主stem, hour_stem
    # Branches: 辰=土, 午=火, 日支, 巳=火
    # Minimum verifiable: 火 >= 2 (午 and 巳 both fire), 土 >= 2 (戊 and 辰)
    try:
        wuxing = report.get("five_elements", report.get("五行分布", report.get("wuxing", {})))
        if isinstance(wuxing, dict):
            fire_count = wuxing.get("火", wuxing.get("fire", wuxing.get("Fire", 0)))
            earth_count = wuxing.get("土", wuxing.get("earth", wuxing.get("Earth", 0)))
            metal_count = wuxing.get("金", wuxing.get("metal", wuxing.get("Metal", 0)))
            try:
                fire_count = int(fire_count)
                earth_count = int(earth_count)
                metal_count = int(metal_count)
            except:
                fire_count = earth_count = metal_count = 0

            fire_ok = fire_count >= 2
            earth_ok = earth_count >= 2
            metal_ok = metal_count >= 1  # 庚=金 at minimum

            wuxing_ok = fire_ok and earth_ok and metal_ok
            checks.append({
                "name": "five_elements_distribution",
                "passed": wuxing_ok,
                "detail": f"火={fire_count}(need>=2), 土={earth_count}(need>=2), 金={metal_count}(need>=1). Full dict: {wuxing}"
            })
            if wuxing_ok:
                total_score += 0.10
        else:
            checks.append({"name": "five_elements_distribution", "passed": False,
                          "detail": f"five_elements not a dict: {type(wuxing)}"})
    except Exception as e:
        checks.append({"name": "five_elements_distribution", "passed": False, "detail": str(e)})

    # ─── CHECK 5: 五格 — 天格 (Heaven Grid) ──────────────────────────────────
    # Single surname 陈 = 7 strokes → 天格 = 7 + 1 = 8
    try:
        name_analysis = report.get("name_analysis", report.get("姓名分析", {}))
        tiange = name_analysis.get("天格", name_analysis.get("tiange", name_analysis.get("heaven_grid", None)))
        try:
            tiange = int(tiange)
        except:
            tiange = None
        tiange_ok = tiange == 8
        checks.append({
            "name": "name_tiange_correct",
            "passed": tiange_ok,
            "detail": f"天格: 陈(7)+1=8. Got: {tiange}"
        })
        if tiange_ok:
            total_score += 0.10
    except Exception as e:
        checks.append({"name": "name_tiange_correct", "passed": False, "detail": str(e)})

    # ─── CHECK 6: 五格 — 人格 (Person Grid) ──────────────────────────────────
    # 人格 = 姓氏最后一字 + 名字第一字 = 陈(7) + 思(9) = 16
    try:
        renge = name_analysis.get("人格", name_analysis.get("renge", name_analysis.get("person_grid", None)))
        try:
            renge = int(renge)
        except:
            renge = None
        renge_ok = renge == 16
        checks.append({
            "name": "name_renge_correct",
            "passed": renge_ok,
            "detail": f"人格: 陈(7)+思(9)=16. Got: {renge}"
        })
        if renge_ok:
            total_score += 0.10
    except Exception as e:
        checks.append({"name": "name_renge_correct", "passed": False, "detail": str(e)})

    # ─── CHECK 7: 五格 — 地格 (Earth Grid) ───────────────────────────────────
    # 地格 = 名字笔画数总和 = 思(9) + 远(7) = 16
    try:
        dige = name_analysis.get("地格", name_analysis.get("dige", name_analysis.get("earth_grid", None)))
        try:
            dige = int(dige)
        except:
            dige = None
        dige_ok = dige == 16
        checks.append({
            "name": "name_dige_correct",
            "passed": dige_ok,
            "detail": f"地格: 思(9)+远(7)=16. Got: {dige}"
        })
        if dige_ok:
            total_score += 0.10
    except Exception as e:
        checks.append({"name": "name_dige_correct", "passed": False, "detail": str(e)})

    # ─── CHECK 8: 五格 — 总格 (Total Grid) ───────────────────────────────────
    # 总格 = 陈(7) + 思(9) + 远(7) = 23
    try:
        zonge = name_analysis.get("总格", name_analysis.get("zonge", name_analysis.get("total_grid", None)))
        try:
            zonge = int(zonge)
        except:
            zonge = None
        zonge_ok = zonge == 23
        checks.append({
            "name": "name_zonge_correct",
            "passed": zonge_ok,
            "detail": f"总格: 陈(7)+思(9)+远(7)=23. Got: {zonge}"
        })
        if zonge_ok:
            total_score += 0.10
    except Exception as e:
        checks.append({"name": "name_zonge_correct", "passed": False, "detail": str(e)})

    # ─── CHECK 9: 五格 — 外格 (Outer Grid) ───────────────────────────────────
    # 外格 = 总格 - 人格 + 1 = 23 - 16 + 1 = 8
    # This is the PROPRIETARY TRAP: many agents will compute 总格-人格=7, forgetting +1
    try:
        waige = name_analysis.get("外格", name_analysis.get("waige", name_analysis.get("outer_grid", None)))
        try:
            waige = int(waige)
        except:
            waige = None
        waige_ok = waige == 8
        checks.append({
            "name": "name_waige_correct_proprietary_formula",
            "passed": waige_ok,
            "detail": f"外格: 总格(23)-人格(16)+1=8. Got: {waige}. NOTE: Common trap is 23-16=7 (missing +1)"
        })
        if waige_ok:
            total_score += 0.15
    except Exception as e:
        checks.append({"name": "name_waige_correct_proprietary_formula", "passed": False, "detail": str(e)})

    # ─── CHECK 10: 三才配置 (Three Talents Configuration) ────────────────────
    # 天格=8 → 金, 人格=16 → 土, 地格=16 → 土
    # Per SKILL.md five elements number mapping:
    # Numbers ending in 1,2 → 木; 3,4 → 火; 5,6 → 土; 7,8 → 金; 9,0 → 水
    # 8 → 金, 16 ends in 6 → 土, 16 ends in 6 → 土
    # 三才: 金土土
    try:
        sancai = name_analysis.get("三才配置", name_analysis.get("sancai", 
                 name_analysis.get("three_talents", name_analysis.get("san_cai", ""))))
        sancai_str = str(sancai).strip()
        # Accept various formats: 金土土, 金-土-土, etc.
        sancai_ok = ("金" in sancai_str and sancai_str.count("土") >= 2)
        checks.append({
            "name": "name_sancai_correct",
            "passed": sancai_ok,
            "detail": f"三才配置应为金土土 (天格8=金, 人格16=土, 地格16=土). Got: '{sancai_str}'"
        })
        if sancai_ok:
            total_score += 0.10
    except Exception as e:
        checks.append({"name": "name_sancai_correct", "passed": False, "detail": str(e)})

    # ─── Final scoring ────────────────────────────────────────────────────────
    # Normalize to [0,1]
    total_score = min(total_score, 1.0)
    passed = total_score >= 0.60

    return {
        "passed": passed,
        "score": round(total_score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))