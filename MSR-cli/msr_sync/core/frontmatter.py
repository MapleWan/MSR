"""Frontmatter 解析与生成模块

提供 Markdown 文件中 YAML frontmatter 的解析、剥离和各 IDE 模板头部的生成功能。
"""

from datetime import datetime, timezone
from typing import Optional, Tuple


def strip_frontmatter(content: str) -> str:
    """移除 Markdown 内容中的 YAML frontmatter，返回纯内容。

    Frontmatter 以 ``---\\n`` 开头，以下一个 ``---\\n``（或 ``---`` 在文件末尾）结束。
    如果内容不包含合法的 frontmatter，则原样返回。

    Args:
        content: 可能包含 frontmatter 的 Markdown 文本。

    Returns:
        去除 frontmatter 后的纯 Markdown 正文。
    """
    _, body = parse_frontmatter(content)
    return body


def parse_frontmatter(content: str) -> Tuple[Optional[dict], str]:
    """解析 Markdown 内容中的 YAML frontmatter。

    Args:
        content: 可能包含 frontmatter 的 Markdown 文本。

    Returns:
        一个元组 ``(frontmatter_dict, body)``。
        如果内容不包含合法的 frontmatter，``frontmatter_dict`` 为 ``None``，
        ``body`` 为原始内容。
    """
    if not content.startswith("---\n") and content != "---":
        # 不以 --- 开头，没有 frontmatter
        return None, content

    # 查找第二个 ---
    end_index = content.find("\n---", 3)
    if end_index == -1:
        # 没有找到闭合的 ---，不是合法 frontmatter
        return None, content

    # 提取 frontmatter 原始文本（不含两端的 ---）
    yaml_text = content[4:end_index]

    # 解析简单的 YAML key: value 对
    frontmatter = _parse_simple_yaml(yaml_text)

    # 计算 body 的起始位置：跳过 \n---\n 或 \n--- 到文件末尾
    body_start = end_index + 4  # len("\n---")
    if body_start < len(content) and content[body_start] == "\n":
        body_start += 1

    body = content[body_start:] if body_start <= len(content) else ""

    return frontmatter, body


def _parse_simple_yaml(text: str) -> dict:
    """解析简单的 YAML key: value 文本为字典。

    仅支持单层 key: value 格式，不支持嵌套结构。
    值会尝试转换为 bool / None / 数字等基本类型。

    Args:
        text: YAML 文本（不含 ``---`` 分隔符）。

    Returns:
        解析后的字典。
    """
    result: dict = {}
    for line in text.split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()
        result[key] = _convert_yaml_value(value)
    return result


def _convert_yaml_value(value: str):
    """将 YAML 值字符串转换为 Python 类型。"""
    if value == "" or value.lower() == "null" or value == "~":
        return None
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False
    # 尝试整数
    try:
        return int(value)
    except ValueError:
        pass
    # 尝试浮点数
    try:
        return float(value)
    except ValueError:
        pass
    return value


def build_qoder_header() -> str:
    """生成 Qoder 的 frontmatter 模板。

    Returns:
        Qoder 格式的 frontmatter 字符串。
    """
    return "---\ntrigger: always_on\n---\n"


def build_lingma_header() -> str:
    """生成 Lingma 的 frontmatter 模板。

    Returns:
        Lingma 格式的 frontmatter 字符串。
    """
    return "---\ntrigger: always_on\n---\n"


def build_codebuddy_header() -> str:
    """生成 CodeBuddy 的 frontmatter 模板（含当前时间戳）。

    Returns:
        CodeBuddy 格式的 frontmatter 字符串，``updatedAt`` 字段为当前 UTC 时间的
        ISO 8601 格式时间戳。
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    return (
        "---\n"
        "description: \n"
        "alwaysApply: true\n"
        "enabled: true\n"
        f"updatedAt: {timestamp}\n"
        "provider: \n"
        "---\n"
    )
