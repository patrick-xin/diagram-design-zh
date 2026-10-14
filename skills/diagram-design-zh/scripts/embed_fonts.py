#!/usr/bin/env python3
"""按实际文本内嵌字体，并把 SVG 字面字体栈同步到 :root。

    python3 scripts/embed_fonts.py 图.html [更多.html] [--font 字体文件 ...]
    python3 scripts/embed_fonts.py 图.html --strip

字体文件直接子集化，不安装到系统；支持 ttf/otf/woff/woff2/ttc/otc。
显式文件按内部 family 匹配，其次递归发现用户/共享字体目录。
保留包内思源回退；找不到字体或缺字时打印 ⚠，不承诺系统回退的像素一致。
重跑替换同一标记块；--strip 只移除标记块，不更改字体栈。
内嵌需要 fonttools + brotli；--strip 无第三方依赖。
"""
from __future__ import annotations

import argparse
import base64
from dataclasses import dataclass
import html
from html.parser import HTMLParser
import io
import json
import logging
import os
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
FACTORY_HEADS = {"sans": "MiSans", "serif": "Noto Serif SC", "mono": "Sarasa Mono SC"}
SYSTEM_FAMILIES = {
    "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "Songti SC", "SimSun",
    "SimHei", "DengXian", "Microsoft JhengHei", "PingFang TC", "PingFang HK",
    "Hiragino Sans", "Heiti SC", "Heiti TC", "system-ui", "sans-serif", "serif",
    "monospace", "ui-monospace", "SF Mono", "Menlo", ".SF NS", "System Font", "Segoe UI",
}
SYS_FONT_DIRS = [
    Path.home() / "Library/Fonts", Path("/Library/Fonts"),
    Path.home() / ".local/share/fonts", Path.home() / ".fonts",
    Path("/usr/local/share/fonts"), Path("/usr/share/fonts"),
]
if sys.platform == "win32":
    SYS_FONT_DIRS += [Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts",
                      Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "Microsoft/Windows/Fonts"]
FONT_SUFFIXES = {".ttf", ".otf", ".woff", ".woff2", ".ttc", ".otc"}
BEGIN = "/*fonts:begin 字体子集——embed_fonts.py 生成，重跑幂等，--strip 可移除*/"
END = "/*fonts:end*/"
EMBED_RE = re.compile(
    r"[ \t]*/\*fonts:begin (?:字体子集|思源字体子集)——embed_fonts\.py 生成，"
    r"重跑幂等，--strip 可移除\*/.*?" + re.escape(END) + r"[ \t]*\n?", re.DOTALL,
)
STACK_RES = {r: re.compile(rf"(?<![\w-])--font-{r}\s*:\s*([^;}}]+);") for r in FACTORY_HEADS}
FAMILY_ATTR_RE = re.compile(r"(?<![\w:-])font-family\s*=\s*([\"'])(.*?)\1", re.S)
BASE_ASCII = set(chr(c) for c in range(0x20, 0x7F))
BASE_PUNCT = set("，。、；：？！“”‘’（）《》【】—…·　")


def load_subsetter():
    try:
        from fontTools import subset
        import brotli  # noqa: F401
        return subset
    except ImportError:
        return None


def families(value: str) -> list[str]:
    """拆字体栈；引号内的逗号保留在 family 中。"""
    parts, current = [], []
    quote, escaped = None, False
    for char in html.unescape(value):
        if escaped:
            current.append(char)
            escaped = False
        elif char == "\\":
            escaped = True
        elif quote:
            if char == quote:
                quote = None
            else:
                current.append(char)
        elif char in "'\"":
            quote = char
        elif char == ",":
            parts.append("".join(current).strip())
            current = []
        else:
            current.append(char)
    parts.append("".join(current).strip())
    return [part for part in parts if part]


def read_stacks(source: str) -> dict[str, str]:
    css = "\n".join(re.findall(r"<style\b[^>]*>(.*?)</style>", source, re.S | re.I))
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    return {role: m.group(1).strip() for role, pattern in STACK_RES.items() if (m := pattern.search(css))}


