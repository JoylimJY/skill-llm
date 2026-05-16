#!/usr/bin/env python3
"""Shared helpers for the One Person Company OS workspace scripts."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import zipfile
from collections.abc import Iterable
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, TextIO
from xml.sax.saxutils import escape

import fcntl

from localization import (
    bool_audit_label as localized_bool_audit_label,
    bool_label as localized_bool_label,
    format_list as localized_format_list,
    joined_text as localized_joined_text,
    localized_role_spec,
    mode_label,
    normalize_language,
    normalize_persistence_mode,
    normalize_round_status,
    normalize_stage as localized_normalize_stage,
    persistence_mode_label,
    pick_text,
    round_status_label,
    stage_label as localized_stage_label,
    stage_meta,
    stage_required_outputs,
    step_meta,
    resolve_step_id,
    template_text,
)
from state_v3 import read_state_any_version, sync_legacy_fields, write_state_v3


ROOT = Path(__file__).resolve().parent.parent
SCRIPT_DIR = ROOT / "scripts"
TEMPLATE_DIR = ROOT / "assets" / "templates"
ROLE_DIR = ROOT / "agents" / "roles"
ORCHESTRATION_DIR = ROOT / "orchestration"
STATE_PATH_PARTS = ("自动化", "当前状态.json")
CORE_WORKSPACE_FILES = (
    "00-经营总盘.md",
    "02-价值承诺与报价.md",
    "03-机会与成交管道.md",
    "04-产品与上线状态.md",
    "05-客户交付与回款.md",
    "自动化/当前状态.json",
)
ARTIFACT_ROOT = "产物"
REQUIRED_SCRIPT_NAMES = (
    "init_company.py",
    "init_business.py",
    "build_agent_brief.py",
    "generate_artifact_document.py",
    "start_round.py",
    "update_round.py",
    "calibrate_round.py",
    "transition_stage.py",
    "update_focus.py",
    "advance_offer.py",
    "advance_pipeline.py",
    "advance_product.py",
    "advance_delivery.py",
    "update_cash.py",
    "record_asset.py",
    "calibrate_business.py",
    "migrate_workspace.py",
    "validate_system.py",
    "preflight_check.py",
    "ensure_python_runtime.py",
    "checkpoint_save.py",
    "validate_release.py",
)
MIN_SUPPORTED_PYTHON = (3, 7)
STATE_BASE_KEY = "__opcos_base_state"
PYTHON_CANDIDATE_COMMANDS = (
    "python3.13",
    "python3.12",
    "python3.11",
    "python3.10",
    "python3.9",
    "python3.8",
    "python3.7",
    "python3",
    "python",
)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def safe_workspace_name(value: str) -> str:
    cleaned = re.sub(r'[\\/:*?"<>|]', "-", value).strip()
    return cleaned or "未命名公司"


def slugify(value: str) -> str:
    slug = re.sub(r"[^\w]+", "-", value.strip().lower(), flags=re.UNICODE).strip("-_")
    return slug or "record"


def safe_document_name(value: str) -> str:
    cleaned = re.sub(r'[\\/:*?"<>|]', "-", value).strip()
    cleaned = re.sub(r"\s+", "-", cleaned)
    cleaned = re.sub(r"-{2,}", "-", cleaned).strip("-")
    return cleaned or "未命名文档"


def numbered_name(index: int, title: str, suffix: str) -> str:
    return f"{index:02d}-{safe_document_name(title)}{suffix}"


def planned_docx_name(index: int, title: str, status: str) -> str:
    _ = status
    return f"{index:02d}-{safe_document_name(title)}.docx"


def parse_planned_docx_name(filename: str) -> Optional[dict[str, Any]]:
    match = re.match(r"^(?P<index>\d{2})-(?:\[(?P<status>待生成|已生成)\])?(?P<title>.+)\.docx$", filename)
    if not match:
        return None
    marker = match.group("status")
    return {
        "index": int(match.group("index")),
        "status": "done" if marker in (None, "已生成") else "pending",
        "legacy_status": marker,
        "title": match.group("title"),
    }


def ensure_planned_docx_path(directory: Path, index: int, title: str, *, completed: bool) -> Path:
    desired = directory / planned_docx_name(index, title, "done" if completed else "pending")
    safe_title = safe_document_name(title)
    existing_matches = []
    if directory.is_dir():
        for path in directory.iterdir():
            parsed = parse_planned_docx_name(path.name)
            if parsed and parsed["index"] == index and parsed["title"] == safe_title:
                existing_matches.append(path)

    for path in existing_matches:
        if path == desired:
            return desired
    if existing_matches:
        source = existing_matches[0]
        if desired.exists():
            source.unlink()
        else:
            source.rename(desired)
    return desired


def planned_docx_path(directory: Path, title: str, *, completed: bool) -> Path:
    safe_title = safe_document_name(title)
    existing_index: Optional[int] = None
    if directory.is_dir():
        for path in directory.iterdir():
            parsed = parse_planned_docx_name(path.name)
            if parsed and parsed["title"] == safe_title:
                existing_index = parsed["index"]
                break
    index = existing_index or next_numbered_index(directory)
    return ensure_planned_docx_path(directory, index, title, completed=completed)


def next_numbered_index(directory: Path) -> int:
    max_index = 0
    if directory.is_dir():
        for path in directory.iterdir():
            match = re.match(r"^(\d{2})-", path.name)
            if match:
                max_index = max(max_index, int(match.group(1)))
    return max_index + 1


def normalize_stage(value: str) -> str:
    return localized_normalize_stage(value)


def now_string() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def round_id_now() -> str:
    return datetime.now().strftime("R%Y%m%d%H%M")


def format_list(items: list[str], language: str = "zh-CN") -> str:
    return localized_format_list(items, language)


def bool_label(value: bool, language: str = "zh-CN") -> str:
    return localized_bool_label(value, language)


def bool_audit_label(value: bool, language: str = "zh-CN") -> str:
    return localized_bool_audit_label(value, language)


def joined_text(values: Iterable[str], language: str = "zh-CN") -> str:
    return localized_joined_text(values, language)


def display_path(path: Path, root: Optional[Path] = None) -> str:
    if root is not None:
        try:
            return str(path.relative_to(root))
        except ValueError:
            pass
    return str(path)


def version_text(version: tuple[int, ...]) -> str:
    return ".".join(str(part) for part in version)


def python_compatibility_label(version: tuple[int, ...]) -> str:
    return f"Python {version_text(version)}"


def is_python_version_supported(version: tuple[int, ...]) -> bool:
    return version >= MIN_SUPPORTED_PYTHON


def probe_python(executable: str) -> Optional[dict[str, Any]]:
    command = [executable, "-c", "import json, sys; print(json.dumps({'executable': sys.executable, 'version': list(sys.version_info[:3])}, ensure_ascii=False))"]
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
    except (FileNotFoundError, subprocess.CalledProcessError, OSError):
        return None
    try:
        payload = json.loads(result.stdout.strip())
    except json.JSONDecodeError:
        return None

    version = tuple(int(part) for part in payload.get("version", [])[:3])
    executable_path = str(payload.get("executable", executable))
    if len(version) < 3 or not executable_path:
        return None

    return {
        "executable": executable_path,
        "version": version,
        "supported": is_python_version_supported(version),
    }


def discover_python_runtimes() -> list[dict[str, Any]]:
    candidates = [sys.executable]
    candidates.extend(PYTHON_CANDIDATE_COMMANDS)

    runtimes: list[dict[str, Any]] = []
    seen: set[str] = set()
    for candidate in candidates:
        resolved = candidate
        if not os.path.isabs(candidate):
            located = shutil.which(candidate)
            if not located:
                continue
            resolved = located

        probe = probe_python(resolved)
        if not probe:
            continue

        executable = probe["executable"]
        if executable in seen:
            continue
        seen.add(executable)
        runtimes.append(probe)
    return runtimes


def choose_compatible_runtime(runtimes: list[dict[str, Any]]) -> Optional[dict[str, Any]]:
    current = os.path.realpath(sys.executable)
    compatible = [
        runtime
        for runtime in runtimes
        if runtime["supported"] and os.path.realpath(runtime["executable"]) != current
    ]
    if not compatible:
        return None
    compatible.sort(key=lambda runtime: runtime["version"], reverse=True)
    return compatible[0]


def build_agent_action(
    *,
    current_supported: bool,
    compatible_runtime: Optional[dict[str, Any]],
    writable: bool,
    language: str = "zh-CN",
) -> str:
    if current_supported:
        return pick_text(
            language,
            "优先在 OpenClaw 中继续执行当前脚本；若脚本失败，再由智能体切到手动落盘模式。",
            "Prefer continuing with the current script in OpenClaw; if the script fails, have the agent fall back to manual persistence.",
        )

    minimum = version_text(MIN_SUPPORTED_PYTHON)
    if compatible_runtime:
        return pick_text(
            language,
            "优先让 OpenClaw 智能体运行 `scripts/ensure_python_runtime.py --run-script <目标脚本>`，改用兼容解释器 "
            f"{compatible_runtime['executable']} ({python_compatibility_label(compatible_runtime['version'])}) 重跑脚本；"
            "若切换失败，再由智能体手动完成脚本任务。",
            "Prefer asking the OpenClaw agent to run `scripts/ensure_python_runtime.py --run-script <target-script>` "
            f"and retry with the compatible interpreter {compatible_runtime['executable']} "
            f"({python_compatibility_label(compatible_runtime['version'])}); if switching fails, let the agent finish the task manually.",
        )

    if writable:
        return pick_text(
            language,
            f"优先让 OpenClaw 智能体运行 `scripts/ensure_python_runtime.py --apply` 安装兼容解释器（目标 {minimum}+）；"
            "若当前环境不便安装，则由智能体直接完成脚本任务并手动落盘。",
            f"Prefer asking the OpenClaw agent to run `scripts/ensure_python_runtime.py --apply` to install a compatible interpreter (target {minimum}+); "
            "if installing is not practical in this environment, let the agent finish the task and persist files manually.",
        )

    return pick_text(
        language,
        f"优先让 OpenClaw 智能体在宿主环境运行 `scripts/ensure_python_runtime.py --apply` 安装兼容解释器（目标 {minimum}+）；"
        "若仍无法写文件，只能由智能体继续纯对话推进并明确未保存。",
        f"Prefer asking the OpenClaw agent to run `scripts/ensure_python_runtime.py --apply` in the host environment to install a compatible interpreter (target {minimum}+); "
        "if files still cannot be written, the agent can only continue in chat and must state clearly that nothing was persisted.",
    )


def render_template(template_name: str, values: dict[str, str]) -> str:
    language = values.get("LANGUAGE", "zh-CN")
    template = template_text(template_name, TEMPLATE_DIR, language)
    rendered = template
    for key, value in values.items():
        rendered = rendered.replace(f"{{{{{key}}}}}", value)
    return rendered


def iso_now() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def docx_content_types_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
  <Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
</Types>
"""


def docx_root_rels_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>
"""


def docx_document_rels_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>
"""


def docx_styles_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:style w:type="paragraph" w:default="1" w:styleId="Normal">
    <w:name w:val="Normal"/>
    <w:qFormat/>
    <w:rPr>
      <w:sz w:val="22"/>
    </w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Heading1">
    <w:name w:val="heading 1"/>
    <w:basedOn w:val="Normal"/>
    <w:next w:val="Normal"/>
    <w:qFormat/>
    <w:rPr>
      <w:b/>
      <w:sz w:val="34"/>
    </w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Heading2">
    <w:name w:val="heading 2"/>
    <w:basedOn w:val="Normal"/>
    <w:next w:val="Normal"/>
    <w:qFormat/>
    <w:rPr>
      <w:b/>
      <w:sz w:val="28"/>
    </w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Heading3">
    <w:name w:val="heading 3"/>
    <w:basedOn w:val="Normal"/>
    <w:next w:val="Normal"/>
    <w:qFormat/>
    <w:rPr>
      <w:b/>
      <w:sz w:val="24"/>
    </w:rPr>
  </w:style>
</w:styles>
"""


def docx_app_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"
 xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">
  <Application>One Person Company OS</Application>
</Properties>
"""


def docx_core_xml(title: str) -> str:
    created = iso_now()
    escaped = escape(title)
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
 xmlns:dc="http://purl.org/dc/elements/1.1/"
 xmlns:dcterms="http://purl.org/dc/terms/"
 xmlns:dcmitype="http://purl.org/dc/dcmitype/"
 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <dc:title>{escaped}</dc:title>
  <dc:creator>One Person Company OS</dc:creator>
  <cp:lastModifiedBy>One Person Company OS</cp:lastModifiedBy>
  <dcterms:created xsi:type="dcterms:W3CDTF">{created}</dcterms:created>
  <dcterms:modified xsi:type="dcterms:W3CDTF">{created}</dcterms:modified>
