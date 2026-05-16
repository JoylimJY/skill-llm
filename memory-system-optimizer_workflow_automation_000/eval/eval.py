import sys
import json
import os
import re
from pathlib import Path
from datetime import datetime

def load_text(path):
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return None

def check(name, passed, detail):
    return {"name": name, "passed": passed, "detail": detail}

def run_eval(workspace):
    ws = Path(workspace)
    checks = []
    score_parts = []

    # ── CHECK 1: Episodic memory layer (YYYY-MM-DD.md) exists ────────────────
    # memlog.sh writes to memory/YYYY-MM-DD.md
    episodic_files = list((ws / "memory").glob("20??-??-??.md")) if (ws / "memory").exists() else []
    ep_ok = len(episodic_files) >= 1
    ep_detail = f"Found episodic files: {[f.name for f in episodic_files]}" if ep_ok else "No episodic memory files (memory/YYYY-MM-DD.md) found."
    checks.append(check("episodic_memory_file_exists", ep_ok, ep_detail))
    score_parts.append(1.0 if ep_ok else 0.0)

    # ── CHECK 2: Episodic content has meaningful entries (session content) ───
    ep_content = ""
    for f in episodic_files:
        ep_content += (load_text(f) or "")
    ep_content_ok = any(keyword in ep_content.lower() for keyword in [
        "embedding", "kubernetes", "schema", "stress", "ingestion", "session", "neural", "accuracy"
    ])
    checks.append(check("episodic_memory_has_session_content", ep_content_ok,
        "Episodic memory contains session-relevant keywords." if ep_content_ok
        else "Episodic memory is empty or lacks session content from interaction logs."))
    score_parts.append(1.0 if ep_content_ok else 0.0)

    # ── CHECK 3: Short-term memory directory has files ───────────────────────
    st_dir = ws / "memory" / "short-term"
    st_files = list(st_dir.glob("*.md")) if st_dir.exists() else []
    st_ok = len(st_files) >= 1
    checks.append(check("short_term_memory_populated", st_ok,
        f"Short-term files: {[f.name for f in st_files]}" if st_ok
        else "No files found in memory/short-term/"))
    score_parts.append(1.0 if st_ok else 0.0)

    # ── CHECK 4: Short-term memory has temperature label (Hot/Warm/Cold) ────
    temp_found = False
    temp_detail = "No temperature label found in short-term memory files."
    for f in st_files:
        content = load_text(f) or ""
        if re.search(r'temperature:\s*(Hot|Warm|Cold)', content, re.IGNORECASE):
            temp_found = True
            temp_detail = f"Temperature label found in {f.name}"
            break
    checks.append(check("short_term_temperature_label", temp_found, temp_detail))
    score_parts.append(1.0 if temp_found else 0.0)

    # ── CHECK 5: Semantic memory layer populated ──────────────────────────────
    sem_dir = ws / "memory" / "semantic"
    sem_files = list(sem_dir.glob("*")) if sem_dir.exists() else []
    sem_files = [f for f in sem_files if f.is_file()]
    sem_ok = len(sem_files) >= 1
    sem_content = "".join(load_text(f) or "" for f in sem_files)
    sem_has_facts = any(kw in sem_content for kw in ["768", "cosine", "kubernetes", "1.29", "94.3", "embedding"])
    checks.append(check("semantic_memory_populated", sem_ok,
        f"Semantic files: {[f.name for f in sem_files]}" if sem_ok else "No files in memory/semantic/"))
    score_parts.append(1.0 if sem_ok else 0.0)
    checks.append(check("semantic_memory_has_facts", sem_has_facts,
        "Semantic memory contains extracted facts." if sem_has_facts
        else "Semantic memory lacks expected factual content (embedding dims, k8s version, etc.)"))
    score_parts.append(1.0 if sem_has_facts else 0.0)

    # ── CHECK 6: Long-term memory (MEMORY.md) exists and is non-trivial ──────
    memory_md = ws / "MEMORY.md"
    mem_ok = memory_md.exists()
    mem_content = load_text(memory_md) or ""
    mem_nontrivial = len(mem_content.strip()) > 50
    checks.append(check("long_term_MEMORY_md_exists", mem_ok,
        "MEMORY.md found." if mem_ok else "MEMORY.md not found at workspace root."))
    score_parts.append(1.0 if mem_ok else 0.0)
    checks.append(check("long_term_MEMORY_md_nontrivial", mem_nontrivial,
        f"MEMORY.md has {len(mem_content)} chars." if mem_nontrivial
        else "MEMORY.md is empty or too short."))
    score_parts.append(1.0 if mem_nontrivial else 0.0)

    # ── CHECK 7: Confidence layer — files in memory/confidence/ or confidence/ ─
    conf_dir1 = ws / "memory" / "confidence"
    conf_dir2 = ws / "confidence"
    conf_files1 = list(conf_dir1.glob("*")) if conf_dir1.exists() else []
    conf_files2 = list(conf_dir2.glob("*")) if conf_dir2.exists() else []
    conf_files = [f for f in conf_files1 + conf_files2 if f.is_file()]
    conf_ok = len(conf_files) >= 1
    checks.append(check("confidence_layer_populated", conf_ok,
        f"Confidence files: {[f.name for f in conf_files]}" if conf_ok
        else "No files found in confidence/ or memory/confidence/"))
    score_parts.append(1.0 if conf_ok else 0.0)

    # ── CHECK 8: Low-confidence items flagged (<50% threshold) ───────────────
    conf_content = "".join(load_text(f) or "" for f in conf_files)
    # also check semantic and episodic for confidence flags
    all_content = conf_content + sem_content + ep_content + (load_text(memory_md) or "")
    # Look for explicit low-confidence flags/clarification request markers
    low_conf_flagged = bool(re.search(
        r'(confidence[:\s]*(3[0-9]|4[0-9])\s*%|clarif|uncertain|low.{0,20}confidence|needs.{0,20}clarif|<\s*50\s*%)',
        all_content, re.IGNORECASE
    ))
    checks.append(check("low_confidence_items_flagged", low_conf_flagged,
        "Found low-confidence / clarification-request flags for uncertain items." if low_conf_flagged
        else "No low-confidence flags or clarification requests found. Items <50% confidence must be flagged."))
    score_parts.append(1.0 if low_conf_flagged else 0.0)

    # ── CHECK 9: Emotion recorded (emotions/ directory) ──────────────────────
    emo_dir = ws / "emotions"
    emo_files = list(emo_dir.glob("*")) if emo_dir.exists() else []
    emo_files = [f for f in emo_files if f.is_file()]
    emo_ok = len(emo_files) >= 1
    emo_content = "".join(load_text(f) or "" for f in emo_files)
    emo_has_stress = bool(re.search(r'(stress|anxious|pressure|concern|deadline|frustrat)', emo_content, re.IGNORECASE))
    checks.append(check("emotion_directory_has_files", emo_ok,
        f"Emotion files: {[f.name for f in emo_files]}" if emo_ok else "No files in emotions/"))
    score_parts.append(1.0 if emo_ok else 0.0)
    checks.append(check("emotion_detects_stress", emo_has_stress,
        "Emotion entry captures user stress/deadline pressure." if emo_has_stress
        else "Emotion files don't capture the stress/deadline emotion from interaction_log_001."))
    score_parts.append(1.0 if emo_has_stress else 0.0)

    # ── CHECK 10: Tasks directory populated with subtasks ────────────────────
    tasks_dir = ws / "tasks"
    task_files = list(tasks_dir.glob("*")) if tasks_dir.exists() else []
    task_files = [f for f in task_files if f.is_file()]
    tasks_ok = len(task_files) >= 1
    tasks_content = "".join(load_text(f) or "" for f in task_files)
    checks.append(check("tasks_directory_populated", tasks_ok,
        f"Task files: {[f.name for f in task_files]}" if tasks_ok else "No files in tasks/"))
    score_parts.append(1.0 if tasks_ok else 0.0)

    # Must have decomposed into multiple subtasks (at least 3 sub-items)
    subtask_count = len(re.findall(r'(\d+\.\s|\-\s|\*\s|step\s+\d|subtask|sub-task|task_\d)', tasks_content, re.IGNORECASE))
    tasks_decomposed = subtask_count >= 3
    checks.append(check("tasks_decomposed_into_subtasks", tasks_decomposed,
        f"Found {subtask_count} subtask references in tasks/." if tasks_decomposed
        else f"Tasks not decomposed into >=3 subtasks (found {subtask_count} task markers)."))
    score_parts.append(1.0 if tasks_decomposed else 0.0)

    # Must include project-specific content (Alpha Demo keywords)
    tasks_has_alpha = bool(re.search(r'(alpha|demo|memory.{0,20}api|latency|load.test|staging|fallback|emotion.{0,20}module)', tasks_content, re.IGNORECASE))
    checks.append(check("tasks_contain_alpha_demo_project", tasks_has_alpha,
        "Task files reference Alpha Demo project components." if tasks_has_alpha
        else "Task files don't reference Alpha Demo project. Should be decomposed from project_brief_alpha.txt."))
    score_parts.append(1.0 if tasks_has_alpha else 0.0)

    # ── CHECK 11: Reflections directory has at least one reflection ──────────
    ref_dir = ws / "reflections"
    ref_files = list(ref_dir.glob("*")) if ref_dir.exists() else []
    ref_files = [f for f in ref_files if f.is_file()]
    ref_ok = len(ref_files) >= 1
    ref_content = "".join(load_text(f) or "" for f in ref_files)
    ref_has_content = len(ref_content.strip()) > 30
    checks.append(check("reflections_directory_populated", ref_ok and ref_has_content,
        f"Reflections: {[f.name for f in ref_files]}" if ref_ok
        else "No reflection files found in reflections/"))
    score_parts.append(1.0 if (ref_ok and ref_has_content) else 0.0)

    # ── Compute final score ───────────────────────────────────────────────────
    total = len(score_parts)
    passed_count = sum(score_parts)
    final_score = round(passed_count / total, 4) if total > 0 else 0.0
    overall_passed = final_score >= 0.75

    result = {
        "passed": overall_passed,
        "score": final_score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))
    return result

if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    run_eval(workspace_dir)