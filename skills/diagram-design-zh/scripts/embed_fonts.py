#!/usr/bin/env python3
"""把字体子集内嵌进图表 HTML——单文件离线完全体。

从文件的实际用字生成 woff2 子集，以 data: URI 写进 <style> 的标记区：
复制到任何机器、断网、无 CJK 字体的环境都按同一字体渲染，且仍是单文件。

    python3 <技能目录>/scripts/embed_fonts.py 图.html [更多.html]
    python3 <技能目录>/scripts/embed_fonts.py 图.html --strip   # 移除内嵌块
    python3 <技能目录>/scripts/embed_fonts.py 图.html --font 字体.woff2
                                                    # 用户字体文件直接子集内嵌，
                                                    # 不装系统；可多次给多个文件

- 重跑幂等：标记区整体替换；改了文案后重跑一次即重建子集。
- --strip 纯文本操作，零依赖；内嵌需要 fonttools + brotli
  （pip install fonttools brotli）。装不上就 --strip，走系统三栈。
- 子集基线 GB2312 全集（见 fonts/）；源文出现集外字时该字按字符回退
  系统字体（PingFang SC / 雅黑 / 宋体），不破版。
- serif 只嵌 400（本设计系统 serif 仅用于标题与旁注，无 600 用例）。
- 换字体只换栈首位（--font-sans / --font-serif）：栈首仍是出厂首位
  （MiSans / Noto Serif SC）时嵌包内思源，行为与默认完全一致；栈首是
  其他字体时按下述顺序解析——--font 给的文件 → 系统字体目录（读字体
  name 表对名，family 名以字体内部 name 表为准）。系统自带字体（苹方/
  雅黑/宋体等）与解析不到的字体不内嵌，打 ⚠ 提示并回落思源——
  跨机渲染回落栈内思源，不破版。
"""

from __future__ import annotations

import argparse
import base64
import io
import logging
import re
import sys
from pathlib import Path

FONTS_DIR = Path(__file__).resolve().parent.parent / "fonts"
FACE_FILES = {
    ("Noto Sans SC", 400): "noto-sans-sc-400.woff2",
    ("Noto Sans SC", 500): "noto-sans-sc-500.woff2",
    ("Noto Sans SC", 600): "noto-sans-sc-600.woff2",
    ("Noto Serif SC", 400): "noto-serif-sc-400.woff2",
}
# 出厂三栈的栈首（偏离才触发字体发现）；MiSans / Sarasa 是环境增强字体，永远嵌思源兜底
FACTORY_HEADS = {"sans": "MiSans", "serif": "Noto Serif SC"}
# 出厂栈的系统兜底与知名系统字体：点名它们 = 点名系统字体，不随图分发
SYSTEM_FAMILIES = {
    "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "Songti SC", "SimSun",
    "SimHei", "DengXian", "Microsoft JhengHei", "PingFang TC", "PingFang HK",
    "Hiragino Sans", "Heiti SC", "Heiti TC", "system-ui", "sans-serif", "serif",
    "monospace", "ui-monospace", "SF Mono", "Menlo", "Sarasa Mono SC",
    ".SF NS", "System Font", "Segoe UI",
}
SYS_FONT_DIRS = [
    Path.home() / "Library" / "Fonts",          # macOS 用户字体
    Path("/Library/Fonts"),                     # macOS 共享
    Path.home() / ".local" / "share" / "fonts", # Linux 用户
    Path("/usr/local/share/fonts"),
    Path("/usr/share/fonts"),
]
if sys.platform == "win32":
    SYS_FONT_DIRS.append(Path("C:/Windows/Fonts"))
FONT_SUFFIXES = {".ttf", ".otf", ".woff", ".woff2"}
BEGIN = "/*fonts:begin 字体子集——embed_fonts.py 生成，重跑幂等，--strip 可移除*/"
END = "/*fonts:end*/"
# 兼容思源时代旧标记，保证存量块的幂等替换/移除仍生效
EMBED_RE = re.compile(
    r"[ \t]*/\*fonts:begin (?:字体子集|思源字体子集)——embed_fonts\.py 生成，"
    r"重跑幂等，--strip 可移除\*/.*?" + re.escape(END) + r"[ \t]*\n",
    re.DOTALL,
)
CJK_RE = re.compile(
    r"[\u3000-\u303f\uff00-\uffef\u4e00-\u9fff"
    r"→←↑↓↔⇒⇄✓×●○◆◇■□▲△▼▽★☆①②③④⑤⑥⑦⑧⑨⑩·—–…]"
)
BASE_ASCII = set(chr(c) for c in range(0x20, 0x7F))
BASE_PUNCT = set("，。、；：？！“”‘’（）《》【】—…·　")


def load_subsetter():
    try:
        from fontTools import subset
    except ImportError:
        return None
    return subset


