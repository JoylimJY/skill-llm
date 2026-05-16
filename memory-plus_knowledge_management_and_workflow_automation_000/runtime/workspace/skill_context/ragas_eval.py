#!/usr/bin/env python3
"""
RAGAS RAG 系统评测脚本
使用现有记忆数据进行评测
"""

import os, sys, json, random, re, time, requests

sys.path.insert(0, '/home/node/.openclaw/workspace')

import importlib.util
spec = importlib.util.spec_from_file_location('memory_ops', '/home/node/.openclaw/workspace/skills/memory-workflow/memory_ops.py')
memory_ops_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(memory_ops_mod)
get_instance = memory_ops_mod.get_instance

from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from ragas.dataset_schema import EvaluationDataset
from ragas import evaluate
from ragas.metrics import Faithfulness, AnswerRelevancy

from langchain_openai import ChatOpenAI
from langchain_community.embeddings import OllamaEmbeddings
from dotenv import load_dotenv

load_dotenv('/home/node/.openclaw/workspace/.env', override=True)

MINIMAX_API_KEY = os.getenv("MINIMAX_API_KEY", "")
MINIMAX_BASE_URL = os.getenv("MINIMAX_BASE_URL", "https://api.minimaxi.com/v1")


def minimax_call(prompt, system_prompt=None, max_tokens=256, retries=3, backoff=10):
    """直调 MiniMax API，返回清洗后的文本"""
    url = f"{MINIMAX_BASE_URL}/chat/completions"
    headers = {"Authorization": f"Bearer {MINIMAX_API_KEY}", "Content-Type": "application/json"}
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    def clean(text):
        """解析 MiniMax 的 <|context|>...</answer|> 格式"""
        if not text:
            return ""
        # 去掉 <|context|>...</answer|> 整块
        while "<|context|>" in text:
            idx = text.index("<|context|>")
            rest = text[idx + len("<|context|>"):]
            # 找下一个标签
            next_tag_idx = -1
            for tag in ["<|context|>", "<|answer|>"]:
                tidx = rest.find(tag)
                if tidx != -1:
                    if next_tag_idx == -1 or tidx < next_tag_idx:
                        next_tag_idx = tidx
            if next_tag_idx == -1:
                text = ""
            else:
                text = rest[next_tag_idx:]
        # 现在 text 以 <|answer|> 开头
        if "<|answer|>" in text:
            idx = text.index("<|answer|>")
            content = text[idx + len("<|answer|>"):]
            # 去掉残余标签
            content = re.sub(r"<\|/?[^>]+>", "", content)
            return content.strip()
        # 没有标签，直接清理
        text = re.sub(r"<\|/?[^>]+>", "", text)
        return text.strip()

    for attempt in range(retries):
        try:
            r = requests.post(url, headers=headers, json={
                "model": "MiniMax-M2.5",
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": 0.2
            }, timeout=30)
            if r.status_code == 200:
                data = r.json()
                if "choices" not in data or not data["choices"]:
                    raise Exception(f"No choices: {data}")
                raw = data["choices"][0]["message"]["content"]
                return clean(raw)
            elif r.status_code in (429, 500, 502, 520):
                print(f"    API {r.status_code} 重试 {attempt+1}/{retries}...")
                time.sleep(backoff * (attempt + 1))
            else:
                raise Exception(f"HTTP {r.status_code}: {r.text[:80]}")
        except Exception as e:
            if attempt < retries - 1:
                print(f"    重试 {attempt+1}/{retries}: {str(e)[:60]}")
                time.sleep(backoff * (attempt + 1))
            else:
                raise
    return ""


# LangChain for RAGAS
llm = ChatOpenAI(model="MiniMax-M2.5", api_key=MINIMAX_API_KEY, base_url=MINIMAX_BASE_URL, temperature=0.2, max_tokens=256)
ragas_llm = LangchainLLMWrapper(llm)

ollama_emb = OllamaEmbeddings(model="bge-m3:latest", base_url="http://host.docker.internal:11434")
ragas_embeddings = LangchainEmbeddingsWrapper(ollama_emb)

# 加载记忆
wf = get_instance()
state = wf.check()
print(f"记忆总数: {state['total_memories']}")
candidates = wf._get_candidates(100)
print(f"加载候选: {len(candidates)} 条")

NUM_SAMPLES = 5
SYS_Q = "只输出中文问题，不要其他内容。"
SYS_A = "只输出答案，不要前缀或思考过程。"

# ========== Step 1: 生成问答对 ==========
QA_FILE = "/tmp/ragas_qa_pairs.json"
if os.path.exists(QA_FILE):
    print(f"从缓存加载: {QA_FILE}")
    with open(QA_FILE) as f:
        qa_pairs = json.load(f)
