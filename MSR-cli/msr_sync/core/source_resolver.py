"""来源解析器 — 解析导入来源（文件/目录/压缩包/URL）"""

import fnmatch
import tarfile
import tempfile
import urllib.request
import zipfile
from enum import Enum
from pathlib import Path
from typing import List, Optional, Tuple

from msr_sync.constants import SKILL_MARKER_FILE
from msr_sync.core.exceptions import InvalidSourceError, NetworkError


class SourceType(Enum):
    """导入来源类型"""

    FILE = "file"
    DIRECTORY = "directory"
    ARCHIVE = "archive"
    URL = "url"


class ResolvedItem:
    """解析后的单个配置项

    Attributes:
        name: 配置项名称
        path: 配置项路径（文件或目录）
        source_type: 来源类型
    """

    def __init__(self, name: str, path: Path, source_type: SourceType):
        self.name = name
        self.path = path
        self.source_type = source_type

    def __repr__(self) -> str:
        return f"ResolvedItem(name={self.name!r}, path={self.path}, source_type={self.source_type})"


class SourceResolver:
    """导入来源解析器

    负责将用户提供的导入来源（文件路径、目录路径、压缩包路径、URL）
    解析为具体的配置项列表，并判断是否需要用户确认。
    """

    def __init__(self) -> None:
        self._temp_dirs: List[tempfile.TemporaryDirectory] = []

    def _should_ignore(self, name: str) -> bool:
        """判断文件名或目录名是否匹配任一忽略模式。

        对每个模式：若模式包含通配符（*、?、[），使用 fnmatch 匹配；
        否则使用精确匹配。仅匹配文件名/目录名部分，不匹配完整路径。

        Args:
            name: 文件名或目录名（不含路径）

        Returns:
            True 表示应跳过
        """
        from msr_sync.core.config import get_config

        patterns = get_config().ignore_patterns
        for pattern in patterns:
            if any(c in pattern for c in ('*', '?', '[')):
                if fnmatch.fnmatch(name, pattern):
                    return True
            else:
                if name == pattern:
                    return True
        return False

    def resolve(
        self, source: str, config_type: str
    ) -> Tuple[List[ResolvedItem], bool]:
        """解析导入来源。

        Args:
            source: 导入来源字符串（文件路径/目录路径/压缩包路径/URL）
            config_type: 配置类型（rules/skills/mcp）

        Returns:
            元组 (配置项列表, 是否需要用户确认)。
            单个配置项时 needs_confirm=False，多个时 needs_confirm=True。

        Raises:
            InvalidSourceError: 来源无效（文件不存在、格式不支持等）
        """
        source_type = self._detect_source_type(source)

        if source_type == SourceType.FILE:
            items = self._resolve_file(Path(source))
        elif source_type == SourceType.DIRECTORY:
            items = self._resolve_directory(Path(source), config_type)
        elif source_type == SourceType.ARCHIVE:
            items = self._resolve_archive(Path(source), config_type)
        elif source_type == SourceType.URL:
            items = self._resolve_url(source, config_type)
        else:
            raise InvalidSourceError(f"无效的导入来源: {source}")

        if not items:
            raise InvalidSourceError(f"未在来源中找到可导入的配置项: {source}")

        needs_confirm = len(items) > 1
        return items, needs_confirm

    def cleanup(self) -> None:
        """清理所有临时目录。"""
        for td in self._temp_dirs:
            td.cleanup()
        self._temp_dirs.clear()

    def _detect_source_type(self, source: str) -> SourceType:
        """检测来源类型。

        Args:
            source: 来源字符串

        Returns:
            对应的 SourceType 枚举值

        Raises:
            InvalidSourceError: 来源无效
        """
        # URL 检测
        if source.startswith("http://") or source.startswith("https://"):
            return SourceType.URL

        path = Path(source)

        # 压缩包检测
        if self._is_archive(source):
            if not path.is_file():
                raise InvalidSourceError(f"压缩包文件不存在: {source}")
            return SourceType.ARCHIVE

        # 文件检测
        if path.is_file():
            return SourceType.FILE

        # 目录检测
        if path.is_dir():
            return SourceType.DIRECTORY

        raise InvalidSourceError(f"无效的导入来源: {source}")

    @staticmethod
    def _is_archive(source: str) -> bool:
        """判断路径是否为支持的压缩包格式。"""
        lower = source.lower()
        return lower.endswith(".zip") or lower.endswith(".tar.gz") or lower.endswith(".tgz")

    def _resolve_file(self, path: Path) -> List[ResolvedItem]:
        """解析单个文件。

        Args:
            path: 文件路径

        Returns:
            包含单个 ResolvedItem 的列表

        Raises:
            InvalidSourceError: 文件不存在或不是 .md 文件
        """
        if not path.is_file():
            raise InvalidSourceError(f"文件不存在: {path}")

        if path.suffix.lower() != ".md":
            raise InvalidSourceError(f"不支持的文件格式: {path}（仅支持 .md 文件）")

        name = path.stem
        return [ResolvedItem(name=name, path=path, source_type=SourceType.FILE)]

    def _resolve_directory(
        self, path: Path, config_type: str, fallback_name: Optional[str] = None
    ) -> List[ResolvedItem]:
        """解析目录，根据 config_type 检测配置项。

        Args:
            path: 目录路径
            config_type: 配置类型（rules/skills/mcp）
            fallback_name: 备用名称，当目录名不可读（如临时目录）时使用

        Returns:
            配置项列表

        Raises:
            InvalidSourceError: 目录不存在
        """
        if not path.is_dir():
            raise InvalidSourceError(f"目录不存在: {path}")

        if config_type == "rules":
            return self._resolve_rules_directory(path)
        elif config_type == "skills":
            return self._resolve_skills_directory(path, fallback_name=fallback_name)
        elif config_type == "mcp":
            return self._resolve_mcp_directory(path, fallback_name=fallback_name)
        else:
            raise InvalidSourceError(f"不支持的配置类型: {config_type}")

    def _resolve_rules_directory(self, path: Path) -> List[ResolvedItem]:
        """解析 rules 目录，检测所有 .md 文件。"""
        items: List[ResolvedItem] = []
        for md_file in sorted(path.iterdir()):
            if self._should_ignore(md_file.name):
                continue
            if md_file.is_file() and md_file.suffix.lower() == ".md":
                items.append(
                    ResolvedItem(
                        name=md_file.stem,
                        path=md_file,
                        source_type=SourceType.FILE,
                    )
                )
        return items

    def _resolve_skills_directory(
        self, path: Path, fallback_name: Optional[str] = None
    ) -> List[ResolvedItem]:
        """解析 skills 目录。

        如果根目录含 SKILL.md，视为单个 skill（名称=目录名）；
        否则每个子目录视为一个独立的 skill。

        Args:
            path: 目录路径
            fallback_name: 备用名称，当目录名不可读（如临时目录）时使用
        """
        if self._is_single_skill(path):
            name = fallback_name if fallback_name else path.name
            return [
                ResolvedItem(
                    name=name,
                    path=path,
                    source_type=SourceType.DIRECTORY,
                )
            ]

        # 多个 skill：每个子目录是一个 skill
        items: List[ResolvedItem] = []
        for entry in sorted(path.iterdir()):
            if self._should_ignore(entry.name):
                continue
            if entry.is_dir():
                items.append(
                    ResolvedItem(
                        name=entry.name,
                        path=entry,
                        source_type=SourceType.DIRECTORY,
                    )
                )
        return items

    def _resolve_mcp_directory(
        self, path: Path, fallback_name: Optional[str] = None
    ) -> List[ResolvedItem]:
        """解析 MCP 目录。

        如果根目录含非子目录文件，视为单个 MCP（名称=目录名）；
        否则每个子目录视为一个独立的 MCP。

        Args:
            path: 目录路径
            fallback_name: 备用名称，当目录名不可读（如临时目录）时使用
        """
        if self._is_single_mcp(path):
            name = fallback_name if fallback_name else path.name
            return [
                ResolvedItem(
                    name=name,
                    path=path,
                    source_type=SourceType.DIRECTORY,
                )
            ]

        # 多个 MCP：每个子目录是一个 MCP
        items: List[ResolvedItem] = []
        for entry in sorted(path.iterdir()):
            if self._should_ignore(entry.name):
                continue
            if entry.is_dir():
                items.append(
                    ResolvedItem(
                        name=entry.name,
                        path=entry,
                        source_type=SourceType.DIRECTORY,
                    )
                )
        return items

    def _resolve_archive(
        self, path: Path, config_type: str
    ) -> List[ResolvedItem]:
        """解压压缩包并解析内容。

        Args:
            path: 压缩包路径
            config_type: 配置类型

        Returns:
            配置项列表

        Raises:
            InvalidSourceError: 压缩包不存在或解压失败
        """
        if not path.is_file():
            raise InvalidSourceError(f"压缩包文件不存在: {path}")

        tmp_dir = tempfile.TemporaryDirectory()
        self._temp_dirs.append(tmp_dir)
        extract_dir = Path(tmp_dir.name)

        try:
            if path.suffix.lower() == ".zip":
                with zipfile.ZipFile(path, "r") as zf:
                    zf.extractall(extract_dir)
            elif path.name.lower().endswith(".tar.gz") or path.suffix.lower() == ".tgz":
                with tarfile.open(path, "r:gz") as tf:
                    tf.extractall(extract_dir)
            else:
                raise InvalidSourceError(f"不支持的压缩包格式: {path}")
        except (zipfile.BadZipFile, tarfile.TarError) as e:
            raise InvalidSourceError(f"压缩包解压失败: {path}") from e

        # 解压后可能有一个顶层目录，也可能直接是文件
        # 检查是否只有一个顶层目录
        top_entries = list(extract_dir.iterdir())
        if len(top_entries) == 1 and top_entries[0].is_dir():
            # 单个顶层目录，进入该目录解析
            actual_dir = top_entries[0]
            return self._resolve_directory(actual_dir, config_type)
        else:
            # 没有单一顶层目录，使用压缩包文件名作为 fallback 名称
            actual_dir = extract_dir
            fallback_name = self._get_archive_stem(path)
            return self._resolve_directory(actual_dir, config_type, fallback_name=fallback_name)

    def _resolve_url(
        self, url: str, config_type: str
    ) -> List[ResolvedItem]:
        """下载 URL 到临时目录后解析。

        Args:
            url: 压缩包 URL
            config_type: 配置类型

        Returns:
            配置项列表

        Raises:
            InvalidSourceError: URL 无效或下载失败
            NetworkError: 网络错误
        """
        tmp_dir = tempfile.TemporaryDirectory()
        self._temp_dirs.append(tmp_dir)
        download_dir = Path(tmp_dir.name)

        # 从 URL 推断文件名
        filename = self._extract_filename_from_url(url)
        if not self._is_archive(filename):
            raise InvalidSourceError(
                f"URL 指向的不是支持的压缩包格式: {url}（仅支持 .zip、.tar.gz、.tgz）"
            )

        download_path = download_dir / filename

        try:
            urllib.request.urlretrieve(url, download_path)
        except Exception as e:
            raise NetworkError(f"下载失败: {url}，请检查网络连接") from e

        return self._resolve_archive(download_path, config_type)

    @staticmethod
    def _get_archive_stem(path: Path) -> str:
        """获取压缩包的 stem 名称（去掉扩展名）。

        处理 .tar.gz 等双重后缀的情况。
        例如：my-skill.zip → my-skill, my-skill.tar.gz → my-skill
        """
        name = path.name
        lower_name = name.lower()
        if lower_name.endswith(".tar.gz"):
            return name[: -len(".tar.gz")]
        elif lower_name.endswith(".tgz"):
            return name[: -len(".tgz")]
        elif lower_name.endswith(".zip"):
            return name[: -len(".zip")]
        else:
            return path.stem

    @staticmethod
    def _extract_filename_from_url(url: str) -> str:
        """从 URL 中提取文件名。"""
        # 去除查询参数和片段
        clean_url = url.split("?")[0].split("#")[0]
        # 取最后一段路径
        filename = clean_url.rstrip("/").rsplit("/", 1)[-1]
        if not filename:
            filename = "download"
        return filename

    @staticmethod
    def _is_single_skill(path: Path) -> bool:
        """判断目录是否为单个 skill。

        根目录含 SKILL.md 则为单个 skill。

        Args:
            path: 目录路径

        Returns:
            True 表示是单个 skill
        """
        return (path / SKILL_MARKER_FILE).is_file()

    @staticmethod
    def _is_single_mcp(path: Path) -> bool:
        """判断目录是否为单个 MCP。

        根目录含非子目录文件则为单个 MCP。

        Args:
            path: 目录路径

        Returns:
            True 表示是单个 MCP
        """
        for entry in path.iterdir():
            if not entry.is_dir():
                return True
        return False
