#!/bin/bash
set -e

HOME_DIR="/home/agent"
SKILL_DIR="$HOME_DIR/.qclaw/skills/guangzhou-daily-news/scripts"

# ─── 1. Create the mock HTTP server that simulates gz-cmc.com ─────────────────
cat > /tmp/mock_news_server.py << 'MOCK_SERVER_EOF'
#!/usr/bin/env python3
"""
Mock server simulating gz-cmc.com / huacheng.gz-cmc.com
Serves a list page and individual article detail pages.
"""
from flask import Flask, Response
import datetime

app = Flask(__name__)

ARTICLES = [
    {"id": "001", "title": "国家对成品油价采取临时调控措施", "category": "要闻",
     "time": "2026-03-23 15:03", "reporter": "张三", "editor": "李四",
     "body": "3月9日以来受美以伊冲突加剧影响，国际油价大幅上涨。为减缓冲击，国家发展改革委决定对国内成品油价格采取临时调控措施，暂缓上调国内成品油价格，继续执行现行价格水平。此举有效保障了民众日常出行和物流运输的成本稳定，各地加油站执行统一调价通知，社会反响积极正面。"},
    {"id": "002", "title": "全球第六！独角兽扎堆！广州这份科创成绩单太燃了", "category": "科技",
     "time": "2026-03-23 14:45", "reporter": "王五", "editor": "赵六",
     "body": "广州科技创新指数再创新高，全球独角兽企业排名跃升至第六位。大湾区科技走廊建设提速，多家独角兽企业宣布落户广州。广州市科技局发布最新数据，显示全市高新技术企业数量突破一万家，研发投入占GDP比重持续上升，科技金融融合不断深化，创新生态体系日趋完善。"},
    {"id": "003", "title": "念念不忘，92岁的他在街头卖书二十多年", "category": "文化",
     "time": "2026-03-23 13:22", "reporter": "陈七", "editor": "林八",
     "body": "在广州老城区的一条小巷里，92岁的老人坚守书摊二十余载。他说，卖书不为钱，只为让街坊邻居有书可读。这位老人的故事感动了无数市民，也引发了社会对文化传承与阅读推广的广泛关注。每逢周末，书摊前总有不少年轻人驻足翻阅，老人的精神成为城市文化的一道温暖风景线。"},
    {"id": "004", "title": "广州地铁新线开通在即，市民翘首以盼", "category": "要闻",
     "time": "2026-03-23 12:00", "reporter": "黄九", "editor": "周十",
     "body": "广州地铁新线路即将于本月底正式开通运营，沿线居民期盼已久。新线全长约30公里，设站18个，覆盖多个重要商业区和居住区，预计日客流量将超过50万人次，极大缓解地面交通压力，改善市民出行体验，带动沿线经济发展和城市更新进程。"},
    {"id": "005", "title": "春暖花开，广州各大公园迎来赏花热潮", "category": "生活",
     "time": "2026-03-23 11:30", "reporter": "", "editor": "吴编辑",
     "body": "三月下旬，广州气温回暖，各大公园木棉花、紫荆花竞相开放，吸引大批市民前来踏青赏花。越秀公园、天河公园、海珠湿地等热门景点游人如织，市民纷纷拍照留念，感受春日美好时光。园林部门提醒市民注意保护植物，文明赏花，共同维护公共绿化环境。"},
    {"id": "006", "title": "粤港澳大湾区跨境电商规模突破新高", "category": "经济",
     "time": "2026-03-23 11:00", "reporter": "郑商", "editor": "冯编",
     "body": "粤港澳大湾区跨境电商业务再创历史新高，首季度交易额同比增长逾40%。广州南沙、深圳前海、珠海横琴三大自贸区协同发力，跨境电商综合试验区政策红利持续释放，带动区域外贸新动能加速集聚，吸引众多国际品牌和平台入驻，形成强大的跨境贸易生态链。"},
    {"id": "007", "title": "广州将举办国际美食节，百国美食汇聚一堂", "category": "生活",
     "time": "2026-03-23 10:45", "reporter": "许美", "editor": "何编",
     "body": "一年一度的广州国际美食节将于下月盛大开幕，来自全球逾百个国家和地区的特色美食将集中亮相。本届美食节设有主题展区、烹饪表演、文化互动等多个板块，预计吸引游客超200万人次。广州作为美食之都，此次盛会将进一步擦亮城市美食名片，带动旅游和文化消费升级。"},
    {"id": "008", "title": "广东省出台新政助力民营企业融资", "category": "经济",
     "time": "2026-03-23 10:20", "reporter": "曹政", "editor": "严编",
     "body": "广东省政府近日发布支持民营企业发展的一揽子政策，重点在融资担保、知识产权质押、供应链金融等方面加大支持力度。新政策明确要求银行金融机构提高民营企业贷款占比，并设立专项引导基金，为科技型中小企业提供低息贷款和股权融资通道，进一步优化营商环境。"},
    {"id": "009", "title": "广州花都区启动千亩花田种植计划", "category": "农业",
     "time": "2026-03-23 09:55", "reporter": "", "editor": "",
     "body": "花都区今年启动千亩连片花田种植示范项目，重点发展玫瑰、向日葵、薰衣草等观赏性花卉，打造城郊休闲农业新品牌。项目预计带动周边农户增收，同时发展花卉相关文创和旅游产品，实现一二三产业融合发展，助力乡村振兴战略落地见效，成为广州近郊旅游新亮点。"},
    {"id": "010", "title": "华南理工大学科研团队突破新型电池技术", "category": "科技",
     "time": "2026-03-23 09:30", "reporter": "宋研", "editor": "韩编",
     "body": "华南理工大学材料科学与工程学院研究团队近日在固态锂电池领域取得重大突破，成功研制出能量密度超过600Wh/kg的新型固态电池原型。相关成果已在国际顶级期刊发表，获得学界广泛关注，有望加速推动电动汽车和储能设备的技术升级，为国家新能源战略提供核心技术支撑。"},
    {"id": "011", "title": "广州港货物吞吐量保持全球前列", "category": "经济",
     "time": "2026-03-23 09:15", "reporter": "唐港", "editor": "邓编",
     "body": "广州港最新发布数据显示，今年一季度货物吞吐量同比增长8.2%，集装箱吞吐量增长11.5%，继续保持全球港口前列地位。南沙港区自动化泊位投入运营后，装卸效率大幅提升，运营成本显著下降，吸引更多航运公司开辟新航线，巩固广州作为全球重要航运枢纽的核心地位。"},
    {"id": "012", "title": "广州市民大量参与垃圾分类，获国家表彰", "category": "环保",
     "time": "2026-03-23 08:55", "reporter": "朱环", "editor": "秦编",
     "body": "广州垃圾分类工作连续三年获国家生态文明建设优秀城市称号。全市垃圾分类正确率达到85%，厨余垃圾资源化利用率大幅提升，可回收物回收量年均增长20%以上。市城管部门表示，广大市民的积极参与是成功的关键，下一步将进一步完善配套设施，推广智能分类回收箱，提升分类便利度。"},
    {"id": "013", "title": "羊城书展本周开幕，百万册图书参展", "category": "文化",
     "time": "2026-03-23 08:40", "reporter": "孟文", "editor": "尤编",
     "body": "第三十届羊城书展本周在广州琶洲展馆盛大开幕，共有来自全国600余家出版机构参展，展出图书超过百万册。本届书展主题为"书香湾区·阅读未来"，设置主题阅读、新书首发、名家签售等多个特色活动，吸引众多书迷和市民前来淘书、品读，再现广州浓厚书香文化氛围。"},
    {"id": "014", "title": "广州天气预报：未来三天持续晴热", "category": "生活",
     "time": "2026-03-23 08:20", "reporter": "", "editor": "气象编辑",
     "body": "广州市气象局发布未来三天天气预报：受副热带高压控制，广州地区将持续晴热天气，最高气温可达32摄氏度，紫外线指数偏高，市民外出请注意防晒补水。周末起南海低压槽北抬，广州可能迎来短时降水，届时气温有所回落，请市民关注最新天气预报及时调整出行计划。"},
    {"id": "015", "title": "广州创业生态报告：新增注册企业创历史新高", "category": "经济",
     "time": "2026-03-23 08:00", "reporter": "鲁创", "editor": "丁编",
     "body": "广州市市场监督管理局最新发布创业生态报告显示，今年一季度全市新注册市场主体数量突破12万家，同比增长15.3%，创历史同期新高。科技类、文化创意类企业注册数增速最为显著，分别增长28%和22%。天河、黄埔等区持续吸引高成长性企业聚集，创业生态圈活力充沛。"},
    {"id": "016", "title": "广州推进城中村改造，提升居民生活品质", "category": "要闻",
     "time": "2026-03-22 22:10", "reporter": "吕城", "editor": "施编",
     "body": "广州市住房和城乡建设局宣布，今年将新启动15个城中村改造项目，涉及改造面积约800万平方米，预计安置居民近10万户。改造方案充分考虑历史文化保护与现代宜居需求，引入社会资本参与开发，通过"留改拆"模式因地制宜，既保留城市记忆，又改善居住条件，提升城市整体形象。"},
    {"id": "017", "title": "南方医科大学发布新冠后遗症研究报告", "category": "健康",
     "time": "2026-03-22 21:30", "reporter": "卫医", "editor": "严健编",
     "body": "南方医科大学流行病学团队历时两年，对广州5000余名新冠康复者进行追踪研究，最新发布的报告显示，约18%的患者在康复6个月后仍存在不同程度的长期症状，以疲劳、睡眠障碍、记忆力下降为主。研究团队建议建立新冠后遗症专科门诊，加强长期随访和干预治疗，保障康复患者健康权益。"},
    {"id": "018", "title": "广州国际马拉松报名人数突破十万", "category": "体育",
     "time": "2026-03-22 20:45", "reporter": "蒋运", "editor": "韦编",
     "body": "2026广州国际马拉松报名通道开放不到24小时，注册人数即突破10万大关，创历届报名人数新纪录。组委会表示，本届马拉松将优化赛道设计，新增若干打卡点和补给站，并引入智能计时和互动AR装置，为参赛选手和观众带来更丰富的运动体验，进一步彰显广州作为国际体育赛事城市的品牌价值。"},
    {"id": "019", "title": "广州日报记者深度调查：网络诈骗新手法揭秘", "category": "社会",
     "time": "2026-03-22 20:00", "reporter": "李调", "editor": "毛编",
     "body": "广州日报记者历时三个月深度调查，揭秘当前最新网络诈骗手法。犯罪分子利用AI换脸技术冒充熟人，通过短视频平台建立信任后实施诈骗，受害人群涉及各年龄层。公安部门提示市民，接到异常转账请求务必当面或视频核实身份，不轻易向陌生账户转账，发现可疑情况立即拨打96110举报。"},
    {"id": "020", "title": "广州首个碳中和示范园区建设全面启动", "category": "环保",
     "time": "2026-03-22 19:15", "reporter": "", "editor": "汪绿编",
     "body": "广州市首个零碳示范产业园区在南沙区正式破土动工，园区规划占地1200亩，将综合应用光伏发电、绿色建筑、智慧能源管理等先进技术，力争于2028年实现全区碳中和目标。项目吸引30余家绿色科技企业签约入驻，预计创造就业岗位超1万个，为广州实现碳达峰碳中和目标提供示范样板。"},
    {"id": "021", "title": "广州中学生在国际数学奥林匹克获佳绩", "category": "教育",
     "time": "2026-03-22 18:30", "reporter": "程教", "editor": "范编",
     "body": "在刚刚结束的2026国际数学奥林匹克竞赛中，广州中学生代表团斩获3金2银1铜的优异成绩，创历史最佳战绩。获奖选手均来自广州市重点中学，他们展现了扎实的数学功底和卓越的解题能力。教育部门表示，将进一步加大数学拔尖人才培养投入，完善竞赛选拔机制，推动基础学科教育高质量发展。"},
    {"id": "022", "title": "广州中山大学附属医院引进最新手术机器人", "category": "健康",
     "time": "2026-03-22 17:55", "reporter": "方医", "editor": "华健编",
     "body": "中山大学附属第一医院近日正式引入最新一代达芬奇Xi手术机器人系统，标志着医院微创外科技术迈上新台阶。该系统具有4K三维视野、精密操控和颤抖过滤功能，已成功完成首批10例复杂腹腔镜手术，患者术后恢复时间平均缩短30%。医院计划将手术机器人技术推广至更多外科专科，造福更多患者。"},
]

