#!/bin/bash
set -e

# ── Create mock flyai CLI tool ────────────────────────────────────────────────
cat > /usr/local/bin/flyai << 'FLYAI_EOF'
#!/usr/bin/env python3
"""Mock flyai CLI - simulates luxury travel search results."""
import sys
import json
import hashlib

def mock_keyword_search(query: str) -> str:
    """Return deterministic mock search results based on query content."""
    q = query.lower()
    
    # New Zealand Helicopter
    if ("直升机" in q or "helicopter" in q) and ("新西兰" in q or "zealand" in q or "冰川" in q or "glacier" in q or "皇后镇" in q or "queenstown" in q):
        return """搜索结果: 新西兰直升机体验

1. 【The Helicopter Line - 冰川直升机】
   描述: 直升机冰川徒步体验，飞越福克斯冰川和弗朗茨约瑟夫冰川
   时长: 2.5小时（含冰川徒步1小时）
   机型: AS350 Squirrel
   人数: 2-6人
   价格: NZD 995/人 约¥4,200/人
   链接: https://thehelicopterline.co.nz/glacier-heli-hike
   特色: 私人直升机，专业冰川向导，降落冰川表面

2. 【Over The Top Helicopters - 私人包机】
   描述: 南岛全景私人直升机包机，米尔福德峡湾、库克山、福克斯冰川
   时长: 全日（6-8小时）
   机型: AS350 / Airbus H125
   人数: 1-4人（2人包机）
   价格: NZD 8,500 约¥35,800（2人包机）
   链接: https://www.otago.co.nz/heli-charter
   特色: 完全定制路线，含山顶野餐午餐

3. 【Mount Cook Ski Planes & Helicopters】
   描述: 直升机库克山观光+冰雪体验
   时长: 55分钟
   价格: NZD 650/人 约¥2,730/人
   链接: https://www.mtcookskiplanes.com/helicopters
"""
    
    # New Zealand Yacht/Boat
    if ("游艇" in q or "yacht" in q or "包船" in q or "charter" in q or "豪华游艇" in q) and ("新西兰" in q or "zealand" in q or "米尔福德" in q or "milford" in q or "峡湾" in q or "doubtful" in q):
        return """搜索结果: 新西兰游艇租赁

1. 【Fiordland Navigator - 米尔福德峡湾豪华游船】
   描述: 过夜豪华游船，米尔福德峡湾深度探索
   游船: Fiordland Navigator（超级游船，全长45米）
   时长: 2天1夜
   人数: 最多56人（可包船: 2人也接受）
   包含: 全餐、皮划艇、潜水装备、自然导览
   价格: NZD 850/人/晚 约¥3,570/人；包船: NZD 25,000 约¥105,000
   链接: https://www.fiordlandnavigator.co.nz
   特色: 停泊深峡湾，夜间星空，晨雾峡湾独享

2. 【Doubtful Sound Overnight Cruise - 豪华私人包船】
   描述: Doubtful Sound私人包船，极致安静峡湾体验
   游艇: Patea Explorer（38米豪华游艇）
   时长: 全日或过夜
   价格: NZD 18,000/天（包船，2人）约¥75,600
   链接: https://www.realnz.com/doubtful-sound-cruise
   特色: 比米尔福德更偏僻，野生海豚、企鹅

3. 【Marlborough Sounds Yacht Charter】
   描述: 马尔伯勒海峡私人游艇，葡萄园海岸线
   游艇: 55英尺豪华帆船
   时长: 全日（8小时）
   价格: NZD 4,200 约¥17,600（包船）
   链接: https://www.marlboroughsounds.co.nz/yacht-charter
"""
    
    # New Zealand Wine/Vineyard
    if ("酒庄" in q or "wine" in q or "品鉴" in q or "葡萄" in q or "vineyard" in q or "马尔伯勒" in q or "marlborough" in q or "central otago" in q or "奥塔哥" in q):
        return """搜索结果: 新西兰私人酒庄体验

1. 【Cloudy Bay Vineyard - 私人品鉴体验】
   描述: 马尔伯勒最著名酒庄私人品鉴，直升机接送可选
   包含: 酒庄主陪同、6款精选、橄榄油品鉴、专属午餐
   时长: 3小时
   价格: NZD 350/人（仅品鉴）约¥1,470/人；+直升机: NZD 2,800/人 约¥11,760/人
   链接: https://www.cloudybay.co.nz/private-tasting
   特色: 长相思白葡萄酒标杆产区

2. 【Rippon Vineyard - Central Otago 私人品鉴】
   描述: 皇后镇旁瓦纳卡湖畔酒庄，黑皮诺圣地
   包含: 酿酒师导览、6款垂直品鉴、有机葡萄园漫步、定制午餐
   时长: 半天（4小时）
   价格: NZD 500/人 约¥2,100/人
   链接: https://www.rippon.co.nz/experiences
   特色: 有机种植、世界级黑皮诺、湖景绝佳

3. 【直升机+多酒庄品鉴 - 私人定制】
   描述: 直升机飞越3大酒庄，私人品鉴+顶级午餐
   路线: 皇后镇→Rippon→Amisfield→Mt Difficulty
   时长: 全日（7小时）
   价格: NZD 4,800/人 约¥20,160/人
   链接: https://www.heliwine.co.nz/private-tour
   特色: 私人飞机+地面私人导游全程陪同
"""
    
    # New Zealand Supercar
    if ("超跑" in q or "豪车" in q or "法拉利" in q or "兰博基尼" in q or "supercar" in q or "luxury car" in q) and ("新西兰" in q or "zealand" in q or "皇后镇" in q or "queenstown" in q):
        return """搜索结果: 新西兰超跑租赁

1. 【Luxury Car Hire Queenstown】
   描述: 皇后镇超跑租赁，南岛公路自驾
   车型可选:
   - 保时捷911 Carrera S: NZD 1,200/天 约¥5,040/天
   - 兰博基尼Huracán EVO: NZD 2,800/天 约¥11,760/天
   - 法拉利F8 Tributo: NZD 3,200/天 约¥13,440/天
   路线推荐: 皇后镇→克伦威尔→瓦纳卡（"世界最美公路"）
   链接: https://www.luxurycarhire.co.nz/queenstown
   包含: 全险、GPS导航、接送服务

2. 【Driven NZ - 超跑体验套餐】
   描述: 专业赛道+公路超跑体验，含驾驶教练
   车型: 法拉利488 GTB、保时捷GT3
   时长: 半天（4小时赛道+2小时公路）
   价格: NZD 2,500/人 约¥10,500
   链接: https://www.drivennz.co.nz/supercar-experience
"""
    
    # Shanghai/NZ Flights
    if ("航班" in q or "flight" in q or "头等舱" in q or "商务舱" in q or "上海" in q or "shanghai" in q or "新西兰" in q or "zealand" in q or "奥克兰" in q or "auckland" in q or "私人飞机" in q):
        return """搜索结果: 上海-新西兰 奢华机票

1. 【新加坡航空 商务舱 SQ285/SQ283】
   路线: 上海浦东(PVG) → 奥克兰(AKL) via 新加坡
   舱位: 商务舱（新加坡航空Vantage XL座椅）
   价格: ¥38,000/人（往返）
   出发: PVG 09:30 → 樟宜转机 → AKL +2天 08:15
   链接: https://a.feizhu.com/SQ285-business
   特色: 全球最佳商务舱、新加坡航空服务

2. 【新加坡航空 头等舱 SQ285】
   路线: 上海浦东(PVG) → 奥克兰(AKL) via 新加坡
   舱位: 头等舱（双人套房可选，Suite Class）
   价格: ¥89,000/人（往返）
   链接: https://a.feizhu.com/SQ285-first
   特色: A380空中套房，全球顶级头等舱产品

3. 【阿联酋航空 头等舱 EK407】
   路线: 上海浦东(PVG) → 奥克兰(AKL) via 迪拜
   舱位: 头等舱（A380私人套房）
   价格: ¥95,000/人（往返）
   链接: https://a.feizhu.com/EK407-first
   特色: 空中淋浴间、私人套房、酒吧

4. 【国泰航空 商务舱 CX198】
   路线: 上海 → 奥克兰 via 香港
   舱位: 商务舱
   价格: ¥32,000/人（往返）
   链接: https://a.feizhu.com/CX198-business
"""
    
    # NZ Hotels
    if ("酒店" in q or "hotel" in q or "住宿" in q or "别墅" in q or "villa" in q) and ("新西兰" in q or "zealand" in q or "皇后镇" in q or "queenstown" in q or "南岛" in q):
        return """搜索结果: 新西兰奢华住宿

1. 【Matakauri Lodge - 皇后镇】
   品牌: 顶级独立豪华酒店
   位置: 皇后镇瓦卡蒂普湖畔，私人保护区内
   房型: 湖景别墅（Lake Suite）
   面积: 120㎡
   价格: NZD 3,500/晚 约¥14,700/晚
   链接: https://www.matakauri.co.nz
   特色: 湖景私人露台、管家服务、直升机停机坪

2. 【Eagles Nest - 罗素（北岛/Bay of Islands）】
   品牌: 独立豪华品牌
   房型: 私人别墅（整栋租用）
   价格: NZD 8,000/晚 约¥33,600/晚
   链接: https://www.eaglesnest.co.nz
   特色: 360度海湾景观，极致隐私

3. 【The Rees Hotel - 皇后镇湖畔】
   品牌: 顶级精品酒店
   位置: 皇后镇镇区，瓦卡蒂普湖畔
   房型: 总统套房 Presidential Suite
   面积: 220㎡双卧室套房
   价格: NZD 2,800/晚 约¥11,760/晚
   链接: https://www.therees.co.nz
   特色: 湖景无边际泳池、私人码头、24小时管家

4. 【Blanket Bay - 瓦纳卡附近】
   品牌: Relais & Châteaux
   位置: 格林诺基（Glenorchy）旁峡湾入口
   房型: Lodge Suite
   价格: NZD 2,200/晚 约¥9,240/晚
   链接: https://www.blanketbay.com
   特色: 荒野私属牧场，直升机可达，世外桃源
"""

    # Michelin restaurants NZ
    if ("米其林" in q or "michelin" in q or "餐厅" in q or "restaurant" in q) and ("新西兰" in q or "zealand" in q or "皇后镇" in q or "queenstown" in q or "奥克兰" in q):
        return """搜索结果: 新西兰顶级餐厅

1. 【Amisfield Winery & Bistro - 皇后镇】
   描述: 新西兰最受赞誉的葡萄园餐厅，Just Cook For Us多道菜盲品套餐
   星级: 非米其林但Cuisine Magazine最高评级（等同米其林体验）
   菜系: 新西兰现代料理
   人均: NZD 250 约¥1,050
   链接: https://www.amisfield.co.nz
   特色: 葡萄园景观，配餐酒选自当地优质酒庄

2. 【Pasture - 奥克兰】
   描述: 新西兰唯一获国际认可的Fine Dining（Michelin Guide Singapore 1⭐参考级别）
   菜系: 炭火料理，季节性新西兰食材
   人均: NZD 350 约¥1,470
   链接: https://www.pastureakl.com
   特色: 主厨餐桌体验，限12席

3. 【Botswana Butchery - 皇后镇】
   描述: 皇后镇最高端牛排餐厅，湖景露台
   菜系: 新西兰牛肉/羊肉
   人均: NZD 180 约¥756
   链接: https://www.botswanabutchery.co.nz
"""

    # Private chef
    if ("私人主厨" in q or "private chef" in q or "定制晚宴" in q):
        return """搜索结果: 私人主厨服务

1. 【Queenstown Private Chef Service】
   描述: 顶级私人主厨上门服务，别墅/游艇均可
   主厨背景: 前高级餐厅主厨，可定制菜单
   时长: 全晚（含购买食材、烹饪、服务、清洁）
   价格: NZD 800-1,500/人 约¥3,360-6,300/人
   链接: https://www.privatechiefnz.co.nz
   特色: 支持中英文沟通，可定制中西融合菜单
"""

    # Generic catch-all
    return f"""搜索结果: "{query}"

未找到完全匹配结果。
建议：
1. 请联系当地专属礼宾部获取定制报价
2. 参考我们的签约供应商列表
3. 标注"需单独预订"

---
通用参考链接: https://www.newzealand.com/cn/luxury/
"""


if __name__ == "__main__":
    args = sys.argv[1:]
    
    if len(args) == 0:
        print("flyai - Luxury Travel Search Tool")
        print("Usage: flyai keyword-search --query <query>")
        sys.exit(0)
    
    if args[0] == "keyword-search":
        query = ""
        i = 1
        while i < len(args):
            if args[i] == "--query" and i + 1 < len(args):
                query = args[i + 1]
                i += 2
            else:
                i += 1
        
        if not query:
            print("Error: --query is required", file=sys.stderr)
            sys.exit(1)
        
        result = mock_keyword_search(query)
        print(result)
    else:
        print(f"Unknown command: {args[0]}", file=sys.stderr)
        sys.exit(1)
FLYAI_EOF

chmod +x /usr/local/bin/flyai

echo "✅ flyai CLI mock installed at /usr/local/bin/flyai"
echo "✅ Setup complete"