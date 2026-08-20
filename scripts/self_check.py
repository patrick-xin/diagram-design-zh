#!/usr/bin/env python3
"""自检生成的图表 HTML——零第三方依赖，随技能分发。

装好技能的 agent 用它验证自己的产出：

    python3 <技能目录>/scripts/self_check.py my-diagram.html

检查分五层：
  安全层   单文件契约：无任何远程引用（字体走 embed_fonts.py 内嵌子集
           或系统三栈）、无可执行属性、无 iframe/embed/object；脚本只允许
           一个——与 assets/template-motion.html 逐字节一致的动效控制器。
  契约层   无障碍 SVG：role=img、title 为首子元素、title/desc 非空、
           id 必须等于 {文件名slug}-title / -desc、aria-labelledby 顺序正确。
  动效层   结构化动效契约：单一 data-motion-root、模式合法、步数 0–8、
           条目 ≤12、步号连续且每步 ≤2 条、语义条目须有 aria-label、
           装饰条目须 aria-hidden、受控模式须控件齐全 + 播报区 + noscript。
  排版层   中文硬规则：lang=zh-CN、三字体栈齐全且含系统兜底、
           禁用纯西文字体（Geist/Inter/Roboto 等）、含汉字文本 ≥10px、
           中英混排空格（警告级）。
  几何层   4px 网格（rect，警告级）；堆叠条带左侧竖向方向标尺与
           堆叠上下缘的对齐关系（警告级）——网格合规不等于几何关系正确。

错误（-）导致退出码 1；警告（~）不拦截但须逐条人工确认。
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
MOTION_TEMPLATE = SKILL_DIR / "assets" / "template-motion.html"
MODES = {"none", "reveal", "step", "loop"}
ACTIONS = {"play", "pause", "replay", "prev", "next"}
ASCII_DECIMAL_RE = re.compile(r"^[0-9]+$")
REFERENCE_ATTRS = {"src", "href", "xlink:href", "poster", "srcset", "action", "formaction"}

CJK_RE = re.compile(r"[\u4e00-\u9fff]")
SPACING_RE = re.compile(r"([\u4e00-\u9fff])([A-Za-z0-9])|([A-Za-z0-9])([\u4e00-\u9fff])")
BANNED_FONTS = ["geist", "instrument serif", "jetbrains mono", "inter", "roboto"]
FONT_VALUE_RE = re.compile(r'font-family\s*[:=]\s*["\']?([^;"\'}]+)', re.IGNORECASE)
CSS_FONT_SIZE_RE = re.compile(r"font-size\s*:\s*([\d.]+)(px|rem)\b")


class DiagramParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.roots: list[dict[str, str]] = []
        self.items: list[dict[str, str]] = []
        self.actions: set[str] = set()
        self.controls = 0
        self.statuses: list[dict[str, str]] = []
        self.statuses_in_controls = 0
        self.scripts: list[dict[str, object]] = []
        self.styles: list[str] = []
        self.svgs: list[dict[str, object]] = []
        self.unsafe: list[str] = []
        self.references: list[tuple[str, str, str]] = []
        self.html_lang: str = ""
        self.svg_texts: list[tuple[str, str]] = []  # (font-size 属性值, 文本)
        self.text_nodes: list[str] = []
        self._svg_depth = 0
        self._current_svg: dict[str, object] | None = None
        self._capture: str | None = None
        self._current_script: dict[str, object] | None = None
        self._in_style = False
        self._element_stack: list[str] = []
        self._motion_root_depth: int | None = None
        self._controls_depth: int | None = None
        self._current_text_size: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.casefold()
        normalized_attrs = [(key.casefold(), value or "") for key, value in attrs]
        data = {key: value for key, value in normalized_attrs}
        if tag == "html" and not self.html_lang:
            self.html_lang = data.get("lang", "")
        if tag in {"base", "embed", "object", "iframe"}:
            self.unsafe.append(f"<{tag}> 不允许出现在图表文件里")
        for key, value in normalized_attrs:
            if key.startswith("on"):
                self.unsafe.append(f"可执行属性 {key} 出现在 <{tag}> 上")
            if key == "srcdoc":
                self.unsafe.append(f"<{tag}> 上的 srcdoc 属性")
            if key in REFERENCE_ATTRS and value:
                self.references.append((tag, data.get("rel", ""), value))
        if "data-motion-root" in data:
            self.roots.append(data)
            if self._motion_root_depth is None:
                self._motion_root_depth = len(self._element_stack)
        if self._motion_root_depth is not None:
            if "data-motion-item" in data:
                self.items.append(data)
            if "data-motion-action" in data:
                self.actions.add(data["data-motion-action"])
            if "data-motion-controls" in data:
                self.controls += 1
                if self._controls_depth is None:
                    self._controls_depth = len(self._element_stack)
            if "data-motion-status" in data:
                self.statuses.append(data)
                if self._controls_depth is not None:
                    self.statuses_in_controls += 1
        if tag == "script":
            self._current_script = {
                "attrs": data,
                "attr_names": [name for name, _value in normalized_attrs],
                "body": [],
                "closed": False,
            }
            self.scripts.append(self._current_script)
        if tag == "style":
            self._in_style = True
        self._element_stack.append(tag)
        if tag == "svg" and self._svg_depth == 0:
            self._svg_depth = 1
            self._current_svg = {"attrs": data, "first": None, "title": {}, "desc": {}}
            self.svgs.append(self._current_svg)
        elif self._svg_depth:
            self._svg_depth += 1
            assert self._current_svg is not None
            if self._svg_depth == 2:
                if self._current_svg["first"] is None:
                    self._current_svg["first"] = tag
                if tag in {"title", "desc"}:
                    self._current_svg[tag] = {"attrs": data, "text": ""}
                    self._capture = tag
            if tag == "text":
                self._current_text_size = data.get("font-size") or None

    def handle_endtag(self, tag: str) -> None:
        tag = tag.casefold()
        if tag == "script" and self._current_script is not None:
            self._current_script["closed"] = True
            self._current_script = None
        if tag == "style":
            self._in_style = False
        if tag == "text":
            self._current_text_size = None
        if self._svg_depth:
            if tag in {"title", "desc"}:
                self._capture = None
            self._svg_depth -= 1
            if self._svg_depth == 0:
                self._current_svg = None
        for index in range(len(self._element_stack) - 1, -1, -1):
            if self._element_stack[index] == tag:
                del self._element_stack[index:]
                break
        if (
            self._motion_root_depth is not None
            and len(self._element_stack) <= self._motion_root_depth
        ):
            self._motion_root_depth = None
        if (
            self._controls_depth is not None
            and len(self._element_stack) <= self._controls_depth
        ):
            self._controls_depth = None

    def handle_data(self, data: str) -> None:
        if self._current_script is not None:
            body = self._current_script["body"]
            assert isinstance(body, list)
            body.append(data)
            return
        if self._in_style:
            self.styles.append(data)
            return
        if self._svg_depth and self._current_text_size is not None:
            self.svg_texts.append((self._current_text_size, data))
        if self._capture and self._current_svg:
            node = self._current_svg[self._capture]
            assert isinstance(node, dict)
            node["text"] = str(node.get("text", "")) + data
        if data.strip():
            self.text_nodes.append(data)


def normalized_controller(body: str) -> str:
    return body.replace("\r\n", "\n").replace("\r", "\n").strip()


def parsed_document(source: str) -> DiagramParser:
    parser = DiagramParser()
    parser.feed(source)
    parser.close()
    return parser


def reference_error(tag: str, rel: str, value: str) -> str | None:
    stripped = value.strip()
    lowered = stripped.casefold()
    if not stripped or stripped.startswith("#"):
        return None
    if lowered.startswith("javascript:") or lowered.startswith("data:text/html"):
        return f"<{tag}> 上的可执行 URL：{stripped[:80]}"
    remote = lowered.startswith(("http://", "https://", "//"))
    if not remote:
        if lowered.startswith("data:") and not lowered.startswith("data:image/"):
            return f"<{tag}> 上的非图片 data URL：{stripped[:80]}"
        return None
    if tag == "link" and "stylesheet" in rel.casefold().split():
        return f"远程样式表不允许——字体内嵌（scripts/embed_fonts.py）或走系统三栈：{stripped[:80]}"
    return f"<{tag}> 上的远程引用：{stripped[:80]}"


def canonical_controller() -> str:
    if not MOTION_TEMPLATE.is_file():
        raise RuntimeError(
            f"找不到规范化控制器 {MOTION_TEMPLATE}；"
            "请在技能目录内的分发位置运行 self_check.py"
        )
    parser = parsed_document(MOTION_TEMPLATE.read_text(encoding="utf-8"))
    if len(parser.scripts) != 1 or not parser.scripts[0]["closed"]:
        raise RuntimeError("template-motion.html 必须恰好包含一个已闭合的控制器")
    body = parser.scripts[0]["body"]
    assert isinstance(body, list)
    return normalized_controller("".join(body))


def check_scripts(parser: DiagramParser, errors: list[str]) -> None:
    if not parser.scripts:
        return
    if len(parser.scripts) > 1:
        errors.append(f"至多允许一个脚本（动效控制器）；发现 {len(parser.scripts)} 个")
    for number, script in enumerate(parser.scripts, 1):
        attrs = script["attrs"]
        attr_names = script["attr_names"]
        body = script["body"]
        assert isinstance(attrs, dict) and isinstance(attr_names, list) and isinstance(body, list)
        if not script["closed"]:
            errors.append(f"脚本 {number} 必须有闭合标签")
        if attr_names != ["data-diagram-controls"] or attrs.get("data-diagram-controls") != "":
            errors.append(f"脚本 {number} 只能携带唯一的规范属性 data-diagram-controls")
            continue
        try:
            if normalized_controller("".join(body)) != canonical_controller():
                errors.append(f"脚本 {number} 必须与 template-motion.html 中的控制器逐字节一致")
        except RuntimeError as exc:
            errors.append(str(exc))


def check_motion(parser: DiagramParser, source: str, errors: list[str]) -> None:
    has_motion_markup = bool(parser.roots or parser.items or parser.scripts)
    if not has_motion_markup:
        return
    if len(parser.roots) != 1:
        errors.append(f"必须恰好一个 data-motion-root；发现 {len(parser.roots)} 个")
        return
    root = parser.roots[0]
    mode = root.get("data-motion-mode", "")
    if mode not in MODES:
        errors.append(f"data-motion-mode 必须是 {sorted(MODES)} 之一；当前是 {mode!r}")
    raw_count = root.get("data-step-count", "")
    if not ASCII_DECIMAL_RE.fullmatch(raw_count):
        count = -1
        errors.append("data-step-count 必须是 ASCII 十进制整数")
    else:
        count = int(raw_count)
    minimum_count = 0 if mode == "none" else 1
    if count < minimum_count or count > 8:
        errors.append(f"语义步数必须是 {minimum_count}..8；当前是 {count}")

    if len(parser.items) > 12:
        errors.append(f"动效条目预算 12；发现 {len(parser.items)} 个")
    semantic_steps: list[int] = []
    for index, item in enumerate(parser.items, 1):
        raw_step = item.get("data-step", "")
        if not ASCII_DECIMAL_RE.fullmatch(raw_step):
            errors.append(f"动效条目 {index} 的 data-step 不是 ASCII 十进制整数")
            continue
        step = int(raw_step)
        decorative = "data-motion-decorative" in item
        if not decorative:
            semantic_steps.append(step)
            if not item.get("aria-label", "").strip():
                errors.append(f"语义动效条目 {index} 需要非颜色的 aria-label")
        elif item.get("aria-hidden") != "true" or item.get("focusable") != "false":
            errors.append(f"装饰动效条目 {index} 需要 aria-hidden=true 与 focusable=false")
        inline = item.get("style", "").replace(" ", "").lower()
        if any(token in inline for token in ("display:none", "visibility:hidden", "opacity:0")):
            errors.append(f"动效条目 {index} 在源里被隐藏；静态回退画面必须可见")

    expected = set(range(1, count + 1)) if count > 0 else set()
    if set(semantic_steps) != expected:
        errors.append(f"语义步必须连续覆盖 1..{count}；发现 {sorted(set(semantic_steps))}")
    crowded = {step: n for step, n in Counter(semantic_steps).items() if n > 2}
    if crowded:
        errors.append(f"每步至多 2 个语义条目；超出的有 {crowded}")

    if mode in {"none", "loop"} and parser.scripts:
        errors.append(f"{mode} 模式必须无脚本")
    if mode in {"none", "loop"} and (parser.controls or parser.actions or parser.statuses):
        errors.append(f"{mode} 模式不得提供播放控件或播报区")
    controlled = mode == "step" or (mode == "reveal" and bool(parser.scripts))
    if controlled:
        if parser.controls != 1:
            errors.append(f"受控模式需要一个根内控件组；发现 {parser.controls} 个")
        missing = ACTIONS - parser.actions
        if missing:
            errors.append(f"受控模式缺少动作：{', '.join(sorted(missing))}")
        if not parser.statuses:
            errors.append("受控模式需要 data-motion-status 播报区")
        else:
            status = parser.statuses[0]
            if (
                status.get("role") != "status"
                or status.get("aria-live") != "polite"
                or status.get("aria-atomic") != "true"
            ):
                errors.append("动效播报区需要 role=status、aria-live=polite、aria-atomic=true")
            if parser.statuses_in_controls:
                errors.append("动效播报区必须在 data-motion-controls 之外")
        if not parser.scripts:
            errors.append("受控模式需要作用域控制脚本")

    style_source = "".join(parser.styles)
    if parser.scripts:
        if re.search(r"prefers-reduced-motion\s*:\s*reduce", style_source, re.IGNORECASE) is None:
            errors.append("缺少减弱动效 CSS 回退（prefers-reduced-motion）")
        if re.search(r"@media\s+print\b", style_source, re.IGNORECASE) is None:
            errors.append("缺少打印 CSS 回退（@media print）")
        if "<noscript" not in source.casefold():
            errors.append("动效文件需要 <noscript> 说明完整静态画面")


def verify(path: Path) -> tuple[list[str], list[str]]:
    source = path.read_text(encoding="utf-8")
    parser = parsed_document(source)
    errors: list[str] = []
    warnings: list[str] = []

    errors.extend(parser.unsafe)
    for tag, rel, value in parser.references:
        finding = reference_error(tag, rel, value)
        if finding:
            errors.append(finding)

    # CSS 内的远程引用（@import / 远程 url() / Google Fonts 域名）——属性扫描抓不到的路径
    css = "\n".join(parser.styles)
    if re.search(r"@import\b", css, re.IGNORECASE):
        errors.append("CSS @import 破坏单文件契约——样式全部内联")
    if re.search(r"url\(\s*['\"]?\s*(?:https?:)?//", css, re.IGNORECASE):
        errors.append("CSS 内远程 url() 引用——字体用 scripts/embed_fonts.py 内嵌，图片转 data: URI")
    if "fonts.googleapis.com" in source.casefold():
        errors.append("Google Fonts 外链残留——字体已自托管，跑 scripts/embed_fonts.py 或走系统三栈")

    # lang
    if parser.html_lang.casefold() != "zh-cn":
        errors.append(f'<html lang> 必须是 "zh-CN"；当前是 {parser.html_lang!r}')

    # 字体层
    stack_defs = {
        role: re.findall(rf"--font-{role}\s*:\s*([^;}}]+)", css)
        for role in ("sans", "serif", "mono")
    }
    for role, values in stack_defs.items():
        if not values:
            errors.append(f":root 缺少 --font-{role} 定义（三栈缺一）")
    if stack_defs["sans"]:
        sans = stack_defs["sans"][0]
        if "pingfang sc" not in sans.casefold() and "microsoft yahei" not in sans.casefold():
            errors.append("--font-sans 缺系统兜底（PingFang SC / Microsoft YaHei）")
    if stack_defs["mono"] and "sarasa mono sc" not in stack_defs["mono"][0].casefold() \
            and "ui-monospace" not in stack_defs["mono"][0].casefold():
        errors.append("--font-mono 缺等宽首选或兜底（Sarasa Mono SC / ui-monospace）")
    font_values = " ; ".join(m.group(1) for m in FONT_VALUE_RE.finditer(source))
    for name in BANNED_FONTS:
        if re.search(rf"\b{re.escape(name)}\b", font_values, re.IGNORECASE):
            errors.append(f"禁用的纯西文字体出现在 font-family：{name}")

    # SVG 契约（slug 绑定）
    checkable = [
        svg for svg in parser.svgs
        if isinstance(svg["attrs"], dict)
        and str(svg["attrs"].get("aria-hidden", "")).casefold() != "true"
    ]
    if not checkable and "data-decorative-gallery" not in source:
        # 装饰性样本页（如 icons.html）自报 data-decorative-gallery 时豁免——
        # 无障碍契约本就要求装饰图用 aria-hidden 而非命名；图表产出页不许带此标记。
        errors.append("至少需要一个可访问（非 aria-hidden）的 SVG")
    stem = path.stem
    for number, svg in enumerate(checkable, 1):
        attrs = svg["attrs"]
        assert isinstance(attrs, dict)
        title = svg["title"]
        desc = svg["desc"]
        assert isinstance(title, dict) and isinstance(desc, dict)
        if attrs.get("role") != "img":
            errors.append(f"svg {number} 需要 role=img")
        if svg["first"] != "title":
            errors.append(f"svg {number} 的首子元素必须是 <title>")
        if not str(title.get("text", "")).strip() or not str(desc.get("text", "")).strip():
            errors.append(f"svg {number} 的 title/desc 不能为空")
        title_id = title.get("attrs", {}).get("id", "")
        desc_id = desc.get("attrs", {}).get("id", "")
        expected = (f"{stem}-title", f"{stem}-desc")
        if (title_id, desc_id) != expected:
            errors.append(f"svg {number} 的 title/desc id 必须是 {expected}；当前是 ({title_id!r}, {desc_id!r})")
        if attrs.get("aria-labelledby", "").split() != [title_id, desc_id]:
            errors.append(f"svg {number} 的 aria-labelledby 必须依次指向 title、desc")

    # 含汉字文本 ≥10px（SVG font-size 属性可判定的部分）
    for size, text in parser.svg_texts:
        if not CJK_RE.search(text):
            continue
        try:
            px = float(str(size).strip().removesuffix("px"))
        except ValueError:
            continue
        if px < 10:
            errors.append(f"含汉字文本字号 {px}px < 10px：「{text.strip()[:20]}」")

    # CSS 里 <10px 的声明（选择器是否含中文脚本判不了，警告级）
    for m in CSS_FONT_SIZE_RE.finditer(css):
        value, unit = float(m.group(1)), m.group(2)
        px = value * 16 if unit == "rem" else value
        if px < 10:
            warnings.append(f"CSS font-size {m.group(0)} < 10px——若该选择器作用于含汉字文本即违规")

    # 中英混排空格（警告级）
    seen: set[str] = set()
    for node in parser.text_nodes:
        for m in SPACING_RE.finditer(node):
            snippet = node[max(0, m.start() - 4):m.end() + 4].strip()
            if snippet not in seen:
                seen.add(snippet)
                warnings.append(f"中英混排疑似缺空格：「…{snippet}…」")

    # 4px 网格（仅结构级 rect：节点/分区/hub/格子；遮罩与小型色板骑线属正常设计，
    # path 的 3 位小数交点是 loop 类型的合法精度）
    for m in re.finditer(r"<rect\s+[^>]*>", source):
        tag_src = m.group(0)
        w = re.search(r'width="([\d.]+)"', tag_src)
        h = re.search(r'height="([\d.]+)"', tag_src)
        if not (w and h and float(w.group(1)) >= 60 and float(h.group(1)) >= 40):
            continue
        for attr in ("x", "y", "width", "height"):
            am = re.search(rf'{attr}="([\d.]+)"', tag_src)
            if am and "." not in am.group(1) and float(am.group(1)) % 4:
                warnings.append(f"结构 rect 的 {attr}={am.group(1)} 不在 4px 网格上")
                break

    # 堆叠标尺对齐（警告级，窄域）：≥4 个同 x 同宽的结构 rect 视为条带堆叠，
    # 其左缘外侧近旁的竖线是方向标尺（type-layers.md），y 两端应与堆叠上下缘
    # 精确咬合（±4px）。网格检查只看单点坐标，这条看的是元素之间的几何关系。
    structural_rects = []
    for m in re.finditer(r"<rect\s+[^>]*>", source):
        tag_src = m.group(0)
        coords = {a: re.search(rf'{a}="([-\d.]+)"', tag_src) for a in ("x", "y", "width", "height")}
        if not all(coords.values()):
            continue
        x, y = float(coords["x"].group(1)), float(coords["y"].group(1))
        w, h = float(coords["width"].group(1)), float(coords["height"].group(1))
        if w >= 60 and h >= 40:
            structural_rects.append((x, y, w, h))
    bands: dict[tuple[float, float], list[tuple[float, float]]] = {}
    for rx, ry, rw, rh in structural_rects:
        bands.setdefault((rx, rw), []).append((ry, rh))
    stacks = [
        (rx, min(ry for ry, _ in ys), max(ry + rh for ry, rh in ys))
        for (rx, rw), ys in bands.items()
        if len(ys) >= 4
    ]
    if stacks:
        for m in re.finditer(r"<line\s+[^>]*>", source):
            tag_src = m.group(0)
            coords = {a: re.search(rf'{a}="([-\d.]+)"', tag_src) for a in ("x1", "y1", "x2", "y2")}
            if not all(coords.values()):
                continue
            x1, y1, x2, y2 = (float(c.group(1)) for c in coords.values())
            if abs(x1 - x2) > 0.5 or abs(y1 - y2) < 60:
                continue  # 只认足够长的竖线；短刻度、水平线不算标尺
            line_top, line_bottom = min(y1, y2), max(y1, y2)
            for stack_x, stack_top, stack_bottom in stacks:
                if not 4 <= stack_x - x1 <= 120:
                    continue  # 必须贴着堆叠左缘外侧（示例间距 40）
                overlap = min(line_bottom, stack_bottom) - max(line_top, stack_top)
                if overlap < 0.5 * (line_bottom - line_top):
                    continue  # y 向不落在堆叠范围内就不是在给这个堆叠当标尺
                if abs(line_top - stack_top) > 4 or abs(line_bottom - stack_bottom) > 4:
                    warnings.append(
                        f"堆叠左缘外侧竖线（x={x1:g}）的 y 范围 {line_top:g}–{line_bottom:g} 与堆叠上下缘 "
                        f"{stack_top:g}–{stack_bottom:g} 不咬合——方向标尺两端应精确对齐堆叠上下缘（±4px）"
                    )
                break

    # 动效层（存在动效标记或脚本时才检查）
    check_scripts(parser, errors)
    check_motion(parser, source, errors)

    return errors, warnings


def main() -> int:
    argument_parser = argparse.ArgumentParser(description=__doc__)
    argument_parser.add_argument("files", nargs="+", type=Path)
    args = argument_parser.parse_args()
    failed = False
    for path in args.files:
        try:
            errors, warnings = verify(path)
        except (OSError, UnicodeError) as exc:
            errors, warnings = [str(exc)], []
        if errors:
            failed = True
            print(f"FAIL {path}")
            for error in errors:
                print(f"  - {error}")
            for warning in warnings:
                print(f"  ~ {warning}")
        elif warnings:
            print(f"OK（有警告） {path}")
            for warning in warnings:
                print(f"  ~ {warning}")
        else:
            print(f"OK {path}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
