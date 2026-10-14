#!/usr/bin/env python3
"""从已验证 HTML 导出 SVG/PNG；不改源文件。

python3 scripts/export.py 图.html --format png --scale 2
python3 scripts/export.py 图.html --format svg --powerpoint
PNG 需要 Playwright；可以 --browser-executable 指定已安装的 Chrome。
"""

from __future__ import annotations

import argparse
import html
from html.parser import HTMLParser
import math
from pathlib import Path
import re
import tempfile
from xml.etree import ElementTree as ET

from embed_fonts import EMBED_RE, load_subsetter, process
from self_check import verify
from html_tools import select_svg, svg_fragments


def first_svg(source: str, svg_id=None) -> str:
    return select_svg(source, svg_id).source


def svg_dimensions(svg: str) -> tuple[float, float]:
    match = re.search(r"\bviewBox\s*=\s*([\"\'])(.*?)\1", svg.split(">", 1)[0])
    values = (
        [float(n) for n in re.split(r"[\s,]+", match.group(2).strip())] if match else []
    )
    if (
        len(values) != 4
        or not all(math.isfinite(n) for n in values)
        or min(values[2:]) <= 0
    ):
        raise ValueError("SVG 缺有效 viewBox")
    return values[2], values[3]


def standalone_svg(svg: str, powerpoint=False) -> str:
    if not re.search(r"\bxmlns\s*=", svg.split(">", 1)[0]):
        svg = svg.replace("<svg", '<svg xmlns="http://www.w3.org/2000/svg"', 1)
    if "xlink:" in svg and "xmlns:xlink=" not in svg.split(">", 1)[0]:
        svg = svg.replace("<svg", '<svg xmlns:xlink="http://www.w3.org/1999/xlink"', 1)
    svg = re.sub(
        r"&([A-Za-z][A-Za-z0-9]+);",
        lambda m: (
            m.group(0)
            if m.group(1) in {"amp", "lt", "gt", "quot", "apos"}
            else html.unescape(m.group(0))
        ),
        svg,
    )
    if powerpoint:
        svg = re.sub(
            r'(?<![\w:-])(fill|stroke)="rgba\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d*\.?\d+)\s*\)"',
            lambda m: f'{m[1]}="#{int(m[2]):02x}{int(m[3]):02x}{int(m[4]):02x}" {m[1]}-opacity="{m[5]}"',
            svg,
        )
        svg = re.sub(r'(?<![\w:-])(fill|stroke)="transparent"', r'\1="none"', svg)
    ET.fromstring(svg)
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + svg + "\n"


def png_export(
    source: Path,
    target: Path,
    scale: float,
    browser_executable=None,
    transparent=False,
    whole_page=False,
    svg_id=None,
):
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise ValueError(
            "PNG 导出需要 Playwright 与浏览器；使用已有环境或先在隔离环境安装，源文件未修改"
        ) from exc
    original = source.read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory(prefix="diagram-export-") as directory:
        copy = Path(directory) / source.name
        copy.write_text(original, encoding="utf-8")
        if not EMBED_RE.search(original):
            subset = load_subsetter()
            if subset is None:
                raise ValueError(
                    "源图未内嵌字体，且当前环境缺 fonttools/brotli；先完成字体内嵌"
                )
            process(copy, subset, False, [])
        width, height = svg_dimensions(first_svg(original, svg_id))
        with sync_playwright() as p:
            options = (
                {"executable_path": browser_executable} if browser_executable else {}
            )
            browser = p.chromium.launch(**options)
            try:
                page = browser.new_page(
                    viewport={
                        "width": max(1440, math.ceil(width) + 128),
                        "height": max(1100, math.ceil(height) + 128),
                    },
                    device_scale_factor=scale,
                )
                page.goto(copy.as_uri() + "?motion=static", wait_until="load")
                page.evaluate("document.fonts.ready")
                if page.locator("[data-motion-root]").count():
                    if (
                        page.locator("[data-motion-root]").first.get_attribute(
                            "data-frame"
                        )
                        != "static"
                    ):
                        raise ValueError("动效文件未进入静态帧")
                if transparent:
                    page.add_style_tag(
                        content="html,body { background: transparent !important; }"
                    )
                if whole_page:
                    page.screenshot(
                        path=str(target), full_page=True, omit_background=transparent
                    )
                else:
                    chosen = select_svg(original, svg_id)
                    # DOM position uses the same selected source root, excluding decorations.
                    index = next(
                        i
                        for i, f in enumerate(svg_fragments(original))
                        if f.start == chosen.start
                    )
                    page.locator("svg").evaluate_all(
                        '(svgs,index)=>{const roots=svgs.filter(s=>!s.parentElement.closest("svg"));roots[index].setAttribute("data-export-target","");}',
                        index,
                    )
                    element = page.locator("svg[data-export-target]")
                    element.evaluate(
                        """(svg,size)=>{
                        document.documentElement.style.backgroundColor=getComputedStyle(document.body).backgroundColor;
                        document.body.style.visibility='hidden';
                        for (const [key,value] of Object.entries({width:size[0]+'px',height:size[1]+'px',
                            'min-width':'0','max-width':'none',position:'fixed',left:'0',top:'0',margin:'0',visibility:'visible'})) {
                            svg.style.setProperty(key,value,'important');
                        }
                    }""",
                        [width, height],
                    )
                    element.screenshot(path=str(target), omit_background=transparent)
            finally:
                browser.close()
    if source.read_text(encoding="utf-8") != original:
        raise ValueError("导出期间源文件被其他进程改变")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--format", choices=["svg", "png"], required=True)
    parser.add_argument("-o", "--output", type=Path)
    parser.add_argument("--scale", type=float, default=2)
    parser.add_argument("--style-guide", type=Path)
    parser.add_argument("--browser-executable")
    parser.add_argument("--transparent", action="store_true")
    parser.add_argument(
        "--page", action="store_true", help="PNG 导出整页包装，而非只导 SVG"
    )
    parser.add_argument("--svg-id", help="多主图页面的顶层 SVG id")
    parser.add_argument("--powerpoint", action="store_true")
    args = parser.parse_args()
    if not math.isfinite(args.scale) or not 0 < args.scale <= 4:
        parser.error("scale 须为有限正数且不超过 4")
    target = args.output or args.source.with_suffix("." + args.format)
    if target.resolve() == args.source.resolve():
        parser.error("导出目标不能覆盖源 HTML")
    if args.page and args.format != "png":
        parser.error("--page 只支持 PNG")
    try:
        errors, warnings = verify(args.source, args.style_guide)
        if errors:
            raise ValueError("源图未过质量门：" + "；".join(errors))
        for warning in warnings:
            print("⚠ " + warning)
        if args.format == "svg":
            target.write_text(
                standalone_svg(
                    first_svg(args.source.read_text(encoding="utf-8"), args.svg_id),
                    args.powerpoint,
                ),
                encoding="utf-8",
            )
        else:
            png_export(
                args.source,
                target,
                args.scale,
                args.browser_executable,
                args.transparent,
                args.page,
                args.svg_id,
            )
        print(f"已导出 {target}")
        return 0
    except Exception as exc:
        print(f"FAIL：{exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