def make_list_page():
    """Generate HTML mimicking gz-cmc.com news list page"""
    items_html = ""
    for art in ARTICLES:
        items_html += f'''
        <div class="news-item">
            <a href="/article/{art["id"]}" class="news-title">{art["title"]}</a>
            <span class="news-time">{art["time"]}</span>
            <span class="news-category">{art["category"]}</span>
        </div>
        '''
    return f"""<!DOCTYPE html>
<html>
<head><title>新花城 - 广州日报</title><meta charset="utf-8"/></head>
<body>
<div class="news-list">
{items_html}
</div>
</body>
</html>"""

def make_article_page(art):
    """Generate HTML mimicking a gz-cmc.com article detail page"""
    reporter_line = ""
    if art["reporter"] and art["editor"]:
        reporter_line = f'<p class="byline">文/广州日报全媒体记者 {art["reporter"]} 编辑/广州日报全媒体编辑 {art["editor"]}</p>'
    elif art["reporter"]:
        reporter_line = f'<p class="byline">文/广州日报全媒体记者 {art["reporter"]}</p>'
    elif art["editor"]:
        reporter_line = f'<p class="byline">编辑/广州日报全媒体编辑 {art["editor"]}</p>'

    return f"""<!DOCTYPE html>
<html>
<head><title>{art["title"]} - 新花城</title><meta charset="utf-8"/></head>
<body>
<div class="article">
  <h1 class="article-title">{art["title"]}</h1>
  <div class="article-meta">
    <span class="pub-time">{art["time"]}</span>
    <span class="category-tag">{art["category"]}</span>
  </div>
  <div class="article-body">
    <p>{art["body"]}</p>
  </div>
  {reporter_line}
</div>
</body>
</html>"""

