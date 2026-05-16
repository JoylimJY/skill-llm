import os
import random

random.seed(42)

# Create deeply nested directory structure with distractor files
dirs = [
    "project/paper",
    "project/paper/figures",
    "project/paper/supplementary",
    "project/paper/old_drafts",
    "project/code/experiments",
    "project/code/models",
    "project/code/utils",
    "project/notes",
    "project/data/raw",
    "project/data/processed",
    "project/reviews",
]

for d in dirs:
    os.makedirs(d, exist_ok=True)

# Distractor files
distractors = {
    "project/code/experiments/train.py": """
import torch
import numpy as np

def train_model(config):
    # Training loop
    for epoch in range(config['epochs']):
        loss = compute_loss()
        optimizer.step()
    return model
""",
    "project/code/models/policy_net.py": """
import torch.nn as nn

class PolicyNetwork(nn.Module):
    def __init__(self, obs_dim, act_dim):
        super().__init__()
        self.fc = nn.Linear(obs_dim, act_dim)
    
    def forward(self, x):
        return self.fc(x)
""",
    "project/code/utils/data_loader.py": """
import os
import json

def load_dataset(path):
    with open(path) as f:
        return json.load(f)
""",
    "project/notes/meeting_notes.txt": """
Meeting 2024-03-15
- Discuss RT-2 comparison
- Need to fix citations
- Rerun ablations on Table 3
""",
    "project/data/raw/config.yaml": """
dataset: bridge_v2
split: train
batch_size: 256
learning_rate: 1e-4
""",
    "project/data/processed/stats.json": """
{"mean": 0.512, "std": 0.234, "n_samples": 48291}
""",
    "project/reviews/reviewer1.txt": """
Review 1:
The paper reads as AI-generated in several places.
Citations need spaces. The math notation is inconsistent.
Please revise.
""",
    "project/reviews/reviewer2.txt": """
Review 2:
Related work is well-organized but other sections 
have too many citations per paragraph. Please consolidate.
""",
    "project/paper/figures/figure1_notes.txt": """
Figure 1: System architecture
- Use vector format
- No big title banner
- Clean diagram
""",
    "project/paper/supplementary/appendix_notes.md": """
# Appendix Notes
- Add ablation details
- Expand on hyperparameter choices
""",
    "project/paper/old_drafts/draft_v0.tex": r"""
\documentclass{article}
\begin{document}
This is an old draft. Ignore this file.
\end{document}
""",
    "project/paper/supplementary/supp_experiments.tex": r"""
\section{Supplementary Experiments}
We provide additional results here.
Table~\ref{tab:supp} shows performance on held-out tasks.
""",
}

for path, content in distractors.items():
    with open(path, "w") as f:
        f.write(content)

