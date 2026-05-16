#!/bin/bash
set -e

# Start the mock LLM server
cat > /tmp/mock_llm_server.py << 'MOCK_SERVER_EOF'
import json
import random
from flask import Flask, request, jsonify

app = Flask(__name__)

# Deterministic call counter per role for controlled responses
call_counts = {}

def make_response(content):
    return jsonify({
        "id": "chatcmpl-mock",
        "object": "chat.completion",
        "model": "mock-debate-model",
        "choices": [{
            "index": 0,
            "message": {"role": "assistant", "content": content},
            "finish_reason": "stop"
        }],
        "usage": {"prompt_tokens": 50, "completion_tokens": 100, "total_tokens": 150}
    })

@app.route('/v1/chat/completions', methods=['POST'])
def chat_completions():
    data = request.get_json()
    messages = data.get('messages', [])
    
    # Extract system prompt and user message
    system_content = ""
    user_content = ""
    for m in messages:
        if m['role'] == 'system':
            system_content = m['content']
        elif m['role'] == 'user':
            user_content = m['content']
    
    combined = system_content + " " + user_content
    
    # Detect role based on content
    
    # Integrity judge - returns JSON score (MUST be detected before others)
    if "只返回 JSON 格式" in user_content or "只返回符合以下示例的 JSON" in user_content:
        # Check if this is the summary JSON (step 4) or integrity score
        if '"pro"' in user_content or "辩论总结" in user_content and "魔鬼辩手攻击" in user_content:
            # Final summary JSON (Step 4)
            summary = {
                "pro": "1. 服兵役强化国家安全，保障公民生命财产。\n2. 军事训练培养纪律性与集体责任感，促进社会凝聚力。",
                "con": "1. 强制服役侵犯个人自由与职业发展权利。\n2. 现代战争依赖技术专业人才，义务兵役效率低下。",
                "rebuttals": "正方：个人自由建立在国家安全之上，无安全则无自由。\n反方：强迫公民冒生命危险服役，本身即是对自由的根本否定。",
                "attacks": "正方安全论点假设外部威胁必然存在，忽视外交解决途径。-> 反方需正视现实威胁而非理想外交。",
                "balance": "正方在国家安全层面论证较为充分，但反方对个人权利的捍卫同样具有说服力。辩论整体质量较高，核心张力未能完全化解，留待听众裁决。"
            }
            return make_response(json.dumps(summary, ensure_ascii=False))
        else:
            # Integrity judge score
            # Track call count
            key = "integrity"
            call_counts[key] = call_counts.get(key, 0) + 1
            count = call_counts[key]
            
            if count == 1:
                # Round 2: score below threshold (8.0)
                result = {"score": 6.5, "reasoning": "正方提出了有力的安全论证，但反方对个人自由的论点尚未得到充分回应，关键经济层面完全缺失。"}
            else:
                # Round 3: score at or above threshold (8.0) - triggers early stop
                result = {"score": 8.2, "reasoning": "双方均已提出核心论点并作出有力反驳，正方安全论证与反方权利论证形成完整对峙，辩论已趋成熟。"}
            
            return make_response(json.dumps(result, ensure_ascii=False))
    
    # Point of information (POI) question detection
    if "信息点提问" in user_content or ("不超过 15 字" in user_content and "问题" in user_content):
        if "反方" in system_content or "你是反方" in user_content or ("正方刚刚说" in user_content):
            return make_response("强制服役是否意味着国家权力凌驾于个人生命之上？")
        else:
            return make_response("反方是否认为国家安全可以完全依赖职业军队来保障？")
    
    # POI answer
    if "你选择接受" in user_content and "25 字以内" in user_content:
        if "正方" in user_content or "正方发言者" in user_content:
            return make_response("国家权力来源于保护公民，服役是共同责任而非凌驾，义务双向存在。")
        else:
            return make_response("职业军队在技术战争中效能更高，但不能完全取代全民防御意识。")
    
    # Devil's advocate (魔鬼辩手)
    if "魔鬼辩手" in system_content or "无情攻击" in user_content:
        key = "devil"
        call_counts[key] = call_counts.get(key, 0) + 1
        count = call_counts[key]
        if count == 1:
            return make_response("正方自以为掌握安全真理，却忽视了一个致命漏洞：强迫不情愿者拿枪，制造的内部撕裂比外部威胁更危险。")
        elif count == 2:
            return make_response("反方高举自由旗帜，却回避了无人愿意服役时国家将如何自保的根本困境，自由需要代价，谁来支付？")
        else:
            return make_response("双方都假设当前政治体制值得用生命捍卫——这个前提本身从未被质疑过。")
    
    # Chair summary (本轮总结)
    if "中立的牛津联盟主席" in user_content and "简要评估" in user_content:
        key = "chair_summary"
        call_counts[key] = call_counts.get(key, 0) + 1
        count = call_counts[key]
        if count == 1:
            return make_response("本轮正方以国家安全框架占据主动，论证结构清晰；反方个人自由论点情感力量强但实证不足。未解决问题：义务兵役与志愿兵役的效能比较，以及个人权利的边界界定。")
        else:
            return make_response("本轮双方均有所深化：正方补充了社会凝聚力论据，反方引入经济机会成本。关键争议：强制手段的正当性标准何在？下轮需聚焦于民主程序与个人同意的关系。")
    
    # Chair verdict (主席裁决 - closing)
    if "中立的牛津联盟主席" in user_content and "简短裁决" in user_content:
        return make_response("正方总结陈词在逻辑层次上更为严密，成功将个人义务嵌入社会契约框架；反方情感诉诸有力但未能化解核心反驳。关键时刻：正方对'自由的代价'的追问令反方陷入被动，但辩论结果终由与会者共同裁量。")
    
    # Pro debater (正方)
    if "正方立场" in system_content or ("为正方" in system_content):
        key = "pro"
        call_counts[key] = call_counts.get(key, 0) + 1
        count = call_counts[key]
        if count == 1:
            return make_response("没有安全，一切自由皆为虚妄。强制兵役是社会契约的具体体现：国家以法律保护每一位公民，公民以服役回馈集体安全。以色列、瑞士等国的实践证明，义务兵役不仅强化了国防，更锻造了超越阶层的公民认同。反对者所谓的'个人自由'，恰恰建立在他人用生命守护的和平之上。")
        elif count == 2:
            return make_response("反方混淆了自由与任意——真正的自由需要制度保障。义务兵役创造共同命运感，使富人与穷人并肩受训，打破社会壁垒。数据表明，服兵役国家的社会信任指数普遍高于纯职业军队国家。责任与权利从来是一体两面，拒绝义务就是拒绝参与这个共同体。")
        else:
            return make_response("正方始终坚守一个核心：共同体的存续优先于个体的舒适。强制兵役是民主社会中少数需要强制执行的集体义务之一，正如纳税与陪审义务。历史证明，没有全民动员能力的国家在危机时刻将土崩瓦解。这不是选项，而是生存法则。")
    
    # Con debater (反方)
    if "反对该辩题" in system_content or "反方立场" in system_content or ("为反方" in system_content):
        key = "con"
        call_counts[key] = call_counts.get(key, 0) + 1
        count = call_counts[key]
        if count == 1:
            return make_response("强迫一个人拿起武器冒死，是国家权力最粗暴的越界。现代民主的根基是同意原则——政府的权威来自被治理者的授权，而非对其身体的强制征用。职业军队在专业化、士气与技术能力上远胜义务兵，芬兰与以色列本身亦依赖高度训练的核心职业部队。强制服役是工业时代的遗产，在信息战与无人机时代已成历史负担。")
        elif count == 2:
            return make_response("正方以安全为名，却对经济代价视而不见：强制抽调数百万青年劳动力，造成人力资本损耗，压制创新生态。更重要的是，强制服役制造的心理创伤与社会撕裂往往超过其防御价值。德国、法国等成熟民主国家已相继废除义务兵役，正是认识到自愿原则与国防效能并不矛盾。")
        else:
            return make_response("反方的最终立场：国家保护公民的手段，不能以剥夺公民权利为代价。义务兵役是一种手段，而非目的；当更有效、更符合伦理的手段存在时，坚持强制只是权力惯性。真正的爱国主义来自自愿，来自认同，而非来自法律威胁下的服从。")
    
    # Pro closing statement
    if "正方一辩" in user_content and "总结陈词" in user_content:
        return make_response("自由的代价从来不是免费的。我方用三轮论证揭示了社会契约的真相：共同体的安全是个人自由的前提，而非对立面。反方用'自愿'掩盖了搭便车困境——当所有人都等待他人挺身而出，国家将如何存续？义务兵役不是压迫，而是公民身份的完整表达。请支持正方立场。")
    
    # Con closing statement  
    if "反方一辩" in user_content and "总结陈词" in user_content:
        return make_response("正方将社会契约偷换为强制征用，这是逻辑谬误。真正的契约建立在同意之上，而非强迫。正方未能解释：为何独独身体服役需要强制，而非其他公民义务？我方证明了自愿机制同样可以保障国防，且成本更低、效能更高。强制不是爱国，是恐惧。请否决这一动议。")
    
    # Default response
    return make_response("辩论继续进行中，各方论点均已得到充分表达。")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9999, debug=False)
MOCK_SERVER_EOF

# Start mock server in background
python /tmp/mock_llm_server.py &
SERVER_PID=$!
echo "Mock LLM server started with PID $SERVER_PID"

# Wait for server to be ready
sleep 2
for i in $(seq 1 10); do
    if curl -s http://localhost:9999/v1/chat/completions -X POST \
        -H "Content-Type: application/json" \
        -d '{"messages":[{"role":"user","content":"test"}]}' > /dev/null 2>&1; then
        echo "Mock server is ready."
        break
    fi
    sleep 1
done

echo "Setup complete."