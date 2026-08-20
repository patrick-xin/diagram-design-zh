#!/usr/bin/env python3
"""把思源字体子集内嵌进图表 HTML——单文件离线完全体。

从文件的实际用字生成 woff2 子集，以 data: URI 写进 <style> 的标记区：
复制到任何机器、断网、无 CJK 字体的环境都按思源渲染，且仍是单文件。

    python3 <技能目录>/scripts/embed_fonts.py 图.html [更多.html]
    python3 <技能目录>/scripts/embed_fonts.py 图.html --strip   # 移除内嵌块

- 重跑幂等：标记区整体替换；改了文案后重跑一次即重建子集。
- --strip 纯文本操作，零依赖；内嵌需要 fonttools + brotli
  （pip install fonttools brotli）。装不上就 --strip，走系统三栈。
- 子集基线 GB2312 全集（见 fonts/）；源文出现集外字时该字按字符回退
  系统字体（PingFang SC / 雅黑 / 宋体），不破版。
- serif 只嵌 400（本设计系统 serif 仅用于标题与旁注，无 600 用例）。
"""

from __future__ import annotations

import argparse
import base64
import io
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
BEGIN = "/*fonts:begin 思源字体子集——embed_fonts.py 生成，重跑幂等，--strip 可移除*/"
END = "/*fonts:end*/"
EMBED_RE = re.compile(
    r"[ \t]*" + re.escape(BEGIN) + r".*?" + re.escape(END) + r"[ \t]*\n",
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


def build_block(subset, source: str) -> tuple[str, str]:
    faces: list[str] = []
    summary: list[str] = []
    sans_chars = charset_of(renderable_source(source))
    for (family, weight), filename in FACE_FILES.items():
        if family == "Noto Sans SC" and weight not in plan_faces(source)["sans"]:
            continue
        if family == "Noto Serif SC":
            chars = serif_charset(source)
            if chars is None:
                continue
        else:
            chars = sans_chars
        encoded = build_face(subset, FONTS_DIR / filename, chars)
        faces.append(
            f"    @font-face {{ font-family: '{family}'; font-style: normal; "
            f"font-weight: {weight}; font-display: swap; "
            f"src: url(data:font/woff2;base64,{encoded}) format('woff2'); }}"
        )
        summary.append(f"{family} {weight}（{len(encoded) * 3 // 4 // 1024} KB）")
    if not faces:
        raise ValueError("没有可内嵌的字面——文件未使用本技能的字体栈")
    block_lines = [BEGIN, *faces, END]
    return block_lines, "、".join(summary)


def process(path: Path, subset, strip: bool) -> None:
    source = path.read_text(encoding="utf-8")
    if strip:
        updated = EMBED_RE.sub("", source)
        if updated == source:
            print(f"跳过 {path.name}：没有内嵌块")
            return
        path.write_text(updated, encoding="utf-8")
        print(f"已移除内嵌块 {path.name}")
        return
    block_lines, summary = build_block(subset, source)
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="+", type=Path)
    parser.add_argument("--strip", action="store_true", help="移除内嵌字体块（零依赖）")
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

    failed = False
    for path in args.files:
        try:
            process(path, subset, args.strip)
        except (OSError, ValueError) as exc:
            failed = True
            print(f"FAIL {path.name}：{exc}", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