def stack_head(source: str, role: str) -> str | None:
    value = read_stacks(source).get(role, "")
    names = families(value)
    return names[0] if names else None


def ensure_embedded_fallbacks(source: str) -> str:
    """首位替换掉包内族时补回它；其他回退的相对顺序不变。"""
    generic = {"system-ui", "sans-serif", "serif", "monospace", "ui-monospace"}
    def update_style(style):
        css = style.group(0)
        for role, pattern in STACK_RES.items():
            fallback = "Noto Serif SC" if role == "serif" else "Noto Sans SC"
            def update_stack(match):
                names = families(match.group(1))
                if not names or fallback.casefold() in {n.casefold() for n in names}:
                    return match.group(0)
                names.insert(1, fallback)
                values = [n if n in generic else "'"+n.replace("\\", "\\\\").replace("'", "\\'")+"'" for n in names]
                return match.group(0).replace(match.group(1), ", ".join(values), 1)
            css = pattern.sub(update_stack, css)
        return css
    return re.sub(r"<style\b[^>]*>.*?</style>", update_style, source, flags=re.S | re.I)


def font_role(value: str, stacks: dict[str, str]) -> str | None:
    m = re.search(r"var\(--font-(sans|serif|mono)\)", value)
    if m:
        return m.group(1)
    names = {n.casefold() for n in families(value)}
    # 泛型与特定回退比共同的 Noto Sans 更能区分 mono/sans。
    for role in ("mono", "serif", "sans"):
        if role in names or (role == "mono" and "monospace" in names):
            return role
    for role, stack in stacks.items():
        if names == {n.casefold() for n in families(stack)}:
            return role
    if names & {"sarasa mono sc", "ui-monospace", "sf mono", "menlo"}:
        return "mono"
    if names & {"noto serif sc", "songti sc", "simsun"}:
        return "serif"
    if names & {"misans", "noto sans sc", "pingfang sc", "microsoft yahei", "system-ui"}:
        return "sans"
    return None


def sync_svg_stacks(source: str) -> str:
    """只改 SVG 的字体属性；坐标、id、aria 与颜色一字不动。"""
    stacks = read_stacks(source)
    offsets, total = [], 0
    for line in source.splitlines(keepends=True):
        offsets.append(total)
        total += len(line)
    replacements = []
    class Synchronizer(HTMLParser):
        depth = 0
        def handle_starttag(self, tag, attrs):
            if tag == "svg":
                self.depth += 1
            if not self.depth:
                return
            raw = self.get_starttag_text()
            def replace_attr(attr):
                role = font_role(attr.group(2), stacks)
                if role not in stacks:
                    return attr.group(0)
                return f'font-family="{html.escape(stacks[role], quote=True)}"'
            updated = FAMILY_ATTR_RE.sub(replace_attr, raw)
            if updated != raw:
                line, column = self.getpos()
                start = offsets[line-1]+column
                replacements.append((start, start+len(raw), updated))
        def handle_startendtag(self, tag, attrs):
            self.handle_starttag(tag, attrs)
            self.handle_endtag(tag)
        def handle_endtag(self, tag):
            if tag == "svg":
                self.depth -= 1
    Synchronizer().feed(source)
    for start, end, updated in reversed(replacements):
        source = source[:start]+updated+source[end:]
    return source


