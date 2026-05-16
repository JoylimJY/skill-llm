#!/bin/bash
set -e

# The ai_customer_service tool should already exist in the skill's installation.
# We need to ensure it is executable and on PATH.
# Per SKILL.md: command-tool is 'ai_customer_service', command-arg-mode is 'raw'

# Try to locate the tool
TOOL_PATH=$(which ai_customer_service 2>/dev/null || find / -name "ai_customer_service" -type f 2>/dev/null | head -1)

if [ -z "$TOOL_PATH" ]; then
    echo "[SETUP] ai_customer_service not found, creating a realistic mock implementation..."
    
    # Create a comprehensive mock that behaves per SKILL.md specification
    cat > /usr/local/bin/ai_customer_service << 'PYTHON_MOCK'
#!/usr/bin/env python3
"""
Mock implementation of ai_customer_service per SKILL.md specification.
Stores state in ~/.ai_customer_service/ directory.
"""
import sys
import json
import os
import re
import time
from pathlib import Path

STATE_DIR = Path.home() / ".ai_customer_service"
STATE_DIR.mkdir(exist_ok=True)
KB_FILE = STATE_DIR / "knowledge_base.json"
SESSION_FILE = STATE_DIR / "session.json"
STATS_FILE = STATE_DIR / "stats.json"

BUILTIN_KB = [
    {"question": "你们支持7天无理由退货吗？", "answer": "支持的，请在收到商品7天内申请退款。"},
    {"question": "运费由谁承担？", "answer": "非人为损坏由商家承担，人为损坏需买家承担。"},
    {"question": "发货需要多长时间？", "answer": "正常情况下24小时内发货，48小时内物流更新。"},
    {"question": "支持哪些支付方式？", "answer": "支持微信、支付宝、银行卡、货到付款。"},
    {"question": "如何查询物流？", "answer": "可以在\"我的订单\"中查看物流信息。"},
    {"question": "你们有实体店吗？", "answer": "目前只支持线上购买，全国可配送。"},
    {"question": "可以修改订单地址吗？", "answer": "未发货前可以修改，请联系客服处理。"},
    {"question": "退货地址在哪里？", "answer": "退货地址：广东省深圳市宝安区xxx，联系电话：400-xxx-xxxx"},
]

def load_kb():
    if KB_FILE.exists():
        with open(KB_FILE, encoding='utf-8') as f:
            return json.load(f)
    return list(BUILTIN_KB)

def save_kb(kb):
    with open(KB_FILE, 'w', encoding='utf-8') as f:
        json.dump(kb, f, ensure_ascii=False, indent=2)

def load_session():
    if SESSION_FILE.exists():
        with open(SESSION_FILE, encoding='utf-8') as f:
            return json.load(f)
    return {"history": [], "turn_count": 0}

def save_session(session):
    with open(SESSION_FILE, 'w', encoding='utf-8') as f:
        json.dump(session, f, ensure_ascii=False, indent=2)

def load_stats():
    if STATS_FILE.exists():
        with open(STATS_FILE, encoding='utf-8') as f:
            return json.load(f)
    return {
        "total_conversations": 0,
        "total_messages": 0,
        "faq_hits": 0,
        "intent_counts": {
            "refund": 0, "logistics": 0, "payment": 0,
            "complaint": 0, "suggestion": 0, "greeting": 0, "unknown": 0
        },
        "sentiment_counts": {"positive": 0, "neutral": 0, "negative": 0},
        "transfers_to_human": 0,
        "kb_entry_count": len(load_kb())
    }