def renderable_source(source: str) -> str:
    """去掉样式 / 脚本 / 注释 / 旧内嵌块——剩下的是可能渲染成字的内容。"""
    src = EMBED_RE.sub("", source)
    src = re.sub(r"<style\b.*?</style>", "", src, flags=re.DOTALL | re.IGNORECASE)
    src = re.sub(r"<script\b.*?</script>", "", src, flags=re.DOTALL | re.IGNORECASE)
    src = re.sub(r"<!--.*?-->", "", src, flags=re.DOTALL)
    return src


def charset_of(text: str) -> str:
    chars = BASE_ASCII | BASE_PUNCT | set(CJK_RE.findall(text))
    return "".join(sorted(chars))


def serif_charset(source: str) -> str | None:
    """serif 只用于 h1（var(--font-serif)）与内联 'Noto Serif SC' 的 <text>——只嵌这些字形。"""
    body = renderable_source(source)
    chunks = re.findall(r"<text\b[^>]*Serif[^>]*>(.*?)</text>", body, re.DOTALL)
    if "var(--font-serif)" in source:
        chunks += re.findall(r"<h1\b[^>]*>(.*?)</h1>", body, re.DOTALL | re.IGNORECASE)
    text = "".join(re.sub(r"<[^>]+>", "", chunk) for chunk in chunks)
    chars = {c for c in text if ord(c) >= 0x20}
    if not chars:
        return None
    return "".join(sorted(chars | BASE_ASCII | BASE_PUNCT))


def plan_faces(source: str) -> dict[str, list[int]]:
    work = EMBED_RE.sub("", source)
    weights = [400] + [
        weight
        for weight in (500, 600)
        if re.search(rf"font-weight[\"']?\s*[:=]\s*[\"']?{weight}\b", work)
    ]
    return {"sans": weights}


def build_face(subset, font_path: Path, chars: str) -> str:
    options = subset.Options()
    options.flavor = "woff2"
    options.name_IDs = ["*"]
    options.name_languages = ["*"]
    options.layout_features = ["*"]
    font = subset.load_font(str(font_path), options)
    subsetter = subset.Subsetter(options)
    subsetter.populate(text=chars)
    subsetter.subset(font)
    buffer = io.BytesIO()
    subset.save_font(font, buffer, options)
    return base64.b64encode(buffer.getvalue()).decode("ascii")


def probe_font(path: Path) -> tuple[str, int]:
    """读字体内部 name 表 family 与 OS/2 字重——family 名以此为准，不以文件名猜。"""
    from fontTools.ttLib import TTFont

    font = TTFont(str(path), lazy=True)
    name = font["name"]
    family = name.getDebugName(16) or name.getDebugName(1)
    if not family:
        raise ValueError("name 表缺 family 名")
    weight = getattr(font.get("OS/2"), "usWeightClass", 400) or 400
    return family, weight


_SYSTEM_INDEX: dict[str, dict[int, Path]] | None = None


def system_index() -> dict[str, dict[int, Path]]:
    """一次性扫系统字体目录，建 {family: {字重: 文件}} 索引；ttc 合集跳过。"""
    global _SYSTEM_INDEX
    if _SYSTEM_INDEX is not None:
        return _SYSTEM_INDEX
    index: dict[str, dict[int, Path]] = {}
    for d in SYS_FONT_DIRS:
        if not d.is_dir():
            continue
        for f in sorted(d.iterdir()):
            if f.suffix.lower() not in FONT_SUFFIXES:
                continue
            try:
                family, weight = probe_font(f)
            except Exception:
                continue
            index.setdefault(family, {}).setdefault(weight, f)
    _SYSTEM_INDEX = index
    return index


STACK_RES = {
    role: re.compile(rf"--font-{role}\s*:\s*([^;}}]+);")
    for role in ("sans", "serif")
}


def stack_head(source: str, role: str) -> str | None:
    m = STACK_RES[role].search(source)
    if not m:
        return None
    first = m.group(1).split(",")[0].strip().strip("'\"")
    return first or None


def resolve_custom(
    head: str, explicit: list[Path], notices: list[str]
) -> dict[int, Path] | None:
    """解析栈首的自定义字体：--font 文件优先，其次系统目录；失败回落思源并 ⚠。"""
    probed: list[tuple[Path, str, int]] = []
    for p in explicit:
        try:
            family, weight = probe_font(p)
            probed.append((p, family, weight))
        except Exception as exc:
            notices.append(f"⚠ --font {p.name} 读取失败：{type(exc).__name__}")
    for p, family, weight in probed:
        if family == head:
            return {weight: p}
    if probed:
        p, family, weight = probed[0]
        notices.append(
            f"⚠ --font {p.name} 的 family 是 {family!r}，栈首 {head!r} 不会命中——栈首应写 {family!r}"
        )
        return {weight: p}
    found = system_index().get(head)
    if found:
        return dict(found)
    if head in SYSTEM_FAMILIES:
        notices.append(f"⚠ {head} 是系统字体，不随图分发——跨机回落思源")
    else:
        notices.append(f"⚠ {head} 未找到字体文件——本机已装则照常显示，发到别的机器回落思源")
    return None