class TextCollector(HTMLParser):
    """采集可渲染文本、实体解码及字体角色；不把标签/属性名当作文字。"""
    VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
    def __init__(self, source: str):
        super().__init__(convert_charrefs=True)
        self.stacks = read_stacks(source)
        self.rules: dict[str, str] = {}
        for selectors, body in re.findall(r"([^{}]+)\{([^{}]*)\}", "\n".join(re.findall(r"<style\b[^>]*>(.*?)</style>", source, re.S | re.I))):
            m = re.search(r"font-family\s*:\s*([^;]+)", body)
            if m and (role := font_role(m.group(1), self.stacks)):
                for selector in selectors.split(","):
                    selector = selector.strip()
                    if re.fullmatch(r"[.#]?[\w-]+", selector):
                        self.rules[selector] = role
        self.stack: list[tuple[str, str, bool]] = []
        self.chars = {r: set() for r in FACTORY_HEADS}
        self.motion_chars: set[str] = set()
        self.feed(source)
        # 锁定控制器会把状态文案/条目名称写到播报区；只采字，不执行脚本。
        for body in re.findall(r"<script\b[^>]*\bdata-diagram-controls[^>]*>(.*?)</script>", source, re.S | re.I):
            self.motion_chars.update(c for c in body if ord(c) >= 128)
        if self.motion_chars:
            self.chars["sans"].update(self.motion_chars)
            self.chars["mono"].update(self.motion_chars)

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if "data-motion-item" in values:
            self.motion_chars.update(values.get("aria-label", ""))
        role = self.stack[-1][1] if self.stack else "sans"
        blocked = (self.stack[-1][2] if self.stack else False) or tag in {"head", "style", "script", "title", "desc"}
        for selector in [tag, *["."+c for c in values.get("class", "").split()], "#"+values.get("id", "")]:
            role = self.rules.get(selector, role)
        value = values.get("font-family", "")
        m = re.search(r"font-family\s*:\s*([^;]+)", values.get("style", ""))
        role = font_role(m.group(1) if m else value, self.stacks) or role
        if tag not in self.VOID:
            self.stack.append((tag, role, blocked))

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in self.VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        for i in range(len(self.stack)-1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]
                return

    def handle_data(self, data):
        if self.stack and not self.stack[-1][2]:
            self.chars[self.stack[-1][1]].update(c for c in data if ord(c) >= 0x20)


def charset_of(text: str) -> str:
    return "".join(sorted(BASE_ASCII | BASE_PUNCT | {c for c in html.unescape(text) if ord(c) >= 0x20}))


def renderable_source(source: str) -> str:
    return "".join(sorted(set().union(*TextCollector(source).chars.values())))


def serif_charset(source: str) -> str | None:
    chars = TextCollector(source).chars["serif"]
    return charset_of("".join(chars)) if chars else None


def plan_faces(source: str) -> dict[str, list[int]]:
    work = EMBED_RE.sub("", source)
    weights = [400] + [w for w in (500, 600) if re.search(rf"font-weight[\"']?\s*[:=]\s*[\"']?{w}\b", work)]
    return {role: weights if role != "serif" else [400] for role in FACTORY_HEADS}


@dataclass(frozen=True)
class FontFace:
    path: Path
    family: str
    weight: int
    index: int = -1
    weight_range: tuple[int, int] | None = None

    @property
    def descriptor(self) -> str:
        return " ".join(map(str, self.weight_range)) if self.weight_range else str(self.weight)


def probe_faces(path: Path) -> list[FontFace]:
    from fontTools.ttLib import TTFont, TTCollection
    faces = []
    collection = TTCollection(str(path), lazy=True) if path.suffix.lower() in {".ttc", ".otc"} else None
    fonts = collection.fonts if collection else [TTFont(str(path), lazy=True)]
    try:
        for i, font in enumerate(fonts):
            # 不拿斜体文件充正体，也不合成中文斜体。
            if (getattr(font.get("OS/2"), "fsSelection", 0) & 1) or (font["head"].macStyle & 2):
                continue
            family = font["name"].getDebugName(16) or font["name"].getDebugName(1)
            if not family:
                raise ValueError("name 表缺 family 名")
            weight = getattr(font.get("OS/2"), "usWeightClass", 400) or 400
            axis = next((a for a in font["fvar"].axes if a.axisTag == "wght"), None) if "fvar" in font else None
            wrange = (int(axis.minValue), int(axis.maxValue)) if axis else None
            faces.append(FontFace(path, family, weight, i if collection else -1, wrange))
    finally:
        if collection:
            collection.close()
        else:
            fonts[0].close()
    return faces


