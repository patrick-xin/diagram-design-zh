#!/usr/bin/env python3
"""生成 assets/index.html 类型画廊（渐进增强：静态清单链接 + 少量 JS 切换预览）。

用法：python3 scripts/build_gallery.py
新增 / 删除示例后重跑本脚本即可，画廊清单与分组计数自动跟随（防手维护漏卡）。
重跑会覆盖 index.html——随后再跑一次 embed_fonts.py 补回内嵌字体（幂等）。

- 45 个内置类型按 README 四组排列；变体 / 导入 / 终端归「变体」组，分步动效（*-animated）归「动效」组。
- 卡片名取示例 eyebrow，副文字取 h1，悬停提示取 svg desc——全部从文件实时提取，零手维护。
- 三档（标准 / 深色 / 全档）与终端变体按文件存在性点亮。
- 高度按 viewBox 与容器几何估算（frame 内容宽 ≈ 1152px），白底页面余量无碍。
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent / "assets"

GROUPS = ["系统与流程", "计划与叙事", "数据图表", "数据平台", "变体", "动效"]

# 45 内置类型 → 分组序（README「图表类型」表同序；组内顺序即此表顺序）
TYPES45: dict[str, int] = {b: g for b, g in [
    ("architecture", 0), ("deployment", 0), ("flowchart", 0), ("sequence", 0),
    ("state", 0), ("er", 0), ("db-schema", 0), ("uml-class", 0),
    ("data-flow", 0), ("process", 0), ("swimlane", 0), ("org-chart", 0),
    ("tree", 0), ("mindmap", 0), ("dependency", 0), ("wardley", 0),
    ("nested", 0), ("layers", 0), ("fishbone", 0), ("kanban", 0),
    ("timeline", 1), ("journey", 1), ("story-map", 1), ("gantt", 1),
    ("quadrant", 1), ("loop", 1), ("pyramid", 1), ("venn", 1),
    ("bar", 2), ("waterfall", 2), ("line", 2), ("scatter", 2),
    ("dumbbell", 2), ("radar", 2), ("polar", 2), ("sankey", 2),
    ("treemap", 2), ("heatmap", 2), ("axonometric-plan", 2), ("exploded", 2),
    ("high-level", 3), ("medallion", 3), ("it-state", 3),
    ("dp-integration", 3), ("dp-security-matrix", 3),
]}

SUFFIXES = {"dark": "-dark", "full": "-full"}  # 终端变体独立成卡，不作档位


def parse_name(filename: str) -> tuple[str, str]:
    """example-<base><suffix>.html → (base, suffix)；suffix ∈ {'', 'dark', 'full', 'terminal'}."""
    stem = filename.removeprefix("example-").removesuffix(".html")
    for key, suf in SUFFIXES.items():
        if stem.endswith(suf):
            return stem[: -len(suf)], key
    if stem.endswith("-terminal"):
        return stem, "terminal"
    return stem, ""


def extract(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    eyebrow = re.search(r'class="eyebrow[^"]*"[^>]*>([^<]+)<', text)
    h1 = re.search(r"<h1>([^<]+)</h1>", text)
    desc = re.search(r"<desc id=\"[^\"]*\">([^<]+)</desc>", text)
    vb = re.search(r'viewBox="0 0 (\d+) (\d+)"', text)
    eyebrow_text = eyebrow.group(1).strip() if eyebrow else ""
    if not eyebrow_text:  # 无 eyebrow 的页型（如终端皮肤）退 <title> 末段
        t = re.search(r"<title>([^<]+)</title>", text)
        if t:
            eyebrow_text = t.group(1).strip().split(" · ")[-1]
    return {
        "eyebrow": eyebrow_text,
        "h1": h1.group(1).strip() if h1 else "",
        "desc": desc.group(1).strip() if desc else "",
        "vb_w": vb.group(1) if vb else "",
        "vb_h": vb.group(2) if vb else "",
    }


def doc_height(vb_h: int, full: bool) -> int:
    """iframe 文档高估算：svg 显示高 = vb_h × (1152/1000)；full 档另有卡片区与页脚。"""
    pad = 1050 if full else 230
    return int((vb_h * 1.152 + pad + 7) // 8 * 8)


def build() -> str:
    cards: dict[str, dict] = {}
    seen_files: list[str] = []
    for f in sorted(ASSETS.glob("example-*.html")):
        base, suffix = parse_name(f.name)
        seen_files.append(f.name)
        if suffix == "terminal":
            suffix = ""  # 终端外壳是独立示例卡，parse_name 已带全名
        card = cards.setdefault(base, {"std": "", "dark": "", "full": "", "terminal": ""})
        card[suffix or "std"] = f.name

    missing = [b for b in TYPES45 if not cards.get(b, {}).get("std")]
    if missing:
        sys.exit(f"缺少内置类型示例: {missing}")
    orphans = [b for b, c in cards.items() if not c["std"]]
    if orphans:
        sys.exit(f"存在无标准档的孤立文件: {orphans}")

    def order(item: tuple[str, dict]) -> tuple[int, str]:
        base, _ = item
        if base in TYPES45:
            return (TYPES45[base], "")
        if base.endswith("-animated"):
            return (5, base)
        return (4, base)

    grouped: list[list[tuple[str, dict]]] = [[] for _ in GROUPS]
    for base, card in sorted(cards.items(), key=order):
        meta = extract(ASSETS / card["std"])
        g = TYPES45.get(base, 5 if base.endswith("-animated") else 4)
        name = meta["eyebrow"].split(" · ")[-1] if meta["eyebrow"] else base
        grouped[g].append((base, {**card, **meta, "name": name}))

    lis: list[str] = []
    sections: list[str] = []
    for gi, group in enumerate(grouped):
        for base, c in group:
            h = int(c["vb_h"]) if c["vb_h"] else 560
            attrs = [f'data-base="{base}"', f'data-h="{doc_height(h, False)}"']
            if c["full"]:
                attrs.append(f'data-full-h="{doc_height(h, True)}"')
            for k in ("dark", "full"):
                if c[k]:
                    attrs.append(f'data-{k}="{c[k]}"')
            esc = (c["desc"].replace("&", "&amp;").replace("<", "&lt;")
                   .replace('"', "&quot;"))
            lis.append(
                f'<li><a href="{c["std"]}" target="_blank" rel="noopener" title="{esc}" '
                + " ".join(attrs)
                + f'><b>{c["name"]}</b><small>{c["h1"]}</small></a></li>'
            )
        sections.append(
            f'<section id="panel-{gi}" role="tabpanel" aria-labelledby="tab-{gi}" data-g="{gi}">\n'
            f"<h2>{GROUPS[gi]}<span data-n=\"{len(group)}\">{len(group)}</span></h2>\n<ul>\n"
            + "\n".join(lis) + "\n</ul>\n</section>"
        )
        lis = []

    tabs = "\n".join(
        f'<button id="tab-{gi}" role="tab" aria-selected="{"true" if gi == 0 else "false"}"'
        f' aria-controls="panel-{gi}" data-g="{gi}">{g}<span>{len(grouped[gi])}</span></button>'
        for gi, g in enumerate(GROUPS)
    )
    total = sum(len(g) for g in grouped)
    template = Path(__file__).with_name("gallery_template.html")
    return template.read_text(encoding="utf-8").replace("%%TABS%%", tabs).replace(
        "%%SECTIONS%%", "\n".join(sections)
    ).replace("%%TOTAL%%", str(total)).replace(
        "%%FIRST%%", grouped[0][0][1]["std"]
    )


if __name__ == "__main__":
    out = ASSETS / "index.html"
    out.write_text(build(), encoding="utf-8")
    n = len(list(ASSETS.glob("example-*.html")))
    print(f"OK index.html（扫描 {n} 个示例文件）")
