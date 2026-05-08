"""
批量下载 MSR-gui 所支持的 IDE 图标。

使用标准库 urllib，无需额外依赖。每个 IDE 配置多个候选下载源，
按顺序尝试，成功一个即停止。

用法:
    python scripts/fetch_icons.py            # 下载所有图标到 msr_gui/assets/icons/
    python scripts/fetch_icons.py --force    # 强制覆盖已存在的文件
    python scripts/fetch_icons.py --only cursor qoder
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

# 脚本所在目录的上一级即 MSR-gui/
ROOT = Path(__file__).resolve().parent.parent
ICON_DIR = ROOT / "msr_gui" / "assets" / "icons"

# LobeHub 图标仓库
# - 彩色版：{name}-color.png / .svg （大多数 IDE 提供）
# - 纯色版：{name}.png / .svg （少数 IDE 仅此一种，如 Cursor）
LOBE_PNG_COLOR = (
    "https://raw.githubusercontent.com/lobehub/lobe-icons/"
    "refs/heads/master/packages/static-png/light/{name}-color.png"
)
LOBE_PNG_MONO = (
    "https://raw.githubusercontent.com/lobehub/lobe-icons/"
    "refs/heads/master/packages/static-png/light/{name}.png"
)
LOBE_SVG_COLOR = (
    "https://raw.githubusercontent.com/lobehub/lobe-icons/"
    "refs/heads/master/packages/static-svg/{name}-color.svg"
)

# 图标 URL 候选列表：按优先级尝试，第一个成功即保存
# 文件名即字典 key（扩展名由具体 URL 决定，脚本自动识别）
ICON_SOURCES: dict[str, list[str]] = {
    # === LobeHub 覆盖的 IDE（彩色 PNG 优先，SVG 备用） ===
    "cursor": [
        # Cursor 在 LobeHub 仅提供纯色版
        LOBE_PNG_MONO.format(name="cursor"),
    ],
    "qoder": [
        LOBE_PNG_COLOR.format(name="qoder"),
        LOBE_SVG_COLOR.format(name="qoder"),
    ],
    "trae": [
        LOBE_PNG_COLOR.format(name="trae"),
        LOBE_SVG_COLOR.format(name="trae"),
    ],
    "codebuddy": [
        LOBE_PNG_COLOR.format(name="codebuddy"),
        LOBE_SVG_COLOR.format(name="codebuddy"),
    ],
    "antigravity": [
        LOBE_PNG_COLOR.format(name="antigravity"),
        LOBE_SVG_COLOR.format(name="antigravity"),
        # 官方 Press Kit 备用
        "https://antigravity.google/assets/antigravity_icon_fullcolor.png",
    ],
    # === LobeHub 未收录，从官网 HTML 提取的高清 logo 直链 ===
    "kiro": [
        # kiro.dev 首页 <link rel="icon" href="/icon.svg"> —— 矢量图最佳
        "https://kiro.dev/icon.svg",
        # 备用：apple-touch-icon 192x192 PNG
        "https://kiro.dev/apple-icon.png",
    ],
    "lingma": [
        # lingma.aliyun.com 的 og:image / favicon 直链（134x133 PNG，官方品牌）
        "https://img.alicdn.com/imgextra/i1/O1CN01BN6Jtc1lCfJNviV7H_!!6000000004783-2-tps-134-133.png",
        "https://lingma.aliyun.com/favicon.ico",
    ],
}

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0 Safari/537.36"
)


def _ext_from_url(url: str) -> str:
    """从 URL 推断文件扩展名（仅支持常见图像类型）。"""
    lower = url.lower().split("?")[0]
    for ext in (".svg", ".png", ".webp", ".ico", ".jpg", ".jpeg"):
        if lower.endswith(ext):
            return ext
    return ".png"


def _download(url: str, dest: Path, timeout: int = 15) -> bool:
    """下载单个 URL 到目标路径；成功返回 True。"""
    req = Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urlopen(req, timeout=timeout) as resp:
            data = resp.read()
        if not data:
            return False
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        return True
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        print(f"    ! 失败: {exc}")
        return False


def fetch_icon(name: str, urls: list[str], force: bool = False) -> Path | None:
    """依次尝试候选 URL，保存到 ICON_DIR/{name}{ext}。"""
    # 若已存在任意扩展名的同名图标且未 --force，则跳过
    if not force:
        for ext in (".png", ".svg", ".webp", ".ico"):
            existing = ICON_DIR / f"{name}{ext}"
            if existing.exists() and existing.stat().st_size > 0:
                print(f"[=] {name}: 已存在 {existing.name}，跳过")
                return existing

    for idx, url in enumerate(urls, 1):
        ext = _ext_from_url(url)
        dest = ICON_DIR / f"{name}{ext}"
        print(f"[>] {name}: 尝试 #{idx} {url}")
        if _download(url, dest):
            print(f"[✓] {name}: 保存至 {dest.relative_to(ROOT)}")
            return dest
    print(f"[x] {name}: 所有候选源均失败")
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="下载 MSR-gui 所需 IDE 图标")
    parser.add_argument("--force", action="store_true", help="覆盖已存在文件")
    parser.add_argument(
        "--only",
        nargs="+",
        metavar="NAME",
        help="仅下载指定图标（可选：%s）" % ", ".join(ICON_SOURCES),
    )
    args = parser.parse_args()

    targets = ICON_SOURCES
    if args.only:
        targets = {k: ICON_SOURCES[k] for k in args.only if k in ICON_SOURCES}
        unknown = set(args.only) - set(ICON_SOURCES)
        if unknown:
            print(f"忽略未知图标: {', '.join(unknown)}")
        if not targets:
            print("没有可下载的图标。")
            return 1

    ICON_DIR.mkdir(parents=True, exist_ok=True)
    print(f"图标输出目录: {ICON_DIR}\n")

    success, failed = 0, []
    for name, urls in targets.items():
        if fetch_icon(name, urls, force=args.force):
            success += 1
        else:
            failed.append(name)
        print()

    print("=" * 48)
    print(f"完成: {success}/{len(targets)} 成功")
    if failed:
        print(f"失败: {', '.join(failed)}")
        print("提示: 可手动访问官网下载，或执行 --only <name> 单独重试。")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
