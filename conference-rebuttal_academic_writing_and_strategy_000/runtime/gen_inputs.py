import os
import json

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# ── distractor directory tree ──────────────────────────────────────────────────
dirs = [
    "reviews",
    "paper",
    "paper/figures",
    "paper/tables",
    "experiments/ablation",
    "experiments/baseline",
    "experiments/timing",
    "drafts/old",
    "drafts/notes",
    "references",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# distractor files
distractors = {
    "paper/main.tex": r"""\documentclass{neurips_2024}
\title{AdaptiveKernel: Dynamic Kernel Selection for Efficient Transformers}
\begin{document}
\maketitle
\begin{abstract}
We propose AdaptiveKernel, a method for dynamic kernel selection...
\end{abstract}
% Line 42: Table 1 shows main results
% Line 87: Section 4.1 ablation study
% Line 134: Appendix A timing analysis
\end{document}
""",
    "paper/figures/fig1_architecture.png.placeholder": "architecture diagram placeholder",
    "paper/tables/table1_main_results.csv": """Method,CIFAR-10,ImageNet-1k,COCO mAP,Params(M),Latency(ms)
Baseline-ViT,94.2,81.3,47.1,86,18.4
LinearAttn,93.8,80.9,46.5,84,11.2
Performer,93.5,80.6,46.1,85,10.9
AdaptiveKernel(ours),95.1,83.2,49.8,88,12.6
""",
    "paper/tables/table2_ablation.csv": """Variant,CIFAR-10,ImageNet-1k,Latency(ms)
w/o dynamic selection,93.9,81.8,11.1
w/o kernel bank,94.3,82.1,12.0
full model,95.1,83.2,12.6
""",
    "experiments/timing/overhead_analysis.txt": """Overhead analysis (A100, batch=64):
AdaptiveKernel additional overhead: 2.2ms/step
Baseline ViT: 18.4ms/step
Overhead percentage: 11.9% raw, but amortized over sequence: <1% latency for seq_len>512
Memory overhead: +3.2% peak GPU memory
""",
    "experiments/ablation/kernel_bank_sizes.txt": """Kernel bank size experiments:
K=2: 94.7 CIFAR-10
K=4: 95.1 CIFAR-10 (chosen)
K=8: 95.2 CIFAR-10, +4ms latency
""",
    "experiments/baseline/performer_comparison.txt": """Performer vs AdaptiveKernel:
Performer uses fixed random features; AdaptiveKernel dynamically selects.
AdaptiveKernel: +2.6pp ImageNet over Performer, same asymptotic complexity O(n).
""",
    "drafts/old/rebuttal_v0.txt": """(ABANDONED DRAFT - DO NOT USE)
Dear reviewers, we disagree with R2's assessment...
""",
    "drafts/notes/author_discussion.txt": """Team notes:
- R1 seems positive, gave 7. Main concern: comparison with Linformer.
- R2 gave 5, borderline. Concerned about computational overhead and novelty vs Performer.
- R3 gave 3, strongly against. Claims our method is incremental, wants LRA benchmark, 
  also complains about missing ablation on kernel bank size.
- We have kernel bank ablation already in Table 2 (R3 missed it).
- Timing: overhead really is only 2.2ms (<1% for long seq).
- R2 and R3 both ask about overhead - merge that response.
""",
    "references/related_work_notes.txt": """Key citations:
- Performer (Choromanski et al. 2021): random Fourier features approximation
- Linformer (Wang et al. 2020): low-rank attention
- FNet (Lee-Thorp et al. 2022): Fourier transforms replacing attention
- LRA benchmark (Tay et al. 2021): standard long-range arena
""",
    "references/acceptance_rates.txt": """NeurIPS 2023: 26.1% acceptance rate
ICML 2023: 27.9% acceptance rate
""",
}
for path, content in distractors.items():
    with open(os.path.join(workspace, path), "w") as f:
        f.write(content)

# ── paper metadata ─────────────────────────────────────────────────────────────
paper_info = {
    "title": "AdaptiveKernel: Dynamic Kernel Selection for Efficient Transformers",
    "authors": ["Alice Chen", "Bob Zhang", "Carol Liu"],
    "venue": "NeurIPS 2024",
    "paper_id": "NeurIPS2024-7821",
    "submission_line_refs": {
        "table1_main_results": "Lines 412-428 / Table 1",
        "table2_ablation": "Lines 501-519 / Table 2",
        "appendix_timing": "Appendix A, Lines 612-630",
        "appendix_lra": "NOT YET IN PAPER - must add to Appendix B"
    }
}
with open(os.path.join(workspace, "paper_info.json"), "w") as f:
    json.dump(paper_info, f, indent=2)

# ── reviews ────────────────────────────────────────────────────────────────────

review_r1 = """Reviewer: R1
Score: 7 (Accept)
Confidence: 4

Summary:
This paper presents AdaptiveKernel, a dynamic kernel selection framework for efficient Transformers. The proposed method maintains a bank of kernel functions and learns to select among them conditioned on the input, achieving better accuracy-efficiency tradeoffs than prior work.

Strengths:
- The paper is well-motivated and tackles an important practical problem in scaling Transformers.
- The adaptive selection mechanism is technically well-executed and theoretically grounded.
- Experimental results on CIFAR-10 and ImageNet are convincing and the ablation study is thorough.
- Writing is clear and the contribution is well-positioned relative to prior work.

Weaknesses:
W1: The comparison with Linformer is missing from the main results table. Given that Linformer is one of the closest competitors in the low-rank attention space, its absence is notable. A direct comparison would significantly strengthen the evaluation.

W2: The theoretical analysis in Section 3 assumes input stationarity, which may not hold in practice for NLP tasks. A brief discussion of this limitation would improve the paper.

Questions:
Q1: Have the authors evaluated on any NLP benchmarks (e.g., GLUE or long document tasks)? The current evaluation is vision-centric, and it is unclear how the method generalizes to language modeling.
"""

review_r2 = """Reviewer: R2
Score: 5 (Borderline Reject)
Confidence: 3

Summary:
The paper proposes a dynamic kernel selection approach for efficient attention. While the idea is reasonable and clever, I have concerns about the computational overhead and the relationship to existing work, particularly Performer.

Strengths:
- The motivation is reasonable and the kernel bank idea is clever.
- The paper is reasonably well-written.

Weaknesses:
W1: The computational overhead of the dynamic selection mechanism is not clearly analyzed. Adding a selection network on top of attention could negate the efficiency gains. The authors should provide a detailed breakdown of the wall-clock time overhead.

W2: The novelty over Performer (Choromanski et al. 2021) is not sufficiently distinguished. Both methods use kernel approximations; the key difference (dynamic vs. static) needs more rigorous justification beyond accuracy numbers.

W3: The method is only evaluated on vision tasks. Broader evaluation would improve confidence in the claims.

Questions:
Q1: What is the actual wall-clock overhead of the selection mechanism compared to standard attention and Performer?
Q2: Can the authors provide a more theoretical analysis of why dynamic selection outperforms static kernel approximations?
"""

review_r3 = """Reviewer: R3
Score: 3 (Reject)
Confidence: 4

Summary:
The paper presents an incremental modification to existing kernel attention methods. I do not believe the contribution is significant enough for NeurIPS.

Strengths:
- The writing is conceptually elegant and practically impactful if the claims hold.
- Some experimental results look reasonable on standard benchmarks.

Weaknesses:
W1: The contribution is incremental. Dynamic kernel selection has been explored in other contexts (e.g., mixture-of-experts), and the application to attention kernels does not seem to require a full NeurIPS paper.

W2: The Long Range Arena (LRA) benchmark (Tay et al. 2021) is the standard evaluation protocol for efficient attention methods. Its complete absence from the evaluation is a critical flaw. Without LRA results, comparisons to Performer and Linformer are not meaningful.

W3: There is no ablation on the kernel bank size K. How sensitive is the method to this hyperparameter? This is a fundamental design choice that is unexplored.

W4: The paper claims O(n) complexity but the selection mechanism adds an undisclosed overhead. This needs to be quantified precisely.

Questions:
Q1: Why was the LRA benchmark omitted? This is the standard evaluation for this type of work.
Q2: What happens when K=1 (degenerate case)?
Q3: What is the overhead of the selection mechanism in wall-clock time?
"""

for fname, content in [("reviews/R1_review.txt", review_r1),
                        ("reviews/R2_review.txt", review_r2),
                        ("reviews/R3_review.txt", review_r3)]:
    with open(os.path.join(workspace, fname), "w") as f:
        f.write(content)

print("Workspace generated successfully.")
print(f"Files created: reviews/R1_review.txt, reviews/R2_review.txt, reviews/R3_review.txt, paper_info.json")