@app.route('/')
@app.route('/index.html')
def index():
    return Response(make_list_page(), content_type='text/html; charset=utf-8')

@app.route('/article/<art_id>')
def article(art_id):
    for art in ARTICLES:
        if art["id"] == art_id:
            return Response(make_article_page(art), content_type='text/html; charset=utf-8')
    return Response("<html><body>404 Not Found</body></html>", status=404, content_type='text/html; charset=utf-8')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8765, debug=False)
MOCK_SERVER_EOF

chmod +x /tmp/mock_news_server.py

# ─── 2. Start the mock server in the background ──────────────────────────────
python3 /tmp/mock_news_server.py &
sleep 2
echo "Mock server started: $(curl -s http://localhost:8765/ | head -5)"

# ─── 3. Create the fetch_news.py script in the skill directory ───────────────
cat > /home/agent/.qclaw/skills/guangzhou-daily-news/scripts/fetch_news.py << 'FETCH_SCRIPT_EOF'
#!/usr/bin/env python3
"""
广州日报新花城新闻获取脚本
版本: 2.1
用法: python3 fetch_news.py [--base-url URL]
"""
import requests
from bs4 import BeautifulSoup
import datetime
import os
import sys
import argparse
import re

def parse_args():
    parser = argparse.ArgumentParser(description='广州日报新花城新闻获取')
    parser.add_argument('--base-url', default=os.environ.get('GZ_NEWS_BASE_URL', 'https://gz-cmc.com'),
                        help='新花城网站基础URL (默认: https://gz-cmc.com, 可通过 GZ_NEWS_BASE_URL 环境变量覆盖)')
    parser.add_argument('--output-dir', default=os.path.expanduser('~/News'),
                        help='输出目录 (默认: ~/News)')
    parser.add_argument('--max-articles', type=int, default=25,
                        help='最大获取文章数 (默认: 25, 范围: 20-30)')
    return parser.parse_args()

