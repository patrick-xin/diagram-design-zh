#!/usr/bin/env python3
"""自检生成的图表 HTML——零第三方依赖，随技能分发。

装好技能的 agent 用它验证自己的产出：

    python3 <技能目录>/scripts/self_check.py my-diagram.html

检查分六层：
  安全层   单文件契约：无任何远程引用（字体走 embed_fonts.py 内嵌子集
           或系统三栈）、无可执行属性、无 iframe/embed/object；脚本只允许
           一个——与 assets/template-motion.html 逐字节一致的动效控制器。
  契约层   无障碍 SVG：role=img、title 为首子元素、title/desc 非空、
           id 必须等于 {文件名slug}-title / -desc、aria-labelledby 顺序正确。
  动效层   结构化动效契约：单一 data-motion-root、模式合法、步数 0–8、
           条目 ≤12、步号连续且每步 ≤2 条、语义条目须有 aria-label、
           装饰条目须 aria-hidden、受控模式须控件齐全 + 播报区 + noscript。
  颜色层   值级出处闭集（复用 reskin.py 的槽位识别，两套机器同一标准）：
           hex 与 rgba 基色必须来自语义槽位表或语义色族，不许自造颜色；
           终端灰阶只在终端外壳文件里合法。
  排版层   中文硬规则：lang=zh-CN、三字体栈齐全且含系统兜底、
           禁用纯西文字体（Geist/Inter/Roboto 等）、含汉字文本 ≥10px、
           中英混排空格（警告级）；角色值——页面 eyebrow 字号 12px
           （拉丁 eyebrow 走 mono 7–8px）、h1 下限 1.5rem（style-guide
           排版角色表 / 字号下限）。
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

# 颜色层与换肤机器同目录分发；直接跑脚本时脚本目录本就在 sys.path[0]，
# 显式补一次是为了 self_check 被当作模块导入时也能找到 reskin。
sys.path.insert(0, str(Path(__file__).resolve().parent))
import reskin  # noqa: E402——同目录模块，槽位闭集与值级识别的唯一实现

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
EYEBROW_BLOCK_RE = re.compile(r"(?:^|[^\w-])(?:header-)?eyebrow\s*\{([^}]*)\}")
H1_BLOCK_RE = re.compile(r"(?:^|[^\w.#-])h1\s*\{([^}]*)\}")


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
        self.gallery_index = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.casefold()
        normalized_attrs = [(key.casefold(), value or "") for key, value in attrs]
        data = {key: value for key, value in normalized_attrs}
        if tag == "html" and not self.html_lang:
            self.html_lang = data.get("lang", "")
        if tag in {"html", "body"} and "data-gallery-index" in data:
            # 画廊目录页自报——iframe 只作本目录示例的索引缩略（画廊非交付物，
            # 本身不是单文件图表）；src 仍走远程引用检查 + 文件级存在性检查。
            self.gallery_index = True
        if tag in {"base", "embed", "object", "iframe"}:
            if not (tag == "iframe" and self.gallery_index):
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


def css_px(value: str) -> float | None:
    """px/rem 字面量折算成 px；clamp 等函数串返回 None（调用方另取最小档）。"""
    m = re.fullmatch(r"([\d.]+)\s*(px|rem)", value.strip())
    if not m:
        return None
    return float(m.group(1)) * (16 if m.group(2) == "rem" else 1)


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
    if parser.gallery_index:
        return  # 画廊目录页：允许内联主题切换脚本（非交付物，与 iframe 豁免同理）
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
    if "data-gallery-index" in source:
        return  # 画廊目录页：内联脚本不是动效控制器，勿按动效契约校验
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


def check_colors(source: str, errors: list[str]) -> None:
    """颜色出处闭集：值级识别复用 reskin.translate——质量门与换肤机器
    同一套槽位表，不存在两套标准。换肤产物按 doctype 后的 reskin 来源
    注释把目标皮肤表的值并进闭集（出处=那张表）；标记指向的表不在
    skins/ 里则直接拦——自带表请拷进 scripts/skins/（gate 顺带把关）。
    终端灰阶只在终端外壳文件里合法（外壳特征：class="terminal" 或
    CSS 变量注释 terminal-page）。"""
    extra = None
    marker = re.search(r"<!--\s*reskin:([\w.-]+)", source)
    if marker:
        skin_path = reskin.SKINS_DIR / f"{marker.group(1)}.json"
        if not skin_path.is_file():
            errors.append(
                f"reskin 标记自报皮肤 {marker.group(1)!r} 不在 scripts/skins/ 里——"
                "自带表先拷进去（--list 会顺带过 gate）再交付"
            )
        else:
            extra = reskin.load_skin(skin_path)["colors"]
    _text, _replaced, kept = reskin.translate(source, {}, extra=extra)
    unknown = sorted(k for k in kept if k.startswith("未知:"))
    if unknown:
        errors.append(
            f"颜色出处不明 {sum(kept[k] for k in unknown)} 处 {unknown}——"
            "色值必须来自语义槽位表（scripts/skins/default.json，与 style-guide 对账）"
            "或语义色族，不许自造颜色"
        )
    terminal = sorted(k.split(":", 1)[1] for k in kept if k.startswith("terminal:"))
    is_terminal = 'class="terminal"' in source or "terminal-page" in source
    if terminal and not is_terminal:
        errors.append(
            f"终端灰阶 {terminal} 用在非终端文件——终端色系只属于终端外壳"
            "（references/primitive-terminal.md）"
        )


def verify(path: Path) -> tuple[list[str], list[str]]:
    source = path.read_text(encoding="utf-8")
    parser = parsed_document(source)
    errors: list[str] = []
    warnings: list[str] = []

    errors.extend(parser.unsafe)
    for tag, rel, value in parser.references:
        finding = reference_error(tag, rel, value)
        if tag == "a" and parser.gallery_index:
            # 画廊目录页：<a> 外链（GitHub 仓库等）是正当导航，非交付物远程依赖
            finding = None
        if tag == "a" and value.startswith("https://github.com/patrick-xin/diagram-design-zh"):
            # 页头导航条的仓库链接（与「← 类型画廊」同层），非内容引用
            finding = None
        if finding:
            errors.append(finding)
        if tag == "iframe" and parser.gallery_index:
            # 画廊缩略的本地索引——目标必须真实存在，防链接腐烂
            target = value.split("#")[0].split("?")[0]
            if target and not (path.parent / target).is_file():
                errors.append(f"画廊 iframe 指向不存在的本地文件：{value}")

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
    if not checkable and "data-decorative-gallery" not in source and "data-gallery-index" not in source:
        # 装饰性样本页（如 icons.html）自报 data-decorative-gallery、画廊目录页
        # （index.html）自报 data-gallery-index 时豁免——无障碍契约本就要求装饰图
        # 用 aria-hidden 而非命名，画廊缩略的命名由各示例自身负责；图表产出页
        # 不许带任何一种标记。
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

    # 排版角色值（style-guide 排版角色表 / 字号下限）：页面 eyebrow 一律 12px，
    # 唯一例外 eyebrow-tech（mono 栈）7–8px；h1 下限 1.5rem，clamp() 取其最小档。
    # 只认块内声明了 font-size 的规则——覆盖性小规则（如卡片内 .eyebrow 只改间距）
    # 不声明字号，自然跳过。
    for m in EYEBROW_BLOCK_RE.finditer(css):
        block = m.group(1)
        fs = re.search(r"font-size\s*:\s*([^;]+)", block)
        if not fs:
            continue
        ff = re.search(r"font-family\s*:\s*([^;]+)", block)
        size = css_px(fs.group(1))
        if size is None:
            continue
        if ff and "mono" in ff.group(1).lower():
            if not 7 <= size <= 8:
                errors.append(f"eyebrow-tech 字号应为 mono 7–8px；当前 {fs.group(1).strip()}")
        elif abs(size - 12) > 0.01:
            errors.append(f"页面 eyebrow 字号应为 12px（0.75rem）；当前 {fs.group(1).strip()}")
    for m in H1_BLOCK_RE.finditer(css):
        fs = re.search(r"font-size\s*:\s*([^;]+)", m.group(1))
        if not fs:
            continue
        value = fs.group(1).strip()
        cm = re.match(r"clamp\(\s*([\d.]+)(px|rem)\s*,", value)
        size = css_px(f"{cm.group(1)}{cm.group(2)}") if cm else css_px(value)
        if size is not None and size < 24:
            errors.append(f"h1 字号下限 1.5rem（24px）；当前 {value}")

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
    # 画廊目录页：多张缩略共一文件，跨图坐标比较全是误报——几何完整性由各源
    # example 的 self_check 保证，画廊层只管引用与结构。
    if "data-gallery-index" in source:
        structural_rects = []
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

    # 图例基线一致性（警告级）：图例横线（最底部贯通全宽的发丝横线）下方 30px 内的
    # 全部文字（「图例」标签、图例项、口径注）应共用同一条基线——分用「样本中心 /
    # 文字基线」两套参照会肉眼可见地错落（实测 agent 漂移 4px）。
    legend_line_y: float | None = None
    through_lines: list[float] = []
    for m in re.finditer(r"<line\s+[^>]*>", source):
        tag = m.group(0)
        coords = {a: re.search(rf'{a}="([-\d.]+)"', tag) for a in ("x1", "y1", "x2", "y2")}
        if not all(coords.values()):
            continue
        x1, y1, x2, y2 = (float(c.group(1)) for c in coords.values())
        if abs(y1 - y2) <= 0.5 and x1 <= 20 and x2 >= 900:
            through_lines.append(y1)
    if "data-gallery-index" in source:  # 画廊页：跨图图例线互不相干，见堆叠检查处注释
        through_lines = []
    if through_lines:
        legend_line_y = max(through_lines)  # 最底部的贯通横线是图例线（道框/分区线更靠上）
        baselines: dict[float, str] = {}
        for t in re.finditer(r"<text\s+[^>]*>", source):
            ty = re.search(r'\by="([-\d.]+)"', t.group(0))
            tfs = re.search(r'font-size="([\d.]+)"', t.group(0))
            if not ty:
                continue
            if tfs and float(tfs.group(1)) < 10:
                continue  # 图例样本芯片内的码字（7px）与项文字本就异层，不参与同线判定
            y = float(ty.group(1))
            if legend_line_y < y <= legend_line_y + 30:
                snippet = re.search(r">\s*([^<\s][^<]{0,11})", source[t.end():t.end() + 80])
                baselines.setdefault(y, (snippet.group(1).strip() if snippet else "?"))
        if len(baselines) > 1:
            detail = "、".join(f"y={y:g}（{txt}…）" for y, txt in sorted(baselines.items()))
            warnings.append(f"图例行文字基线不一致：{detail}——同行图例文字应共用一条基线")

    # 焦点信号簇计数（警告级）：accent 系的「面与线」语义簇 ≤2——焦点盒
    # （rect ≥40×20、fill 为 accent 且 α≥0.08）+ 焦点线（line stroke accent、
    # 长 ≥20px）分簇累计；焦点淡染面积（α<0.08）、文字、圆点、图例样本不占预算。
    # 「都重要 = 都不重要」——状态条 / 分组标题再拿 accent 就是第三簇。
    ACCENT_RE = r"(?:#1a4dd9|#7d98ff|rgba\((?:26,\s*77,\s*217|125,\s*152,\s*255),)"
    focal_boxes = 0
    for m in re.finditer(r"<rect\s+[^>]*>", source):
        tag = m.group(0)
        w = re.search(r'width="([\d.]+)"', tag)
        h = re.search(r'height="([\d.]+)"', tag)
        fill = re.search(r'fill="([^"]+)"', tag)
        ry = re.search(r'\by="([-\d.]+)"', tag)
        if not (w and h and fill and ry):
            continue
        if float(w.group(1)) < 40 or float(h.group(1)) < 20:
            continue
        if not re.match(ACCENT_RE, fill.group(1)):
            continue
        alpha_m = re.search(r",\s*0\.(\d+)\)", fill.group(1))
        if alpha_m and float(f"0.{alpha_m.group(1)}") < 0.08:
            continue
        if legend_line_y is not None and float(ry.group(1)) > legend_line_y:
            continue
        focal_boxes += 1
    focal_lines_count = 0
    for m in re.finditer(r"<line\s+[^>]*>", source):
        tag = m.group(0)
        stroke = re.search(r'stroke="([^"]+)"', tag)
        xy = {a: re.search(rf'{a}="([-\d.]+)"', tag) for a in ("x1", "y1", "x2", "y2")}
        if not (stroke and all(xy.values())):
            continue
        if not re.match(ACCENT_RE, stroke.group(1)):
            continue
        x1, y1, x2, y2 = (float(c.group(1)) for c in xy.values())
        length = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
        if length < 20:
            continue
        if legend_line_y is not None and max(y1, y2) > legend_line_y:
            continue
        focal_lines_count += 1
    # 焦点盒 >2 必警；无焦点盒的纯线焦点图（折线 / 雷达），焦点线 >2 警。
    # 焦点盒的关联线不计数——「任一端是焦点的连线默认 accent」是正当模式。
    if "data-step=" in source:
        pass  # 分步动效图豁免：accent 按步骤轮换是叙事强调，预算归 animation.md 管
    elif focal_boxes > 2 or (focal_boxes == 0 and focal_lines_count > 2):
        warnings.append(
            f"焦点信号簇过多（焦点盒 {focal_boxes} + 焦点线 {focal_lines_count}）"
            "——accent 至多落在 1–2 处，再多「都重要 = 都不重要」"
        )

    # 连线端点贴边（警告级）：line/path 端点落进节点盒或菱形内部（距各边 >2px）
    # = 箭头埋进盒子或起点悬空在盒内。家族规矩是端点贴盒边（type-it-state §3.3）；
    # 容器（分区/道槽）边缘是合法附着面，图例贯通线不参与。
    # 支撑面 = rect（≥40×20，白垫板与节点同几何不碍事）与 polygon（判定菱形等，
    # 按外接框算——marker/微型箭头的 polygon 因尺寸不足自动出局）；
    # <g transform="translate()"> 内的坐标按累计偏移换算。
    surfaces: list[tuple[float, float, float, float]] = []
    endpoint_specs: list[tuple[float, float, str, str]] = []

    def _apply(tx: float, ty: float, nums: list[float]) -> list[float]:
        return [nums[0] + tx, nums[1] + ty]

    translate_stack: list[tuple[float, float]] = []
    current_vb: tuple[float, float] | None = None
    for m in re.finditer(r"<g\b[^>]*>|</g>|<svg\b[^>]*>|<rect\s[^>]*>|<polygon\s[^>]*>|<line\s[^>]*>|<path\s[^>]*>", source):
        tag = m.group(0)
        if tag.startswith("<svg"):
            vbm = re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', tag)
            current_vb = (float(vbm.group(1)), float(vbm.group(2))) if vbm else None
            continue
        if tag.startswith("<g"):
            t = re.search(r"translate\(([-\d.]+)[ ,]+([-\d.]+)\)", tag)
            translate_stack.append((float(t.group(1)), float(t.group(2))) if t else (0.0, 0.0))
            continue
        if tag == "</g>":
            if translate_stack:
                translate_stack.pop()
            continue
        tx = sum(o[0] for o in translate_stack)
        ty = sum(o[1] for o in translate_stack)
        if tag.startswith("<rect") or tag.startswith("<polygon"):
            coords = {a: re.search(rf'{a}="([-\d.]+)"', tag) for a in ("x", "y", "width", "height")}
            if tag.startswith("<rect") and all(coords.values()):
                x, y = float(coords["x"].group(1)) + tx, float(coords["y"].group(1)) + ty
                w, h = float(coords["width"].group(1)), float(coords["height"].group(1))
            elif tag.startswith("<polygon"):
                pts = [float(v) for v in re.findall(r"-?\d+\.?\d*", re.search(r'points="([^"]+)"', tag).group(1))]
                xs, ys = pts[0::2], pts[1::2]
                x, y, w, h = min(xs) + tx, min(ys) + ty, max(xs) - min(xs), max(ys) - min(ys)
            else:
                continue
            if w >= 40 and h >= 20:
                surfaces.append((x, y, w, h, current_vb))
        elif tag.startswith("<line"):
            coords = {a: re.search(rf'{a}="([-\d.]+)"', tag) for a in ("x1", "y1", "x2", "y2")}
            if not all(coords.values()):
                continue
            x1, y1, x2, y2 = (float(c.group(1)) for c in coords.values())
            if abs(y1 - y2) < 0.5 and abs(x2 - x1) > 500 and "0.10" in tag:
                continue  # 图例贯通线
            endpoint_specs.append((x1 + tx, y1 + ty, "起", tag, current_vb))
            endpoint_specs.append((x2 + tx, y2 + ty, "终", tag, current_vb))
        elif tag.startswith("<path"):
            d = re.search(r' d="(M [\d.]+,[\d.]+ [^"]+)"', tag)
            if not d:
                continue
            nums = re.findall(r"[\d.]+", d.group(1))
            cur = [float(nums[0]) + tx, float(nums[1]) + ty]
            endpoint_specs.append((cur[0], cur[1], "path起", tag, current_vb))
            for cmd, argstr in re.findall(r"([MHVLQ]) ([\d., ]+)", d.group(1)):
                args = [float(v) for v in re.findall(r"-?\d+\.?\d*", argstr)]
                if cmd == "M":
                    cur = [args[0] + tx, args[1] + ty]
                elif cmd == "H":
                    cur[0] = args[-1] + tx
                elif cmd == "V":
                    cur[1] = args[-1] + ty
                else:  # L / Q：终点取最后两个数
                    cur = [args[-2] + tx, args[-1] + ty]
            endpoint_specs.append((cur[0], cur[1], "path终", tag, current_vb))

    if "data-gallery-index" in source:  # 画廊页：跨图端点/容器互不相干，见堆叠检查处注释
        endpoint_specs = []
    for (px, py, kind, tag_src, _vb) in endpoint_specs:
        holders = [
            (x, y, w, h) for (x, y, w, h, _b) in surfaces
            if x - 1 <= px <= x + w + 1 and y - 1 <= py <= y + h + 1
        ]
        if not holders:
            continue
        if any(
            abs(px - x) <= 2 or abs(px - x - w) <= 2 or abs(py - y) <= 2 or abs(py - y - h) <= 2
            for (x, y, w, h) in holders
        ):
            continue
        # hub-and-spoke 豁免：≥3 根辐条从同一盒内部同一点辐射（radar 轴辐 / 全景 hub）
        # ——辐条压在 hub 底下是设计，不是埋箭头。
        cluster = sum(
            1 for (qx, qy, _k, _t, _vb) in endpoint_specs
            if abs(qx - px) <= 8 and abs(qy - py) <= 8
        )
        if cluster >= 3:
            continue
        if any(not (w >= 400 or h >= 150) for (x, y, w, h) in holders):
            warnings.append(f"连线{kind}端点埋进节点盒/菱形内 ({px:g},{py:g})——端点应贴边线 | {tag_src[:70]}")
        else:
            warnings.append(f"连线{kind}端点悬在容器内空白处 ({px:g},{py:g})——应贴容器边或目标盒边 | {tag_src[:70]}")

    # 内容越界（警告级）：有效坐标（含组平移）超出 viewBox——动效图曾因此溢出
    # 画布 80 单位而 EXEMPT 漏检（paved 右列 1080>1000 一案），此为回归闸。
    for (x, y, w, h, vb) in surfaces:
        if vb and (x + w > vb[0] + 2 or y + h > vb[1] + 2):
            warnings.append(f"元素 ({x:g},{y:g},{w:g},{h:g}) 越出画布 {vb[0]:g}×{vb[1]:g}")
    for (px, py, kind, tag_src, vb) in endpoint_specs:
        if vb and (px > vb[0] + 2 or py > vb[1] + 2):
            warnings.append(f"连线{kind}端点 ({px:g},{py:g}) 越出画布 {vb[0]:g}×{vb[1]:g} | {tag_src[:60]}")

    # 动效层（存在动效标记或脚本时才检查）
    check_scripts(parser, errors)
    check_motion(parser, source, errors)

    # 颜色出处层（值级闭集，与 reskin 换肤机器同源）
    check_colors(source, errors)

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
