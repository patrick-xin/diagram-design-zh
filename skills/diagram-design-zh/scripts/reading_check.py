"""测量目标窗口下的 SVG 汉字显示字号与页面溢出；可输出保持尺度的滚动版本。"""

import argparse
import json
import math
from pathlib import Path
import sys
from html_tools import SourceParser, select_svg
from self_check import verify

READING_CSS = """\n/*reading:begin*/
.frame, [data-motion-root] { box-sizing: border-box; min-width: 0; }
.diagram-scroll { box-sizing: border-box; min-width: 0; max-width: 100%; overflow-x: auto; padding: READING_PADDING; }
.diagram-scroll > svg { min-width: READING_WIDTHpx; }
/*reading:end*/\n"""


def measure_page(page, svg_id=None):
    """测量已加载的图，可复用于隔离测试上下文。"""
    selector = 'svg[role="img"]:not([aria-hidden="true"])'
    page.evaluate("document.fonts.ready")
    if svg_id:
        locator = page.locator("[id=" + json.dumps(svg_id) + "]")
    else:
        locator = page.locator(selector).filter(has=page.locator(":scope > title"))
    return locator.evaluate("""svg=>{
        const texts=Array.from(svg.querySelectorAll('text')).filter(e=>/[\\u4e00-\\u9fff]/.test(e.textContent));
        const sizes=texts.map(e=>{const m=e.getScreenCTM();return parseFloat(getComputedStyle(e).fontSize)*Math.hypot(m.a,m.b)});
        const root=svg.getBoundingClientRect();
        const elements=Array.from(svg.querySelectorAll('text,path,line,rect,circle,ellipse,polygon,polyline,image,use,foreignObject'))
            .filter(e=>!e.closest('defs,clipPath,mask,marker,pattern,symbol') && getComputedStyle(e).visibility!=='hidden')
            .map(e=>({element:e,rect:e.getBoundingClientRect()})).filter(({rect:r})=>r.width||r.height);
        const bounds={top:root.top,right:root.right,bottom:root.bottom,left:root.left};
        for(const {rect:r} of elements){bounds.top=Math.min(bounds.top,r.top);bounds.right=Math.max(bounds.right,r.right);bounds.bottom=Math.max(bounds.bottom,r.bottom);bounds.left=Math.min(bounds.left,r.left);}
        const bleed=[root.top-bounds.top,bounds.right-root.right,bounds.bottom-root.bottom,root.left-bounds.left].map(n=>n/root.width);
        const scroll=svg.closest('.diagram-scroll');
        const clipped=[];
        if(scroll){
            const box=scroll.getBoundingClientRect(),left=box.left+scroll.clientLeft,top=box.top+scroll.clientTop;
            for(const {element:e,rect:r} of elements){
                // Horizontal content may be off screen but must remain reachable by scrolling.
                const sides=[];
                if(r.left+scroll.scrollLeft<left-.5)sides.push('left');
                if(r.right+scroll.scrollLeft>left+scroll.scrollWidth+.5)sides.push('right');
                if(r.top<top-.5)sides.push('top');
                if(r.bottom>top+scroll.clientHeight+.5)sides.push('bottom');
                if(sides.length)clipped.push({tag:e.tagName,text:e.textContent,sides});
            }
        }
        return {viewport:innerWidth,svgWidth:root.width,documentWidth:document.documentElement.scrollWidth,minCjkScreenPx:sizes.length?Math.min(...sizes):null,svgBleedRatio:bleed,clippedElements:clipped};
    }""")


def measure(path, width, height, browser=None, svg_id=None):
    from playwright.sync_api import sync_playwright

    select_svg(path.read_text(), svg_id)
    with sync_playwright() as p:
        engine = p.chromium.launch(**({"executable_path": browser} if browser else {}))
        try:
            page = engine.new_page(viewport={"width": width, "height": height})
            page.goto(path.resolve().as_uri() + "?motion=static")
            return measure_page(page, svg_id)
        finally:
            engine.close()


def prepare(source, min_width, svg_id=None, bleed=None):
    fragment = select_svg(source, svg_id)
    import re

    # Scroll containers clip SVG overflow on both axes. Reserve measured overhang
    # outside the unchanged SVG, at its minimum width and at larger display sizes.
    padding = (
        "16px"
        if bleed is None
        else " ".join(
            f"max({math.ceil(ratio * min_width) + 2}px, calc({ratio * 100:.6f}% + 2px))"
            for ratio in bleed
        )
    )
    css = READING_CSS.replace("READING_WIDTH", str(min_width)).replace(
        "READING_PADDING", padding
    )
    if "/*reading:begin*/" in source:
        return re.sub(
            r"/\*reading:begin\*/.*?/\*reading:end\*/", css.strip(), source, flags=re.S
        )
    wrapped = '<div class="diagram-scroll">' + fragment.source + "</div>"
    source = source[: fragment.start] + wrapped + source[fragment.end :]
    # HTML permits an omitted </head>; insert before <body> in that case.
    head_end = re.search(r"</head\s*>", source, re.I)
    if head_end:
        insertion = head_end.start()
    else:
        insertion = next(
            (
                start
                for start, raw in SourceParser(source).tags
                if re.match(r"<body\b", raw, re.I)
            ),
            None,
        )
        if insertion is None:
            raise ValueError("阅读包装需要 head 结束标签或 body 开始标签")
    return source[:insertion] + "<style>" + css + "</style>\n" + source[insertion:]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("source", type=Path)
    p.add_argument("--width", type=int, default=360)
    p.add_argument("--height", type=int, default=800)
    p.add_argument("--browser-executable")
    p.add_argument("--svg-id")
    p.add_argument("-o", "--output", type=Path)
    p.add_argument("--style-guide", type=Path)
    a = p.parse_args()
    try:
        errors, _ = verify(a.source, a.style_guide)
        if errors:
            raise ValueError("源文件未过质量门：" + "；".join(errors))
        before = measure(a.source, a.width, a.height, a.browser_executable, a.svg_id)
        if a.output:
            if a.source.resolve() == a.output.resolve():
                raise ValueError("不能覆盖源文件")
            fragment = select_svg(a.source.read_text(), a.svg_id)
            from export import svg_dimensions

            width, _ = svg_dimensions(fragment.source)
            factor = 10 / before["minCjkScreenPx"] if before["minCjkScreenPx"] else 1
            needed = math.ceil(max(width, before["svgWidth"] * factor) / 4) * 4
            a.output.write_text(
                prepare(a.source.read_text(), needed, a.svg_id, before["svgBleedRatio"])
            )
            from reskin import restem

            a.output.write_text(
                restem(a.output.read_text(), a.source.stem, a.output.stem)
            )
            errors, _ = verify(a.output, a.style_guide)
            if errors:
                raise ValueError("阅读版本未过质量门：" + "；".join(errors))
            after = measure(a.output, a.width, a.height, a.browser_executable, a.svg_id)
        else:
            after = before
        print(
            json.dumps({"before": before, "after": after}, ensure_ascii=False, indent=2)
        )
        if after["minCjkScreenPx"] is not None and after["minCjkScreenPx"] < 9.99:
            return 1
        if after["clippedElements"]:
            return 1
        return int(after["documentWidth"] > after["viewport"] + 1)
    except (ValueError, OSError, ImportError) as exc:
        print("FAIL：" + str(exc))
        return 1


if __name__ == "__main__":
    sys.exit(main())
