"""Prompt template loader for SkillBench."""

import string
from pathlib import Path

_PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


class RobustFormatter(string.Formatter):
    """
    一个极其健壮的字符串格式化器。
    专门应对 Prompt 模板中混杂的 Bash 脚本（如 {1}）和 JSON 结构（如 {"a": 1}）。
    遇到未知的占位符时不会崩溃，而是原样保留。
    """
    def vformat(self, format_string, args, kwargs):
        result = []
        # self.parse 会把字符串拆解成：(普通文本, 括号里的变量名, 格式化符, 转换符)
        for literal_text, field_name, format_spec, conversion in self.parse(format_string):
            # 1. 拼接普通的文本部分
            if literal_text:
                result.append(literal_text)

            # 2. 如果碰到了 {...} 的块
            if field_name is not None:
                try:
                    # 尝试像正常 format 一样去 kwargs 里取值并转换
                    # 注意：args 传入空元组 () 确保 {0}, {1} 这种位置参数也会触发异常从而被保留
                    obj, _ = self.get_field(field_name, args, kwargs)
                    obj = self.convert_field(obj, conversion)
                    result.append(self.format_field(obj, format_spec))
                    
                except (KeyError, IndexError, ValueError, AttributeError):
                    # 3. 【核心容错魔法】
                    # 一旦触发报错（比如找不到键、索引越界，或者遇到 JSON 里的冒号导致解析失败）
                    # 直接把它原本的样子重新组装起来，当成普通字符串塞回去
                    original_bracket = "{" + field_name
                    if conversion:
                        original_bracket += "!" + conversion
                    if format_spec:
                        original_bracket += ":" + format_spec
                    original_bracket += "}"
                    
                    result.append(original_bracket)

        return "".join(result)

# 全局实例化我们的容错 Formatter
_formatter = RobustFormatter()


def load_prompt(name: str, **kwargs) -> str:
    """Load a prompt template from prompts/{name}.txt and fill in variables.

    Args:
        name: Template name (without .txt extension).
        **kwargs: Variables to substitute via our RobustFormatter.

    Returns:
        The filled prompt string, gracefully ignoring Bash/JSON brackets.
    """
    template_path = _PROMPTS_DIR / f"{name}.txt"
    if not template_path.exists():
        raise FileNotFoundError(f"Prompt template not found: {template_path}")
        
    template = template_path.read_text(encoding="utf-8")
    
    if kwargs:
        # 【关键修正点】
        # 使用 _formatter.vformat 代替 template.format(**kwargs)
        # args=() 强制让所有 {0}, {1} 这种形式都被当做未知占位符处理
        return _formatter.vformat(template, args=(), kwargs=kwargs)
        
    return template