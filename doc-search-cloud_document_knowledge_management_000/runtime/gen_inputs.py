import os
import json
import random

random.seed(42)

BASE = "/workspace"

# --- Directory structure (distractor files) ---
dirs = [
    "contracts/active",
    "contracts/archive",
    "contracts/templates",
    "compliance/reports/2023",
    "compliance/reports/2024",
    "compliance/checklists",
    "internal/hr",
    "internal/finance",
    "tools/scripts",
    "tools/configs",
    "logs",
]
for d in dirs:
    os.makedirs(os.path.join(BASE, d), exist_ok=True)

# --- Distractor files ---
distractors = [
    ("contracts/archive/old_vendor_agreement_2019.txt", "This is an archived vendor agreement from 2019. No longer active."),
    ("contracts/templates/nda_template.txt", "NON-DISCLOSURE AGREEMENT TEMPLATE\nParty A: ___\nParty B: ___\nEffective Date: ___"),
    ("compliance/checklists/gdpr_checklist.txt", "GDPR Compliance Checklist\n1. Data mapping complete\n2. DPA signed\n3. Breach notification procedure in place"),
    ("compliance/reports/2023/annual_audit.txt", "Annual Compliance Audit 2023\nStatus: Completed\nFindings: 3 minor issues resolved"),
    ("compliance/reports/2024/q1_summary.txt", "Q1 2024 Summary\nContracts reviewed: 45\nIssues flagged: 2"),
    ("internal/hr/employee_handbook.txt", "Employee Handbook v4.2\nSection 1: Code of Conduct\nSection 2: Leave Policy"),
    ("internal/finance/budget_2024.txt", "Finance Budget 2024\nTotal: $2,500,000\nAllocated: $1,800,000"),
    ("tools/configs/db_config.json", json.dumps({"host": "localhost", "port": 5432, "db": "contracts_db"})),
    ("tools/scripts/backup.sh", "#!/bin/bash\necho 'Backup started'\ntar -czf backup.tar.gz /workspace/contracts"),
    ("logs/access_2024_01.log", "2024-01-15 09:23:11 INFO User admin accessed contract NDA-2024-001\n2024-01-15 10:45:32 INFO User jdoe accessed contract SVC-2024-003"),
    ("logs/error_2024_01.log", "2024-01-15 11:00:00 ERROR Contract parser failed on malformed PDF\n2024-01-15 11:05:00 WARN Retry succeeded"),
]

for rel_path, content in distractors:
    full_path = os.path.join(BASE, rel_path)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

# --- Primary input documents to be vectorized ---

# Document 1: TXT - Software Service Agreement
txt_content = """软件服务协议

本协议由甲方（客户）与乙方（服务提供商）于2024年1月1日签订。

第一条 服务范围
乙方应向甲方提供云端SaaS软件平台的访问权限及相关技术支持服务。服务内容包括系统部署、维护、升级以及7×24小时技术响应。

第二条 费用与支付
甲方应按月支付服务费用，金额为人民币50,000元/月。付款应于每月1日前完成。逾期付款将产生0.05%/日的违约金。

第三条 保密条款
双方承诺对协议内容及执行过程中获知的商业秘密严格保密。保密期限为协议终止后五年。任何一方不得将对方的技术资料、客户信息、商业计划向第三方披露。

第四条 知识产权
乙方平台的所有知识产权归乙方所有。甲方仅获得有限的使用许可，不得复制、修改或二次开发相关软件。

第五条 违约责任
如任何一方违反本协议约定，违约方应向守约方支付合同总价值20%的违约金，并赔偿由此造成的全部实际损失。

第六条 争议解决
本协议产生的任何争议，双方应首先协商解决。协商不成的，提交中国国际经济贸易仲裁委员会仲裁。

第七条 协议期限
本协议自签署之日起生效，有效期为一年，到期前30日内任一方未提出终止则自动续期。
"""

with open(os.path.join(BASE, "contracts/active/software_service_agreement.txt"), "w", encoding="utf-8") as f:
    f.write(txt_content)

# Document 2: Markdown - Data Processing Agreement
md_content = """# 数据处理协议

## 协议背景

本数据处理协议（以下简称"协议"）依据《个人信息保护法》及相关法规订立，规范甲方委托乙方处理个人数据的行为。

## 数据处理范围

乙方仅在执行服务所必要的范围内处理个人数据，包括用户注册信息、交易记录及使用行为数据。严禁将数据用于协议约定目的之外的任何用途。

## 数据安全措施

乙方承诺采取以下技术与管理措施保障数据安全：
- 数据传输采用TLS 1.3加密协议
- 存储数据使用AES-256加密
- 访问控制采用最小权限原则
- 定期进行安全漏洞扫描和渗透测试

## 数据泄露通知

如发生数据安全事件，乙方应在发现后72小时内通知甲方，并提供事件详情、影响范围及应对措施。

## 数据跨境传输

未经甲方书面同意，乙方不得将个人数据传输至中华人民共和国境外。如需跨境传输，须符合监管机构的相关规定。

## 数据删除与返还

协议终止后，乙方应在30个工作日内删除或返还所有甲方数据，并提供书面证明。
"""