def fetch_news_list(base_url, session):
    """获取新闻列表"""
    resp = session.get(base_url, timeout=15)
    resp.encoding = 'utf-8'
    soup = BeautifulSoup(resp.text, 'html.parser')
    
    articles = []
    for item in soup.select('.news-item'):
        link_tag = item.select_one('.news-title')
        time_tag = item.select_one('.news-time')
        cat_tag = item.select_one('.news-category')
        if link_tag:
            href = link_tag.get('href', '')
            if href and not href.startswith('http'):
                href = base_url.rstrip('/') + href
            articles.append({
                'title': link_tag.get_text(strip=True),
                'url': href,
                'time': time_tag.get_text(strip=True) if time_tag else '',
                'category': cat_tag.get_text(strip=True) if cat_tag else '综合',
            })
    return articles

def fetch_article_detail(url, session):
    """获取文章详情：摘要、记者、编辑"""
    try:
        resp = session.get(url, timeout=15)
        resp.encoding = 'utf-8'
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # 摘要：文章正文前200字
        body_div = soup.select_one('.article-body')
        summary = ''
        if body_div:
            text = body_div.get_text(separator=' ', strip=True)
            summary = text[:200] + ('...' if len(text) > 200 else '')
        
        # 记者/编辑提取
        reporter = '—'
        editor = '—'
        byline = soup.select_one('.byline')
        if byline:
            byline_text = byline.get_text(strip=True)
            # 支持多种格式
            r_match = re.search(r'记者[：:\s]+([^\s/编辑，。]+)', byline_text)
            e_match = re.search(r'编辑[：:\s]+([^\s/，。]+)', byline_text)
            if r_match:
                reporter = r_match.group(1).strip()
            if e_match:
                editor = e_match.group(1).strip()
        
        return summary, reporter, editor
    except Exception as e:
        return '', '—', '—'

