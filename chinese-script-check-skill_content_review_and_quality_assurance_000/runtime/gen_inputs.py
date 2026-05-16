import os
import random

random.seed(42)

base = "/workspace"

# Create distractor directory structure
dirs = [
    "production/scripts/drafts",
    "production/scripts/archive",
    "production/storyboard/rough",
    "production/storyboard/final",
    "production/casting/auditions",
    "production/casting/confirmed",
    "production/schedule/week1",
    "production/schedule/week2",
    "production/budget/equipment",
    "production/budget/crew",
    "production/notes/director",
    "production/notes/producer",
]

for d in dirs:
    os.makedirs(os.path.join(base, d), exist_ok=True)

# Distractor files
distractors = {
    "production/scripts/drafts/outline_v1.txt": "第一幕：相遇\n第二幕：误会\n第三幕：和解\n（大纲草稿，待细化）",
    "production/scripts/archive/script_v0.1.txt": "这是最早的剧本草稿，已废弃。角色设定尚未确定。",
    "production/storyboard/rough/scene1_notes.txt": "场景一分镜备注：广角镜头，展示城市全景，然后推进到咖啡馆门口。",
    "production/storyboard/final/approved_shots.txt": "已批准镜头列表：\nShot 001 - EXT 咖啡馆外 - 日\nShot 002 - INT 咖啡馆内 - 日",
    "production/casting/auditions/candidates.txt": "试镜候选人：\n张伟 - 男主角候选\n李梅 - 女主角候选\n王芳 - 女配角候选",
    "production/casting/confirmed/final_cast.txt": "确定演员表：\n男主角 陈明 - 张伟 饰\n女主角 林晓雨 - 李梅 饰\n女配角 苏婷 - 王芳 饰",
    "production/schedule/week1/shooting_plan.txt": "第一周拍摄计划：\n周一：场景1、2\n周二：场景3、4\n周三：场景5、6",
    "production/schedule/week2/shooting_plan.txt": "第二周拍摄计划：\n周一：补拍场景2\n周二：场景7、8\n周三：杀青宴",
    "production/budget/equipment/camera_rental.txt": "摄影机租赁费用：\nARRI ALEXA Mini LF - 3000元/天\n镜头组 - 800元/天",
    "production/budget/crew/crew_fees.txt": "剧组人员费用：\n导演 - 50000元\n摄影指导 - 30000元\n美术指导 - 20000元",
    "production/notes/director/creative_vision.txt": "导演阐述：\n本片希望呈现都市年轻人在压力下的情感状态，风格写实，色调偏冷。",
    "production/notes/producer/production_notes.txt": "制片备忘：\n1. 确认取景地许可证\n2. 联系道具公司\n3. 确认演员档期",
}

for path, content in distractors.items():
    with open(os.path.join(base, path), "w", encoding="utf-8") as f:
        f.write(content)

# THE MAIN SCRIPT FILE - with embedded continuity errors
script_content = """《错过》短片剧本

编剧：张华
版本：V2.3
日期：2024年3月15日

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

【场景一】INT. 咖啡馆内景 — 上午9:00

（晴天，阳光透过玻璃窗洒入咖啡馆，暖光氛围。）

女主角**林晓雨**身穿红色连衣裙，戴着珍珠耳环，左手拿着一杯满满的热咖啡，右手翻看着一份厚厚的合同文件，神情专注。

咖啡馆内轻音乐流淌，几位客人低声交谈。

男主角**陈明**推门而入，身穿深蓝色西装，打着深红色领带，提着一个黑色皮质公文包。他四处张望，眼神中透露出一丝焦虑。

陈明（快步走向林晓雨，语气急促）：
"晓雨，不好意思，堵车了，让你久等了。"

林晓雨（抬头，微微一笑）：
"没事，我刚到。你看一下这份合同，有几个条款我觉得需要讨论。"

陈明坐下，将公文包放在椅子旁，从公文包侧袋掏出手机看了看时间，随手将手机塞进了左侧裤兜。

林晓雨将合同推到陈明面前，两人开始认真讨论条款细节。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

【场景二】INT. 咖啡馆内景 — 上午9:15（场景一结束约十五分钟后）

（与场景一连续，时间仅过去十五分钟，二人仍在同一咖啡馆同一桌位。）

林晓雨身穿牛仔裤和白色T恤，将一张名片递给陈明。

林晓雨：
"这是我们法务顾问的联系方式，有任何合同疑问可以直接问他。"

陈明（接过名片，点头）：
"好的，我回头让我们团队也看看。对了，下午你有空吗？我们去上海见一下王总，顺便把合同的事情当面敲定。"

林晓雨（略作思考）：
"上海？从北京过去要飞一个小时，下午来得及吗？"

陈明（挥手示意）：
"没问题，我们开车去吧，路上可以继续聊。"

苏婷（林晓雨的好友，突然从门外走进来，穿着橙色卫衣）：
"晓雨！你在这啊！"

林晓雨：
"苏婷，你怎么来了？"

苏婷（看向陈明）：
"这位是？"

林晓雨（介绍）：
"这是陈明，我们合作项目的对接人。陈明，这是我朋友苏婷。"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

【场景三】EXT. 咖啡馆外景 — 上午9:30

（三人从咖啡馆走出，室外阳光明媚，气温适宜。）

陈明（走出门，回头看了看咖啡馆）：
"时间不早了，我先走了，下午的事情联系。"

林晓雨点头，目送陈明离开。

陈明走向停车场方向，他的眼神充满了对未来憧憬着。

苏婷凑近林晓雨，低声说：
"这个陈明，看起来挺靠谱的嘛。"

林晓雨（轻笑）：
"先看看吧，合同还没签呢。"

苏婷（突然想起什么，拉住小雨的手臂）：
"对了，晚上有没有空？我们去吃火锅！"

林晓雨：
"好啊，你定地方。"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

【场景四】EXT. 停车场 — 上午9:35

（停车场位于咖啡馆旁，室外，阳光明媚。）

陈明走到自己的车旁，从包里掏出手机，拨打电话。

陈明（电话中，语气轻松）：
"喂，王总，我这边和对方谈得差不多了，下午应该能确认方案……好的好的，下午见。"

挂断电话，陈明打开车门坐进去，发动汽车，驶离停车场。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

【场景五】INT. 林晓雨的办公室 — 下午2:00

（现代化写字楼内景，明亮整洁。林晓雨坐在办公桌前。）

林晓雨的同事小张走进来：
"晓雨姐，陈明那边来电话了，说下午的会议改到线上了。"

林晓雨（皱眉）：
"线上？怎么突然改了？"

小张（耸肩）：
"好像是王总临时有事，去不了上海。"

林晓雨拿起桌上的手机，看到陈明发来的微信消息，叹了口气，开始回复。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

剧本完
"""

script_path = os.path.join(base, "production/scripts/script_v2.3.txt")
with open(script_path, "w", encoding="utf-8") as f:
    f.write(script_content)

print("Workspace generated successfully.")
print(f"Main script: {script_path}")
print(f"Total distractor files: {len(distractors)}")