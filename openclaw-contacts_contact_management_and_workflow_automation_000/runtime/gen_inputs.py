import os
import random
import textwrap

random.seed(42)

workspace = "/workspace"

# --- Directory structure ---
dirs = [
    "memory/contacts/contacts.d",
    "memory/contacts/channels",
    "memory/logs",
    "memory/tasks",
    "memory/notes",
    "skills/contacts/scripts",
    "skills/messaging",
    "skills/calendar",
    "projects/remix-collab",
    "projects/visual-identity",
    "tmp/inbox",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# --- schema.md (as per SKILL.md structure) ---
schema_md = textwrap.dedent("""\
    # Contact Schema

    Each contact YAML must include the required fields as described in the contacts skill.

    contact_id: internal unique identifier (also the filename without .yaml)
    name: display name
    channels.feishu.open_id: Feishu open_id for @ routing
    channels.feishu.nickname: display name inside Feishu groups
    channels.feishu.chat_id: group chat_id
    channels.feishu.account_id: accountId used by the message tool
    """)
with open(os.path.join(workspace, "memory/contacts/schema.md"), "w") as f:
    f.write(schema_md)

# --- feishu.md channel guidance ---
feishu_md = textwrap.dedent("""\
    # 飞书交流规范

    - 使用 open_id 进行 @ 操作
    - 发送消息时，message 工具需要传入 accountId（即 account_id 字段）
    - 群 chat_id 用于确定消息发送目标群
    - 群内显示名用 nickname 字段
    """)
with open(os.path.join(workspace, "memory/contacts/channels/feishu.md"), "w") as f:
    f.write(feishu_md)

# --- Existing contact (mala) as reference ---
mala_yaml = textwrap.dedent("""\
    contact_id: "mala"
    name: "麻辣小龙虾"

    channels:
      feishu:
        open_id: "ou_abc123def456"
        nickname: "麻辣小龙虾"
        chat_id: "oc_group_main001"
        account_id: "mala_feishu"

    internal:
      agent_id: "mala"
      role: "创意总监"
      project: "remix-collab"

    preferences:
      preferred: "feishu"
      language: "中文"
      formality: "随意"

    notes:
      - "喜欢用表情包回复"
    """)
with open(os.path.join(workspace, "memory/contacts/contacts.d/mala.yaml"), "w") as f:
    f.write(mala_yaml)

# --- The list.sh script ---
list_sh = textwrap.dedent("""\
    #!/bin/bash
    # List all contacts
    DIR="$(cd "$(dirname "$0")/../../../memory/contacts/contacts.d" 2>/dev/null && pwd)"
    if [ ! -d "$DIR" ]; then
        echo "contacts.d not found at $DIR"
        exit 1
    fi
    for f in "$DIR"/*.yaml; do
        [ -f "$f" ] || continue
        contact_id=$(basename "$f" .yaml)
        name=$(grep '^name:' "$f" | head -1 | sed 's/name: *//;s/"//g')
        echo "$contact_id | $name"
    done
    """)
with open(os.path.join(workspace, "skills/contacts/scripts/list.sh"), "w") as f:
    f.write(list_sh)

# --- The search.sh script ---
search_sh = textwrap.dedent("""\
    #!/bin/bash
    # Search contacts by name
    QUERY="$1"
    DIR="$(cd "$(dirname "$0")/../../../memory/contacts/contacts.d" 2>/dev/null && pwd)"
    if [ -z "$QUERY" ]; then
        echo "Usage: search.sh <name>"
        exit 1
    fi
    grep -rl "$QUERY" "$DIR" 2>/dev/null | while read f; do
        contact_id=$(basename "$f" .yaml)
        name=$(grep '^name:' "$f" | head -1 | sed 's/name: *//;s/"//g')
        echo "$contact_id | $name | $f"
    done
    """)
with open(os.path.join(workspace, "skills/contacts/scripts/search.sh"), "w") as f:
    f.write(search_sh)

# --- The get.sh script ---
get_sh = textwrap.dedent("""\
    #!/bin/bash
    # Get a single contact by contact_id
    CONTACT_ID="$1"
    DIR="$(cd "$(dirname "$0")/../../../memory/contacts/contacts.d" 2>/dev/null && pwd)"
    if [ -z "$CONTACT_ID" ]; then
        echo "Usage: get.sh <contact_id>"
        exit 1
    fi
    FILE="$DIR/$CONTACT_ID.yaml"
    if [ ! -f "$FILE" ]; then
        echo "Contact not found: $CONTACT_ID"
        exit 1
    fi
    cat "$FILE"
    """)
with open(os.path.join(workspace, "skills/contacts/scripts/get.sh"), "w") as f:
    f.write(get_sh)

# --- THE MESSY ONBOARDING SHEET (the raw input the agent must process) ---
# This is the core "problem" — unstructured data the agent must parse and register
onboarding_sheet = textwrap.dedent("""\
    ===== 新协作者入职联络表 =====
    整理人：项目协调助手
    日期：2024-06-15
    备注：以下人员已确认加入「视觉混音」项目，请尽快录入通讯录，方便后续飞书联系。

    ---

    1. 联系人：节拍制作人-零
       英文ID建议: zero-producer
       飞书账号：
         - open_id: ou_z3r0pr0duc3r9988
         - 群内昵称: 零·节拍
         - 所属群 chat_id: oc_visualremix_main
         - 消息工具账户名: zero_feishu_acct
       角色: 音乐制作人
       项目: visual-remix
       沟通偏好: 中文，比较正式，不喜欢语音消息
       认识途径: 项目招募

    ---

    2. 联系人：像素画师阿橙
       英文ID建议: acheng-pixel
       飞书账号：
         - open_id: ou_ACH3NGp1x3L2077
         - 群内昵称: 阿橙🎨
         - 所属群 chat_id: oc_visualremix_main
         - 消息工具账户名: acheng_pixel_fs
       角色: 视觉设计师
       项目: visual-identity
       沟通偏好: 偏好发图，语言随意，中英混用
       坑: 回复较慢，重要事项要@两次

    ---

    3. 联系人：运营统筹-宋微
       英文ID建议: songwei-ops
       飞书账号：
         - open_id: ou_S0NGW31ops5566
         - 群内昵称: 宋微运营
         - 所属群 chat_id: oc_ops_collab_007
         - 消息工具账户名: songwei_ops_acct
       角色: 运营统筹
       沟通偏好: 严肃正式，只在工作时间回复
       认识途径: 客户推荐

    ---

    任务要求：
    - 请将上述三人录入通讯录
    - 完成后，请使用通讯录查询工具查询「像素画师阿橙」的完整联系人信息，
      并将查询结果保存到文件 acheng_lookup.txt
    """)
with open(os.path.join(workspace, "tmp/inbox/onboarding_sheet.txt"), "w") as f:
    f.write(onboarding_sheet)

# --- Distractor files ---
distractor_files = {
    "memory/logs/session_2024-06-10.log": "Agent session started.\nTask: remix review\nCompleted: yes\n",
    "memory/tasks/pending.md": "# Pending Tasks\n- Review new collab contracts\n- Update project timeline\n",
    "memory/notes/project_ideas.txt": "- Try generative beat sync\n- Pixel art + music video\n",
    "skills/messaging/README.md": "# Messaging Skill\nSend messages via Feishu.\nRequired param: accountId\n",
    "skills/calendar/events.json": '{"events": [{"date": "2024-06-20", "title": "Kickoff Meeting"}]}\n',
    "projects/remix-collab/brief.md": "# Remix Collab\nVision: blend electronic + visual art.\nTeam: TBD\n",
    "projects/visual-identity/assets.txt": "logo_v1.png\nbanner_draft.svg\n",
    "tmp/inbox/old_contacts_dump.txt": "Old data - DO NOT USE\nname: 废弃联系人\nfeishu: unknown\n",
    "memory/contacts/channels/wechat.md": "# 微信规范\n暂不支持，请使用飞书。\n",
    "skills/contacts/scripts/README.md": "# Contact Scripts\nlist.sh, search.sh, get.sh\nAdd this dir to PATH before use.\n",
}
for rel_path, content in distractor_files.items():
    full_path = os.path.join(workspace, rel_path)
    with open(full_path, "w") as f:
        f.write(content)

print("Workspace generated successfully.")
print(f"Key input file: {os.path.join(workspace, 'tmp/inbox/onboarding_sheet.txt')}")