with open(os.path.join(BASE, "contracts/active/data_processing_agreement.md"), "w", encoding="utf-8") as f:
    f.write(md_content)

# Document 3: DOCX - Intellectual Property License
try:
    from docx import Document
    doc = Document()
    doc.add_heading("知识产权许可协议", 0)

    doc.add_heading("第一章 定义", level=1)
    doc.add_paragraph('本协议中，\u201c许可方\u201d指拥有相关知识产权的一方。\u201c被许可方\u201d指获得使用权的一方。\u201c授权作品\u201d指许可方授权使用的专利、商标、著作权及相关技术资料。')

    doc.add_heading("第二章 许可授权", level=1)
    doc.add_paragraph('许可方授予被许可方在中华人民共和国境内使用授权作品的非独家、不可转让的使用权。被许可方不得将授权作品许可给任何第三方使用，也不得对授权作品进行反向工程。')

    doc.add_heading("第三章 许可费用", level=1)
    doc.add_paragraph('被许可方应向许可方支付一次性许可费人民币200,000元，及按年净收入2%计算的持续性特许权使用费。特许权使用费每年结算一次，于每年12月31日前完成支付。')

    doc.add_heading("第四章 质量控制", level=1)
    doc.add_paragraph('被许可方在使用授权作品时须遵守许可方的质量标准。许可方有权对被许可方的使用情况进行定期审查，被许可方须配合提供相关资料。')

    doc.add_heading("第五章 保证与免责", level=1)
    doc.add_paragraph('许可方保证其对授权作品享有完整的知识产权，不存在任何权利瑕疵。如因第三方对授权作品提出权利主张，许可方应承担相应的法律责任并赔偿被许可方损失。')

    doc.add_heading("第六章 协议终止", level=1)
    doc.add_paragraph('若被许可方违反本协议任何条款，许可方可在提前30日书面通知后终止本协议。协议终止后，被许可方须立即停止使用授权作品并销毁相关副本。')

    doc.save(os.path.join(BASE, "contracts/active/ip_license_agreement.docx"))
    print("DOCX created successfully")
except ImportError:
    # fallback: create a txt if docx not available yet
    with open(os.path.join(BASE, "contracts/active/ip_license_agreement.docx.notready"), "w") as f:
        f.write("docx not available")