else:
    topics = {}
    for m in candidates:
        topics.setdefault(m.get("topic", "unknown"), []).append(m)

    samples = []
    for t, mems in topics.items():
        if mems and len(samples) < NUM_SAMPLES:
            samples.append(random.choice(mems))
    remaining = [m for m in candidates if m not in samples]
    while len(samples) < NUM_SAMPLES and remaining:
        samples.append(random.choice(remaining))
        remaining.remove(samples[-1])

    random.shuffle(samples)
    samples = samples[:NUM_SAMPLES]
    print(f"生成 {len(samples)} 个问答对...")

    qa_pairs = []
    for i, mem in enumerate(samples):
        content = mem["content"][:300]
        user_prompt = f"记忆：{content}\n根据以上记忆生成一个可以用它回答的中文问题。"
        print(f"  [{i+1}/{len(samples)}] 生成问题...")
        try:
            q = minimax_call(user_prompt, system_prompt=SYS_Q)
            if q and 4 <= len(q) <= 60:
                qa_pairs.append({"memory_id": mem["id"], "topic": mem.get("topic", ""), "question": q})
                print(f"    Q: {q}")
            else:
                print(f"    无效: {q[:40] if q else 'EMPTY'}")
        except Exception as e:
            print(f"    失败: {e}")
        time.sleep(3)

    with open(QA_FILE, "w") as f:
        json.dump(qa_pairs, f, ensure_ascii=False, indent=2)

print(f"\n有效问答对: {len(qa_pairs)}")

# ========== Step 2: 检索 + 生成答案 ==========
EVAL_FILE = "/tmp/ragas_eval_data.json"
if os.path.exists(EVAL_FILE):
    print(f"从缓存加载: {EVAL_FILE}")
    with open(EVAL_FILE) as f:
        eval_samples = json.load(f)
else:
    print("检索 + 生成答案...")
    eval_samples = []

    for i, item in enumerate(qa_pairs):
        q = item["question"]
        print(f"  [{i+1}/{len(qa_pairs)}] Q: {q[:40]}...")
        try:
            sr = wf.search(q, limit=5)
            contexts = [r["content"] for r in sr["results"]] or []
        except Exception as e:
            print(f"    检索失败: {e}")
            wf.use_milvus = False
            fs = wf._get_candidates(50)
            wf.use_milvus = True
            kws = set(q.replace("?", "").replace("?", "").split())
            contexts = [c["content"] for c in fs if any(k in c["content"] for k in kws)]

        if not contexts:
            print(f"    无上下文，跳过")
            continue

        ctx_text = "\n\n".join([f"[{j+1}] {c[:300]}" for j, c in enumerate(contexts)])
        user_prompt = f"上下文：\n{ctx_text}\n\n问题：{q}"
        try:
            answer = minimax_call(user_prompt, system_prompt=SYS_A)
            if answer:
                eval_samples.append({
                    "user_input": q,
                    "retrieved_contexts": contexts,
                    "response": answer,
                })
                print(f"    A: {answer[:50]}... (ctx={len(contexts)})")
        except Exception as e:
            print(f"    失败: {e}")
        time.sleep(3)

    with open(EVAL_FILE, "w") as f:
        json.dump(eval_samples, f, ensure_ascii=False, indent=2)

print(f"\n评测样本数: {len(eval_samples)}")
if len(eval_samples) < 3:
    print("样本太少，无法评测")
    sys.exit(1)

# ========== Step 3: RAGAS 评估 ==========
print("\n开始 RAGAS 评估...")

dataset = EvaluationDataset.from_list(eval_samples)

metrics = [
    Faithfulness(llm=ragas_llm),
    AnswerRelevancy(llm=ragas_llm, embeddings=ragas_embeddings),
]

result = evaluate(
    dataset,
    metrics=metrics,
    llm=ragas_llm,
    embeddings=ragas_embeddings,
    raise_exceptions=False,
    show_progress=True,
    batch_size=2,
)

# ========== 输出结果 ==========
print("\n" + "=" * 60)
print("RAGAS 评估结果")
print("=" * 60)

for name in ["faithfulness", "answer_relevancy"]:
    try:
        print(f"  {name}: {result[name]:.4f}")
    except:
        print(f"  {name}: N/A")

try:
    df = result.to_pandas()
    for i, row in df.iterrows():
        q = eval_samples[i]["user_input"][:50]
        f = row.get("faithfulness", "N/A")
        ar = row.get("answer_relevancy", "N/A")
        fs = f"{f:.4f}" if isinstance(f, float) else str(f)
        ars = f"{ar:.4f}" if isinstance(ar, float) else str(ar)
        print(f"  [{i}] {q}... | faithfulness={fs}, answer_relevancy={ars}")
except Exception as e:
    print(f"详细打印失败: {e}")

out = {"total_samples": len(eval_samples)}
for name in ["faithfulness", "answer_relevancy"]:
    try:
        out[name] = float(result[name])
    except:
        pass
with open("/tmp/ragas_result.json", "w") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print(f"\n结果已保存: /tmp/ragas_result.json")