def save_stats(stats):
    with open(STATS_FILE, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

def detect_intent(text):
    text = text.lower()
    if any(w in text for w in ['退货', '退款', '不想要', '退']):
        return 'refund'
    if any(w in text for w in ['物流', '快递', '到哪里', '发货', '快递']):
        return 'logistics'
    if any(w in text for w in ['支付', '付款', '怎么付', '分期']):
        return 'payment'
    if any(w in text for w in ['投诉', '差评', '失望', '太差', '太烂']):
        return 'complaint'
    if any(w in text for w in ['建议', '希望', '能够']):
        return 'suggestion'
    if any(w in text for w in ['你好', 'hi', 'hello', '您好', '喂']):
        return 'greeting'
    return 'unknown'

def detect_sentiment(text):
    positive_words = ['谢谢', '满意', '太好了', '不错', '好的', '感谢']
    negative_words = ['生气', '失望', '太差', '太烂', '投诉', '差评', '坏了', '愤怒', '质量差']
    pos = sum(1 for w in positive_words if w in text)
    neg = sum(1 for w in negative_words if w in text)
    if neg > pos:
        return 'negative'
    elif pos > neg:
        return 'positive'
    return 'neutral'

def find_faq_match(text, kb):
    for entry in kb:
        q_words = set(entry['question'].replace('？','').replace('?',''))
        t_words = set(text)
        overlap = len(q_words & t_words)
        if overlap >= 3:
            return entry['answer']
    return None

def cmd_chat(args_text):
    kb = load_kb()
    session = load_session()
    stats = load_stats()
    
    user_msg = args_text.strip()
    intent = detect_intent(user_msg)
    sentiment = detect_sentiment(user_msg)
    
    stats['total_messages'] += 1
    stats['intent_counts'][intent] = stats['intent_counts'].get(intent, 0) + 1
    stats['sentiment_counts'][sentiment] = stats['sentiment_counts'].get(sentiment, 0) + 1
    
    # Check FAQ match
    faq_answer = find_faq_match(user_msg, kb)
    
    if faq_answer:
        stats['faq_hits'] += 1
        response = f"📚 根据知识库为您解答：\n{faq_answer}"
    elif intent == 'complaint' or sentiment == 'negative':
        stats['transfers_to_human'] += 1
        response = ("非常抱歉给您带来不便！您的反馈非常重要。\n"
                   "⚠️ 系统检测到您的问题需要人工处理。\n"
                   "🔔 已为您转接专属客服人员，预计等待时间：2-5分钟。\n"
                   "您也可以直接拨打：400-800-0001")
    elif intent == 'refund':
        response = ("您好！关于退货申请，请按以下步骤操作：\n"
                   "1. 在订单页面点击【申请退货】\n"
                   "2. 选择退货原因\n"
                   "3. 等待审核（1-2个工作日）\n"
                   "4. 收到退货标签后按指引寄回商品")
    elif intent == 'greeting':
        response = ("您好！欢迎使用智能客服系统 👋\n"
                   "我可以帮助您解答：退货退款、物流查询、支付问题等。\n"
                   "请问有什么可以帮助您？")
    else:
        response = ("感谢您的咨询！\n"
                   "我理解您的问题，让我为您查询相关信息。\n"
                   "如果我的回答不能满足您的需求，可以随时说【转人工】获取专业帮助。")
    
    session['history'].append({"role": "user", "content": user_msg})
    session['history'].append({"role": "assistant", "content": response})
    session['turn_count'] += 1
    
    if session['turn_count'] == 1:
        stats['total_conversations'] += 1
    
    stats['kb_entry_count'] = len(kb)
    
    save_session(session)
    save_stats(stats)
    
    print(f"\n🤖 AI客服回复：\n{response}")
    print(f"\n[意图: {intent} | 情绪: {sentiment}]")

def cmd_add(args_text):
    parts = args_text.strip().split(' ', 1)
    if len(parts) < 2:
        print("❌ 错误：请提供问题和答案，格式：add <问题> <答案>")
        sys.exit(1)
    question = parts[0].strip()
    answer = parts[1].strip()
    
    kb = load_kb()
    # Check for duplicate
    for entry in kb:
        if entry['question'] == question:
            print(f"⚠️ 该FAQ已存在：{question}")
            return
    
    kb.append({"question": question, "answer": answer})
    save_kb(kb)
    
    stats = load_stats()
    stats['kb_entry_count'] = len(kb)
    save_stats(stats)
    
    print(f"✅ FAQ已成功添加！")
    print(f"   问题：{question}")
    print(f"   答案：{answer}")
    print(f"   当前知识库共 {len(kb)} 条记录")

def cmd_list():
    kb = load_kb()
    print(f"\n📚 知识库列表（共 {len(kb)} 条）：\n")
    print(f"{'序号':<4} {'问题':<35} {'答案'}")
    print("-" * 80)
    for i, entry in enumerate(kb, 1):
        q = entry['question'][:33] + '..' if len(entry['question']) > 35 else entry['question']
        a = entry['answer'][:40] + '..' if len(entry['answer']) > 42 else entry['answer']
        print(f"{i:<4} {q:<35} {a}")

def cmd_stats():
    stats = load_stats()
    kb = load_kb()
    stats['kb_entry_count'] = len(kb)
    save_stats(stats)
    
    print("\n📊 系统统计信息：")
    print(json.dumps(stats, ensure_ascii=False, indent=2))

def cmd_clear():
    if SESSION_FILE.exists():
        SESSION_FILE.unlink()
    print("✅ 对话历史已清空")

def main():
    if len(sys.argv) < 2:
        print("用法: ai_customer_service <操作> [参数]")
        print("操作: chat, add, list, stats, clear")
        sys.exit(1)
    
    cmd = sys.argv[1].strip()
    # Raw mode: rest of argv joined
    rest = ' '.join(sys.argv[2:]) if len(sys.argv) > 2 else ''
    
    if cmd == 'chat':
        cmd_chat(rest)
    elif cmd == 'add':
        cmd_add(rest)
    elif cmd == 'list':
        cmd_list()
    elif cmd == 'stats':
        cmd_stats()
    elif cmd == 'clear':
        cmd_clear()
    else:
        print(f"❌ 未知操作：{cmd}")
        sys.exit(1)

if __name__ == '__main__':
    main()
PYTHON_MOCK

    chmod +x /usr/local/bin/ai_customer_service
    echo "[SETUP] Mock ai_customer_service installed at /usr/local/bin/ai_customer_service"
else
    echo "[SETUP] Found existing ai_customer_service at: $TOOL_PATH"
    chmod +x "$TOOL_PATH"
fi

# Verify tool is callable
ai_customer_service list > /dev/null 2>&1 && echo "[SETUP] Tool verified OK" || echo "[SETUP] WARNING: Tool verification failed"

echo "[SETUP] Setup complete."