# --- The main chromadb_document_vectorizer_simple.py module ---
# This is the skill script that MUST already exist in workspace
vectorizer_code = '''import os
import json
import pickle
import hashlib
import math
import re
from pathlib import Path


def _md5_vector(text: str, dim: int = 384) -> list:
    """Generate a deterministic pseudo-vector from text using MD5."""
    result = []
    seed = text
    while len(result) < dim:
        h = hashlib.md5(seed.encode("utf-8")).hexdigest()
        for i in range(0, len(h), 2):
            val = int(h[i:i+2], 16) / 255.0
            result.append(val)
            if len(result) >= dim:
                break
        seed = h
    return result[:dim]


def _cosine_similarity(a: list, b: list) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _bm25_score(query_tokens: list, doc_tokens: list, avg_dl: float, k1: float = 1.5, b: float = 0.75) -> float:
    """Simple BM25 score for a single document."""
    score = 0.0
    dl = len(doc_tokens)
    doc_freq = {}
    for t in doc_tokens:
        doc_freq[t] = doc_freq.get(t, 0) + 1
    for token in query_tokens:
        if token in doc_freq:
            tf = doc_freq[token]
            idf = math.log(2.0)  # simplified IDF
            score += idf * (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * dl / max(avg_dl, 1)))
    return score


class DocumentVectorizer:
    def __init__(self, persist_directory: str = "./chroma_data", use_real_embedding: bool = False,
                 chunk_size: int = 200, cache_size: int = 1000, alpha: float = 0.7):
        self.persist_directory = persist_directory
        self.use_real_embedding = use_real_embedding
        self.chunk_size = chunk_size
        self.cache_size = cache_size
        self.alpha = alpha  # weight for vector similarity vs BM25 in hybrid search
        self.collection_name = "documents"

        os.makedirs(persist_directory, exist_ok=True)
        self._data_path = os.path.join(persist_directory, "documents_data.pkl")
        self._index_path = os.path.join(persist_directory, "documents_index.json")

        # Storage: list of dicts {id, content, vector, metadata, tokens}
        self._documents = []
        self._query_cache = {}  # LRU cache: query_key -> results
        self._cache_order = []

        self._load()

        if use_real_embedding:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
            except ImportError:
                print("Warning: sentence-transformers not installed, falling back to MD5 mode.")
                self.use_real_embedding = False
                self._model = None
        else:
            self._model = None

    def _load(self):
        if os.path.exists(self._data_path):
            try:
                with open(self._data_path, "rb") as f:
                    self._documents = pickle.load(f)
            except Exception:
                self._documents = []

    def _save(self):
        with open(self._data_path, "wb") as f:
            pickle.dump(self._documents, f)
        index = {
            "collection_name": self.collection_name,
            "total_documents": len(self._documents),
            "sources": list(set(d.get("metadata", {}).get("source", "") for d in self._documents if isinstance(d.get("metadata"), dict)))
        }
        with open(self._index_path, "w", encoding="utf-8") as f:
            json.dump(index, f, ensure_ascii=False, indent=2)

    def _get_embedding(self, text: str) -> list:
        if self.use_real_embedding and self._model:
            return self._model.encode(text).tolist()
        return _md5_vector(text)

    def _split_text(self, text: str) -> list:
        """Split text by Chinese period, then chunk by chunk_size."""
        sentences = re.split(r\'(?<=。)\', text)
        chunks = []
        current = ""
        for sent in sentences:
            if len(current) + len(sent) <= self.chunk_size:
                current += sent
            else:
                if current:
                    chunks.append(current.strip())
                current = sent
        if current.strip():
            chunks.append(current.strip())
        return [c for c in chunks if c]

    def _read_file(self, file_path: str) -> str:
        ext = Path(file_path).suffix.lower()
        if ext == ".txt":
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        elif ext == ".md":
            with open(file_path, "r", encoding="utf-8") as f:
                raw = f.read()
            try:
                import markdown
                from bs4 import BeautifulSoup
                html = markdown.markdown(raw)
                return BeautifulSoup(html, "html.parser").get_text()
            except ImportError:
                return raw
        elif ext == ".docx":
            try:
                from docx import Document
                doc = Document(file_path)
                return "\\n".join(p.text for p in doc.paragraphs if p.text.strip())
            except Exception as e:
                return f"Error reading docx: {e}"
        elif ext == ".pdf":
            try:
                import PyPDF2
                text = ""
                with open(file_path, "rb") as f:
                    reader = PyPDF2.PdfReader(f)
                    for page in reader.pages:
                        text += page.extract_text() or ""
                return text
            except Exception as e:
                return f"Error reading PDF: {e}"
        else:
            raise ValueError(f"Unsupported file format: {ext}")

    def vectorize_file(self, file_path: str, metadata: dict = None) -> dict:
        if not os.path.exists(file_path):
            return {"status": "error", "message": f"File not found: {file_path}", "chunks_added": 0, "source": file_path}
        try:
            text = self._read_file(file_path)
            if not text.strip():
                return {"status": "error", "message": "File is empty", "chunks_added": 0, "source": file_path}
            chunks = self._split_text(text)
            if metadata is None:
                metadata = {}
            metadata["source"] = file_path
            added = 0
            for i, chunk in enumerate(chunks):
                vec = self._get_embedding(chunk)
                tokens = list(chunk)
                doc_id = hashlib.md5(f"{file_path}_{i}_{chunk[:50]}".encode()).hexdigest()
                self._documents.append({
                    "id": doc_id,
                    "content": chunk,
                    "vector": vec,
                    "metadata": dict(metadata),
                    "tokens": tokens,
                })
                added += 1
            self._save()
            self._query_cache.clear()
            self._cache_order.clear()
            return {"status": "success", "message": f"Added {added} chunks from {file_path}", "chunks_added": added, "source": file_path}
        except Exception as e:
            return {"status": "error", "message": str(e), "chunks_added": 0, "source": file_path}

    def search_vectors(self, query_text: str, top_k: int = 5) -> list:
        cache_key = f"{query_text}||{top_k}"
        if cache_key in self._query_cache:
            return self._query_cache[cache_key]

        if not self._documents:
            return []

        query_vec = self._get_embedding(query_text)
        query_tokens = list(query_text)

        avg_dl = sum(len(d["tokens"]) for d in self._documents) / len(self._documents)

        scored = []
        for doc in self._documents:
            vec_sim = _cosine_similarity(query_vec, doc["vector"])
            bm25 = _bm25_score(query_tokens, doc["tokens"], avg_dl)
            bm25_norm = min(bm25 / 10.0, 1.0)
            hybrid = self.alpha * vec_sim + (1 - self.alpha) * bm25_norm
            scored.append({
                "content": doc["content"],
                "similarity": round(hybrid, 6),
                "metadata": doc.get("metadata", {}),
            })

        scored.sort(key=lambda x: x["similarity"], reverse=True)
        results = scored[:top_k]

        # LRU cache update
        if len(self._cache_order) >= self.cache_size:
            oldest = self._cache_order.pop(0)
            self._query_cache.pop(oldest, None)
        self._query_cache[cache_key] = results
        self._cache_order.append(cache_key)

        return results

    def get_collection_stats(self) -> dict:
        return {
            "total_documents": len(self._documents),
            "collection_name": self.collection_name,
        }

    def clear_collection(self) -> dict:
        self._documents = []
        self._query_cache.clear()
        self._cache_order.clear()
        self._save()
        return {"status": "success", "message": "Collection cleared"}
'''

with open(os.path.join(BASE, "chromadb_document_vectorizer_simple.py"), "w", encoding="utf-8") as f:
    f.write(vectorizer_code)

print("Workspace initialized successfully.")
print(f"Files created:")
for root, dirs_, files in os.walk(BASE):
    for fname in files:
        print(f"  {os.path.join(root, fname)}")