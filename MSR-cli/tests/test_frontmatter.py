"""Frontmatter 模块单元测试与属性测试"""

from datetime import datetime, timezone

from hypothesis import given
from hypothesis import strategies as st

from msr_sync.core.frontmatter import (
    build_codebuddy_header,
    build_lingma_header,
    build_qoder_header,
    parse_frontmatter,
    strip_frontmatter,
)


# ---------------------------------------------------------------------------
# strip_frontmatter 测试
# ---------------------------------------------------------------------------


class TestStripFrontmatter:
    """strip_frontmatter 函数测试"""

    def test_strip_standard_frontmatter(self):
        """标准 frontmatter 应被正确移除"""
        content = "---\ntrigger: always_on\n---\n# Hello\nWorld"
        result = strip_frontmatter(content)
        assert result == "# Hello\nWorld"

    def test_strip_no_frontmatter(self):
        """无 frontmatter 的内容应原样返回"""
        content = "# Hello\nWorld"
        result = strip_frontmatter(content)
        assert result == "# Hello\nWorld"

    def test_strip_empty_content(self):
        """空字符串应原样返回"""
        assert strip_frontmatter("") == ""

    def test_strip_frontmatter_with_empty_body(self):
        """frontmatter 后无正文时应返回空字符串"""
        content = "---\nkey: value\n---\n"
        result = strip_frontmatter(content)
        assert result == ""

    def test_strip_frontmatter_multiline_body(self):
        """多行正文应完整保留"""
        content = "---\nfoo: bar\n---\nLine 1\nLine 2\nLine 3"
        result = strip_frontmatter(content)
        assert result == "Line 1\nLine 2\nLine 3"

    def test_strip_content_with_triple_dashes_in_body(self):
        """正文中的 --- 不应被误认为 frontmatter 结束"""
        content = "---\nkey: val\n---\nSome text\n---\nMore text"
        result = strip_frontmatter(content)
        assert result == "Some text\n---\nMore text"

    def test_strip_unclosed_frontmatter(self):
        """未闭合的 frontmatter（缺少结束 ---）应原样返回"""
        content = "---\nkey: value\nno closing"
        result = strip_frontmatter(content)
        assert result == content


# ---------------------------------------------------------------------------
# parse_frontmatter 测试
# ---------------------------------------------------------------------------


class TestParseFrontmatter:
    """parse_frontmatter 函数测试"""

    def test_parse_standard_frontmatter(self):
        """标准 frontmatter 应被正确解析为字典"""
        content = "---\ntrigger: always_on\n---\n# Body"
        fm, body = parse_frontmatter(content)
        assert fm == {"trigger": "always_on"}
        assert body == "# Body"

    def test_parse_multiple_keys(self):
        """多个键值对应全部解析"""
        content = "---\nkey1: value1\nkey2: value2\n---\nBody"
        fm, body = parse_frontmatter(content)
        assert fm == {"key1": "value1", "key2": "value2"}
        assert body == "Body"

    def test_parse_boolean_values(self):
        """布尔值应正确转换"""
        content = "---\nenabled: true\ndisabled: false\n---\n"
        fm, body = parse_frontmatter(content)
        assert fm["enabled"] is True
        assert fm["disabled"] is False

    def test_parse_empty_values(self):
        """空值应解析为 None"""
        content = "---\ndescription: \nprovider: \n---\nBody"
        fm, body = parse_frontmatter(content)
        assert fm["description"] is None
        assert fm["provider"] is None
        assert body == "Body"

    def test_parse_integer_values(self):
        """整数值应正确转换"""
        content = "---\ncount: 42\n---\n"
        fm, _ = parse_frontmatter(content)
        assert fm["count"] == 42

    def test_parse_no_frontmatter(self):
        """无 frontmatter 时返回 None 和原始内容"""
        content = "# Just a heading\nSome text"
        fm, body = parse_frontmatter(content)
        assert fm is None
        assert body == content

    def test_parse_empty_content(self):
        """空字符串应返回 None 和空字符串"""
        fm, body = parse_frontmatter("")
        assert fm is None
        assert body == ""

    def test_parse_unclosed_frontmatter(self):
        """未闭合的 frontmatter 应返回 None 和原始内容"""
        content = "---\nkey: value\nno closing"
        fm, body = parse_frontmatter(content)
        assert fm is None
        assert body == content

    def test_parse_codebuddy_style_frontmatter(self):
        """CodeBuddy 风格的 frontmatter 应正确解析"""
        content = (
            "---\n"
            "description: \n"
            "alwaysApply: true\n"
            "enabled: true\n"
            "updatedAt: 2024-01-01T00:00:00+00:00\n"
            "provider: \n"
            "---\n"
            "# Rule content"
        )
        fm, body = parse_frontmatter(content)
        assert fm is not None
        assert fm["description"] is None
        assert fm["alwaysApply"] is True
        assert fm["enabled"] is True
        assert fm["updatedAt"] == "2024-01-01T00:00:00+00:00"
        assert fm["provider"] is None
        assert body == "# Rule content"