# THE MAIN PROBLEM FILE: draft_paper.tex with multiple AI-flavor issues
draft_content = r"""\documentclass{article}
\usepackage{amsmath}
\usepackage{amssymb}
\usepackage{bm}

\title{Towards Generalist Robot Policies via Scalable Imitation Learning}
\author{Anonymous}
\date{}

\begin{document}
\maketitle

\begin{abstract}
We present a scalable approach to robot learning that leverages large-scale demonstration data.
Our method achieves state-of-the-art performance on multiple benchmarks—outperforming prior
baselines by a significant margin—and generalizes to novel tasks without fine-tuning.
Experiments across three robot platforms demonstrate the effectiveness of our framework.
\end{abstract}

\section{Introduction}

Recent advances in large language models(Brown et al., 2020) and vision-language models(Radford et al., 2021)
have inspired a new generation of robot learning methods. The challenge is rarely "predicting
the next action correctly." Instead, the bottleneck lies in obtaining sufficient high-quality
demonstrations at scale.

Prior work has attempted to address this through data augmentation(Laskin et al., 2020),
reward shaping(Ng et al., 1999), and self-supervised pre-training(He et al., 2020)—yet none
of these approaches fully resolve the distribution shift problem—which remains a central
obstacle in imitation learning today.

In this work, we propose a unified architecture that scales up the policy itself—through
larger data, more unified action spaces, and stronger representations—including RT-1, RT-2,
Gato, OpenVLA, and SayCan. Our key contributions are:

\begin{itemize}
\item A scalable data collection pipeline that reduces "annotation burden" by 60\%.
\item A novel architecture combining visual encoders and language conditioning.
\item Comprehensive evaluation across diverse robot manipulation tasks.
\end{itemize}

\section{Related Work}

\textbf{Imitation Learning.} Behavioral cloning(Pomerleau, 1989) is the simplest form of
imitation learning. More recent approaches include DAgger(Ross et al., 2011), GAIL(Ho \& Ermon, 2016),
IBC(Florence et al., 2021), Diffusion Policy(Chi et al., 2023), ACT(Zhao et al., 2023),
RoboFlamingo(Li et al., 2024), OpenVLA(Kim et al., 2024), and $\pi_0$(Black et al., 2024).

\textbf{Foundation Models for Robotics.} Large-scale pre-training has shown promise in robotics(Brohan et al., 2022).
RT-2(Brohan et al., 2023) demonstrates that VLMs can be fine-tuned for robot control.
Gato(Reed et al., 2022) trains a single transformer on heterogeneous data.
SayCan(Ahn et al., 2022) grounds language instructions in robot affordances.
PaLM-E(Driess et al., 2023) integrates embodied reasoning with language modeling.
GR-1(Wu et al., 2023) uses video prediction as a pre-training objective.

\section{Method}

\subsection{Problem Formulation}

We model robot manipulation as a Markov Decision Process. At each timestep $t$, the robot
observes state $s_t$ and must produce action $a_t$. The observation includes an image $I_t$
and a language instruction $l$.

Let $x$ denote the joint configuration vector. The policy $\pi_\theta$ maps observations
to actions: $\pi_\theta: (I_t, l) \rightarrow a_t$.

We parameterize the policy using a weight matrix $W$ that transforms visual features $v$
into action predictions. The update rule is:

\begin{equation}
W_{t+1} = W_t - \alpha \nabla_W \mathcal{L}(W_t)
\end{equation}

where $\alpha$ is the learning rate and $\mathcal{L}$ denotes the imitation loss.

The visual encoder $E$ produces embeddings $z = E(I_t)$. The cross-attention mechanism
combines $z$ with language tokens $q$ to produce context-aware features $f = \text{Attn}(z, q, q)$.

\subsection{Architecture}

Our architecture consists of three components. The "visual backbone" processes raw images
into compact feature representations. The language module encodes task instructions.
The action decoder maps combined features to motor commands.

The core transformation is $a_t = D(W \cdot [z; q])$ where $D$ is the decoder network,
$z$ is the visual embedding, and $q$ represents language features.

\subsection{Training}

We train our model using behavior cloning on a dataset of $N$ demonstrations.
The loss function is:

\begin{equation}
\mathcal{L}_{BC} = \frac{1}{N} \sum_{i=1}^{N} \| a_i - \pi_\theta(o_i) \|^2
\end{equation}

To improve "generalization capability," we apply several data augmentation strategies—including
random cropping, color jitter, and spatial perturbations—which collectively reduce overfitting
to appearance variations in the training environments.

\section{Experiments}

\subsection{Setup}

We evaluate on three benchmarks: LIBERO(Liu et al., 2024), MetaWorld(Yu et al., 2020), and RLBench(James et al., 2020).
Baselines include ACT(Zhao et al., 2023), Diffusion Policy(Chi et al., 2023), OpenVLA(Kim et al., 2024),
RoboFlamingo(Li et al., 2024), and GR-1(Wu et al., 2023).

\subsection{Main Results}

Our method outperforms all baselines on all benchmarks. The improvement is
particularly pronounced in "long-horizon" tasks requiring multi-step reasoning.

Table 1 shows quantitative results. Our method achieves 87.3\% success rate on LIBERO—compared
to 71.2\% for the strongest baseline—representing a 16.1 percentage point improvement.

The strong performance demonstrates that scaling training data yields consistent
gains—even without architectural changes—validating our core hypothesis.

\subsection{Ablation Study}

We ablate three components: the visual encoder, the language module, and the data augmentation pipeline.
Removing each component degrades performance, confirming the necessity of each design choice.

Let $v$ and $q$ represent visual and language feature vectors respectively.
When computing attention, we use key matrix $K$ and value matrix $V$ from the cross-attention layer.
The output feature $f$ is computed as $f = \text{softmax}(\frac{z K^\top}{\sqrt{d}}) V$.

\section{Conclusion}

We presented a scalable imitation learning framework for generalist robot policies.
Our approach addresses the "data bottleneck" in robot learning through a combination
of efficient data collection and a unified multi-task architecture. Future work will
explore "sim-to-real transfer" and online fine-tuning with human feedback.

\end{document}
"""

with open("project/paper/draft_paper.tex", "w") as f:
    f.write(draft_content)

print("Workspace generated successfully.")
print("Main file: project/paper/draft_paper.tex")