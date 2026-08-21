#!/usr/bin/env python3
"""reskin.py —— 成品图表 HTML 的皮肤值替换器（零第三方依赖，随技能分发）。

    python3 scripts/reskin.py --list
    python3 scripts/reskin.py --skin zhongguohong 输入.html -o 输出.html
    python3 scripts/reskin.py --skin default --dry-run 输入.html   # 颜色出处普查

机制：皮肤 = 语义槽位 → 色值的映射表（scripts/skins/*.json），
对成品 HTML 做**值级替换**：hex → 新 hex；rgba(基, α) → 新基色 + 原 α 逐字保留。
α 档位是结构不是颜色——只换基色、永远不动透明度，因此 15 档梯子、
treemap 六档坡道、深色 0.72 文字契约在换肤后原样成立。

不吃换肤（PINNED，皮肤表试图覆盖即报错）：
  语义色族五色 sem-security / sem-observability / sem-governance /
  sem-backup / sem-workspace——换皮不换义。
  终端外壳灰阶七色（TERMINAL_NEUTRALS）——终端就是黑底灰字，不吃皮肤；
  是否允许出现在某个文件里由 self_check 的上下文判定管（非终端文件用了会红）。

皮肤表未覆盖的槽位保持默认值；皮肤缺深色档而文件含深色值时给警告
（深色部分保持默认，不产出半套猜测值）。

gate（在皮肤表层做，不过门的皮肤不让用）：
  - ink 对 paper 的 WCAG 对比度 ≥ 4.5（AA，硬门槛；< 7 给提示）
  - 槽位互相撞值报错（accent 与任何其他槽位同值即错——焦点必须唯一）
  - accent 与语义五色距离过近给警告（焦点色混进领域色）
  - series 覆盖须五色齐上且两两色相差 ≥ 25°（防彩虹）
  - 未知槽位名 / 覆盖 PINNED / 非法色值 → 报错

已知边界：reskin 是机械换值。皮肤若含结构性语义（新中式钤印/题签/朱批、
黛蓝 link），值替换只能逼近色板，完整效果走生成时皮肤文档
（references/skin-*.md）。写入 -o 且文件名词干变化时，自动同步改写
title/desc 的 slug id，保持 self_check.py 的 slug 契约。产物默认打
reskin 来源注释（--no-tag 关闭）——self_check 的颜色层靠它把目标皮肤表
的值并进闭集。
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from collections import Counter
from pathlib import Path

SKINS_DIR = Path(__file__).resolve().parent / "skins"

# ---- 默认槽位表（现行值快照；与 references/style-guide.md 对账）----
SLOTS: dict[str, tuple[str, tuple[int, int, int]]] = {
    "paper":       ("#ffffff", (255, 255, 255)),
    "paper-2":     ("#f3f2ff", (243, 242, 255)),
    "ink":         ("#29314f", (41, 49, 79)),
    "muted":       ("#565e7e", (86, 94, 126)),
    "soft":        ("#8f94ab", (143, 148, 171)),
    "accent":      ("#1a4dd9", (26, 77, 217)),
    # 深色档：paper-dark 是深色文字的纸色基（hex 形 #e0e4ff 与 rgba 基 224,228,255 同源）。
    "paper-dark":  ("#e0e4ff", (224, 228, 255)),
    "dark-bg":     ("#0a0d1b", (10, 13, 27)),
    "muted-dark":  ("#a2a9ce", (162, 169, 206)),
    "soft-dark":   ("#787fa2", (120, 127, 162)),
    "accent-dark": ("#7d98ff", (125, 152, 255)),
    "series-1":    ("#3ba272", (59, 162, 114)),
    "series-2":    ("#ed7d31", (237, 125, 49)),
    "series-3":    ("#d9605b", (217, 96, 91)),
    "series-4":    ("#5470c6", (84, 112, 198)),
    "series-5":    ("#9a6fb8", (154, 111, 184)),
    "series-1-dark": ("#5fbf93", (95, 191, 147)),
    "series-2-dark": ("#f2a267", (242, 162, 103)),
    "series-3-dark": ("#e78c88", (231, 140, 136)),
    "series-4-dark": ("#8498dc", (132, 152, 220)),
    "series-5-dark": ("#b795cf", (183, 149, 207)),
}

# 语义色族：换皮不换义。出现在皮肤表里即报错；在成品里识别后原样保留。
# 浅深两档、色相恒定（style-guide「语义色族」表）。
PINNED: dict[str, tuple[str, tuple[int, int, int]]] = {
    "sem-security":      ("#b85450", (184, 84, 80)),
    "sem-observability": ("#5a7d9a", (90, 125, 154)),
    "sem-governance":    ("#7a8c47", (122, 140, 71)),
    "sem-backup":        ("#8c6d3f", (140, 109, 63)),
    "sem-workspace":     ("#c9a23a", (201, 162, 58)),
    "sem-security-dark":      ("#bf6561", (191, 101, 97)),
    "sem-observability-dark": ("#5e83a1", (94, 131, 161)),
    "sem-governance-dark":    ("#7a8c47", (122, 140, 71)),
    "sem-backup-dark":        ("#9b7946", (157, 121, 70)),
    "sem-workspace-dark":     ("#c9a23a", (201, 162, 58)),
}

DARK_SLOTS = {"paper-dark", "dark-bg", "muted-dark", "soft-dark", "accent-dark"}

# 终端外壳灰阶（assets/template-terminal.html 的题材专用色系，按 RGB 基收录，
# hex 与 rgba 两种写法同时盖住）。换肤与普查均原样保留。
TERMINAL_NEUTRALS: frozenset[tuple[int, int, int]] = frozenset({
    (10, 10, 10),      # terminal-page   #0a0a0a
    (20, 20, 20),      # terminal-paper  #141414
    (27, 27, 27),      # terminal-bar    #1b1b1b
    (43, 43, 43),      # terminal-border #2b2b2b
    (92, 92, 92),      # terminal-soft   #5c5c5c
    (154, 154, 154),   # terminal-muted  #9a9a9a
    (245, 245, 245),   # terminal-ink    #f5f5f5
})

HEX_RE = re.compile(r"(?<!url\()#([0-9a-fA-F]{6})\b")
RGBA_RE = re.compile(
    r"rgba?\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*(?:,\s*([0-9.]+)\s*)?\)"
)

# 反查表：默认 hex / 默认 rgba 基 → 槽位名（含 PINNED）
HEX_TO_SLOT = {value[0]: slot for slot, value in {**SLOTS, **PINNED}.items()}
BASE_TO_SLOT = {value[1]: slot for slot, value in {**SLOTS, **PINNED}.items()}


def parse_color(value: str) -> tuple[str, tuple[int, int, int]]:
    """'#rrggbb' 或 'rgba(r,g,b[,a])' → (规范化值串, RGB 基)。"""
    v = value.strip().lower()
    if v.startswith("#"):
        if re.fullmatch(r"#[0-9a-f]{6}", v) is None:
            raise ValueError(f"非法 hex：{value!r}")
        rgb = tuple(int(v[i:i + 2], 16) for i in (1, 3, 5))
        return v, rgb  # type: ignore[return-value]
    m = re.fullmatch(
        r"rgba?\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*(?:,\s*([0-9.]+))?\)", v
    )
    if m is None or any(int(c) > 255 for c in m.group(1, 2, 3)):
        raise ValueError(f"非法颜色值：{value!r}")
    return v, (int(m.group(1)), int(m.group(2)), int(m.group(3)))


class SkinError(Exception):
    pass


def load_skin(path: Path) -> dict:
    """读皮肤 JSON 并做结构校验（gate 另行调用）。"""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SkinError(f"读不了皮肤表 {path.name}：{exc}") from exc
    colors: dict[str, tuple[str, tuple[int, int, int]]] = {}
    problems: list[str] = []
    for slot, value in data.get("colors", {}).items():
        if slot in PINNED:
            problems.append(f"{slot} 是语义色族，换皮不换义（PINNED）")
            continue
        if slot not in SLOTS:
            problems.append(f"未知槽位 {slot!r}")
            continue
        try:
            colors[slot] = parse_color(str(value))
        except ValueError as exc:
            problems.append(str(exc))
    if problems:
        raise SkinError(f"皮肤表 {path.stem} 校验失败：" + "；".join(problems))
    return {
        "name": path.stem,
        "label": data.get("label", path.stem),
        "source": data.get("source", ""),
        "note": data.get("note", ""),
        "colors": colors,
    }


def rel_luminance(rgb: tuple[int, int, int]) -> float:
    def chan(c: int) -> float:
        x = c / 255
        return x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4

    r, g, b = map(chan, rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a: tuple[int, int, int], b: tuple[int, int, int]) -> float:
    la, lb = sorted((rel_luminance(a), rel_luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def rgb_to_hsl(rgb: tuple[int, int, int]) -> tuple[float, float, float]:
    r, g, b = (c / 255 for c in rgb)
    mx, mn = max(r, g, b), min(r, g, b)
    l = (mx + mn) / 2
    if mx == mn:
        return 0.0, 0.0, l
    d = mx - mn
    s = d / (2 - mx - mn) if l > 0.5 else d / (mx + mn)
    if mx == r:
        h = ((g - b) / d + (6 if g < b else 0)) / 6
    elif mx == g:
        h = ((b - r) / d + 2) / 6
    else:
        h = ((r - g) / d + 4) / 6
    return h * 360, s, l


def gate(skin: dict) -> tuple[list[str], list[str]]:
    """皮肤门：错误挡下（exit 1），警告放行但必须给人看见。"""
    errors: list[str] = []
    warnings: list[str] = []
    colors = skin["colors"]
    eff = {slot: colors.get(slot, default) for slot, default in SLOTS.items()}

    ratio = contrast(eff["ink"][1], eff["paper"][1])
    if ratio < 4.5:
        errors.append(f"ink 对 paper 对比度 {ratio:.2f} < 4.5（AA 硬门槛）")
    elif ratio < 7.0:
        warnings.append(f"ink 对 paper 对比度 {ratio:.2f} 偏紧（< 7，长正文会累）")

    for slot in sorted(colors):
        value = colors[slot][0]
        for other, (other_value, _ob) in eff.items():
            if other > slot and other_value == value:
                errors.append(f"槽位撞值：{slot} 与 {other} 同为 {value}——焦点必须唯一")
                break

    accent_rgb = eff["accent"][1]
    for pname, (phex, prgb) in PINNED.items():
        d = math.dist(accent_rgb, prgb)
        if d < 40:
            warnings.append(
                f"accent 与 {pname}（{phex}）距离 {d:.0f} 过近——焦点色会混进领域语义色"
            )

    overridden_dark = DARK_SLOTS & colors.keys()
    if overridden_dark and overridden_dark != DARK_SLOTS:
        warnings.append(
            f"深色槽位只覆盖 {sorted(overridden_dark)}——深色成品会得到半套皮肤"
        )

    overridden_series = {
        s for s in colors if re.fullmatch(r"series-[1-5]", s)
    }
    if overridden_series:
        if len(overridden_series) != 5:
            warnings.append(f"系列色只覆盖 {sorted(overridden_series)}——建议五色齐上或全不动")
        hues = [rgb_to_hsl(colors[s][1])[0] for s in overridden_series]
        hues.sort()
        for h1, h2 in zip(hues, hues[1:] + [hues[0] + 360]):
            if h2 - h1 < 20:
                errors.append(f"系列色色相拥挤（相邻 {h2 - h1:.0f}° < 20°）——这是彩虹，不是皮肤")
        for s in overridden_series:
            _h, sat, light = rgb_to_hsl(colors[s][1])
            if sat > 0.9 or not 0.25 <= light <= 0.8:
                warnings.append(f"{s} 饱和/明度出舒适区（s={sat:.2f}, l={light:.2f}）")

    return errors, warnings


def translate(
    source: str,
    colors: dict,
    extra: dict | None = None,
) -> tuple[str, Counter, Counter]:
    """值级替换。返回 (新文本, 替换统计, 原样保留统计)。
    extra：额外合法值 → 槽位映射（self_check 对换肤产物复用本识别器时
    传入目标皮肤表的值，出处=那张表），仅用于识别、不参与替换。"""
    replaced: Counter = Counter()
    kept: Counter = Counter()
    if extra:
        hex_map = {**HEX_TO_SLOT, **{v[0]: f"皮肤/{slot}" for slot, v in extra.items()}}
        base_map = {**BASE_TO_SLOT, **{v[1]: f"皮肤/{slot}" for slot, v in extra.items()}}
    else:
        hex_map, base_map = HEX_TO_SLOT, BASE_TO_SLOT

    def hex_sub(m: re.Match) -> str:
        canonical = "#" + m.group(1).lower()
        slot = hex_map.get(canonical)
        if slot is None:
            rgb = tuple(int(m.group(1)[i:i + 2], 16) for i in (0, 2, 4))
            if rgb in TERMINAL_NEUTRALS:
                kept[f"terminal:{canonical}"] += 1
            else:
                kept[f"未知:{m.group(0)}"] += 1
            return m.group(0)
        if slot in colors:
            replaced[slot] += 1
            return colors[slot][0]
        kept[slot] += 1
        return m.group(0)

    def rgba_sub(m: re.Match) -> str:
        base = (int(m.group(1)), int(m.group(2)), int(m.group(3)))
        slot = base_map.get(base)
        if slot is None:
            if base in TERMINAL_NEUTRALS:
                kept[f"terminal:rgb({base[0]},{base[1]},{base[2]})"] += 1
            else:
                kept[f"未知:rgb({base[0]},{base[1]},{base[2]})"] += 1
            return m.group(0)
        if slot in colors:
            replaced[slot] += 1
            r, g, b = colors[slot][1]
            alpha = m.group(4)
            if alpha is None:
                return f"rgb({r},{g},{b})"
            return f"rgba({r},{g},{b},{alpha})"
        kept[slot] += 1
        return m.group(0)

    # 先 rgba 后 hex：rgba 的产物不含 #，不会被 hex 轮二次命中；
    # 反过来 hex 的 rgba 产物会被 rgba 轮误判成未知基色。
    text = RGBA_RE.sub(rgba_sub, source)
    text = HEX_RE.sub(hex_sub, text)
    return text, replaced, kept


def restem(text: str, old: str, new: str) -> str:
    """-o 换名时同步 slug id，保住 self_check 的 {stem}-title/-desc 契约。"""
    if old == new:
        return text
    return text.replace(f"{old}-title", f"{new}-title").replace(f"{old}-desc", f"{new}-desc")


def report_stats(path: Path, replaced: Counter, kept: Counter, dry: bool) -> None:
    unknown = {k: v for k, v in kept.items() if k.startswith("未知:")}
    verb = "普查" if dry else "替换"
    detail = " · ".join(f"{slot} {n}" for slot, n in replaced.most_common())
    line = f"{path.name}：{verb} {sum(replaced.values())} 处"
    if detail:
        line += f"（{detail}）"
    pinned_detail = " · ".join(
        f"{k} {v}" for k, v in kept.most_common()
        if not k.startswith("未知:") and not k.startswith("terminal:")
    )
    if pinned_detail:
        line += f"；原样 {pinned_detail}"
    terminal_detail = " · ".join(
        f"{k.removeprefix('terminal:')} {v}" for k, v in kept.most_common()
        if k.startswith("terminal:")
    )
    if terminal_detail:
        line += f"；终端 {terminal_detail}"
    if unknown:
        line += f"；⚠ 未知颜色 {sum(unknown.values())} 处 {sorted(unknown)}"
    print(line, file=sys.stderr)


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--list", action="store_true", help="列出皮肤并逐个过 gate")
    ap.add_argument("--skin", help="皮肤名（scripts/skins/<名>.json）或 JSON 路径")
    ap.add_argument("--dry-run", action="store_true", help="只统计不输出（配合 --skin default 做普查）")
    ap.add_argument("-o", "--output", type=Path, help="输出文件（缺省打印到 stdout）")
    ap.add_argument("--tag", action="store_true", default=True,
                    help="在 doctype 后插入皮肤来源注释（默认开——self_check 靠它认换肤产物的出处）")
    ap.add_argument("--no-tag", dest="tag", action="store_false", help="不插皮肤来源注释")
    ap.add_argument("--skins-dir", type=Path, default=SKINS_DIR)
    ap.add_argument("files", nargs="*", type=Path)
    args = ap.parse_args()

    skins_dir = args.skins_dir
    if args.list:
        found = False
        for path in sorted(skins_dir.glob("*.json")):
            found = True
            try:
                skin = load_skin(path)
            except SkinError as exc:
                print(f"{path.stem:<14} ✗ {exc}")
                continue
            errors, warnings = gate(skin)
            status = "✗ " + "；".join(errors) if errors else "✓"
            print(f"{path.stem:<14} {skin['label']}")
            print(f"{'':14} {status}")
            for w in warnings:
                print(f"{'':14} ~ {w}")
        if not found:
            print(f"skins 目录里没有皮肤表：{skins_dir}", file=sys.stderr)
            return 1
        return 0

    if not args.skin or not args.files:
        ap.error("需要 --skin 和至少一个输入文件（或用 --list）")
    skin_path = Path(args.skin)
    if not skin_path.is_file():
        skin_path = skins_dir / f"{args.skin}.json"
    if not skin_path.is_file():
        print(f"找不到皮肤表：{args.skin}", file=sys.stderr)
        return 2

    try:
        skin = load_skin(skin_path)
    except SkinError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    errors, warnings = gate(skin)
    for w in warnings:
        print(f"~ {w}", file=sys.stderr)
    if errors:
        for e in errors:
            print(f"✗ {e}", file=sys.stderr)
        print(f"皮肤 {skin['name']} 没过 gate，拒绝执行", file=sys.stderr)
        return 1

    if args.output and len(args.files) > 1:
        ap.error("多个输入文件时不支持 -o，逐个跑或重定向 stdout")

    failed = False
    for path in args.files:
        try:
            source = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            print(f"读不了 {path}：{exc}", file=sys.stderr)
            failed = True
            continue
        text, replaced, kept = translate(source, skin["colors"])
        report_stats(path, replaced, kept, args.dry_run)
        dark_in_file = DARK_SLOTS & kept.keys()
        if dark_in_file and not (DARK_SLOTS & skin["colors"].keys()):
            print(
                f"~ {path.name} 含深色值 {sorted(dark_in_file)}，但皮肤无深色档——深色部分保持默认",
                file=sys.stderr,
            )
        if args.dry_run:
            continue
        if args.tag:
            doctype = re.match(r"<!DOCTYPE[^>]*>\n?", text)
            mark = f"<!-- reskin:{skin['name']}（{skin['label']}）· 源 {skin['source'] or '默认'} -->\n"
            text = mark + text[doctype.end():] if doctype else mark + text
        if args.output:
            out = args.output
            out = out if out.is_absolute() else path.parent / out.name
            text = restem(text, path.stem, out.stem)
            out.write_text(text, encoding="utf-8")
            print(f"→ {out}", file=sys.stderr)
        else:
            sys.stdout.write(text)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