# ---------------------------------------------------------------------------
# build_*_header 测试
# ---------------------------------------------------------------------------


class TestBuildHeaders:
    """各 IDE frontmatter 模板生成测试"""

    def test_build_qoder_header(self):
        """Qoder 头部应为 trigger: always_on 格式"""
        header = build_qoder_header()
        assert header == "---\ntrigger: always_on\n---\n"

    def test_build_lingma_header(self):
        """Lingma 头部应为 trigger: always_on 格式"""
        header = build_lingma_header()
        assert header == "---\ntrigger: always_on\n---\n"

    def test_build_qoder_and_lingma_identical(self):
        """Qoder 和 Lingma 头部应完全相同"""
        assert build_qoder_header() == build_lingma_header()

    def test_build_codebuddy_header_structure(self):
        """CodeBuddy 头部应包含所有必需字段"""
        header = build_codebuddy_header()
        assert header.startswith("---\n")
        assert header.endswith("---\n")
        assert "description: \n" in header
        assert "alwaysApply: true\n" in header
        assert "enabled: true\n" in header
        assert "updatedAt: " in header
        assert "provider: \n" in header

    def test_build_codebuddy_header_timestamp_is_current(self):
        """CodeBuddy 头部的时间戳应接近当前时间"""
        before = datetime.now(timezone.utc)
        header = build_codebuddy_header()
        after = datetime.now(timezone.utc)

        # 从 header 中提取时间戳
        for line in header.split("\n"):
            if line.startswith("updatedAt: "):
                ts_str = line[len("updatedAt: "):]
                ts = datetime.fromisoformat(ts_str)
                assert before <= ts <= after
                break
        else:
            raise AssertionError("updatedAt field not found in header")

    def test_build_codebuddy_header_parseable(self):
        """CodeBuddy 头部加正文后应能被 parse_frontmatter 正确解析"""
        header = build_codebuddy_header()
        content = header + "# My Rule\nSome content"
        fm, body = parse_frontmatter(content)
        assert fm is not None
        assert fm["alwaysApply"] is True
        assert fm["enabled"] is True
        assert body == "# My Rule\nSome content"

    def test_qoder_header_parseable(self):
        """Qoder 头部加正文后应能被 parse_frontmatter 正确解析"""
        header = build_qoder_header()
        content = header + "# Rule\nContent"
        fm, body = parse_frontmatter(content)
        assert fm is not None
        assert fm["trigger"] == "always_on"
        assert body == "# Rule\nContent"


# =============================================================================
# 属性基测试 (Property-Based Tests)
# =============================================================================


def _simple_yaml_key():
    """生成合法的简单 YAML 键名（字母开头，字母数字组合）。"""
    return st.from_regex(r"[a-zA-Z][a-zA-Z0-9_]{0,15}", fullmatch=True)


def _simple_yaml_value():
    """生成合法的简单 YAML 值（不含换行和冒号，避免解析歧义）。"""
    return st.from_regex(r"[a-zA-Z0-9_./ -]{1,30}", fullmatch=True)


def _yaml_frontmatter_block():
    """生成合法的 YAML frontmatter 块（含 --- 分隔符）。

    返回 (frontmatter_text, yaml_body) 元组，其中 frontmatter_text 是完整的
    frontmatter 块（含 --- 分隔符），yaml_body 是 frontmatter 内的 YAML 文本。
    """
    return st.lists(
        st.tuples(_simple_yaml_key(), _simple_yaml_value()),
        min_size=1,
        max_size=5,
    ).map(lambda pairs: _build_frontmatter(pairs))


def _build_frontmatter(pairs):
    """从键值对列表构建 frontmatter 块。"""
    yaml_lines = [f"{k}: {v}" for k, v in pairs]
    yaml_body = "\n".join(yaml_lines)
    frontmatter_text = f"---\n{yaml_body}\n---\n"
    return frontmatter_text, yaml_body