</cp:coreProperties>
"""


def docx_paragraph_xml(text: str, style: Optional[str] = None) -> str:
    escaped_text = escape(text)
    paragraph_style = f"<w:pPr><w:pStyle w:val=\"{style}\"/></w:pPr>" if style else ""
    return (
        "<w:p>"
        f"{paragraph_style}"
        "<w:r><w:t xml:space=\"preserve\">"
        f"{escaped_text}"
        "</w:t></w:r>"
        "</w:p>"
    )


def markdown_to_docx_xml(markdown_text: str) -> str:
    paragraphs: list[str] = []
    for raw_line in markdown_text.splitlines():
        line = raw_line.rstrip()
        if not line:
            paragraphs.append("<w:p/>")
            continue
        style = None
        text = line
        if line.startswith("# "):
            style = "Heading1"
            text = line[2:]
        elif line.startswith("## "):
            style = "Heading2"
            text = line[3:]
        elif line.startswith("### "):
            style = "Heading3"
            text = line[4:]
        elif line.startswith("- "):
            text = f"• {line[2:]}"
        paragraphs.append(docx_paragraph_xml(text, style))

    body = "".join(paragraphs) or "<w:p/>"
    return (
        "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
        "<w:document xmlns:wpc=\"http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas\" "
        "xmlns:mc=\"http://schemas.openxmlformats.org/markup-compatibility/2006\" "
        "xmlns:o=\"urn:schemas-microsoft-com:office:office\" "
        "xmlns:r=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships\" "
        "xmlns:m=\"http://schemas.openxmlformats.org/officeDocument/2006/math\" "
        "xmlns:v=\"urn:schemas-microsoft-com:vml\" "
        "xmlns:wp14=\"http://schemas.microsoft.com/office/word/2010/wordprocessingDrawing\" "
        "xmlns:wp=\"http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing\" "
        "xmlns:w10=\"urn:schemas-microsoft-com:office:word\" "
        "xmlns:w=\"http://schemas.openxmlformats.org/wordprocessingml/2006/main\" "
        "xmlns:w14=\"http://schemas.microsoft.com/office/word/2010/wordml\" "
        "xmlns:wpg=\"http://schemas.microsoft.com/office/word/2010/wordprocessingGroup\" "
        "xmlns:wpi=\"http://schemas.microsoft.com/office/word/2010/wordprocessingInk\" "
        "xmlns:wne=\"http://schemas.microsoft.com/office/2006/wordml\" "
        "xmlns:wps=\"http://schemas.microsoft.com/office/word/2010/wordprocessingShape\" "
        "mc:Ignorable=\"w14 wp14\">"
        f"<w:body>{body}"
        "<w:sectPr><w:pgSz w:w=\"11906\" w:h=\"16838\"/><w:pgMar w:top=\"1440\" w:right=\"1440\" w:bottom=\"1440\" w:left=\"1440\" w:header=\"708\" w:footer=\"708\" w:gutter=\"0\"/></w:sectPr>"
        "</w:body></w:document>"
    )


def write_docx(path: Path, markdown_text: str, *, title: Optional[str] = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    doc_title = title or path.stem
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", docx_content_types_xml())
        archive.writestr("_rels/.rels", docx_root_rels_xml())
        archive.writestr("docProps/app.xml", docx_app_xml())
        archive.writestr("docProps/core.xml", docx_core_xml(doc_title))
        archive.writestr("word/_rels/document.xml.rels", docx_document_rels_xml())
        archive.writestr("word/styles.xml", docx_styles_xml())
        archive.writestr("word/document.xml", markdown_to_docx_xml(markdown_text))


def read_docx_text(path: Path) -> str:
    with zipfile.ZipFile(path) as archive:
        return archive.read("word/document.xml").decode("utf-8")


def artifact_maturity_label(path: Path, language: str = "zh-CN") -> str:
    parsed = parse_planned_docx_name(path.name)
    legacy_status = parsed.get("legacy_status") if parsed else None
    if legacy_status == "已生成":
        return pick_text(language, "交付就绪版", "Delivery-Ready")
    if legacy_status == "待生成":
        return pick_text(language, "起始版", "Starter Formal Doc")

    try:
        text = read_docx_text(path)
    except (KeyError, OSError, zipfile.BadZipFile):
        return pick_text(language, "已建档", "Filed")

    if "交付就绪版" in text or "Delivery-Ready" in text:
        return pick_text(language, "交付就绪版", "Delivery-Ready")
    if "起始版" in text or "Starter Formal Doc" in text:
        return pick_text(language, "起始版", "Starter Formal Doc")
    return pick_text(language, "已建档", "Filed")


def load_role_specs() -> dict[str, dict[str, Any]]:
    specs: dict[str, dict[str, Any]] = {}
    for path in sorted(ROLE_DIR.glob("*.json")):
        spec = load_json(path)
        specs[spec["role_id"]] = spec
    return specs


def load_stage_defaults() -> dict[str, Any]:
    return load_json(ORCHESTRATION_DIR / "stage-defaults.json")


def default_role_ids_for_stage(stage_id: str) -> list[str]:
    return list(load_stage_defaults()["stage_defaults"][stage_id])


def stage_label(stage_id: str, language: str = "zh-CN") -> str:
    return localized_stage_label(stage_id, language)


def state_path(company_dir: Path) -> Path:
    return company_dir.joinpath(*STATE_PATH_PARTS)


def workspace_core_paths(company_dir: Path) -> list[Path]:
    return [company_dir / relative for relative in CORE_WORKSPACE_FILES]


def ensure_workspace_dirs(company_dir: Path) -> None:
    for relative in [
        "",
        "product",
        "sales",
        "delivery",
        "ops",
        "assets",
        "records",
        "automation",
        "角色智能体",
        "流程",
        "产物/01-实际交付",
        "产物/02-软件与代码",
        "产物/03-非软件与业务",
        "产物/04-部署与生产",
        "产物/05-上线与增长",
        "记录/推进日志",
        "记录/决策记录",
        "记录/校准记录",
        "记录/检查点",
        "自动化",
        ]:
        (company_dir / relative).mkdir(parents=True, exist_ok=True)


def _strip_internal_state(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _strip_internal_state(item) for key, item in value.items() if key != STATE_BASE_KEY}
    if isinstance(value, list):
        return [_strip_internal_state(item) for item in value]
    return value


def _merge_state_changes(base: Any, updated: Any, latest: Any) -> Any:
    if isinstance(base, dict) and isinstance(updated, dict) and isinstance(latest, dict):
        merged = deepcopy(latest)
        for key, value in updated.items():
            if key == STATE_BASE_KEY:
                continue
            if key not in base:
                merged[key] = deepcopy(value)
                continue
            base_value = base.get(key)
            latest_value = latest.get(key)
            if value == base_value:
                merged[key] = deepcopy(latest_value)
                continue
            if isinstance(base_value, dict) and isinstance(value, dict) and isinstance(latest_value, dict):
                merged[key] = _merge_state_changes(base_value, value, latest_value)
            else:
                merged[key] = deepcopy(value)
        return merged
    return deepcopy(updated if updated != base else latest)


def save_state(company_dir: Path, state: dict[str, Any]) -> None:
    ensure_workspace_dirs(company_dir)
    path = state_path(company_dir)
    lock_path = path.with_suffix(path.suffix + ".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    prepared = _strip_internal_state(state)
    base_state = deepcopy(state.get(STATE_BASE_KEY)) if isinstance(state.get(STATE_BASE_KEY), dict) else None
    with lock_path.open("w", encoding="utf-8") as lock_handle:
        fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX)
        if base_state is not None and path.exists():
            latest = read_state_any_version(company_dir)
            merged_state = _merge_state_changes(base_state, prepared, latest)
        else:
            merged_state = prepared
        saved_state = write_state_v3(company_dir, merged_state)
        fcntl.flock(lock_handle.fileno(), fcntl.LOCK_UN)
    try:
        lock_path.unlink()
    except FileNotFoundError:
        pass
    state.clear()
    state.update(saved_state)
    state[STATE_BASE_KEY] = deepcopy(saved_state)


def load_state(company_dir: Path) -> dict[str, Any]:
    state = read_state_any_version(company_dir)
    state[STATE_BASE_KEY] = deepcopy(_strip_internal_state(state))
    return state


def role_display_names(role_ids: list[str], role_specs: dict[str, dict[str, Any]], language: str = "zh-CN") -> list[str]:
    names: list[str] = []
    for role_id in role_ids:
        if role_id in role_specs:
            names.append(localized_role_spec(role_specs[role_id], language)["display_name"])
    return names


def role_spec(role_id: str, role_specs: dict[str, dict[str, Any]], language: str = "zh-CN") -> dict[str, Any]:
    if role_id not in role_specs:
        raise ValueError(f"unknown role id: {role_id}")
    return localized_role_spec(role_specs[role_id], language)


def write_record(company_dir: Path, subdir: str, suffix: str, title: str, lines: list[str]) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    path = company_dir / "记录" / subdir / f"{timestamp}-{suffix}.md"
    content = "\n".join([f"# {title}", "", *lines]) + "\n"
    write_text(path, content)
    return path


def preflight_status(company_dir: Optional[Path] = None, language: Optional[str] = None) -> dict[str, Any]:
    if company_dir and state_path(company_dir).is_file():
        language = normalize_language(language, load_json(state_path(company_dir)).get("language"))
    language = normalize_language(language)
    current_version = tuple(sys.version_info[:3])
    current_supported = is_python_version_supported(current_version)
    runtimes = discover_python_runtimes()
    compatible_runtime = choose_compatible_runtime(runtimes)

    required_paths = [SCRIPT_DIR / name for name in REQUIRED_SCRIPT_NAMES]
    required_paths.extend(
        [
            TEMPLATE_DIR / "company-overview-template.md",
            TEMPLATE_DIR / "artifact-output-guide-template.md",
            TEMPLATE_DIR / "artifact-docx-ready-template.md",
            TEMPLATE_DIR / "artifact-delivery-index-template.md",
            TEMPLATE_DIR / "artifact-software-delivery-template.md",
            TEMPLATE_DIR / "artifact-non-software-delivery-template.md",
            TEMPLATE_DIR / "artifact-quality-template.md",
            TEMPLATE_DIR / "artifact-deployment-template.md",
            TEMPLATE_DIR / "artifact-production-template.md",
            TEMPLATE_DIR / "artifact-launch-feedback-template.md",
            TEMPLATE_DIR / "artifact-validate-evidence-template.md",
            TEMPLATE_DIR / "artifact-growth-template.md",
            TEMPLATE_DIR / "stage-role-deliverable-matrix-template.md",
            TEMPLATE_DIR / "current-stage-deliverable-template.md",
            ORCHESTRATION_DIR / "stage-defaults.json",
            ORCHESTRATION_DIR / "handoff-schema.json",
        ]
    )
    missing = [display_path(path, ROOT) for path in required_paths if not path.exists()]
    installed = ROLE_DIR.is_dir() and not missing

    runtime_error = pick_text(language, "无", "None")
    runnable = False

    if company_dir is None:
        writable_target = ROOT
    elif company_dir.exists():
        writable_target = company_dir
    else:
        writable_target = company_dir.parent
    writable = writable_target.exists() and os.access(writable_target, os.W_OK)

    if not current_supported:
        minimum = version_text(MIN_SUPPORTED_PYTHON)
        if compatible_runtime:
            runtime_error = pick_text(
                language,
                f"当前解释器 {python_compatibility_label(current_version)} 不在兼容范围内；"
                f"可改用 {compatible_runtime['executable']} ({python_compatibility_label(compatible_runtime['version'])})。",
                f"The current interpreter {python_compatibility_label(current_version)} is outside the supported range; "
                f"you can switch to {compatible_runtime['executable']} ({python_compatibility_label(compatible_runtime['version'])}).",
            )
        else:
            runtime_error = pick_text(
                language,
                f"当前解释器 {python_compatibility_label(current_version)} 不在兼容范围内；"
                f"未发现可直接切换的 Python {minimum}+。",
                f"The current interpreter {python_compatibility_label(current_version)} is outside the supported range; "
                f"no directly switchable Python {minimum}+ runtime was found.",
            )
    elif installed:
        try:
            load_stage_defaults()
            load_role_specs()
            render_template("company-overview-template.md", {"COMPANY_NAME": "Preflight", "LANGUAGE": language})
        except Exception as exc:
            runtime_error = f"{type(exc).__name__}: {exc}"
        else:
            runnable = True
    else:
        runtime_error = pick_text(
            language,
            f"缺少文件: {joined_text(missing, language)}",
            f"Missing files: {joined_text(missing, language)}",
        )

    workspace_created = bool(company_dir and company_dir.exists())
    persisted = bool(company_dir and all(path.is_file() for path in workspace_core_paths(company_dir)))

    if runnable and writable:
        recommended_mode_id = "script-execution"
    elif compatible_runtime and installed and writable:
        recommended_mode_id = "script-execution-switch-python"
    elif writable:
        recommended_mode_id = "manual-persistence"
    else:
        recommended_mode_id = "chat-only"

    if company_dir is None:
        unsaved_reason = pick_text(language, "尚未指定目标工作区", "No target workspace has been specified yet")
    elif not workspace_created:
        unsaved_reason = pick_text(language, "目标工作区尚未创建", "The target workspace has not been created yet")
    elif not persisted:
        unsaved_reason = pick_text(language, "工作区已存在，但关键文件未全部落盘", "The workspace exists, but not all core files have been persisted")
    else:
        unsaved_reason = pick_text(language, "无", "None")

    agent_action = build_agent_action(
        current_supported=current_supported,
        compatible_runtime=compatible_runtime,
        writable=writable,
        language=language,
    )
    return {
        "language": language,
        "installed": installed,
        "runnable": runnable,
        "python_supported": current_supported,
        "python_minimum": version_text(MIN_SUPPORTED_PYTHON),
        "current_python_version": version_text(current_version),
        "current_python_label": python_compatibility_label(current_version),
        "compatible_python_found": compatible_runtime is not None,
        "compatible_python_path": compatible_runtime["executable"] if compatible_runtime else pick_text(language, "无", "None"),
        "compatible_python_version": version_text(compatible_runtime["version"]) if compatible_runtime else pick_text(language, "无", "None"),
        "recovery_script": "scripts/ensure_python_runtime.py",
        "agent_action": agent_action,
        "workspace_created": workspace_created,
        "persisted": persisted,
        "writable": writable,
        "writable_target": str(writable_target),
        "python_path": sys.executable,
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "recommended_mode_id": recommended_mode_id,
        "recommended_mode": persistence_mode_label(recommended_mode_id, language),
        "runtime_error": (
            pick_text(language, f"{runtime_error} 建议动作: {agent_action}", f"{runtime_error} Recommended action: {agent_action}")
            if runtime_error != pick_text(language, "无", "None")
            else runtime_error
        ),
        "missing_files": joined_text(missing, language),
        "unsaved_reason": unsaved_reason,
    }


def print_step(
    step: int,
    total: int,
    title: str,
    *,
    status: str = "已完成",
    stream: TextIO = sys.stdout,
    language: str = "zh-CN",
) -> None:
    resolved_step_id = resolve_step_id(title)
    step_id = resolved_step_id or step
    meta = step_meta(step_id, language) or {"human": title, "system": title}
    human_label = meta["human"]
    system_label = meta["system"]
    if status == "已完成" and language != "zh-CN":
        status = "Completed"
    if resolved_step_id == 0 and title not in (human_label, system_label):
        status = f"{status}（{title}）" if language == "zh-CN" else f"{status} ({title})"
    print(f"Step {step}/{total} {human_label} [{system_label}]: {status}", file=stream)


def print_block(title: str, items: list[tuple[str, str]], *, stream: TextIO = sys.stdout) -> None:
    print(f"{title}:", file=stream)
    for label, value in items:
        print(f"- {label}: {value}", file=stream)


def step_display(step_number: int, phase: str, language: str = "zh-CN") -> str:
    step_id = resolve_step_id(phase) or step_number
    meta = step_meta(step_id, language) or {"human": phase, "system": phase}
    return f"Step {step_number}/5 {meta['human']} [{meta['system']}]"


def explain_save_status(
    *,
    saved: bool,
    save_path: str,
    filenames: str,
    save_details: str,
    unsaved_reason: str,
    persistence_mode: str,
    language: str,
) -> list[tuple[str, str]]:
    if saved:
        return [
            (
                pick_text(language, "保存结论", "Persistence Result"),
                pick_text(language, "本次关键内容已经真实写入工作区，不只是停留在聊天里。", "The key output from this run has been written into the workspace instead of staying only in chat."),
            ),
            (pick_text(language, "你可以去哪里看", "Where To Look"), save_path),
            (pick_text(language, "这次写入了什么", "Files Written"), filenames),
            (pick_text(language, "写入明细", "Write Details"), save_details),
            (pick_text(language, "当前保存方式", "Current Persistence Mode"), persistence_mode),
        ]

    mode_id = normalize_persistence_mode(persistence_mode)
    save_next = {
        "script-execution": pick_text(language, "先修复脚本执行问题，再重跑当前步骤。", "Fix the script-execution issue first, then rerun this step."),
        "script-execution-switch-python": pick_text(language, "先切换到兼容 Python，再重跑当前步骤。", "Switch to a compatible Python runtime first, then rerun this step."),
        "manual-persistence": pick_text(language, "当前适合直接手动写入 markdown/json 到工作区。", "This environment is better suited for writing markdown/json directly into the workspace."),
        "chat-only": pick_text(language, "当前只能在对话里推进；如果要落盘，需要先确认创建或恢复写入能力。", "This run can only progress in chat; to persist output, confirm workspace creation or restore write access first."),
    }.get(mode_id, pick_text(language, "先确认是否允许写文件，再决定脚本执行或手动落盘。", "Confirm whether file writing is allowed before choosing script execution or manual persistence."))

    return [
        (pick_text(language, "保存结论", "Persistence Result"), pick_text(language, "本次内容还没有真实写入工作区。", "This run has not written the output into the workspace yet.")),
        (pick_text(language, "为什么还没保存", "Why It Is Not Persisted Yet"), unsaved_reason),
        (pick_text(language, "现在内容在哪里", "Where The Content Is Now"), pick_text(language, "当前内容只存在于本次输出或标准输出里。", "The current content only exists in this output or standard output.")),
        (pick_text(language, "如果你要保存", "How To Persist It"), save_next),
        (pick_text(language, "当前保存方式", "Current Persistence Mode"), persistence_mode),
    ]


def explain_runtime_status(runtime: dict[str, Any], language: str) -> list[tuple[str, str]]:
    if runtime["runnable"]:
        runtime_summary = pick_text(language, "当前环境可以直接运行脚本，适合走模式 A。", "The current environment can run the scripts directly, so Mode A is appropriate.")
    elif runtime["compatible_python_found"]:
        runtime_summary = pick_text(language, "当前解释器不理想，但已经找到可切换的兼容 Python。", "The current interpreter is not ideal, but a compatible Python runtime is available.")
    elif runtime["writable"]:
        runtime_summary = pick_text(language, "脚本暂时不稳，但当前环境还能直接写文件，适合走手动落盘。", "Script execution is not reliable right now, but the environment can still write files directly, so manual persistence is appropriate.")
    else:
        runtime_summary = pick_text(language, "当前环境既不适合直接跑脚本，也不适合直接写文件，只能先纯对话推进。", "The environment is not suitable for direct script execution or direct file writes, so chat-only progression is the only safe option for now.")

    install_summary = (
        pick_text(language, "技能文件齐全，可以继续恢复运行。", "The skill files are complete, so recovery can continue.")
        if runtime["installed"]
        else pick_text(language, "技能文件还不完整，先补齐缺失文件。", "The skill files are incomplete, so fill the missing files first.")
    )
    persistence_summary = (
        pick_text(language, "当前工作区已经具备核心落盘文件。", "The current workspace already contains the core persisted files.")
        if runtime["persisted"]
        else runtime["unsaved_reason"]
    )

    return [
        (pick_text(language, "运行结论", "Runtime Summary"), runtime_summary),
        (pick_text(language, "安装情况", "Installation Status"), install_summary),
        (
            pick_text(language, "工作区情况", "Workspace Status"),
            pick_text(language, "目标工作区已存在。", "The target workspace already exists.") if runtime["workspace_created"] else pick_text(language, "目标工作区还没有创建。", "The target workspace has not been created yet."),
        ),
        (pick_text(language, "落盘情况", "Persistence Status"), persistence_summary),
        (pick_text(language, "Python 兼容", "Python Compatibility"), pick_text(language, f"当前是 {runtime['current_python_label']}；兼容目标是 Python {runtime['python_minimum']}+。", f"The current runtime is {runtime['current_python_label']}; the compatibility target is Python {runtime['python_minimum']}+.")),
        (pick_text(language, "推荐动作", "Recommended Action"), runtime["agent_action"]),
    ]


def build_round_dashboard(
    *,
    company_dir: Optional[Path],
    stage: str,
    round_name: str,
    role: str,
    artifact: str,
    next_action: str,
    language: str,
) -> list[tuple[str, str]]:
    if company_dir is not None:
        state_file = state_path(company_dir)
        if state_file.is_file():
            state = load_state(company_dir)
            focus = state.get("focus", {})
            product = state.get("product", {})
            pipeline = state.get("pipeline", {}).get("stage_summary", {})
            delivery_state = state.get("delivery", {})
            return [
                (pick_text(language, "当前阶段标签", "Current Stage Label"), state.get("stage_label", stage)),
                (pick_text(language, "当前主目标", "Current Goal"), focus.get("primary_goal", stage)),
                (pick_text(language, "当前主战场", "Primary Arena"), primary_arena_label(focus.get("primary_arena", "sales"), language)),
                (pick_text(language, "产品状态", "Product State"), product_state_label(product.get("state", "idea"), language)),
                (pick_text(language, "成交概览", "Revenue Pipeline"), f"{pick_text(language, '对话', 'Talking')} {pipeline.get('talking', 0)} / {pick_text(language, '报价', 'Proposal')} {pipeline.get('proposal', 0)} / {pick_text(language, '成交', 'Won')} {pipeline.get('won', 0)}"),
                (pick_text(language, "交付状态", "Delivery Status"), delivery_state.get("delivery_status", pick_text(language, "待确认", "Pending"))),
                (pick_text(language, "当前瓶颈", "Current Bottleneck"), focus.get("primary_bottleneck", pick_text(language, "无", "None"))),
                (pick_text(language, "下一步最短动作", "Shortest Next Action"), focus.get("today_action", next_action)),
            ]

    return [
        (pick_text(language, "当前阶段标签", "Current Stage Label"), stage),
        (pick_text(language, "当前主目标", "Current Goal"), round_name),
        (pick_text(language, "当前主战场", "Primary Arena"), primary_arena_label("sales", language)),
        (pick_text(language, "产品状态", "Product State"), product_state_label("idea", language)),
        (pick_text(language, "成交概览", "Revenue Pipeline"), pick_text(language, "待确认", "Pending")),
        (pick_text(language, "交付状态", "Delivery Status"), pick_text(language, "待确认", "Pending")),
        (pick_text(language, "当前瓶颈", "Current Bottleneck"), pick_text(language, "待确认", "Pending")),
        (pick_text(language, "下一步最短动作", "Shortest Next Action"), next_action),
    ]


def default_work_scope(artifact: str, language: str) -> list[str]:
    return [
        pick_text(language, f"说明本次与 {artifact} 相关的关键结果。", f"Explain the key results from this run related to {artifact}."),
        pick_text(language, "明确这次是否真正保存、保存到哪里。", "Explain clearly whether this run persisted output and where it was written."),
        pick_text(language, "明确当前环境该继续脚本执行、手动落盘，还是只做对话推进。", "Explain whether the current environment should continue with script execution, manual persistence, or chat-only progression."),
    ]


def default_non_scope(mode: str, language: str) -> list[str]:
    if mode == "创建公司" or mode == "Create Company":
        return [pick_text(language, "不会在未确认前假装已经完成正式创建。", "Do not pretend the formal creation already happened before approval.")]
    return [pick_text(language, "不会把未执行的动作说成已经完成。", "Do not claim unfinished actions are already complete.")]


def emit_runtime_report(
    *,
    mode: str,
    phase: str,
    stage: str,
    round_name: str,
    role: str,
    artifact: str,
    next_action: str,
    needs_confirmation: str,
    persistence_mode: str,
    company_dir: Optional[Path],
    saved_paths: list[Path],
    unsaved_reason: str = "无",
    work_scope: Optional[list[str]] = None,
    non_scope: Optional[list[str]] = None,
    changes: Optional[list[str]] = None,
    output_view: str = "both",
    step_number: int = 5,
    stream: TextIO = sys.stdout,
    language: Optional[str] = None,
) -> None:
    language = normalize_language(language, stage, round_name, role, artifact, next_action)
    runtime = preflight_status(company_dir, language=language)
    saved = bool(saved_paths) and all(path.exists() for path in saved_paths)
    save_path = str(company_dir) if company_dir is not None else "未指定"
    if company_dir is None:
        save_path = pick_text(language, "未指定", "Unspecified")
    save_details = joined_text((display_path(path, company_dir) for path in saved_paths), language)
    filenames = joined_text((path.name for path in saved_paths), language)

    if not saved and unsaved_reason == pick_text(language, "无", "None"):
        unsaved_reason = runtime["unsaved_reason"]
    work_scope = work_scope or default_work_scope(artifact, language)
    non_scope = non_scope or default_non_scope(mode, language)
    changes = changes or (
        [pick_text(language, f"已更新或写入 {joined_text((path.name for path in saved_paths), language)}。", f"Updated or wrote {joined_text((path.name for path in saved_paths), language)}.")] if saved_paths else [pick_text(language, "本次没有写入新文件。", "No new files were written in this run.")]
    )
    step_label = step_display(step_number, phase, language)
    localized_mode = mode_label(mode, language)
    localized_persistence_mode = persistence_mode_label(persistence_mode, language)
    round_dashboard = build_round_dashboard(
        company_dir=company_dir,
        stage=stage,
        round_name=round_name,
        role=role,
        artifact=artifact,
        next_action=next_action,
        language=language,
    )
    save_explanation = explain_save_status(
        saved=saved,
        save_path=save_path,
        filenames=filenames,
        save_details=save_details,
        unsaved_reason=unsaved_reason,
        persistence_mode=localized_persistence_mode,
        language=language,
    )
    runtime_explanation = explain_runtime_status(runtime, language)
    review_guidance = [
        (pick_text(language, "查看路径", "Review Path"), save_path),
        (pick_text(language, "重点文件", "Key Files"), save_details or pick_text(language, "本次没有新增保存文件", "No files were persisted in this run")),
        (
            pick_text(language, "如需继续改进", "If You Want Changes"),
            pick_text(language, "如果有不合适的地方，直接告诉我你想调整哪一项，我会继续改进。", "If anything feels off, tell me what to adjust and I will continue improving it."),
        ),
    ]

    if output_view in ("both", "navigation"):
        print(pick_text(language, "用户导航版:", "User Navigation View:"), file=stream)
        print_block(
            pick_text(language, "三层导航条", "Three-Layer Navigation"),
            [
                (pick_text(language, "阶段", "Stage"), stage),
                (pick_text(language, "回合", "Round"), round_name),
                (pick_text(language, "本次 Step", "Current Step"), step_label),
            ],
            stream=stream,
        )
        print_block(
            pick_text(language, "本次范围", "Scope This Run"),
            [
                (pick_text(language, "本次会做", "Will Do"), joined_text(work_scope, language)),
                (pick_text(language, "本次不会做", "Will Not Do"), joined_text(non_scope, language)),
            ],
            stream=stream,
        )
        print_block(
            pick_text(language, "本次变化", "Changes This Run"),
            [
                (pick_text(language, f"变化 {index}", f"Change {index}"), value)
                for index, value in enumerate(changes, start=1)
            ],
            stream=stream,
        )
        print_block(pick_text(language, "回合仪表盘", "Round Dashboard"), round_dashboard, stream=stream)
        print_block(pick_text(language, "查看与改进", "Review And Improve"), review_guidance, stream=stream)
        print_block(pick_text(language, "保存解释", "Persistence Explanation"), save_explanation, stream=stream)
        print_block(pick_text(language, "运行解释", "Runtime Explanation"), runtime_explanation, stream=stream)
        if output_view == "both":
            print("", file=stream)

    if output_view in ("both", "audit"):
        print(pick_text(language, "审计版:", "Audit View:"), file=stream)
        print_block(
            pick_text(language, "状态栏", "Status Bar"),
            [
                (pick_text(language, "当前模式", "Current Mode"), localized_mode),
                (pick_text(language, "当前步骤", "Current Step"), step_label),
                (pick_text(language, "当前阶段", "Current Stage"), stage),
                (pick_text(language, "当前回合", "Current Round"), round_name),
                (pick_text(language, "当前角色", "Current Role"), role),
                (pick_text(language, "当前产物", "Current Artifact"), artifact),
                (pick_text(language, "当前保存模式", "Current Persistence Mode"), localized_persistence_mode),
                (pick_text(language, "下一步动作", "Next Action"), next_action),
                (pick_text(language, "是否需要确认", "Needs Confirmation"), needs_confirmation),
            ],
            stream=stream,
        )
        print_block(
            pick_text(language, "保存状态", "Persistence Status"),
            [
                (pick_text(language, "是否已保存", "Persisted"), bool_label(saved, language)),
                (pick_text(language, "保存路径", "Save Path"), save_path),
                (pick_text(language, "文件名", "File Names"), filenames),
                (pick_text(language, "保存明细", "Save Details"), save_details),
                (pick_text(language, "未保存原因", "Unsaved Reason"), pick_text(language, "无", "None") if saved else unsaved_reason),
            ],
            stream=stream,
        )
        print_block(
            pick_text(language, "运行状态", "Runtime Status"),
            [
                ("installed", bool_audit_label(runtime["installed"], language)),
                ("runnable", bool_audit_label(runtime["runnable"], language)),
                ("python_supported", bool_audit_label(runtime["python_supported"], language)),
                ("workspace_created", bool_audit_label(runtime["workspace_created"], language)),
                ("persisted", bool_audit_label(runtime["persisted"], language)),
                ("writable", bool_audit_label(runtime["writable"], language)),
                (pick_text(language, "当前 Python", "Current Python"), f"{runtime['python_path']} ({runtime['python_version']})"),
                (pick_text(language, "兼容目标", "Compatibility Target"), f"Python {runtime['python_minimum']}+"),
                (pick_text(language, "可切换解释器", "Switchable Interpreter"), pick_text(language, "无", "None") if not runtime["compatible_python_found"] else f"{runtime['compatible_python_path']} ({runtime['compatible_python_version']})"),
                (pick_text(language, "恢复脚本", "Recovery Script"), runtime["recovery_script"]),
                (pick_text(language, "推荐模式", "Recommended Mode"), runtime["recommended_mode"]),
                (pick_text(language, "智能体建议动作", "Suggested Agent Action"), runtime["agent_action"]),
                (pick_text(language, "环境异常", "Runtime Error"), runtime["runtime_error"]),
            ],
            stream=stream,
        )


def build_matrix_values(role_specs: dict[str, dict[str, Any]], language: str) -> dict[str, str]:
    defaults = load_stage_defaults()
    values: dict[str, str] = {}
    for stage_id in ("validate", "build", "launch", "operate", "grow"):
        stage_upper = stage_id.upper()
        stage_roles = role_display_names(defaults["stage_defaults"][stage_id], role_specs, language)
        optional_roles = role_display_names(defaults["stage_optional_roles"].get(stage_id, []), role_specs, language)
        values[f"{stage_upper}_DEFAULT_ROLES"] = format_list(stage_roles, language)
        values[f"{stage_upper}_OPTIONAL_ROLES"] = format_list(optional_roles, language)
        values[f"{stage_upper}_REQUIRED_OUTPUTS"] = format_list(stage_required_outputs(stage_id, language), language)
    return values


def stage_artifact_specs(stage_id: str) -> list[dict[str, str]]:
    common_specs = [
        {
            "subdir": "01-实际交付",
            "index": "01",
            "title": "实际产出总表",
            "template": "artifact-delivery-index-template.md",
        },
        {
            "subdir": "02-软件与代码",
            "index": "01",
            "title": "代码与功能交付清单",
            "template": "artifact-software-delivery-template.md",
        },
        {
            "subdir": "03-非软件与业务",
            "index": "01",
            "title": "非软件交付清单",
            "template": "artifact-non-software-delivery-template.md",
        },
    ]
    stage_specific = {
        "validate": [
            {
                "subdir": "01-实际交付",
                "index": "02",
                "title": "问题与用户证据包",
                "template": "artifact-validate-evidence-template.md",
            },
        ],
        "build": [
            {
                "subdir": "02-软件与代码",
                "index": "02",
                "title": "测试与验收记录",
                "template": "artifact-quality-template.md",
            },
        ],
        "launch": [
            {
                "subdir": "02-软件与代码",
                "index": "02",
                "title": "测试与验收记录",
                "template": "artifact-quality-template.md",
            },
            {
                "subdir": "04-部署与生产",
                "index": "01",
                "title": "部署与回滚清单",
                "template": "artifact-deployment-template.md",
            },
            {
                "subdir": "04-部署与生产",
                "index": "02",
                "title": "生产观测与告警清单",
                "template": "artifact-production-template.md",
            },
            {
                "subdir": "05-上线与增长",
                "index": "01",
                "title": "上线公告与反馈回收清单",
                "template": "artifact-launch-feedback-template.md",
            },
        ],
        "operate": [
            {
                "subdir": "04-部署与生产",
                "index": "01",
                "title": "部署与回滚清单",
                "template": "artifact-deployment-template.md",
            },
            {
                "subdir": "04-部署与生产",
                "index": "02",
                "title": "生产观测与告警清单",
                "template": "artifact-production-template.md",
            },
            {
                "subdir": "04-部署与生产",
                "index": "03",
                "title": "事故响应与复盘记录",
                "template": "artifact-production-template.md",
            },
            {
                "subdir": "05-上线与增长",
                "index": "01",
                "title": "上线公告与反馈回收清单",
                "template": "artifact-launch-feedback-template.md",
            },
        ],
        "grow": [
            {
                "subdir": "04-部署与生产",
                "index": "01",
                "title": "部署与回滚清单",
                "template": "artifact-deployment-template.md",
            },
            {
                "subdir": "04-部署与生产",
                "index": "02",
                "title": "生产观测与告警清单",
                "template": "artifact-production-template.md",
            },
            {
                "subdir": "05-上线与增长",
                "index": "01",
                "title": "增长实验与经营复盘",
                "template": "artifact-growth-template.md",
            },
        ],
    }
    return common_specs + stage_specific.get(stage_id, [])


def artifact_template_values(common_values: dict[str, str], state: dict[str, Any]) -> dict[str, str]:
    current_round = state.get("current_round", {})
    current_stage = state["stage_id"]
    language = state.get("language", "zh-CN")
    return {
        **common_values,
        "ARTIFACT_TITLE": pick_text(language, "正式交付文件", "Formal Deliverable"),
        "ARTIFACT_TYPE": pick_text(language, "正式交付文档", "Formal Deliverable Document"),
        "ARTIFACT_OWNER": current_round.get("owner_role_name", pick_text(language, "总控台", "Control Tower")),
        "ARTIFACT_OBJECTIVE": current_round.get("goal", pick_text(language, "沉淀一个可直接继续补齐的正式交付文档", "Create a formal deliverable that can be completed directly in place")),
        "ARTIFACT_SUMMARY": pick_text(language, "这份文档已经按最终交付文件命名落盘，接下来直接在原文件里补齐真实产出、证据、责任人和下一步动作。", "This document already uses its final deliverable name. Continue refining the real outputs, evidence, owner, and next action in place."),
        "ARTIFACT_SCOPE_IN": format_list(
            [
                pick_text(language, "实际软件产出或实际非软件产出", "Real software outputs or real non-software outputs"),
                pick_text(language, "验收证据与责任人", "Acceptance evidence and accountable owners"),
                pick_text(language, "与当前阶段匹配的部署/生产资料", "Deployment or production materials that match the current stage"),
            ],
            language,
        ),
        "ARTIFACT_SCOPE_OUT": format_list(
            [
                pick_text(language, "只有聊天记录、没有文件或链接的伪交付", "Fake deliverables that only exist in chat without files or links"),
                pick_text(language, "缺少证据路径的空泛总结", "Vague summaries without evidence paths"),
            ],
            language,
        ),
        "ARTIFACT_DELIVERABLES": format_list(stage_required_outputs(current_stage, language), language),
        "ARTIFACT_CHANGES": format_list(
            [
                pick_text(language, "文件名使用两位序号开头。", "File names should start with a two-digit index."),
                pick_text(language, "文件名直接使用最终交付名，不再把状态写进文件名。", "Use the final deliverable name directly instead of encoding document status in the file name."),
                pick_text(language, "产物目录默认只落 DOCX。", "Artifact directories default to DOCX-only formal outputs."),
                pick_text(language, "上线后自动要求部署与生产资料。", "Deployment and production materials become mandatory after launch."),
            ],
            language,
        ),
        "ARTIFACT_DECISIONS": format_list(
            [
                pick_text(language, "关键产物统一进入正式交付文档路径。", "Critical artifacts should enter the formal deliverable path."),
                pick_text(language, "软件和非软件产出都必须可被审计。", "Both software and non-software outputs must remain auditable."),
            ],
            language,
        ),
        "ARTIFACT_RISKS": format_list(
            [pick_text(language, "没有真实文件、代码、配置、材料或证据时，不应视为完成交付。", "If there are no real files, code, configuration, materials, or evidence, the work should not be treated as a completed delivery.")],
            language,
        ),
        "ARTIFACT_NEXT_ACTION": current_round.get("next_action", pick_text(language, "补齐本轮真实交付与证据。", "Fill in the real deliverables and evidence for this round.")),
        "ARTIFACT_STATUS": pick_text(language, "起始版", "Starter Formal Doc"),
        "ARTIFACT_PROGRESS_SUMMARY": pick_text(language, "当前已经生成正式文档起始版，文件名和目录均按最终交付结构落盘，后续直接在原文件内补齐实际内容。", "A starter formal document has been created in the final folder and with the final file name. Continue completing the real content in place."),
        "ARTIFACT_MISSING_ITEMS": format_list(
            [
                pick_text(language, "真实文件、代码、材料或业务证据", "Real files, code, materials, or business evidence"),
                pick_text(language, "责任人与验收结论", "Owner and acceptance conclusion"),
                pick_text(language, "与当前阶段匹配的下一步动作", "A next action that matches the current stage"),
            ],
            language,
        ),
        "ARTIFACT_FILE_PATH": pick_text(language, "落盘后回填", "Filled after the file is written"),
    }


def build_founder_start_here(language: str) -> str:
    if language == "en-US":
        return "\n".join(
            [
                "# Founder Start Card",
                "",
                "## Reply Burden: Keep It To One Sentence",
                "",
                "- Tell me the founder idea in one sentence, or pick one direction below.",
                "- If you are not ready, reply with a single number and I will turn it into the first company draft.",
                "",
                "## Default AI-Era Path",
                "",
                "- Start from one narrow pain, not from a full business plan.",
                "- Validate demand quickly, ship the smallest useful MVP, launch narrowly, then improve from feedback.",
                "- Treat stages as lightweight bottleneck labels, not as bureaucracy.",
                "",
                "## Suggested Directions",
                "",
                "- 1. Sell an AI efficiency tool to a narrow professional role.",
                "- 2. Turn your own workflow into a reusable AI product.",
                "- 3. Build an AI service-plus-software hybrid for a niche industry.",
                "- 4. Build a small launchable product first and expand later.",
                "",
                "## Minimum Input Format",
                "",
                "- Idea: what you want to sell",
                "- User: who pays first",
                "- Problem: what pain is urgent",
                "",
                "## Good Enough Example",
                "",
                '- "I want to build an AI copilot for cross-border sellers who spend too much time writing product listings."',
                "",
                "## After You Reply",
                "",
                "- I will propose the company direction, the current bottleneck stage, the first round, and the first set of formal deliverable documents.",
                "- Review `11-交付目录总览.md` and `12-AI时代快循环.md` in this workspace next.",
                "- If the files, naming, or scope feel off, tell me what to tighten and I will keep refining it.",
            ]
        ) + "\n"
    return "\n".join(
        [
            "# 创始人启动卡",
            "",
            "## 你的回复负担只要一句话",
            "",
            "- 直接说一句你想做什么，或者从下面选一个方向。",
            "- 如果你还没想清楚，只回一个数字也可以，我会把它展开成第一版公司草案。",
            "",
            "## 默认 AI 时代路径",
            "",
            "- 先从一个足够窄的痛点开始，不先写一套大商业计划。",
            "- 先快速验证需求，再做最小可上线 MVP，上线后靠反馈迭代。",
            "- 阶段只是当前主瓶颈标签，不是官僚流程。",
            "",
            "## 可直接选的创业方向",
            "",
            "- 1. 给某个细分职业卖 AI 效率工具。",
            "- 2. 把你自己正在用的工作流产品化。",
            "- 3. 做一个“服务 + 软件”混合型 AI 业务。",
            "- 4. 先做一个可上线的小产品，再逐步扩展。",
            "",
            "## 最小输入格式",
            "",
            "- 想卖什么",
            "- 谁会先付费",
            "- 他现在最痛的点是什么",
            "",
            "## 合格示例",
            "",
            '- “我想做一个给跨境卖家的 AI 上架助手，帮他们更快写标题和描述。”',
            "",
            "## 你回复后我会做什么",
            "",
            "- 我会给出方向建议、当前主瓶颈阶段、首个回合和首批正式交付文档。",
            "- 你可以先看 `11-交付目录总览.md` 和 `12-AI时代快循环.md`，再告诉我还要怎么收紧或改进。",
        ]
    ) + "\n"


def build_ai_fast_loop(language: str) -> str:
    if language == "en-US":
        return "\n".join(
            [
                "# AI-Era Solo Company Fast Loop",
                "",
                "## Core Principle",
                "",
                "- Do not run a solo company like a heavy startup bureaucracy.",
                "- Move through a fast loop: narrow pain, validate demand, ship the smallest useful MVP, launch narrowly, collect feedback, improve, then scale what works.",
                "- Internal stages exist to mark the current bottleneck, not to force unnecessary ceremony.",
                "",
                "## Recommended Loop",
                "",
                "- 1. Narrow the user and pain: make the first buyer and urgent pain concrete.",
                "- 2. Validate with real evidence: interviews, waitlist, pre-sales, manual service, or usage signals.",
                "- 3. Ship the smallest launchable MVP: solve one valuable path end to end.",
                "- 4. Launch narrowly: release to a small user set and a small channel mix first.",
                "- 5. Capture feedback and production reality: keep notes on behavior, objections, bugs, support, and metrics.",
                "- 6. Improve before scaling: fix retention, value delivery, and reliability before widening distribution.",
                "",
                "## How Internal Stages Map To The Loop",
                "",
                "- Validation: find a sharp problem and real demand signals.",
                "- Build: ship the minimum MVP that proves value.",
                "- Launch: put the MVP in front of real users with deployment and feedback paths.",
                "- Operate: keep improving the product through feedback, support, and production stability.",
                "- Grow: scale only after value, retention, and delivery quality are real enough.",
                "",
                "## How To Use This Workspace",
                "",
                "- Start from `10-创始人启动卡.md` if the idea is still fuzzy.",
                "- Use `11-交付目录总览.md` to see which formal documents already exist and which one to improve next.",
                "- Keep one round to roughly 2 to 3 hours, then update the current state.",
                "- Trigger calibration when blocked, drifting, or when a key artifact has just completed.",
                "- Keep formal outputs in `产物/`, and keep software, non-software, and post-launch operations evidence auditable.",
            ]
        ) + "\n"
    return "\n".join(
        [
            "# AI 时代一人公司快循环",
            "",
            "## 核心原则",
            "",
            "- 不要把一人公司跑成重型创业官僚流程。",
            "- 默认走一条快循环：收窄痛点，快速验证，做最小可上线 MVP，小范围上线，收反馈，再迭代，然后再放大。",
            "- 内部阶段只用来标记当前主瓶颈，不用来制造额外手续。",
            "",
            "## 推荐循环",
            "",
            "- 1. 收窄用户和痛点：先说清谁最痛、为什么现在痛、谁会先付费。",
            "- 2. 快速验证需求：用访谈、预约、预售、手动服务或真实使用信号验证。",
            "- 3. 产出最小可上线 MVP：只打通一个真正有价值的闭环。",
            "- 4. 小范围上线：先推给一小批目标用户和少量渠道，不求铺满。",
            "- 5. 回收反馈与生产现实：持续记录使用行为、异议、故障、支持和关键指标。",
            "- 6. 先改再放大：先把价值交付、留存和稳定性修稳，再谈大规模增长。",
            "",
            "## 内部阶段如何映射到这条快循环",
            "",
            "- 验证期：找到尖锐问题和真实需求信号。",
            "- 构建期：做出能证明价值的最小 MVP。",
            "- 上线期：把 MVP 推到真实用户面前，并补齐部署和反馈链路。",
            "- 运营期：围绕反馈、支持和生产稳定性持续修产品。",
            "- 增长期：只在价值、留存和交付质量足够真实后再放大渠道和收益。",
            "",
            "## 在这个工作区里怎么跑",
            "",
            "- 如果想法还模糊，先看 `10-创始人启动卡.md`。",
            "- 用 `11-交付目录总览.md` 看当前正式文档目录、文档成熟度和下一步要补哪一份。",
            "- 单个回合建议控制在 2 到 3 小时，再回来更新当前状态。",
            "- 卡住、偏航或刚完成关键产物时再触发校准。",
            "- 正式件统一进 `产物/`，软件、非软件和上线后生产资料都必须可审计。",
        ]
    ) + "\n"


def primary_arena_label(arena: str, language: str) -> str:
    labels = {
        "sales": pick_text(language, "卖前", "Sales"),
        "product": pick_text(language, "产品", "Product"),
        "delivery": pick_text(language, "交付", "Delivery"),
        "cash": pick_text(language, "现金", "Cash"),
        "asset": pick_text(language, "资产", "Asset"),
    }
    return labels.get(arena, arena)


def product_state_label(state_id: str, language: str) -> str:
    labels = {
        "idea": pick_text(language, "只有想法", "Idea Only"),
        "defined": pick_text(language, "已定义范围", "Scope Defined"),
        "prototype": pick_text(language, "原型中", "In Prototype"),
        "internal": pick_text(language, "内部可用", "Internally Usable"),
        "external": pick_text(language, "外部可测", "Externally Testable"),
        "launchable": pick_text(language, "可上线售卖", "Launchable"),
        "live": pick_text(language, "已上线运行", "Live"),
    }
    return labels.get(state_id, state_id)


def write_text_if_missing(path: Path, text: str) -> None:
    if not path.exists():
        write_text(path, text)


def build_operating_dashboard(state: dict[str, Any], company_dir: Path) -> str:
    language = state["language"]
    focus = state["focus"]
    offer = state["offer"]
    pipeline = state["pipeline"]["stage_summary"]
    product = state["product"]
    delivery = state["delivery"]
    cash = state["cash"]
    lines = [
        pick_text(language, "# 经营总盘", "# Operating Dashboard"),
        "",
        f"{pick_text(language, '更新时间', 'Updated At')}: {now_string()}",
        "",
        pick_text(language, "## 当前结论", "## Current Read"),
        "",
        f"- {pick_text(language, '公司', 'Company')}: {state['company_name']}",
        f"- {pick_text(language, '产品', 'Product')}: {state['product_name']}",
        f"- {pick_text(language, '头号目标', 'Primary Goal')}: {focus['primary_goal']}",
        f"- {pick_text(language, '当前主瓶颈', 'Primary Bottleneck')}: {focus['primary_bottleneck']}",
        f"- {pick_text(language, '当前主战场', 'Primary Arena')}: {primary_arena_label(focus['primary_arena'], language)}",
        f"- {pick_text(language, '今天最短动作', 'Shortest Action Today')}: {focus['today_action']}",
        f"- {pick_text(language, '本周唯一结果', 'Single Weekly Outcome')}: {focus['week_outcome']}",
        "",
        pick_text(language, "## 闭环健康", "## Loop Health"),
        "",
        f"- {pick_text(language, '价值承诺', 'Offer Promise')}: {offer['promise']}",
        f"- {pick_text(language, '目标客户', 'Target Customer')}: {offer['target_customer']}",
        f"- {pick_text(language, '产品状态', 'Product State')}: {product_state_label(product['state'], language)} | {pick_text(language, '版本', 'Version')}: {product['current_version']}",
        f"- {pick_text(language, '成交管道', 'Pipeline')}: {pick_text(language, '发现', 'Discovering')} {pipeline['discovering']} / {pick_text(language, '对话', 'Talking')} {pipeline['talking']} / {pick_text(language, '试用', 'Trial')} {pipeline['trial']} / {pick_text(language, '报价', 'Proposal')} {pipeline['proposal']} / {pick_text(language, '成交', 'Won')} {pipeline['won']}",
        f"- {pick_text(language, '客户交付', 'Delivery')}: {delivery['delivery_status']}",
        f"- {pick_text(language, '现金面', 'Cash')}: in {cash['cash_in']} | out {cash['cash_out']} | {pick_text(language, '待回款', 'Receivable')} {cash['receivable']}",
        "",
        pick_text(language, "## 现在先看哪里", "## Where To Look Next"),
        "",
        f"- [01-创始人约束.md]({display_path(company_dir / '01-创始人约束.md', company_dir)})",
        f"- [02-价值承诺与报价.md]({display_path(company_dir / '02-价值承诺与报价.md', company_dir)})",
        f"- [03-机会与成交管道.md]({display_path(company_dir / '03-机会与成交管道.md', company_dir)})",
        f"- [04-产品与上线状态.md]({display_path(company_dir / '04-产品与上线状态.md', company_dir)})",
        f"- [05-客户交付与回款.md]({display_path(company_dir / '05-客户交付与回款.md', company_dir)})",
        "",
        pick_text(language, "## 关键支撑文档", "## Key Support Documents"),
        "",
        f"- [{pick_text(language, '对外落地页文案', 'Landing Page Copy')}]({display_path(company_dir / 'sales' / '04-对外落地页文案.md', company_dir)})",
        f"- [{pick_text(language, '访谈冲刺看板', 'Interview Sprint Board')}]({display_path(company_dir / 'sales' / '05-访谈冲刺看板.md', company_dir)})",
        f"- [{pick_text(language, '试用申请问卷', 'Trial Application Form')}]({display_path(company_dir / 'sales' / '06-试用申请问卷.md', company_dir)})",
        f"- [{pick_text(language, '可演示静态页', 'Demo Page')}]({display_path(company_dir / 'product' / 'demo' / 'index.html', company_dir)})",
        f"- [{pick_text(language, 'MVP 与上线清单', 'MVP And Launch Checklist')}]({display_path(company_dir / 'product' / '01-MVP与上线清单.md', company_dir)})",
        f"- [{pick_text(language, '上线检查清单', 'Launch Checklist')}]({display_path(company_dir / 'ops' / '01-上线检查清单.md', company_dir)})",
        f"- [{pick_text(language, '试用反馈回收表', 'Trial Feedback Capture')}]({display_path(company_dir / 'delivery' / '04-试用反馈回收表.md', company_dir)})",
        "",
    ]
    return "\n".join(lines) + "\n"


def build_founder_constraints_doc(state: dict[str, Any]) -> str:
    language = state["language"]
    founder = state["founder"]
    lines = [
        pick_text(language, "# 创始人约束", "# Founder Constraints"),
        "",
        f"{pick_text(language, '更新时间', 'Updated At')}: {now_string()}",
        "",
        pick_text(language, "## 经营方式", "## Founder Operating Mode"),
        "",
        f"- {pick_text(language, '当前模式', 'Current Mode')}: {founder['working_mode']}",
        f"- {pick_text(language, '目标模式', 'Goal Mode')}: {founder['goal_mode']}",
        f"- {pick_text(language, '时间预算', 'Time Budget')}: {founder['time_budget']}",
        f"- {pick_text(language, '现金压力', 'Cash Pressure')}: {founder['cash_pressure']}",
        "",
        pick_text(language, "## 优势", "## Strengths"),
        "",
        format_list(founder.get("strengths", []), language),
        "",
        pick_text(language, "## 约束", "## Constraints"),
        "",
        format_list(founder.get("constraints", []), language),
        "",
    ]
    return "\n".join(lines) + "\n"


def build_offer_doc(state: dict[str, Any]) -> str:
    language = state["language"]
    offer = state["offer"]
    lines = [
        pick_text(language, "# 价值承诺与报价", "# Value Promise And Pricing"),
        "",
        f"{pick_text(language, '更新时间', 'Updated At')}: {now_string()}",
        "",
        pick_text(language, "## 当前可卖承诺", "## Current Sellable Promise"),
        "",
        f"- {pick_text(language, '卖什么结果', 'Promised Result')}: {offer['promise']}",
        f"- {pick_text(language, '卖给谁', 'Target Buyer')}: {offer['target_customer']}",
        f"- {pick_text(language, '高频场景', 'High-Frequency Scenario')}: {offer['scenario']}",
        f"- {pick_text(language, '定价方式', 'Pricing')}: {offer['pricing']}",
        "",
        pick_text(language, "## 为什么现在值得买", "## Why It Is Worth Buying Now"),
        "",
        format_list(offer.get("proof", []), language),
        "",
        pick_text(language, "## 当前缺口", "## Current Gap"),
        "",
        f"- {pick_text(language, '如果还卖不动，优先补价值表达、试用路径和报价，而不是盲加功能。', 'If this still does not sell, improve the value story, trial path, and pricing before adding more features.')}",
        "",
    ]
    return "\n".join(lines) + "\n"


def build_pipeline_doc(state: dict[str, Any]) -> str:
    language = state["language"]
    pipeline = state["pipeline"]
    summary = pipeline["stage_summary"]
    opportunities = pipeline.get("opportunities", [])
    lines = [
        pick_text(language, "# 机会与成交管道", "# Opportunity And Revenue Pipeline"),
        "",
        f"{pick_text(language, '更新时间', 'Updated At')}: {now_string()}",
        "",
        pick_text(language, "## 管道概览", "## Pipeline Summary"),
        "",
        f"- {pick_text(language, '发现', 'Discovering')}: {summary['discovering']}",
        f"- {pick_text(language, '对话', 'Talking')}: {summary['talking']}",
        f"- {pick_text(language, '试用', 'Trial')}: {summary['trial']}",
        f"- {pick_text(language, '报价', 'Proposal')}: {summary['proposal']}",
        f"- {pick_text(language, '成交', 'Won')}: {summary['won']}",
        f"- {pick_text(language, '丢失', 'Lost')}: {summary['lost']}",
        "",
        f"{pick_text(language, '下一条真实成交动作', 'Next Real Revenue Action')}: {pipeline['next_revenue_action']}",
        "",
        pick_text(language, "## 当前机会", "## Current Opportunities"),
        "",
    ]
    if opportunities:
        for item in opportunities:
            lines.extend(
                [
                    f"- {item.get('name', pick_text(language, '未命名机会', 'Untitled Opportunity'))} | "
                    f"{pick_text(language, '阶段', 'Stage')}: {item.get('stage', pick_text(language, '待确认', 'TBD'))} | "
                    f"{pick_text(language, '下一步', 'Next Step')}: {item.get('next_action', pick_text(language, '待补充', 'Add next step'))}",
                ]
            )
    else:
        lines.append(pick_text(language, "- 还没有录入具体机会。先补最早能推进收入的一条。", "- No concrete opportunity is recorded yet. Add the earliest revenue-moving one first."))
    lines.extend(["", ""])
    return "\n".join(lines)


def build_product_doc(state: dict[str, Any]) -> str:
    language = state["language"]
    product = state["product"]
    lines = [
        pick_text(language, "# 产品与上线状态", "# Product And Launch Status"),
        "",
        f"{pick_text(language, '更新时间', 'Updated At')}: {now_string()}",
        "",
        pick_text(language, "## 当前状态", "## Current State"),
        "",
        f"- {pick_text(language, '产品状态', 'Product State')}: {product_state_label(product['state'], language)}",
        f"- {pick_text(language, '当前版本', 'Current Version')}: {product['current_version']}",
        f"- {pick_text(language, '上线阻塞', 'Launch Blocker')}: {product['launch_blocker']}",
        f"- {pick_text(language, '仓库', 'Repository')}: {product['repository'] or pick_text(language, '待补充', 'Add repository path')}",
        f"- {pick_text(language, '上线入口', 'Launch Entry')}: {product['launch_path'] or pick_text(language, '待补充', 'Add launch path')}",
        "",
        pick_text(language, "## 核心能力", "## Core Capability"),
        "",
        format_list(product.get("core_capability", []), language),
        "",
        pick_text(language, "## 当前缺口", "## Current Gap"),
        "",
        format_list(product.get("current_gap", []), language),
        "",
        pick_text(language, "## 当前产品策略", "## Current Product Strategy"),
        "",
        pick_text(language, "- 先做训练型助手，不做临床建议型助手。", "- Ship as a training assistant first, not a clinical recommendation assistant."),
        pick_text(language, "- 先做单人可交付的 demo + 试用闭环，不先做全自动平台。", "- Start with a founder-deliverable demo and trial loop before building a fully automated platform."),
        pick_text(language, "- 先验证医生端 willingness to pay，再决定是否扩到护士、机构和雇主端。", "- Validate doctor-side willingness to pay before expanding to nurses, institutions, or employers."),
        "",
        pick_text(language, "## 现在直接打开", "## Open Next"),
        "",
        f"- [product/01-MVP与上线清单.md](product/01-MVP与上线清单.md)",
        f"- [product/demo/index.html](product/demo/index.html)",
        f"- [ops/01-上线检查清单.md](ops/01-上线检查清单.md)",
        "",
    ]
    return "\n".join(lines) + "\n"


def build_delivery_doc(state: dict[str, Any]) -> str:
    language = state["language"]
    delivery = state["delivery"]
    cash = state["cash"]
    lines = [
        pick_text(language, "# 客户交付与回款", "# Delivery And Cash Collection"),
        "",
        f"{pick_text(language, '更新时间', 'Updated At')}: {now_string()}",
        "",
        f"- {pick_text(language, '活跃客户数', 'Active Customers')}: {delivery['active_customers']}",
        f"- {pick_text(language, '当前交付状态', 'Delivery Status')}: {delivery['delivery_status']}",
        f"- {pick_text(language, '交付阻塞', 'Delivery Blocker')}: {delivery['blocking_issue']}",
        f"- {pick_text(language, '下一步交付动作', 'Next Delivery Action')}: {delivery['next_delivery_action']}",
        f"- {pick_text(language, '待回款', 'Receivable')}: {cash['receivable']}",
        "",
        pick_text(language, "## 原则", "## Principle"),
        "",
        pick_text(
            language,
            "- 一人公司不是卖完就结束。这里要持续看交付质量、回款速度、复购机会和口碑风险。",
            "- A solo company does not end at the sale. Track delivery quality, collection speed, renewal opportunity, and reputation risk here.",
        ),
        "",
    ]
    return "\n".join(lines) + "\n"


def build_mvp_checklist_doc(state: dict[str, Any]) -> str:
    language = state["language"]
    product = state["product"]
    focus = state["focus"]
    lines = [
        pick_text(language, "# MVP 与上线清单", "# MVP And Launch Checklist"),
        "",
        f"{pick_text(language, '更新时间', 'Updated At')}: {now_string()}",
        "",
        pick_text(language, "## 这版先交付什么", "## What This Version Must Deliver"),
        "",
        f"- {pick_text(language, '当前版本', 'Current Version')}: {product['current_version']}",
        f"- {pick_text(language, '当前状态', 'Current State')}: {product_state_label(product['state'], language)}",
        f"- {pick_text(language, '当前主瓶颈', 'Primary Bottleneck')}: {focus['primary_bottleneck']}",
        "",
        pick_text(language, "## Demo 必须出现", "## Demo Must Show"),
        "",
        format_list(product.get("core_capability", []), language),
        "",
        pick_text(language, "## 上线前必须补齐", "## Must Be Closed Before Launch"),
        "",
        format_list(product.get("current_gap", []), language),
        "",
        pick_text(language, "## 当前发版原则", "## Current Release Principle"),
        "",
        pick_text(language, "- 先做能演示、能试用、能收反馈的最小版本，不先堆完整功能。", "- Ship the smallest version that can be demoed, trialed, and observed before building out the full product."),
        pick_text(language, "- 先把价值边界、试用入口、反馈闭环跑通，再决定要不要重投入工程化。", "- Get the value boundary, trial entry, and feedback loop working before committing to heavy engineering."),
        "",
    ]
    return "\n".join(lines) + "\n"


def build_sales_action_doc(state: dict[str, Any]) -> str:
    language = state["language"]
    pipeline = state["pipeline"]
    summary = pipeline["stage_summary"]
    lines = [
        pick_text(language, "# 成交动作清单", "# Revenue Action Checklist"),
        "",
        f"{pick_text(language, '更新时间', 'Updated At')}: {now_string()}",
        "",
        pick_text(language, "## 当前漏斗", "## Current Funnel"),
        "",
        f"- {pick_text(language, '发现', 'Discovering')}: {summary['discovering']}",
        f"- {pick_text(language, '对话', 'Talking')}: {summary['talking']}",
        f"- {pick_text(language, '试用', 'Trial')}: {summary['trial']}",
        f"- {pick_text(language, '报价', 'Proposal')}: {summary['proposal']}",
        f"- {pick_text(language, '成交', 'Won')}: {summary['won']}",
        "",
        f"- {pick_text(language, '下一条真实成交动作', 'Next Real Revenue Action')}: {pipeline['next_revenue_action']}",
        "",
        pick_text(language, "## 本周必须推进", "## Must Move This Week"),
        "",
        pick_text(language, "- 锁定 10 个真实目标客户或渠道对象。", "- Lock 10 real target buyers or channel partners."),
        pick_text(language, "- 完成 5 次深访，记录原话、卡点和付费信号。", "- Run 5 interviews and capture exact words, blockers, and buying signals."),
        pick_text(language, "- 约出至少 3 个愿意看 demo 的对象。", "- Book at least 3 people willing to watch the demo."),
        pick_text(language, "- 给每个机会都写清楚下一步，而不是只记名字。", "- Give every opportunity a next step instead of just a name."),
        "",
    ]
    return "\n".join(lines) + "\n"


def build_landing_copy_doc(state: dict[str, Any]) -> str:
    language = state["language"]
    offer = state["offer"]
    product = state["product"]
    product_name = state["product_name"]
    modules = product.get("core_capability", [])[:5]
    pains = [
        pick_text(language, "英语标准是硬门槛，但备考、临床沟通和岗位准备是割裂的。", "Language standards are a hard gate, but exam prep, clinical communication, and job readiness are fragmented."),
        pick_text(language, "医生常常会做临床判断，却很难用当地语境把病情解释、handover 和病历表达说清楚。", "Doctors may know the medicine, but still struggle to explain cases, handovers, and notes in the local context."),
        pick_text(language, "现有替代方案分散在老师、社群、模板和零碎咨询里，缺连续训练闭环。", "Current substitutes are scattered across tutors, groups, templates, and ad hoc consulting instead of one continuous training loop."),
    ]
    lines = [
        pick_text(language, "# 对外落地页文案", "# Landing Page Copy"),
        "",
        f"{pick_text(language, '更新时间', 'Updated At')}: {now_string()}",
        "",
        pick_text(language, "## Hero", "## Hero"),
        "",
        f"- {pick_text(language, '标题', 'Headline')}: {product_name}：帮助中国医生更快完成赴澳执业前的语言、沟通与岗位准备",
        f"- {pick_text(language, '副标题', 'Subheadline')}: {offer['promise']}",
        f"- {pick_text(language, '主 CTA', 'Primary CTA')}: 预约 20 分钟演示",
        f"- {pick_text(language, '次 CTA', 'Secondary CTA')}: 申请 14 天试用",
        "",
        pick_text(language, "## 适合谁", "## Who This Is For"),
        "",
        f"- {offer['target_customer']}",
        pick_text(language, "- 已经确定澳洲是优先目标国家，希望在 6-18 个月内把准备推进到可投递、可面试、可试岗。", "- People who have already chosen Australia as their first target and want to become application-, interview-, and trial-shift-ready within 6-18 months."),
        pick_text(language, "- 不想再靠零散备考、口语陪练和模板堆叠，而是希望把路径准备、临床英语和岗位训练连起来。", "- People who want one connected system for pathway prep, clinical English, and job readiness instead of fragmented prep tools."),
        "",
        pick_text(language, "## 你现在为什么会卡住", "## Why You Are Stuck Today"),
        "",
        format_list(pains, language),
        "",
        pick_text(language, "## 产品怎么帮你推进", "## How The Product Moves You Forward"),
        "",
        format_list(modules, language),
        "",
        pick_text(language, "## 14 天试用里你会拿到什么", "## What The 14-Day Trial Delivers"),
        "",
        pick_text(language, "- 第 1 天：创始人访谈，确认目标岗位、时间窗和当前最大弱项。", "- Day 1: founder interview to confirm target role, timeline, and biggest weakness."),
        pick_text(language, "- 第 2-7 天：完成 1 次患者沟通训练、1 次面试模拟、1 次文书表达任务。", "- Days 2-7: complete one patient-communication drill, one interview simulation, and one documentation task."),
        pick_text(language, "- 第 7 天：拿到中期反馈，知道最需要补的不是哪门考试，而是哪种真实执业表达能力。", "- Day 7: receive a midpoint review that highlights the real practice-expression gap, not just the exam gap."),
        pick_text(language, "- 第 14 天：收到 readiness 复盘，决定继续月订阅、12 周冲刺营，还是暂停。", "- Day 14: receive a readiness recap and decide whether to continue with the monthly plan, the 12-week sprint, or pause."),
        "",
        pick_text(language, "## 定价", "## Pricing"),
        "",
        f"- {offer['pricing']}",
        "",
        pick_text(language, "## 边界说明", "## Product Boundary"),
        "",
        pick_text(language, "- 这不是诊断建议系统，也不替代医生的临床判断。", "- This is not a diagnostic advice system and does not replace a doctor's clinical judgment."),
        pick_text(language, "- 首版定位在训练、准备、文书表达辅助和岗位适应。", "- The first version stays focused on training, preparation, documentation support, and job readiness."),
        pick_text(language, "- 涉及真实患者诊疗时，最终医疗决策仍由持证医生和当地医疗机构承担。", "- For real patient care, final medical responsibility stays with the licensed clinician and local institution."),
        "",
        pick_text(language, "## 页尾 CTA", "## Footer CTA"),
        "",
        pick_text(language, "- 想确认你离赴澳执业 readiness 还差哪一步？先约一次 20 分钟演示。", "- Want to know which step still blocks your Australia-readiness? Start with a 20-minute demo."),
        "",
    ]
    return "\n".join(lines) + "\n"


def build_interview_sprint_doc(state: dict[str, Any]) -> str:
    language = state["language"]
    lines = [
        pick_text(language, "# 访谈冲刺看板", "# Interview Sprint Board"),
        "",
        f"{pick_text(language, '更新时间', 'Updated At')}: {now_string()}",
        "",
        pick_text(language, "## 本轮目标", "## Sprint Goal"),
        "",
        pick_text(language, "- 7 天内约到 10 个访谈对象，完成 5 次深访，拿到 3 个愿意看 demo 的对象。", "- Book 10 interview targets within 7 days, complete 5 interviews, and secure 3 people willing to watch the demo."),
        "",
        pick_text(language, "## 10 个目标席位", "## 10 Target Slots"),
        "",
        pick_text(language, "1. 澳洲路径中国医生 | 来源: 医生社群 / 同学网络 | 条件: 6-18 个月内推进出海 | 下一步: 发首轮邀约", "1. Australia-path Chinese doctor | Source: doctor groups / alumni network | Criteria: planning to move in 6-18 months | Next: send first outreach"),
        pick_text(language, "2. 澳洲路径中国医生 | 来源: OET / IELTS 培训班学员群 | 条件: 已在备考 | 下一步: 找班主任转介绍 2 人", "2. Australia-path Chinese doctor | Source: OET / IELTS class groups | Criteria: actively preparing | Next: ask class manager for 2 referrals"),
        pick_text(language, "3. 澳洲路径中国医生 | 来源: AMC / PESCI 备考圈 | 条件: 已开始岗位申请 | 下一步: 约 20 分钟访谈", "3. Australia-path Chinese doctor | Source: AMC / PESCI prep circles | Criteria: already applying for roles | Next: book a 20-minute interview"),
        pick_text(language, "4. 澳洲路径中国医生 | 来源: 海外临床导师 / 校友 | 条件: 已在澳工作 1-3 年 | 下一步: 验证真实沟通场景", "4. Australia-path Chinese doctor | Source: overseas clinical mentors / alumni | Criteria: already working in Australia for 1-3 years | Next: validate real communication scenarios"),
        pick_text(language, "5. 澳洲路径中国医生 | 来源: 小红书 / 公众号出海内容评论区 | 条件: 公开表达过出海意向 | 下一步: 私信邀约", "5. Australia-path Chinese doctor | Source: public outbound-work content comments | Criteria: explicitly stated interest in moving abroad | Next: direct-message outreach"),
        pick_text(language, "6. OET 培训机构负责人 | 来源: 官网 / 公开课程页 | 条件: 有医生学员 | 下一步: 约渠道访谈", "6. OET training provider lead | Source: official site / public course page | Criteria: serves doctors | Next: channel interview"),
        pick_text(language, "7. 医学英语陪练负责人 | 来源: 公开课程页 | 条件: 有 1 对 1 服务 | 下一步: 讨论联合试用", "7. Medical-English coaching lead | Source: public course page | Criteria: offers 1:1 training | Next: discuss joint trial"),
        pick_text(language, "8. 澳洲医疗招聘顾问 | 来源: 招聘机构官网 | 条件: 负责 IMG 或 rural doctor 招聘 | 下一步: 验证岗位适应痛点", "8. Australia medical recruiter | Source: agency website | Criteria: handles IMG or rural doctor hiring | Next: validate readiness pain points"),
        pick_text(language, "9. 出海服务机构负责人 | 来源: 公开服务页 | 条件: 提供留学 / 移民 / 求职整合服务 | 下一步: 判断是否存在 B2B2C 试点", "9. Overseas-career service lead | Source: public service page | Criteria: offers study / migration / job support | Next: test B2B2C pilot potential"),
        pick_text(language, "10. 澳洲在岗中国医生 KOL | 来源: 公开内容账号 | 条件: 持续分享求职或执业经验 | 下一步: 邀请做产品顾问访谈", "10. Chinese doctor creator in Australia | Source: public content account | Criteria: regularly shares work-abroad experience | Next: invite to advisor interview"),
        "",
        pick_text(language, "## 每次访谈必须产出", "## Every Interview Must Produce"),
        "",
        pick_text(language, "- 当前目标国家和时间窗", "- target country and time horizon"),
        pick_text(language, "- 最贵、最慢、最焦虑的一步", "- the most expensive, slowest, and most anxiety-inducing step"),
        pick_text(language, "- 是否愿意看 demo", "- whether they will watch the demo"),
        pick_text(language, "- 是否愿意试用或付订金", "- whether they will trial or place a deposit"),
        "",
        pick_text(language, "## 结束标准", "## Exit Criteria"),
        "",
        pick_text(language, "- 访谈原话足够支撑落地页改写和 demo 收口。", "- the exact user language is strong enough to rewrite the landing page and tighten the demo."),
        pick_text(language, "- 至少 3 个对象愿意进入 demo 或试用。", "- at least 3 people agree to enter the demo or trial."),
        "",
    ]
    return "\n".join(lines) + "\n"


def build_trial_application_doc(state: dict[str, Any]) -> str:
    language = state["language"]
    product_name = state["product_name"]
    lines = [
        pick_text(language, "# 试用申请问卷", "# Trial Application Form"),
        "",
        f"{pick_text(language, '更新时间', 'Updated At')}: {now_string()}",
        "",
        pick_text(language, "## 开场说明", "## Intro"),
        "",
        f"- {product_name} 当前只开放给明确计划赴澳执业、愿意在 14 天内完成训练任务的首批试用对象。",
        pick_text(language, "- 目标不是广撒网，而是筛出 5-10 位最可能给出高质量反馈和转化信号的人。", "- The goal is not broad lead capture. It is to identify 5-10 early users who will generate strong feedback and conversion signals."),
        "",
        pick_text(language, "## 必填字段", "## Required Fields"),
        "",
        pick_text(language, "1. 姓名或称呼", "1. Name"),
        pick_text(language, "2. 当前所在城市", "2. Current city"),
        pick_text(language, "3. 当前执业年限与科室", "3. Years in practice and specialty"),
        pick_text(language, "4. 目标国家与预计出海时间窗", "4. Target country and timing"),
        pick_text(language, "5. 当前卡点排序：英语考试 / 患者沟通 / 面试 / 文书 / 注册材料", "5. Current blockers ranked: exam / patient communication / interview / documentation / registration"),
        pick_text(language, "6. 最近 6 个月已经为此花了多少钱和多少时间", "6. Money and time spent in the last 6 months"),
        pick_text(language, "7. 你最想先用试用解决哪个环节", "7. Which part you most want the trial to solve first"),
        pick_text(language, "8. 是否愿意完成 14 天内 3 个固定训练任务", "8. Whether you will complete 3 fixed tasks in 14 days"),
        pick_text(language, "9. 是否愿意接受 20 分钟访谈和第 14 天复盘", "9. Whether you accept a 20-minute interview and a day-14 review"),
        pick_text(language, "10. 联系方式", "10. Contact info"),
        "",
        pick_text(language, "## 筛选规则", "## Screening Rules"),
        "",
        pick_text(language, "- 优先收：6-18 个月内会真实推进澳洲路径的人。", "- Prioritize applicants who will realistically pursue the Australia path within 6-18 months."),
        pick_text(language, "- 优先收：已经为英语、岗位或材料投入过时间和金钱的人。", "- Prioritize people who have already invested real time or money in language, jobs, or documentation."),
        pick_text(language, "- 延后收：只是泛泛咨询、没有时间窗、也不愿意完成训练任务的人。", "- Delay applicants who are only browsing, have no timeline, and will not complete the tasks."),
        "",
    ]
    return "\n".join(lines) + "\n"


def build_trial_feedback_doc(state: dict[str, Any]) -> str:
    language = state["language"]
    lines = [
        pick_text(language, "# 试用反馈回收表", "# Trial Feedback Capture"),
        "",
        f"{pick_text(language, '更新时间', 'Updated At')}: {now_string()}",
        "",
        pick_text(language, "## 第 7 天必须回收", "## Must Capture On Day 7"),
        "",
        pick_text(language, "- 哪个模块最有帮助：路径导航 / 沟通训练 / 面试模拟 / 文书表达", "- Which module helped most: pathway guidance / communication drill / interview simulation / documentation"),
        pick_text(language, "- 你实际花了多少分钟使用", "- How many minutes you actually spent"),
        pick_text(language, "- 你最不愿意继续用的是哪一步，为什么", "- Which step you are least willing to continue and why"),
        pick_text(language, "- 如果今天结束试用，你会不会付费继续", "- If the trial ended today, would you pay to continue"),
        "",
        pick_text(language, "## 第 14 天必须回收", "## Must Capture On Day 14"),
        "",
        pick_text(language, "- readiness 哪一项最明显提升", "- Which readiness dimension improved the most"),
        pick_text(language, "- 哪个环节仍然没有解决", "- Which part remains unsolved"),
        pick_text(language, "- 你觉得合理的付费方式是月订阅、训练营还是按次陪跑", "- Which payment mode feels right: monthly, cohort sprint, or concierge support"),
        pick_text(language, "- 你愿不愿意推荐给另一个正在准备赴澳的医生", "- Whether you would recommend it to another doctor preparing for Australia"),
        "",
        pick_text(language, "## 结果记录", "## Outcome Record"),
        "",
        pick_text(language, "- 是否转化为继续试用 / 月付 / 冲刺营 / 退出", "- Whether the user converted into continued trial / monthly / sprint / exit"),
        pick_text(language, "- 如果退出，退出原因只写原话，不写自我解释", "- If they exit, record the exact reason in their words instead of your interpretation"),
        "",
    ]
    return "\n".join(lines) + "\n"


def build_demo_html(state: dict[str, Any]) -> str:
    language = state["language"]
    product_name = escape(state["product_name"])
    company_name = escape(state["company_name"])
    offer = state["offer"]
    product = state["product"]
    promise = escape(offer["promise"])
    target = escape(offer["target_customer"])
    pricing = escape(offer["pricing"])
    proof_items = "".join(f"<li>{escape(item)}</li>" for item in offer.get("proof", []))
    capability_cards = "".join(
        f"<article class=\"card\"><h3>模块 {index + 1}</h3><p>{escape(item)}</p></article>"
        for index, item in enumerate(product.get("core_capability", [])[:5])
    )
    gap_items = "".join(f"<li>{escape(item)}</li>" for item in product.get("current_gap", [])[:5])
    return f"""<!doctype html>