def probe_font(path: Path) -> tuple[str, int]:
    faces = probe_faces(path)
    if len(faces) != 1:
        raise ValueError("需要明确的单一正体 face；合集请用 probe_faces 逐项读取")
    return faces[0].family, faces[0].weight


_SYSTEM_INDEX: dict[str, list[FontFace]] | None = None


def system_index() -> dict[str, list[FontFace]]:
    global _SYSTEM_INDEX
    if _SYSTEM_INDEX is None:
        _SYSTEM_INDEX = {}
        for directory in SYS_FONT_DIRS:
            if not directory.is_dir():
                continue
            for path in sorted(directory.rglob("*")):
                if path.suffix.lower() not in FONT_SUFFIXES or not path.is_file():
                    continue
                try:
                    for face in probe_faces(path):
                        _SYSTEM_INDEX.setdefault(face.family.casefold(), []).append(face)
                except Exception:
                    continue
    return _SYSTEM_INDEX


def resolve_custom(head: str, explicit: list[FontFace], notices: list[str]) -> list[FontFace]:
    if head.casefold() in {f.casefold() for f in SYSTEM_FAMILIES}:
        notices.append(f"⚠ {head} 是系统字体，不随图分发——跨机回落思源")
        return []
    matches = [face for face in explicit if face.family.casefold() == head.casefold()]
    if matches:
        return matches
    if head.casefold() in {n.casefold() for n in [*FACTORY_HEADS.values(), "Noto Sans SC", "Noto Serif SC"]}:
        return []  # 默认路径不遍历本机字库。
    found = system_index().get(head.casefold(), [])
    if found:
        return found
    notices.append(f"⚠ {head} 未找到匹配的正体字体文件——跨机回落思源")
    return []


def build_face(subset, font_path: Path | FontFace, chars: str) -> str:
    face = font_path if isinstance(font_path, FontFace) else FontFace(font_path, "", 400)
    options = subset.Options()
    options.flavor = "woff2"
    options.font_number = face.index
    options.name_IDs = ["*"]
    options.name_languages = ["*"]
    options.layout_features = ["*"]
    font = subset.load_font(str(face.path), options)
    try:
        subsetter = subset.Subsetter(options)
        subsetter.populate(text=chars)
        subsetter.subset(font)
        buffer = io.BytesIO()
        subset.save_font(font, buffer, options)
        return base64.b64encode(buffer.getvalue()).decode("ascii")
    finally:
        font.close()


