"""HTML/SVG 的结构定位与颜色值走查；不执行页面，不改文字或标识符。"""

from __future__ import annotations
from dataclasses import dataclass
from html.parser import HTMLParser
import re


@dataclass
class SvgFragment:
    start: int
    end: int
    attrs: dict[str, str]
    source: str


class SourceParser(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=False)
        self.source = source
        self.offsets = []
        total = 0
        for line in source.splitlines(keepends=True):
            self.offsets.append(total)
            total += len(line)
        self.tags = []
        self.styles = []
        self.svgs = []
        self.depth = 0
        self.root = None
        self.style_start = None
        self.feed(source)
        self.close()
        if self.depth:
            raise ValueError("SVG 标签未闭合")

    def position(self):
        row, col = self.getpos()
        return self.offsets[row - 1] + col

    def handle_starttag(self, tag, attrs):
        raw = self.get_starttag_text()
        start = self.position()
        self.tags.append((start, raw))
        if tag == "style":
            self.style_start = start + len(raw)
        if tag == "svg":
            if not self.depth:
                self.root = (start, dict(attrs))
            self.depth += 1

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag == "svg":
            self.close_svg(self.position() + len(self.get_starttag_text()))

    def close_svg(self, end):
        if not self.depth:
            raise ValueError("SVG 结束标签没有对应开始标签")
        self.depth -= 1
        if not self.depth:
            start, attrs = self.root
            self.svgs.append(
                SvgFragment(
                    start,
                    end,
                    {k: v or "" for k, v in attrs.items()},
                    self.source[start:end],
                )
            )

    def handle_endtag(self, tag):
        if tag == "style" and self.style_start is not None:
            self.styles.append(
                (self.style_start, self.source[self.style_start : self.position()])
            )
            self.style_start = None
        if tag == "svg":
            self.close_svg(self.source.index(">", self.position()) + 1)


def svg_fragments(source):
    return SourceParser(source).svgs


def select_svg(source, svg_id=None):
    candidates = [
        s
        for s in svg_fragments(source)
        if s.attrs.get("aria-hidden", "").lower() != "true"
        and s.attrs.get("role") == "img"
    ]
    if svg_id is not None:
        candidates = [s for s in candidates if s.attrs.get("id") == svg_id]
    if len(candidates) != 1:
        raise ValueError(
            f"需要唯一的顶层可访问主图，发现 {len(candidates)} 个；多图请用 --svg-id 指定"
        )
    return candidates[0]


COLOR_RE = re.compile(
    r"#[0-9a-fA-F]{6}\b|rgba?\(\s*\d{1,3}\s*,\s*\d{1,3}\s*,\s*\d{1,3}\s*(?:,\s*[0-9.]+\s*)?\)"
)
ATTR_RE = re.compile(
    r"""(?<![\w:-])([\w:-]+)\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s>]+))"""
)
COLOR_ATTRS = {"fill", "stroke", "color", "stop-color", "flood-color", "lighting-color"}
COLOR_PROPERTIES = COLOR_ATTRS | {
    "background",
    "background-color",
    "box-shadow",
    "text-shadow",
    "outline",
    "outline-color",
    "border",
    "border-color",
    "border-top",
    "border-right",
    "border-bottom",
    "border-left",
    "border-top-color",
    "border-right-color",
    "border-bottom-color",
    "border-left-color",
}


def css_values(css):
    """定位声明值；注释、引号、url/data 的分号不作为声明边界。"""
    i = 0
    begin = 0
    quote = None
    depth = 0
    while i < len(css):
        c = css[i]
        if quote:
            if c == "\\":
                i += 2
                continue
            if c == quote:
                quote = None
        elif css.startswith("/*", i):
            end = css.find("*/", i + 2)
            i = len(css) if end < 0 else end + 2
            # A comment at a declaration boundary has no semantic content.
            if not css[begin:i].strip() or css[begin:i].lstrip().startswith("/*"):
                begin = i
            continue
        elif c in "\"'":
            quote = c
        elif c == "(":
            depth += 1
        elif c == ")":
            depth = max(0, depth - 1)
        elif c in ";{}" and not depth:
            piece = css[begin:i]
            m = re.match(r"\s*([\w-]+)\s*:\s*", piece)
            if m:
                prop = m[1].lower()
                if prop in COLOR_PROPERTIES or (
                    prop.startswith("--") and not prop.startswith("--font")
                ):
                    yield begin + m.end(), i
            begin = i + 1
        i += 1
    piece = css[begin:]
    m = re.match(r"\s*([\w-]+)\s*:\s*", piece)
    if m and (
        m[1].lower() in COLOR_PROPERTIES
        or (m[1].startswith("--") and not m[1].startswith("--font"))
    ):
        yield begin + m.end(), len(css)


def colors_in_value(value):
    protected = [
        (m.start(), m.end())
        for m in re.finditer(
            r"""url\([^)]*\)|"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|/\*.*?\*/""",
            value,
            re.S | re.I,
        )
    ]
    for m in COLOR_RE.finditer(value):
        if not any(a <= m.start() < b for a, b in protected):
            yield m.start(), m.end(), m.group()


def color_occurrences(source):
    parser = SourceParser(source)
    regions = []
    for start, raw in parser.tags:
        for m in ATTR_RE.finditer(raw):
            name = m[1].lower()
            group = next(g for g in (2, 3, 4) if m[g] is not None)
            pos = start + m.start(group)
            value = m[group]
            if name == "style":
                regions.extend((pos + a, pos + b) for a, b in css_values(value))
            elif name in COLOR_ATTRS:
                regions.append((pos, pos + len(value)))
    for pos, css in parser.styles:
        regions.extend((pos + a, pos + b) for a, b in css_values(css))
    for a, b in sorted(regions):
        for x, y, raw in colors_in_value(source[a:b]):
            yield a + x, a + y, raw


def map_colors(source, mapper):
    edits = [(a, b, mapper(raw)) for a, b, raw in color_occurrences(source)]
    for a, b, value in reversed(edits):
        source = source[:a] + value + source[b:]
    return source
