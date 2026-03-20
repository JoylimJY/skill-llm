"""Prompt template loader for SkillBench."""

from pathlib import Path

_PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


def load_prompt(name: str, **kwargs) -> str:
    """Load a prompt template from prompts/{name}.txt and fill in variables.

    Args:
        name: Template name (without .txt extension).
        **kwargs: Variables to substitute via str.format().

    Returns:
        The filled prompt string.
    """
    template_path = _PROMPTS_DIR / f"{name}.txt"
    if not template_path.exists():
        raise FileNotFoundError(f"Prompt template not found: {template_path}")
    template = template_path.read_text()
    if kwargs:
        return template.format(**kwargs)
    return template