def _emit_face(
    subset, faces: list[str], summary: list[str],
    family: str, weight: int, path: Path, chars: str,
) -> None:
    encoded = build_face(subset, path, chars)
    faces.append(
        f"    @font-face {{ font-family: '{family}'; font-style: normal; "
        f"font-weight: {weight}; font-display: swap; "
        f"src: url(data:font/woff2;base64,{encoded}) format('woff2'); }}"
    )
    summary.append(f"{family} {weight}（{len(encoded) * 3 // 4 // 1024} KB）")


def build_block(
    subset, source: str, explicit: list[Path]
) -> tuple[list[str], str, list[str]]:
    faces: list[str] = []
    summary: list[str] = []
    notices: list[str] = []
    sans_chars = charset_of(renderable_source(source))
    sans_plan = plan_faces(source)["sans"]
    ser_chars = serif_charset(source)

    # sans 位：栈首偏离出厂首位才做字体发现；解析失败回落思源
    head = stack_head(source, "sans")
    custom = (
        resolve_custom(head, explicit, notices)
        if head not in (None, FACTORY_HEADS["sans"])
        else None
    )
    if custom:
        weights = [w for w in sans_plan if w in custom]
        if not weights:  # 字体无 400/500/600 命名档：用最轻档顶 base（声明真实字重）
            weights = [min(custom)]
        for w in sorted(set(weights)):
            _emit_face(subset, faces, summary, head, w, custom[w], sans_chars)
    else:
        for (family, weight), filename in FACE_FILES.items():
            if family == "Noto Sans SC" and weight not in sans_plan:
                continue
            if family == "Noto Serif SC":
                continue  # serif 位独立处理，见下
            _emit_face(subset, faces, summary, family, weight, FONTS_DIR / filename, sans_chars)

    # serif 位：只嵌标题用字；自定义时取最接近 400 的档
    head = stack_head(source, "serif")
    custom = (
        resolve_custom(head, explicit, notices)
        if ser_chars and head not in (None, FACTORY_HEADS["serif"], "Noto Serif SC")
        else None
    )
    if ser_chars:
        if custom:
            w = min(custom, key=lambda x: abs(x - 400))
            _emit_face(subset, faces, summary, head, w, custom[w], ser_chars)
        else:
            _emit_face(
                subset, faces, summary, "Noto Serif SC", 400,
                FONTS_DIR / FACE_FILES[("Noto Serif SC", 400)], ser_chars,
            )

    if not faces:
        raise ValueError("没有可内嵌的字面——文件未使用本技能的字体栈")
    block_lines = [BEGIN, *faces, END]
    return block_lines, "、".join(summary), notices


def process(path: Path, subset, strip: bool, explicit: list[Path]) -> None:
    source = path.read_text(encoding="utf-8")
    if strip:
        updated = EMBED_RE.sub("", source)
        if updated == source:
            print(f"跳过 {path.name}：没有内嵌块")
            return
        path.write_text(updated, encoding="utf-8")
        print(f"已移除内嵌块 {path.name}")
        return
    block_lines, summary, notices = build_block(subset, source, explicit)
    updated = EMBED_RE.sub("", source)
    updated = re.sub(r"[ \t]*<link[^>]*fonts\.googleapis\.com[^>]*>\n?", "", updated)

    def inject(match: re.Match[str]) -> str:
        indent = match.group(1)
        return "\n".join(indent + line for line in block_lines) + "\n" + match.group(0)

    updated, count = re.subn(r"([ \t]*)</style>", inject, updated, count=1)
    if not count:
        raise ValueError(f"{path.name}：找不到 </style> 注入点")
    path.write_text(updated, encoding="utf-8")
    print(f"已内嵌 {path.name}：{summary}，文件 {path.stat().st_size // 1024} KB")
    for notice in notices:
        print(notice)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="+", type=Path)
    parser.add_argument("--strip", action="store_true", help="移除内嵌字体块（零依赖）")
    parser.add_argument(
        "--font", action="append", default=[], type=Path,
        metavar="字体文件",
        help="用户字体文件（ttf/otf/woff/woff2），直接子集内嵌不装系统；可多次",
    )
    args = parser.parse_args()

    subset = None
    if not args.strip:
        subset = load_subsetter()
        if subset is None:
            sys.stderr.write(
                "内嵌需要 fonttools + brotli：pip install fonttools brotli\n"
                "装不上就 --strip 走系统三栈（PingFang / 雅黑 / 宋体兜底）。\n"
            )
            return 2
        logging.getLogger("fontTools.subset").setLevel(logging.CRITICAL)

    failed = False
    for path in args.files:
        try:
            process(path, subset, args.strip, args.font)
        except (OSError, ValueError) as exc:
            failed = True
            print(f"FAIL {path.name}：{exc}", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