def get_category_emoji(category):
    mapping = {
        '要闻': '🔴', '科技': '💻', '文化': '📚', '生活': '🌿',
        '经济': '💰', '国际': '🌍', '社会': '👥', '体育': '⚽',
        '健康': '🏥', '教育': '🎓', '环保': '♻️', '农业': '🌾',
    }
    return mapping.get(category, '📌')

def format_markdown(articles, date_str):
    """生成符合规范的 Markdown 内容"""
    count = len(articles)
    lines = []
    lines.append(f'# 📰 广州日报新闻简报')
    lines.append(f'')
    lines.append(f'📅 {date_str} · 来源：新花城 · 共 {count} 条')
    lines.append(f'')
    lines.append(f'---')
    lines.append(f'')
    
    for i, art in enumerate(articles, 1):
        emoji = get_category_emoji(art.get('category', ''))
        lines.append(f'> ## {i}. {art["title"]}')
        lines.append(f'> ')
        lines.append(f'> {emoji} {art.get("category", "综合")} · ⏰ {art.get("time", "")}')
        lines.append(f'> ')
        if art.get('summary'):
            lines.append(f'> {art["summary"]}')
            lines.append(f'> ')
        reporter = art.get('reporter', '—')
        editor = art.get('editor', '—')
        lines.append(f'> ✍️ 记者：**{reporter}** · 📝 编辑：**{editor}** · 🔗 [阅读原文]({art["url"]})')
        lines.append(f'')
    
    return '\n'.join(lines)

def main():
    args = parse_args()
    base_url = args.base_url.rstrip('/')
    output_dir = args.output_dir
    max_articles = max(20, min(30, args.max_articles))
    
    today = datetime.date.today().strftime('%Y-%m-%d')
    
    print(f'[INFO] 开始获取广州日报新闻，来源: {base_url}')
    
    session = requests.Session()
    session.headers.update({'User-Agent': 'Mozilla/5.0 (guangzhou-daily-news/2.1)'})
    
    # 获取新闻列表
    articles = fetch_news_list(base_url, session)
    articles = articles[:max_articles]
    print(f'[INFO] 获取到 {len(articles)} 条新闻标题')
    
    # 获取每篇详情
    for i, art in enumerate(articles):
        print(f'[INFO] 获取详情 [{i+1}/{len(articles)}]: {art["title"][:30]}...')
        summary, reporter, editor = fetch_article_detail(art['url'], session)
        art['summary'] = summary
        art['reporter'] = reporter
        art['editor'] = editor
    
    # 生成 Markdown
    md_content = format_markdown(articles, today)
    
    # 保存文件
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f'广州日报_{today}.md')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(md_content)
    
    print(f'[SUCCESS] 新闻已保存到: {output_path}')
    return output_path

if __name__ == '__main__':
    main()
FETCH_SCRIPT_EOF

chmod +x /home/agent/.qclaw/skills/guangzhou-daily-news/scripts/fetch_news.py
chown agent:agent /home/agent/.qclaw/skills/guangzhou-daily-news/scripts/fetch_news.py

# ─── 4. Create ~/News directory for the agent ────────────────────────────────
mkdir -p /home/agent/News
chown -R agent:agent /home/agent/News

echo "[SETUP COMPLETE] Mock server running on :8765, fetch_news.py ready."