def build_block(subset, source: str, explicit: list[Path]) -> tuple[list[str], str, list[str]]:
    notices, faces, summary = [], [], []
    candidates = []
    for path in explicit:
        try:
            candidates.extend(probe_faces(path))
        except Exception as exc:
            notices.append(f"⚠ --font {path.name} 读取失败：{type(exc).__name__}")
    collector = TextCollector(source)
    plan = plan_faces(source)
    emitted = set()
    active_heads = {head.casefold() for role, chars in collector.chars.items()
                    if chars and (head := stack_head(source, role))}
    for path in explicit:
        file_faces = [face for face in candidates if face.path == path]
        if file_faces and not any(face.family.casefold() in active_heads for face in file_faces):
            notices.append(f"⚠ --font {path.name} 未被任何在用栈首采用；请先按内部 family 修改目标栈")

    def emit(family, face, chars):
        key = (family, face.path, face.index)
        if key in emitted:
            return
        emitted.add(key)
        encoded = build_face(subset, face, charset_of("".join(chars)))
        safe_family = "".join(f"\\{ord(c):x} " if c == "<" or ord(c) < 32 else c for c in family.replace("\\", "\\\\").replace("'", "\\'"))
        faces.append(f"    @font-face {{ font-family: '{safe_family}'; font-style: normal; font-weight: {face.descriptor}; font-display: swap; src: url(data:font/woff2;base64,{encoded}) format('woff2'); }}")
        summary.append(f"{family} {face.descriptor}（{len(encoded) * 3 // 4 // 1024} KB）")

    for role, chars in collector.chars.items():
        if not chars:
            continue
        head = stack_head(source, role)
        if head:
            custom = resolve_custom(head, candidates, notices)
            selected = set()
            for weight in plan[role]:
                if custom:
                    def distance(face):
                        lo, hi = face.weight_range or (face.weight, face.weight)
                        return max(lo-weight, weight-hi, 0)
                    selected.add(min(custom, key=distance))
            for face in sorted(selected, key=lambda f: (f.weight, str(f.path), f.index)):
                # 同一字体用于多个角色时内嵌全部实际用字，避免后一角色缺字。
                all_chars = set().union(*(values for r, values in collector.chars.items() if stack_head(source, r) and stack_head(source, r).casefold() == head.casefold()))
                emit(head, face, all_chars)
                from fontTools.ttLib import TTFont
                with TTFont(str(face.path), fontNumber=face.index) as font:
                    missing = all_chars - {chr(c) for c in font.getBestCmap()}
                if missing:
                    notices.append(f"⚠ {head} 缺 {len(missing)} 个用字（{''.join(sorted(missing))[:16]}）——已保留内嵌思源回退，余字依赖系统")
    # 回退先声明、自定义后声明，避免同 family/weight 的包内 face 覆盖显式文件。
    custom_faces, custom_summary = faces[:], summary[:]
    faces.clear()
    summary.clear()
    # 自定义 face 之外始终携带包内回退；mono 的中文也纳入 sans 回退。
    sans_chars = set().union(*collector.chars.values())
    for weight in plan["sans"]:
        emit("Noto Sans SC", FontFace(FONTS_DIR/FACE_FILES[("Noto Sans SC",weight)], "Noto Sans SC",weight), sans_chars)
    if collector.chars["serif"]:
        emit("Noto Serif SC", FontFace(FONTS_DIR/FACE_FILES[("Noto Serif SC",400)], "Noto Serif SC",400), collector.chars["serif"])
    faces.extend(custom_faces)
    summary.extend(custom_summary)
    return [BEGIN, *faces, END], "、".join(summary), list(dict.fromkeys(notices))


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
    source = sync_svg_stacks(ensure_embedded_fallbacks(source))
    block, summary, notices = build_block(subset, source, explicit)
    updated = EMBED_RE.sub("", source)
    updated = re.sub(r"[ \t]*<link[^>]*fonts\.googleapis\.com[^>]*>\n?", "", updated)
    def inject(match):
        return "\n".join(match.group(1)+line for line in block)+"\n"+match.group(0)
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
    parser.add_argument("--strip", action="store_true", help="只移除内嵌块（零依赖）")
    parser.add_argument("--inspect-font", action="store_true", help="读取 files 中字体文件的 family、字重与合集索引，不修改任何文件")
    parser.add_argument("--font", action="append", default=[], type=Path, help="可重复；字体文件按内部 family 和字重匹配")
    args = parser.parse_args()
    if args.inspect_font:
        try:
            for path in args.files:
                print(json.dumps([{"file": str(face.path), "family": face.family,
                                   "weight": face.weight, "index": face.index,
                                   "weight_range": face.weight_range}
                                  for face in probe_faces(path)], ensure_ascii=False))
            return 0
        except Exception as exc:
            print(f"FAIL 字体读取：{exc}", file=sys.stderr)
            return 1
    subset = None if args.strip else load_subsetter()
    if not args.strip and subset is None:
        print("内嵌需要 fonttools + brotli；装不上就明说降级系统字体，--strip 可移除内嵌块。", file=sys.stderr)
        return 2
    logging.getLogger("fontTools.subset").setLevel(logging.CRITICAL)
    failed = False
    for path in args.files:
        try:
            process(path, subset, args.strip, args.font)
        except Exception as exc:
            failed = True
            print(f"FAIL {path.name}：{type(exc).__name__}：{exc}", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
