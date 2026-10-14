#!/usr/bin/env python3
"""reskin.py —— 成品图表 HTML 的皮肤值替换器（零第三方依赖，随技能分发）。

    python3 scripts/reskin.py --list
    python3 scripts/reskin.py --skin zhongguohong 输入.html -o 输出.html
    python3 scripts/reskin.py --skin default --dry-run 输入.html   # 颜色出处普查

机制：皮肤 = 语义槽位 → 色值的映射表（scripts/skins/*.json），
只在 CSS 颜色声明与 SVG 呈现属性中做**值级替换**，正文、描述、ID 和数据字符串不参与：hex → 新 hex；rgba(基, α) → 新基色 + 原 α 逐字保留。
α 档位是结构不是颜色——只换基色、永远不动透明度，因此 15 档梯子、
treemap 六档坡道、深色 0.72 文字契约在换肤后原样成立。

不吃换肤（PINNED，皮肤表试图覆盖即报错）：
  语义色族五色 sem-security / sem-observability / sem-governance /
  sem-backup / sem-workspace——换皮不换义。
  终端外壳灰阶七色（TERMINAL_NEUTRALS）——终端就是黑底灰字，不吃皮肤；
  是否允许出现在某个文件里由 self_check 的上下文判定管（非终端文件用了会红）。

皮肤表未覆盖的槽位保持默认值；皮肤缺深色档而文件含深色值时给警告
（深色部分保持来源值，不产出半套猜测值）。

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
from html_tools import map_colors, color_occurrences

SKINS_DIR = Path(__file__).resolve().parent / "skins"

# 样式数据统一从随包默认配置读取；规则和角色用途见样式指南。
DEFAULT_CONFIG = Path(__file__).resolve().parent.parent / "styles/default.json"
DEFAULT_DATA = json.loads(DEFAULT_CONFIG.read_text(encoding="utf-8"))


def _default_slot(value):
    return value, tuple(int(value[i : i + 2], 16) for i in (1, 3, 5))


SLOTS = {
    k: _default_slot(DEFAULT_DATA["colors"][k]) for k in DEFAULT_DATA["skin_slots"]
}
PINNED = {k: _default_slot(v) for k, v in DEFAULT_DATA["pinned"].items()}

DARK_SLOTS = {
    "paper-dark",
    "dark-bg",
    "muted-dark",
    "soft-dark",
    "accent-dark",
    "link-dark",
}

# 终端外壳灰阶（assets/template-terminal.html 的题材专用色系，按 RGB 基收录，
# hex 与 rgba 两种写法同时盖住）。换肤与普查均原样保留。
TERMINAL_NEUTRALS = frozenset(tuple(v) for v in DEFAULT_DATA["terminal_neutrals"])

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
        rgb = tuple(int(v[i : i + 2], 16) for i in (1, 3, 5))
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

    overridden_series = {s for s in colors if re.fullmatch(r"series-[1-5]", s)}
    if overridden_series:
        if len(overridden_series) != 5:
            warnings.append(
                f"系列色只覆盖 {sorted(overridden_series)}——建议五色齐上或全不动"
            )
        hues = [rgb_to_hsl(colors[s][1])[0] for s in overridden_series]
        hues.sort()
        for h1, h2 in zip(hues, hues[1:] + [hues[0] + 360]):
            if h2 - h1 < 20:
                errors.append(
                    f"系列色色相拥挤（相邻 {h2 - h1:.0f}° < 20°）——这是彩虹，不是皮肤"
                )
        for s in overridden_series:
            _h, sat, light = rgb_to_hsl(colors[s][1])
            if sat > 0.9 or not 0.25 <= light <= 0.8:
                warnings.append(f"{s} 饱和/明度出舒适区（s={sat:.2f}, l={light:.2f}）")

    return errors, warnings


DERIVED_ROLES = {
    "rule": "ink",
    "rule-dark": "paper-dark",
    "accent-tint": "accent",
    "accent-tint-dark": "accent-dark",
    "paper-2-dark": "dark-bg",
}

STYLE_MARKER = re.compile(r"<!--\s*diagram-style:(\{.*?\})\s*-->", re.S)
RESKIN_MARKER = re.compile(r"<!--\s*reskin:[^>]*-->\s*")


def read_style_snapshot(source):
    marks = STYLE_MARKER.findall(source)
    if len(marks) > 1:
        raise SkinError("存在多个样式来源快照")
    if not marks:
        return None
    try:
        data = json.loads(marks[0])
        if (
            data.get("schema") != 1
            or not isinstance(data.get("uses"), list)
            or not isinstance(data.get("colors"), dict)
        ):
            raise ValueError("无效 schema/uses/colors")
        if set(data["colors"]) - set(DEFAULT_DATA["colors"]) - set(PINNED):
            raise ValueError("未知样式角色")
        for k, v in PINNED.items():
            if data["colors"].get(k, v[0]) != v[0]:
                raise ValueError("语义色不能由来源快照改写")
        if len(data["uses"]) != len(list(color_occurrences(source))):
            raise ValueError(
                "颜色数量已变化，请显式指定 --from-style-guide 或 --from-skin"
            )
        return data
    except (ValueError, TypeError) as exc:
        raise SkinError(f"样式来源快照无效：{exc}") from exc


def color_signature(raw):
    literal, rgb = parse_color(raw)
    match = RGBA_RE.fullmatch(literal)
    alpha = float(match.group(4)) if match and match.group(4) is not None else 1.0
    return rgb, alpha


def translate(
    source,
    colors,
    extra=None,
    source_colors=None,
    source_uses=None,
    strict=False,
    role_log=None,
):
    """仅转换颜色声明/呈现属性。来源角色快照用于再次换肤；文字/ID 不参与。"""
    active = {**SLOTS, **PINNED, **(source_colors or {})}
    known = {**active, **(extra or {})}
    replaced, kept = Counter(), Counter()
    ordinal = 0

    def lookup(raw):
        value, rgb = parse_color(raw)
        exact = [
            k
            for k, v in known.items()
            if color_signature(v[0]) == color_signature(value)
        ]
        # Alpha-based derived roles have their own full literal; plain bases prefer ink/accent.
        candidates = exact or [
            k for k, v in known.items() if v[1] == rgb and not v[0].startswith("rgba(")
        ]
        candidates = [
            k
            for k in candidates
            if k not in {"rule", "rule-dark", "accent-tint", "accent-tint-dark"}
        ] or candidates
        if not candidates:
            return None
        if len({known[k][1] for k in candidates}) != 1:
            raise SkinError("来源角色冲突")
        # Pinned semantic aliases share RGB; they must never enter a skin transformation.
        if any(k in PINNED for k in candidates):
            return next(k for k in candidates if k in PINNED)
        distinct = [k for k in candidates if k in colors]
        if strict and len({colors[k][0] for k in distinct}) > 1:
            raise SkinError(f"颜色 {raw} 对应多个来源角色 {distinct}，无法安全换肤")
        return candidates[0]

    def convert(raw):
        nonlocal ordinal
        canonical, rgb = parse_color(raw)
        if source_uses is not None:
            if ordinal >= len(source_uses):
                raise SkinError("样式来源颜色数量不符")
            record = source_uses[ordinal]
            if (
                not isinstance(record, dict)
                or color_signature(record.get("value", ""))
                != color_signature(canonical)
                or (
                    record.get("role") not in active
                    and not (record.get("role") is None and rgb in TERMINAL_NEUTRALS)
                )
            ):
                raise SkinError(
                    "成品颜色与样式来源快照不符，请显式指定来源样式重新解析"
                )
            slot = record["role"]
            expected = active[slot] if slot else (canonical, rgb)
            if rgb != expected[1]:
                raise SkinError("样式来源角色与颜色基不符")
        else:
            slot = lookup(raw)
        ordinal += 1
        result = raw
        if slot is None:
            label = ("terminal:" if rgb in TERMINAL_NEUTRALS else "未知:") + canonical
            kept[label] += 1
            if strict and rgb not in TERMINAL_NEUTRALS:
                raise SkinError(f"未知来源颜色 {raw}，换肤未写出；请指定来源样式")
        elif (
            slot in colors or DERIVED_ROLES.get(slot) in colors
        ) and slot not in PINNED:
            replaced[slot] += 1
            destination = colors.get(slot) or colors[DERIVED_ROLES[slot]]
            if canonical.startswith("rgb") and (
                color_signature(canonical) != color_signature(active[slot][0])
                or slot not in colors
            ):
                r, g, b = destination[1]
                match = RGBA_RE.fullmatch(canonical)
                alpha = match.group(4)
                result = (
                    f"rgba({r},{g},{b},{alpha})"
                    if alpha is not None
                    else f"rgb({r},{g},{b})"
                )
            else:
                result = destination[0]
        else:
            kept[slot] += 1
        if role_log is not None:
            # Terminal neutrals are fixed; no palette role is assigned.
            role_log.append({"role": slot, "value": parse_color(result)[0]})
        return result

    text = map_colors(source, convert)
    return text, replaced, kept


def restem(text: str, old: str, new: str) -> str:
    if old == new:
        return text
    from html_tools import SourceParser, ATTR_RE
    from html import escape

    ids = {old + "-title": new + "-title", old + "-desc": new + "-desc"}
    parser = SourceParser(text)
    for start, raw in parser.tags:
        if re.match(r"<(?:title|desc)\b", raw, re.I):
            for match in ATTR_RE.finditer(raw):
                value = next((match[g] for g in (2, 3, 4) if match[g] is not None), "")
                if match[1] == "id" and value.startswith(old + "-"):
                    ids[value] = new + value[len(old) :]
    edits = []
    for start, raw in parser.tags:
        for m in ATTR_RE.finditer(raw):
            if m[1] not in {
                "id",
                "aria-labelledby",
                "aria-describedby",
                "href",
                "xlink:href",
            }:
                continue
            group = next(g for g in (2, 3, 4) if m[g] is not None)
            value = m[group]
            if m[1] == "id":
                updated = ids.get(value, value)
            elif m[1].startswith("aria-"):
                updated = " ".join(ids.get(x, x) for x in value.split())
            else:
                updated = (
                    "#" + ids.get(value[1:], value[1:])
                    if value.startswith("#")
                    else value
                )
            if updated != value:
                edits.append(
                    (
                        start + m.start(group),
                        start + m.end(group),
                        escape(updated, quote=True),
                    )
                )
    for a, b, value in reversed(edits):
        text = text[:a] + value + text[b:]
    return text


def report_stats(path: Path, replaced: Counter, kept: Counter, dry: bool) -> None:
    unknown = {k: v for k, v in kept.items() if k.startswith("未知:")}
    verb = "普查" if dry else "替换"
    detail = " · ".join(f"{slot} {n}" for slot, n in replaced.most_common())
    line = f"{path.name}：{verb} {sum(replaced.values())} 处"
    if detail:
        line += f"（{detail}）"
    pinned_detail = " · ".join(
        f"{k} {v}"
        for k, v in kept.most_common()
        if not k.startswith("未知:") and not k.startswith("terminal:")
    )
    if pinned_detail:
        line += f"；原样 {pinned_detail}"
    terminal_detail = " · ".join(
        f"{k.removeprefix('terminal:')} {v}"
        for k, v in kept.most_common()
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
    ap.add_argument(
        "--from-skin", help="输入图的来源皮肤；不指定时读取输出快照/皮肤标记"
    )
    ap.add_argument(
        "--from-style-guide", type=Path, help="输入图的品牌样式指南或 JSON 配置"
    )
    ap.add_argument("--skin", help="皮肤名（scripts/skins/<名>.json）或 JSON 路径")
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="只统计不输出（配合 --skin default 做普查）",
    )
    ap.add_argument("-o", "--output", type=Path, help="输出文件（缺省打印到 stdout）")
    ap.add_argument(
        "--tag",
        action="store_true",
        default=True,
        help="在 doctype 后插入皮肤来源注释（默认开——self_check 靠它认换肤产物的出处）",
    )
    ap.add_argument(
        "--no-tag", dest="tag", action="store_false", help="不插皮肤来源注释"
    )
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
        try:
            if args.from_skin and args.from_style_guide:
                raise SkinError("来源皮肤与来源指南只能指定一个")
            snapshot = (
                None
                if (args.from_skin or args.from_style_guide)
                else read_style_snapshot(source)
            )
            source_colors = None
            if args.from_style_guide:
                from style_config import load_style_colors

                source_colors = load_style_colors(args.from_style_guide)
            elif args.from_skin or (
                not snapshot
                and (oldmark := re.search(r"<!--\s*reskin:([\w.-]+)", source))
            ):
                name = args.from_skin or oldmark.group(1)
                if not re.fullmatch(r"[a-z0-9-]+", name):
                    raise SkinError("非法来源皮肤名")
                origin = load_skin(SKINS_DIR / (name + ".json"))
                problems, _ = gate(origin)
                if problems:
                    raise SkinError("来源皮肤未过质量门：" + "；".join(problems))
                source_colors = origin["colors"]
            elif snapshot:
                source_colors = {
                    k: parse_color(v) for k, v in snapshot["colors"].items()
                }
            uses = []
            text, replaced, kept = translate(
                source,
                skin["colors"],
                source_colors=source_colors,
                source_uses=snapshot["uses"] if snapshot else None,
                strict=True,
                role_log=uses,
            )
        except (SkinError, ValueError, OSError, KeyError, TypeError) as exc:
            print(f"{path.name}：{exc}", file=sys.stderr)
            failed = True
            continue
        report_stats(path, replaced, kept, args.dry_run)
        dark_in_file = DARK_SLOTS & kept.keys()
        if dark_in_file and not (DARK_SLOTS & skin["colors"].keys()):
            print(
                f"~ {path.name} 含深色值 {sorted(dark_in_file)}，但皮肤无深色档——深色部分保持来源值",
                file=sys.stderr,
            )
        if args.dry_run:
            continue
        text = STYLE_MARKER.sub("", text)
        text = RESKIN_MARKER.sub("", text)
        palette = {**SLOTS, **PINNED, **(source_colors or {}), **skin["colors"]}
        for derived, parent in DERIVED_ROLES.items():
            if (
                parent in skin["colors"]
                and derived not in skin["colors"]
                and derived in palette
            ):
                literal = palette[derived][0]
                if literal.startswith("rgba("):
                    alpha = literal.rstrip(")").split(",")[-1]
                    r, g, b = palette[parent][1]
                    palette[derived] = (f"rgba({r},{g},{b},{alpha})", (r, g, b))
                else:
                    palette[derived] = palette[parent]
        if args.tag:
            payload = {
                "schema": 1,
                "colors": {k: v[0] for k, v in palette.items()},
                "uses": uses,
            }
            mark = (
                f"<!-- reskin:{skin['name']} -->\n<!-- diagram-style:"
                + json.dumps(payload, ensure_ascii=True, separators=(",", ":"))
                + " -->\n"
            )
            doctype = re.match(r"<!DOCTYPE[^>]*>\s*", text, re.I)
            position = doctype.end() if doctype else 0
            text = text[:position] + mark + text[position:]
        out = args.output
        if out is not None:
            text = restem(text, path.stem, out.stem)
        # Preserve type identity when a bundled example receives a new filename.
        from html_tools import svg_fragments

        kind = (
            path.stem.removeprefix("example-")
            .removesuffix("-dark")
            .removesuffix("-full")
        )
        if kind.startswith(
            ("treemap", "marimekko", "exploded", "axonometric-plan", "state-lifecycle")
        ):
            for fragment in reversed(svg_fragments(text)):
                if (
                    fragment.attrs.get("role") == "img"
                    and "data-diagram-type" not in fragment.attrs
                ):
                    pos = text.index(">", fragment.start)
                    text = text[:pos] + f' data-diagram-type="{kind}"' + text[pos:]
        import tempfile
        from self_check import verify

        with tempfile.TemporaryDirectory(prefix="diagram-reskin-") as directory:
            candidate = Path(directory) / (out.name if out else path.name)
            candidate.write_text(text, encoding="utf-8")
            config = Path(directory) / "target.json"
            config.write_text(
                json.dumps(
                    {
                        "schema": 1,
                        "colors": {
                            k: v[0]
                            for k, v in palette.items()
                            if k in DEFAULT_DATA["colors"]
                        },
                    }
                ),
                encoding="utf-8",
            )
            issues, _ = verify(candidate, config)
            if issues:
                print(
                    "换肤产物未过质量门，未写出：" + "；".join(issues), file=sys.stderr
                )
                failed = True
                continue
        if out is not None:
            try:
                with tempfile.NamedTemporaryFile(
                    mode="w",
                    encoding="utf-8",
                    dir=out.parent,
                    delete=False,
                    prefix=".diagram-reskin-",
                ) as handle:
                    handle.write(text)
                    temporary = Path(handle.name)
                temporary.replace(out)
            except OSError as exc:
                if "temporary" in locals() and temporary.exists():
                    temporary.unlink()
                print(f"写出失败：{exc}", file=sys.stderr)
                failed = True
                continue
            print(f"→ {out}", file=sys.stderr)
        else:
            sys.stdout.write(text)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