def _markdown_body():
    """生成非空的 Markdown 正文内容（不以 --- 开头，避免与 frontmatter 混淆）。"""
    return st.from_regex(
        r"# [A-Z][a-z]{2,10}\n[A-Za-z0-9 .,!?]{5,50}",
        fullmatch=True,
    )


@st.composite
def markdown_with_frontmatter(draw):
    """生成含合法 YAML frontmatter 的完整 Markdown 内容。

    返回 (full_content, frontmatter_text, yaml_body, body) 元组。
    """
    fm_text, yaml_body = draw(_yaml_frontmatter_block())
    body = draw(_markdown_body())
    full_content = fm_text + body
    return full_content, fm_text, yaml_body, body


# Feature: msr-cli, Property 4: Frontmatter 剥离与 IDE 头部转换
# Validates: Requirements 5.1, 5.2, 5.3, 5.4
class TestFrontmatterStripAndIDEHeaderTransformation:
    """Property 4: 对任意含合法 YAML frontmatter 的 Markdown 内容，
    strip_frontmatter 后不包含原始 frontmatter，各 IDE 的头部函数
    以正确模板头部开始且包含原始正文。"""

    @given(data=markdown_with_frontmatter())
    def test_strip_removes_frontmatter_and_preserves_body(self, data):
        """**Validates: Requirements 5.1, 5.2, 5.3, 5.4**

        strip_frontmatter 应移除 frontmatter 并保留原始正文。
        """
        full_content, frontmatter_text, yaml_body, body = data

        stripped = strip_frontmatter(full_content)

        # (a) 剥离后不包含原始 frontmatter 的 YAML 内容
        # 检查每个 YAML 键值行不在剥离结果中（除非正文碰巧包含相同文本）
        assert stripped == body

    @given(data=markdown_with_frontmatter())
    def test_qoder_header_transformation(self, data):
        """**Validates: Requirements 5.1**

        Qoder: strip_frontmatter 后添加 Qoder 头部，结果以正确模板开始且包含正文。
        """
        full_content, frontmatter_text, yaml_body, body = data

        stripped = strip_frontmatter(full_content)
        qoder_header = build_qoder_header()
        result = qoder_header + stripped

        # (a) 结果不包含原始 frontmatter 的 YAML 行
        for line in yaml_body.split("\n"):
            line = line.strip()
            if line and line not in ("trigger: always_on",):
                # 排除 Qoder 自身头部中的字段
                assert line not in result.split("---\n")[0] + "---\n" or line in body

        # (b) 以 Qoder 模板头部开始
        assert result.startswith("---\ntrigger: always_on\n---\n")

        # (c) 包含原始正文
        assert body in result

    @given(data=markdown_with_frontmatter())
    def test_lingma_header_transformation(self, data):
        """**Validates: Requirements 5.2**

        Lingma: strip_frontmatter 后添加 Lingma 头部，结果以正确模板开始且包含正文。
        """
        full_content, frontmatter_text, yaml_body, body = data

        stripped = strip_frontmatter(full_content)
        lingma_header = build_lingma_header()
        result = lingma_header + stripped

        # (b) 以 Lingma 模板头部开始
        assert result.startswith("---\ntrigger: always_on\n---\n")

        # (c) 包含原始正文
        assert body in result

    @given(data=markdown_with_frontmatter())
    def test_trae_no_header(self, data):
        """**Validates: Requirements 5.3**

        Trae: strip_frontmatter 后不添加额外头部，结果就是纯正文。
        """
        full_content, frontmatter_text, yaml_body, body = data

        stripped = strip_frontmatter(full_content)

        # Trae 不添加头部，结果就是剥离后的正文
        assert stripped == body

        # (a) 不包含原始 frontmatter
        assert frontmatter_text not in stripped

    @given(data=markdown_with_frontmatter())
    def test_codebuddy_header_transformation(self, data):
        """**Validates: Requirements 5.4**

        CodeBuddy: strip_frontmatter 后添加 CodeBuddy 头部，结果以正确模板开始且包含正文。
        """
        full_content, frontmatter_text, yaml_body, body = data

        stripped = strip_frontmatter(full_content)
        codebuddy_header = build_codebuddy_header()
        result = codebuddy_header + stripped

        # (a) 结果不包含原始 frontmatter 块
        assert frontmatter_text not in result

        # (b) 以 CodeBuddy 模板头部开始（以 --- 开头，包含必需字段）
        assert result.startswith("---\n")
        assert "description: \n" in result
        assert "alwaysApply: true\n" in result
        assert "enabled: true\n" in result
        assert "updatedAt: " in result
        assert "provider: \n" in result

        # (c) 包含原始正文
        assert body in result