<html lang="{escape('zh-CN' if language == 'zh-CN' else 'en')}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{product_name} Demo</title>
  <style>
    :root {{
      --bg: #f5efe4;
      --ink: #17211d;
      --muted: #51605a;
      --accent: #c95f35;
      --panel: #fffaf2;
      --line: #d9ccb9;
      --ok: #2f7d4d;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "Noto Sans SC", "PingFang SC", "Helvetica Neue", sans-serif;
      color: var(--ink);
      background:
        radial-gradient(circle at top right, rgba(201,95,53,.12), transparent 28%),
        linear-gradient(180deg, #f8f3ea 0%, #efe5d4 100%);
    }}
    .shell {{ max-width: 1120px; margin: 0 auto; padding: 40px 20px 72px; }}
    .hero {{
      display: grid;
      grid-template-columns: 1.1fr .9fr;
      gap: 24px;
      align-items: stretch;
    }}
    .panel {{
      background: rgba(255,250,242,.92);
      border: 1px solid var(--line);
      border-radius: 28px;
      padding: 28px;
      box-shadow: 0 24px 60px rgba(40,31,20,.08);
    }}
    h1, h2, h3 {{ font-family: "Sora", "Avenir Next", sans-serif; margin: 0 0 12px; }}
    h1 {{ font-size: clamp(32px, 6vw, 62px); line-height: 1.02; letter-spacing: -.04em; }}
    h2 {{ font-size: 28px; }}
    p {{ line-height: 1.65; color: var(--muted); }}
    .eyebrow {{
      display: inline-block; padding: 6px 12px; border-radius: 999px;
      background: rgba(201,95,53,.12); color: var(--accent); font-size: 13px; font-weight: 700;
      letter-spacing: .04em; text-transform: uppercase;
    }}
    .cta-row {{ display: flex; flex-wrap: wrap; gap: 12px; margin-top: 20px; }}
    .btn {{
      display: inline-flex; align-items: center; justify-content: center;
      padding: 12px 18px; border-radius: 999px; text-decoration: none; font-weight: 700;
      border: 1px solid var(--ink); color: var(--ink);
    }}
    .btn.primary {{ background: var(--ink); color: #fffdf7; border-color: var(--ink); }}
    .metrics {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-top: 20px; }}
    .metric {{ background: #f1e5d3; border-radius: 18px; padding: 16px; }}
    .metric strong {{ display: block; font-size: 26px; }}
    .grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 18px; margin-top: 28px; }}
    .card {{ background: var(--panel); border: 1px solid var(--line); border-radius: 22px; padding: 20px; }}
    ul {{ margin: 0; padding-left: 20px; color: var(--muted); }}
    li {{ margin: 0 0 10px; line-height: 1.6; }}
    .steps {{ counter-reset: step; display: grid; gap: 14px; }}
    .step {{ position: relative; padding: 18px 18px 18px 64px; }}
    .step::before {{
      counter-increment: step; content: counter(step);
      position: absolute; left: 18px; top: 16px; width: 32px; height: 32px;
      border-radius: 50%; background: var(--accent); color: white;
      display: grid; place-items: center; font-weight: 700;
    }}
    .footer-note {{ font-size: 14px; color: var(--muted); margin-top: 24px; }}
    .form {{ display: grid; gap: 12px; margin-top: 16px; }}
    label {{ font-size: 14px; color: var(--ink); font-weight: 600; }}
    input, textarea, select {{
      width: 100%; margin-top: 6px; padding: 12px 14px; border-radius: 14px;
      border: 1px solid var(--line); background: #fffdf8; color: var(--ink);
      font: inherit;
    }}
    textarea {{ min-height: 110px; resize: vertical; }}
    @media (max-width: 860px) {{
      .hero, .grid {{ grid-template-columns: 1fr; }}
      .metrics {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <div class="shell">
    <section class="hero">
      <div class="panel">
        <span class="eyebrow">Australia Readiness Demo</span>
        <h1>{product_name}</h1>
        <p>{promise}</p>
        <p>面向人群：{target}</p>
        <div class="cta-row">
          <a class="btn primary" href="#trial">预约 20 分钟演示</a>
          <a class="btn" href="#pricing">申请 14 天试用</a>
        </div>
        <div class="metrics">
          <div class="metric"><strong>12 周</strong><span>Readiness 冲刺周期</span></div>
          <div class="metric"><strong>14 天</strong><span>首轮试用与反馈闭环</span></div>
          <div class="metric"><strong>3 个模块</strong><span>沟通、面试、文书先跑通</span></div>
        </div>
      </div>
      <div class="panel">
        <h2>这不是另一个备考资料包</h2>
        <p>它把路径准备、患者沟通、PESCI / 面试模拟和临床文书表达放到同一个训练闭环里。先帮医生达到可解释、可面试、可试岗，而不是直接碰临床决策边界。</p>
        <ul>
          <li>首版不做诊断建议或治疗推荐</li>
          <li>首版重点是语言、沟通、岗位适应和材料准备</li>
          <li>适合作为赴澳执业前的能力补充层</li>
        </ul>
        <p class="footer-note">公司：{company_name}</p>
      </div>
    </section>

    <section class="grid">
      <div class="card">
        <h2>核心模块</h2>
        <div class="grid">{capability_cards}</div>
      </div>
      <div class="card">
        <h2>为什么现在先做这个版本</h2>
        <ul>{proof_items}</ul>
      </div>
    </section>

    <section class="grid" id="trial">
      <div class="card">
        <h2>14 天试用路径</h2>
        <div class="steps">
          <div class="card step"><h3>创始人访谈</h3><p>确认目标岗位、时间窗、语言与沟通弱项。</p></div>
          <div class="card step"><h3>三项训练任务</h3><p>病史采集 / 患者解释、PESCI / 岗位面试、handover / note 改写。</p></div>
          <div class="card step"><h3>中期反馈</h3><p>第 7 天输出薄弱点与训练优先级。</p></div>
          <div class="card step"><h3>readiness 复盘</h3><p>第 14 天决定继续月订阅、冲刺营或机构试点。</p></div>
        </div>
      </div>
      <div class="card" id="pricing">
        <h2>定价与当前阻塞</h2>
        <p><strong>定价：</strong>{pricing}</p>
        <p><strong>当前还要补齐：</strong></p>
        <ul>{gap_items}</ul>
        <div class="cta-row">
          <a class="btn primary" href="#trial">加入首批试用名单</a>
        </div>
        <form class="form">
          <label>你的出海时间窗
            <select>
              <option>3-6 个月</option>
              <option>6-12 个月</option>
              <option>12-18 个月</option>
              <option>18 个月以上</option>
            </select>
          </label>
          <label>你最卡的一步
            <input type="text" value="英语考试 / 患者沟通 / 面试 / 文书 / 注册材料">
          </label>
          <label>你希望 14 天试用先帮你解决什么
            <textarea>我最想先解决患者沟通和岗位面试里的真实表达问题。</textarea>
          </label>
        </form>
      </div>
    </section>
  </div>
</body>
</html>
"""


def build_launch_checklist_doc(state: dict[str, Any]) -> str:
    language = state["language"]
    product = state["product"]
    offer = state["offer"]
    lines = [
        pick_text(language, "# 上线检查清单", "# Launch Checklist"),
        "",
        f"{pick_text(language, '更新时间', 'Updated At')}: {now_string()}",
        "",
        pick_text(language, "## 上线前要确认", "## Confirm Before Launch"),
        "",
        f"- {pick_text(language, '卖什么结果', 'Promised Result')}: {offer['promise']}",
        f"- {pick_text(language, '面向谁', 'Target Buyer')}: {offer['target_customer']}",
        f"- {pick_text(language, '上线入口', 'Launch Entry')}: {product['launch_path'] or pick_text(language, '待补充', 'Add launch path')}",
        f"- {pick_text(language, '当前阻塞', 'Current Blocker')}: {product['launch_blocker']}",
        "",
        pick_text(language, "## 最低上线标准", "## Minimum Launch Bar"),
        "",
        pick_text(language, "- 能被解释清楚：用户 30 秒内知道你解决什么问题。", "- Explainable: the user understands the promised result within 30 seconds."),
        pick_text(language, "- 能被试用：有明确 demo、表单、预约或开通入口。", "- Trialable: there is a clear demo, form, booking, or activation path."),
        pick_text(language, "- 能被收集反馈：知道看什么数据、问什么问题。", "- Observable: you know which feedback and signals to collect."),
        pick_text(language, "- 能解释边界：不做什么、风险在哪里、谁来承担最终决策。", "- Bounded: you can explain what the product does not do, the risks, and who keeps final responsibility."),
        "",
    ]
    return "\n".join(lines) + "\n"


def build_cash_doc(state: dict[str, Any]) -> str:
    language = state["language"]
    cash = state["cash"]
    lines = [
        pick_text(language, "# 现金流与经营健康", "# Cashflow And Business Health"),
        "",
        f"{pick_text(language, '更新时间', 'Updated At')}: {now_string()}",
        "",
        f"- cash in: {cash['cash_in']}",
        f"- cash out: {cash['cash_out']}",
        f"- {pick_text(language, '待回款', 'Receivable')}: {cash['receivable']}",
        f"- {pick_text(language, '月目标收入', 'Monthly Target')}: {cash['monthly_target']}",
        f"- runway: {cash['runway_note']}",
        "",
    ]
    return "\n".join(lines) + "\n"


def build_asset_doc(state: dict[str, Any]) -> str:
    language = state["language"]
    assets = state["assets"]
    lines = [
        pick_text(language, "# 资产与自动化", "# Assets And Automation"),
        "",
        f"{pick_text(language, '更新时间', 'Updated At')}: {now_string()}",
        "",
        "## SOP",
        "",
        format_list(assets.get("sops", []), language),
        "",
        pick_text(language, "## 模板", "## Templates"),
        "",
        format_list(assets.get("templates", []), language),
        "",
        pick_text(language, "## 案例", "## Cases"),
        "",
        format_list(assets.get("cases", []), language),
        "",
        pick_text(language, "## 自动化", "## Automations"),
        "",
        format_list(assets.get("automations", []), language),
        "",
        pick_text(language, "## 可复用代码", "## Reusable Code"),
        "",
        format_list(assets.get("reusable_code", []), language),
        "",
    ]
    return "\n".join(lines) + "\n"


def build_risk_doc(state: dict[str, Any]) -> str:
    language = state["language"]
    risk = state["risk"]
    lines = [
        pick_text(language, "# 风险与关键决策", "# Risks And Key Decisions"),
        "",
        f"{pick_text(language, '更新时间', 'Updated At')}: {now_string()}",
        "",
        pick_text(language, "## 顶级风险", "## Top Risks"),
        "",
        format_list(risk.get("top_risks", []), language),
        "",
        pick_text(language, "## 待决策", "## Pending Decisions"),
        "",
        format_list(risk.get("pending_decisions", []), language),
        "",
    ]
    return "\n".join(lines) + "\n"


def build_week_focus_doc(state: dict[str, Any]) -> str:
    language = state["language"]
    focus = state["focus"]
    lines = [
        pick_text(language, "# 本周唯一主目标", "# Single Weekly Goal"),
        "",
        f"- {pick_text(language, '主目标', 'Primary Goal')}: {focus['primary_goal']}",
        f"- {pick_text(language, '主战场', 'Primary Arena')}: {primary_arena_label(focus['primary_arena'], language)}",
        f"- {pick_text(language, '本周唯一结果', 'Weekly Outcome')}: {focus['week_outcome']}",
        f"- {pick_text(language, '为什么现在先做这个', 'Why This Comes First')}: {focus['primary_bottleneck']}",
        "",
    ]
    return "\n".join(lines) + "\n"


def build_today_action_doc(state: dict[str, Any]) -> str:
    language = state["language"]
    focus = state["focus"]
    lines = [
        pick_text(language, "# 今日最短动作", "# Shortest Action Today"),
        "",
        f"- {pick_text(language, '今天只推进这一件事', 'Only Push This Today')}: {focus['today_action']}",
        f"- {pick_text(language, '当前主瓶颈', 'Primary Bottleneck')}: {focus['primary_bottleneck']}",
        f"- {pick_text(language, '完成标准', 'Definition Of Done')}: {pick_text(language, '今天结束前，当前主瓶颈至少向前推进一格。', 'By the end of today, the current bottleneck should move forward by at least one step.')}",
        "",
    ]
    return "\n".join(lines) + "\n"


def build_collaboration_memory_doc(state: dict[str, Any]) -> str:
    language = state["language"]
    lines = [
        pick_text(language, "# 协作记忆", "# Collaboration Memory"),
        "",
        pick_text(language, "- 每次用户纠偏、风格偏好或交付约束，都要及时补到这里。", "- Record every user correction, delivery preference, and collaboration constraint here."),
        pick_text(language, "- 开工前先读这个文件，再读会话交接。", "- Read this file before starting, then read the session handoff."),
        pick_text(language, "- 不要把文档规范当成最终文档输出。", "- Do not output document specifications instead of final documents."),
        pick_text(language, "- 已完成的文件名不要加状态词。", "- Do not add status words to completed file names."),
        "",
    ]
    return "\n".join(lines) + "\n"


def build_session_handoff_doc(state: dict[str, Any]) -> str:
    language = state["language"]
    focus = state["focus"]
    lines = [
        pick_text(language, "# 会话交接", "# Session Handoff"),
        "",
        f"{pick_text(language, '更新时间', 'Updated At')}: {now_string()}",
        "",
        f"- {pick_text(language, '当前主目标', 'Current Primary Goal')}: {focus['primary_goal']}",
        f"- {pick_text(language, '当前主瓶颈', 'Current Primary Bottleneck')}: {focus['primary_bottleneck']}",
        f"- {pick_text(language, '当前主战场', 'Current Primary Arena')}: {primary_arena_label(focus['primary_arena'], language)}",
        f"- {pick_text(language, '下一步最短动作', 'Shortest Next Action')}: {focus['today_action']}",
        "",
    ]
    return "\n".join(lines) + "\n"


def artifact_status_summary_markdown(company_dir: Path, language: str) -> str:
    category_names = {
        "01-实际交付": pick_text(language, "实际交付", "Actual Deliverables"),
        "02-软件与代码": pick_text(language, "软件与代码", "Software And Code"),
        "03-非软件与业务": pick_text(language, "非软件与业务", "Non-Software And Business"),
        "04-部署与生产": pick_text(language, "部署与生产", "Deployment And Production"),
        "05-上线与增长": pick_text(language, "上线与增长", "Launch And Growth"),
    }
    lines = [
        pick_text(language, "# 交付目录总览", "# Deliverable Directory Overview"),
        "",
        f"{pick_text(language, '更新于', 'Updated At')}: {now_string()}",
        "",
        pick_text(
            language,
            "- 这里列的是当前工作区内已经落盘的正式交付文档，以及每份文档当前的成熟度。",
            "- This page lists the formal deliverable documents already written into the workspace and the current maturity of each one.",
        ),
        pick_text(
            language,
            "- 文件名直接使用最终交付名，不再额外写 `[待生成]` 或 `[已生成]`。",
            "- File names use the final deliverable name directly instead of carrying `[待生成]` or `[已生成]` markers.",
        ),
        "",
    ]

    for subdir, label in category_names.items():
        lines.extend([f"## {label}", ""])
        artifact_dir = company_dir / ARTIFACT_ROOT / subdir
        entries = []
        if artifact_dir.is_dir():
            for path in sorted(artifact_dir.glob("*.docx")):
                status_text = artifact_maturity_label(path, language)
                entries.append(
                    pick_text(
                        language,
                        f"- {path.name} | 文档成熟度: {status_text} | 路径: {display_path(path, company_dir)}",
                        f"- {path.name} | Document Maturity: {status_text} | Path: {display_path(path, company_dir)}",
                    )
                )
        if not entries:
            entries.append(pick_text(language, "- 当前目录还没有 DOCX 文件。", "- No DOCX files exist in this directory yet."))
        lines.extend(entries)
        lines.append("")

    lines.extend(
        [
            pick_text(language, "## 使用方式", "## How To Use"),
            "",
            pick_text(language, "- 先打开本文件看清当前有哪些正式件，再进入对应目录直接补齐内容。", "- Open this file first to see the formal documents that already exist, then continue refining the matching files directly."),
            pick_text(language, "- 如果文件名、顺序或内容边界不合适，直接告诉我你要怎么改，我会继续收口。", "- If the file names, ordering, or scope feel wrong, tell me what to adjust and I will tighten the system further."),
            "",
        ]
    )
    return "\n".join(lines)


def render_workspace(company_dir: Path, state: dict[str, Any]) -> None:
    ensure_workspace_dirs(company_dir)
    role_specs = load_role_specs()
    language = normalize_language(state.get("language"), state.get("company_name"), state.get("product_name"))
    state["language"] = language
    state = sync_legacy_fields(state)

    legacy_root_dir = company_dir / "records" / "legacy-root"
    legacy_root_dir.mkdir(parents=True, exist_ok=True)
    for legacy_name in [
        "00-公司总览.md",
        "01-产品定位.md",
        "02-当前阶段.md",
        "03-组织架构.md",
        "04-当前回合.md",
        "05-推进规则.md",
        "06-触发器与校准规则.md",
        "07-文档产物规范.md",
        "07-交付物地图.md",
        "08-阶段角色与交付矩阵.md",
        "09-当前阶段交付要求.md",
        "10-创始人启动卡.md",
        "11-交付状态总览.md",
        "11-交付目录总览.md",
        "12-AI时代快循环.md",
    ]:
        legacy_path = company_dir / legacy_name
        if legacy_path.exists():
            target = legacy_root_dir / legacy_name
            if target.exists():
                legacy_path.unlink()
            else:
                legacy_path.rename(target)

    artifact_dir = company_dir / ARTIFACT_ROOT
    if artifact_dir.is_dir():
        for path in sorted(artifact_dir.rglob("*.docx")):
            parsed = parse_planned_docx_name(path.name)
            if not parsed or parsed.get("legacy_status") is None:
                continue
            desired = path.with_name(f"{parsed['index']:02d}-{parsed['title']}.docx")
            if desired.exists():
                path.unlink()
            else:
                path.rename(desired)

    stage_id = state["stage_id"]
    stage = stage_meta(stage_id, language)
    state["stage_label"] = stage["label"]
    active_roles = state.get("active_roles") or default_role_ids_for_stage(stage_id)
    active_display = role_display_names(active_roles, role_specs, language)
    available_display = [
        localized_role_spec(spec, language)["display_name"]
        for role_id, spec in sorted(role_specs.items())
        if role_id not in active_roles
    ]
    current_round = state.get("current_round", {})
    current_round["status_id"] = normalize_round_status(current_round.get("status_id") or current_round.get("status", "undefined"))
    current_round["status"] = round_status_label(current_round["status_id"], language)
    round_name = current_round.get("name", pick_text(language, "未启动", "Not Started"))
    round_next_action = current_round.get("next_action", pick_text(language, "待定义", "Undefined"))

    common_values = {
        "LANGUAGE": language,
        "COMPANY_NAME": state["company_name"],
        "PRODUCT_NAME": state["product_name"],
        "STAGE_LABEL": stage["label"],
        "UPDATED_AT": now_string(),
        "COMPANY_GOAL": state["company_goal"],
        "CURRENT_BOTTLENECK": state["current_bottleneck"],
        "CURRENT_ROUND_NAME": round_name,
        "CURRENT_NEXT_ACTION": round_next_action,
        "TARGET_USER": state["target_user"],
        "CORE_PROBLEM": state["core_problem"],
        "PRODUCT_PITCH": state["product_pitch"],
        "STAGE_GOAL": stage["goal"],
        "STAGE_EXIT_CRITERIA": stage["exit_criteria"],
        "NEXT_STAGE_REQUIREMENTS": stage["next_requirements"],
        "STAGE_RISKS": format_list(stage["risks"], language),
        "CURRENT_STAGE_REQUIRED_OUTPUTS": format_list(stage_required_outputs(stage_id, language), language),
        "ACTIVE_ROLE_LIST": format_list(active_display, language),
        "AVAILABLE_ROLE_LIST": format_list(available_display, language),
        "ACTIVE_ROLE_INLINE": ("、".join(active_display) if language == "zh-CN" else ", ".join(active_display)) or pick_text(language, "无", "None"),
    }

    write_text(company_dir / "00-经营总盘.md", build_operating_dashboard(state, company_dir))
    write_text(company_dir / "01-创始人约束.md", build_founder_constraints_doc(state))
    write_text(company_dir / "02-价值承诺与报价.md", build_offer_doc(state))
    write_text(company_dir / "03-机会与成交管道.md", build_pipeline_doc(state))
    write_text(company_dir / "04-产品与上线状态.md", build_product_doc(state))
    write_text(company_dir / "05-客户交付与回款.md", build_delivery_doc(state))
    write_text(company_dir / "06-现金流与经营健康.md", build_cash_doc(state))
    write_text(company_dir / "07-资产与自动化.md", build_asset_doc(state))
    write_text(company_dir / "08-风险与关键决策.md", build_risk_doc(state))
    write_text(company_dir / "09-本周唯一主目标.md", build_week_focus_doc(state))
    write_text(company_dir / "10-今日最短动作.md", build_today_action_doc(state))
    write_text_if_missing(company_dir / "11-协作记忆.md", build_collaboration_memory_doc(state))
    write_text_if_missing(company_dir / "12-会话交接.md", build_session_handoff_doc(state))

    write_text(company_dir / "records" / "01-当前经营快照.md", build_operating_dashboard(state, company_dir))
    write_text(company_dir / "sales" / "01-成交动作清单.md", build_sales_action_doc(state))
    write_text(company_dir / "sales" / "04-对外落地页文案.md", build_landing_copy_doc(state))
    write_text(company_dir / "sales" / "05-访谈冲刺看板.md", build_interview_sprint_doc(state))
    write_text(company_dir / "sales" / "06-试用申请问卷.md", build_trial_application_doc(state))
    write_text(company_dir / "product" / "01-MVP与上线清单.md", build_mvp_checklist_doc(state))
    write_text(company_dir / "product" / "demo" / "index.html", build_demo_html(state))
    write_text(company_dir / "delivery" / "01-客户交付追踪.md", build_delivery_doc(state))
    write_text(company_dir / "delivery" / "02-交付目录总览.md", artifact_status_summary_markdown(company_dir, language))
    write_text(company_dir / "delivery" / "04-试用反馈回收表.md", build_trial_feedback_doc(state))
    write_text(company_dir / "ops" / "01-上线检查清单.md", build_launch_checklist_doc(state))
    write_text(company_dir / "assets" / "01-资产沉淀清单.md", build_asset_doc(state))
    write_text(
        company_dir / "automation" / "01-状态说明.md",
        "\n".join(
            [
                pick_text(language, "# 状态说明", "# State Notes"),
                "",
                f"- {pick_text(language, '主状态文件', 'Primary State File')}: {display_path(state_path(company_dir), company_dir)}",
                f"- {pick_text(language, '当前主战场', 'Current Primary Arena')}: {primary_arena_label(state['focus']['primary_arena'], language)}",
                f"- {pick_text(language, '今天最短动作', 'Shortest Action Today')}: {state['focus']['today_action']}",
                "",
            ]
        )
        + "\n",
    )

    write_text(company_dir / "角色智能体" / "角色清单.md", render_template("role-index-template.md", common_values))
    for role_id in active_roles:
        spec = role_spec(role_id, role_specs, language)
        role_values = {
            "LANGUAGE": language,
            "ROLE_NAME": spec["display_name"],
            "ROLE_MISSION": spec["mission"],
            "ROLE_OWNS": format_list(spec["owns"], language),
            "ROLE_INPUTS": format_list(spec["inputs_required"], language),
            "ROLE_OUTPUTS": format_list(spec["outputs_required"], language),
            "ROLE_GUARDRAILS": format_list(spec["do_not_do"], language),
            "ROLE_APPROVALS": format_list(spec["approval_required_for"], language),
            "ROLE_HANDOFFS": format_list(role_display_names(spec["handoff_to"], role_specs, language), language),
        }
        filename = spec.get("workspace_filename", spec["display_name"])
        write_text(company_dir / "角色智能体" / f"{filename}.md", render_template("role-brief-template.md", role_values))

    write_text(company_dir / "流程" / "创建公司流程.md", render_template("bootstrap-flow-template.md", common_values))
    write_text(company_dir / "流程" / "推进回合流程.md", render_template("round-flow-template.md", common_values))
    write_text(company_dir / "流程" / "校准回合流程.md", render_template("calibration-flow-template.md", common_values))
    write_text(company_dir / "流程" / "阶段切换流程.md", render_template("stage-flow-template.md", common_values))
    write_text(company_dir / "自动化" / "提醒规则.md", render_template("reminder-rules-template.md", common_values))
    write_text(company_dir / "自动化" / "定时任务定义.md", render_template("scheduler-spec-template.md", common_values))

    for spec in stage_artifact_specs(stage_id):
        output_dir = company_dir / ARTIFACT_ROOT / spec["subdir"]
        output_path = ensure_planned_docx_path(output_dir, int(spec["index"]), spec["title"], completed=False)
        docx_values = {
            **artifact_template_values(common_values, state),
            "ARTIFACT_TITLE": spec["title"],
            "ARTIFACT_STATUS": pick_text(language, "起始版", "Starter Formal Doc"),
            "ARTIFACT_PROGRESS_SUMMARY": pick_text(language, "当前已经生成正式文档起始版，可直接在本文件继续补齐真实内容、证据和验收结论。", "A starter formal document has been created. Continue filling in the real content, evidence, and acceptance result in this file directly."),
            "ARTIFACT_FILE_PATH": display_path(output_path, company_dir),
        }
        rendered = render_template(spec["template"], docx_values)
        write_docx(output_path, rendered, title=spec["title"])
