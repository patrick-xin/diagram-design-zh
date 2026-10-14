#!/usr/bin/env python3
"""家族一致性扫描——给「单文件合法」的 self_check 补上家族视角。

self_check 只看一个文件自己（安全/契约/颜色闭集/字号下限/4px 网格），
单文件各自合法、家族互相漂移的情况它天然看不见（eyebrow 0.7/0.75rem
分裂存活多轮就是这个盲区）。本脚本对 assets/ 成品家族提取页面骨架指纹，
按档位取多数派：偏离多数派的文件即漂移项。

指纹维度：eyebrow 字号与下距、h1 字号与下距、frame 左内边距、viewBox 宽；
full 档另有页脚上距（卡区 → 页脚，2026-08-22 line-full 定 1rem，存量 2rem）。

棘轮用法（漂移项报错，但快照冻住现状当待改清单）：
    python3 tools/family_check.py                    # 首跑：列出全部漂移项
    python3 tools/family_check.py --update-baseline  # 冻结为基线（有意识接受现状时）
    python3 tools/family_check.py                    # 对照：基线外新漂移 = FAIL（exit 1），
                                                     #        基线内已修复的报 ✓，清单只减不增

基线条目可手工补 "reason" 字段——合法的按设计偏离（如参数化宽度的矩阵图）
写明理由后留档，和待改项区分开。

另跑三档齐全守卫（不走棘轮，直接 FAIL）：每个 example-{类型} 必须
std/dark/full 三档齐全，白名单 TRIO_EXEMPT 点名豁免。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent / "skills/diagram-design-zh"
ASSETS = REPO / "assets"
BASELINE = Path(__file__).resolve().parent / "family-baseline.json"

# 豁免：动效三张（坐标与控制器耦合，单独评估）、装饰图标页、三张模板骨架
EXEMPT = {"icons.html", "template-dark.html", "template-motion.html", "template-terminal.html",
           "example-loop-terminal.html"}  # 终端外壳页：无 eyebrow/.frame 标准页解剖（同 template-terminal）
EXEMPT_SUFFIX = "-animated"

EYEBROW_RE = re.compile(r"\.(?:header-)?eyebrow\s*\{([^}]*)\}")
H1_RE = re.compile(r"(?:^|\})\s*h1\s*\{([^}]*)\}")
FRAME_RE = re.compile(r"\.frame\s*\{([^}]*)\}")
FOOTER_RE = re.compile(r"\.footer\s*\{([^}]*)\}")
CARDS_RE = re.compile(r"\.cards\s*\{([^}]*)\}")
VIEWBOX_RE = re.compile(r'<svg[^>]*\bviewBox="0 0 (\d+)')

DIMS = ("eyebrow.font-size", "eyebrow.margin-bottom",
        "h1.font-size", "h1.margin-bottom",
        "frame.padding-left", "viewBox.width")
FULL_DIMS = ("footer.margin-top", "cards.margin-top")  # 页脚/卡区元素只在 full 版存在

# 方向已定的维度不走多数派，直接量目标值——否则快照会把「已迁移的少数派」
# 错标成问题侧（h1 下距 3rem 是新档时多数派还是 1.5rem 存量）。目标值来源：
# style-guide 角色表（eyebrow-text 12px）与「容器对齐与画布基线」节（3rem / full 层间档），
# 规矩定稿升级时同步改这里。
TARGETS = {
    ("标准+dark", "eyebrow.font-size"): "0.75rem",
    ("full", "eyebrow.font-size"): "0.75rem",
    ("标准+dark", "h1.margin-bottom"): "3rem",
    ("full", "h1.margin-bottom"): "1.5rem",
    ("full", "footer.margin-top"): "1rem",
    ("full", "cards.margin-top"): "2rem",
}

# —— 间距锚（style-guide「容器对齐与画布基线」节：分隔线距内容底 56）——
# 图例分隔线（全宽发丝横线）应距其上方最下内容底 56（±4 容差，文字底按基线+3 估）。
# 「内容」不含发丝级网格/刻度（宽 ≤0.8 的细线全视为 chrome——gantt 周刻度、
# 折线/柱状网格都在此类），轴线与数据连线（宽 ≥1）算内容。
HAIRLINE_STROKES = ("rgba(41,49,79,0.10)", "rgba(224,228,255,0.10)", "rgba(224,228,255,0.12)")
AXIS_STROKES = ("rgba(41,49,79,0.30)", "rgba(224,228,255,0.30)")  # 坐标轴 = chrome，不算内容
GAP_TARGET, GAP_TOL = 56.0, 4.0


def hairline(source: str) -> tuple[float, float] | None:
    """返回（最低图例分隔线的 y, 右端 x2）；识别不了返回 None。"""
    m_vb = re.search(r'<svg[^>]*\bviewBox="0 0 ([\d.]+) ([\d.]+)"', source)
    if not m_vb:
        return None
    canvas_h = float(m_vb.group(2))
    best = None
    for m in re.finditer(r"<line\s+[^>]*>", source):
        tag = m.group(0)
        xy = {a: re.search(rf'{a}="([-\d.]+)"', tag) for a in ("x1", "y1", "x2", "y2")}
        stroke = re.search(r'stroke="([^"]+)"', tag)
        width = re.search(r'stroke-width="([\d.]+)"', tag)
        if not all(xy.values()) or not stroke:
            continue
        x1, y1, x2, y2 = (float(c.group(1)) for c in xy.values())
        w = float(width.group(1)) if width else 1.0
        if (y1 == y2 and stroke.group(1) in HAIRLINE_STROKES
                and w <= 0.8 and abs(x2 - x1) >= 600 and y1 > 0.5 * canvas_h):
            if best is None or y1 > best[0]:
                best = (y1, max(x1, x2))
    return best


def legend_gap(source: str) -> float | None:
    anchor = hairline(source)
    if anchor is None:
        return None
    hairline_y = anchor[0]

    bottom = 0.0
    for m in re.finditer(r"<rect\s+[^>]*>", source):
        tag = m.group(0)
        coords = {a: re.search(rf'{a}="([-\d.]+)"', tag) for a in ("y", "height")}
        if all(coords.values()):
            y, h = float(coords["y"].group(1)), float(coords["height"].group(1))
            if y + h < hairline_y:
                bottom = max(bottom, y + h)
    for m in re.finditer(r"<text\s+[^>]*>", source):
        y = re.search(r'\by="([-\d.]+)"', m.group(0))
        if y and float(y.group(1)) + 3 < hairline_y:
            bottom = max(bottom, float(y.group(1)) + 3)
    for m in re.finditer(r"<circle\s+[^>]*>", source):
        cy, r = re.search(r'\bcy="([-\d.]+)"', m.group(0)), re.search(r'\br="([\d.]+)"', m.group(0))
        if cy and float(cy.group(1)) + float(r.group(1) if r else 4) < hairline_y:
            bottom = max(bottom, float(cy.group(1)) + float(r.group(1) if r else 4))
    for m in re.finditer(r"<polygon\s+[^>]*>", source):
        pts = re.search(r'points="([^"]+)"', m.group(0))
        if not pts:
            continue
        nums = [float(v) for v in re.findall(r"-?\d+\.?\d*", pts.group(1))]
        ys = nums[1::2]
        if not ys:
            continue
        span = max(ys) - min(ys)
        if span < 16:
            continue  # marker/微型箭头不算内容
        if max(ys) < hairline_y:
            bottom = max(bottom, max(ys))
    for m in re.finditer(r"<line\s+[^>]*>", source):
        tag = m.group(0)
        xy = {a: re.search(rf'{a}="([-\d.]+)"', tag) for a in ("y1", "y2")}
        if not all(xy.values()):
            continue
        stroke = re.search(r'stroke="([^"]+)"', tag)
        width = re.search(r'stroke-width="([\d.]+)"', tag)
        w = float(width.group(1)) if width else 1.0
        is_chrome = (w <= 0.8 or (stroke and stroke.group(1) in HAIRLINE_STROKES)
                     or (stroke and stroke.group(1) in AXIS_STROKES))
        if not is_chrome and max(float(xy["y1"].group(1)), float(xy["y2"].group(1))) < hairline_y:
            bottom = max(bottom, float(xy["y1"].group(1)), float(xy["y2"].group(1)))
    gap = hairline_y - bottom
    return gap if 0 < gap < 200 else None


# —— 三档齐全守卫（二元检查，不走棘轮）——
# assets/ 里每个 example-{类型} 基名必须三档齐全（std/dark/full）。
# 白名单点名豁免，新类型落不全三档 = FAIL，防「类型加了、变体忘了」。
TRIO_EXEMPT = {
    "example-mindmap": "孤儿资产：有 example 无文档无路由，等拍板",
    "example-loop-terminal": "终端皮肤变体，单档（终端九 token 固定色板，无深浅分档）",
    "example-paved-road-animated": "动效示例，单档",
    "example-policy-trace-animated": "动效示例，单档",
    "example-queue-animated": "动效示例，单档",
    "example-axonometric-plan-campus-animated": "动效示例，单档",
    "example-exploded-phone-animated": "动效示例，单档",
    "example-exploded-unboxing-animated": "动效示例，单档",
}


def check_trios() -> list[str]:
    groups: dict[str, set[str]] = {}
    for f in ASSETS.glob("example-*.html"):
        base = f.name.removesuffix(".html")
        base = re.sub(r"-(dark|full)$", "", base)
        kind = "full" if f.stem.endswith("-full") else ("dark" if f.stem.endswith("-dark") else "std")
        groups.setdefault(base, set()).add(kind)
    problems = []
    for base in sorted(groups):
        if base in TRIO_EXEMPT:
            continue
        missing = {"std", "dark", "full"} - groups[base]
        if missing:
            problems.append(f"{base} 缺 {'/'.join(sorted(missing))} 档")
    for base in sorted(TRIO_EXEMPT):
        if base not in groups:
            problems.append(f"白名单 {base} 已不存在——该行该删了")
    return problems


def prop(block: str, name: str) -> str:
    m = re.search(rf"{name}\s*:\s*([^;]+)", block)
    return re.sub(r"\s+", " ", m.group(1)).strip() if m else "<缺>"


def fingerprint(path: Path) -> dict[str, str]:
    source = path.read_text(encoding="utf-8")
    eyebrow = EYEBROW_RE.search(source)
    h1 = H1_RE.search(source)
    frame = FRAME_RE.search(source)
    footer = FOOTER_RE.search(source)
    cards = CARDS_RE.search(source)
    vb = VIEWBOX_RE.search(source)
    return {
        "eyebrow.font-size": prop(eyebrow.group(1), "font-size") if eyebrow else "<缺>",
        "eyebrow.margin-bottom": prop(eyebrow.group(1), "margin-bottom") if eyebrow else "<缺>",
        "h1.font-size": prop(h1.group(1), "font-size") if h1 else "<缺>",
        "h1.margin-bottom": prop(h1.group(1), "margin-bottom") if h1 else "<缺>",
        "frame.padding-left": prop(frame.group(1), "padding-left") if frame else "<缺>",
        "footer.margin-top": prop(footer.group(1), "margin-top") if footer else "<缺>",
        "cards.margin-top": prop(cards.group(1), "margin-top") if cards else "<缺>",
        "has_subtitle": "有" if re.search(r'class="subtitle"', source) else "无",
        "viewBox.width": vb.group(1) if vb else "<缺>",
    }


def scan() -> list[dict]:
    """返回全部漂移项：[{cohort, file, dim, value, mode}]。多数派按 (档位, 维度) 统计。"""
    files = sorted(
        f for f in ASSETS.glob("example-*.html")
        if f.name not in EXEMPT and not f.stem.endswith(EXEMPT_SUFFIX)
    )
    if not files:
        raise SystemExit(f"没找到资产：{ASSETS}")
    prints = {f: fingerprint(f) for f in files}
    findings: list[dict] = []
    for dim in DIMS + FULL_DIMS:  # FULL_DIMS 在标准档全为 <缺>，由 TARGETS/多数派管不到——单独跳过
        by_cohort: dict[str, list[Path]] = {}
        for f in files:
            cohort = "full" if f.stem.endswith("-full") else "标准+dark"
            if dim in FULL_DIMS and cohort != "full":
                continue
            by_cohort.setdefault(cohort, []).append(f)
        for cohort, cohort_files in by_cohort.items():
            values = Counter(prints[f][dim] for f in cohort_files)
            mode, _ = values.most_common(1)[0]
            target = TARGETS.get((cohort, dim))
            for f in cohort_files:
                ruler = target if target is not None else mode
                # 页面带可见副题时（与 full 版式同一条）：h1→副题 1.5rem、副题→图 4rem
                if (dim == "h1.margin-bottom" and cohort == "标准+dark"
                        and prints[f]["has_subtitle"] == "有"):
                    ruler = "1.5rem"
                if prints[f][dim] != ruler:
                    findings.append({
                        "cohort": cohort, "file": f.name, "dim": dim,
                        "value": prints[f][dim], "mode": ruler,
                    })

    # 间距锚：图例分隔线距最下内容底 56（style-guide 容器对齐节）
    # 图例线右缘：贯通 0→画布右缘（图块底边满宽；2026-08-22 line 首例——full 卡片通栏
    # 参照下，内容右缘 948-984 各自为政的留白带现形，先立「底边满宽」再逐图收内容右缘）
    for f in files:
        cohort = "full" if f.stem.endswith("-full") else "标准+dark"
        source = f.read_text(encoding="utf-8")
        anchor = hairline(source)
        if anchor is not None:
            x2 = int(round(anchor[1]))
            if x2 != 1000:
                findings.append({
                    "cohort": cohort, "file": f.name, "dim": "图例线右缘",
                    "value": str(x2), "mode": "1000",
                })
        gap = legend_gap(source)
        if gap is not None and abs(gap - GAP_TARGET) > GAP_TOL:
            findings.append({
                "cohort": cohort, "file": f.name, "dim": "图例锚56",
                "value": f"{gap:g}", "mode": f"{GAP_TARGET:g}",
            })
    return findings


def key_of(f: dict) -> tuple:
    return (f["cohort"], f["file"], f["dim"], f["value"], f["mode"])


def load_baseline() -> list[dict]:
    if not BASELINE.is_file():
        return []
    return json.loads(BASELINE.read_text(encoding="utf-8"))["findings"]


def save_baseline(findings: list[dict]) -> None:
    reasons = {key_of(f): f.get("reason", "") for f in load_baseline()}
    for f in findings:
        f["reason"] = reasons.get(key_of(f), "")
    BASELINE.write_text(
        json.dumps({"updated": date.today().isoformat(), "findings": findings},
                   ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--update-baseline", action="store_true",
                    help="用当前扫描结果重写基线快照（保留已写 reason）")
    args = ap.parse_args()

    findings = scan()
    trios = check_trios()
    if trios:
        for t in trios:
            print(f"FAIL（三档不全） {t}")
        print()
    if args.update_baseline:
        save_baseline(findings)
        print(f"基线已更新：{len(findings)} 条漂移项冻结进 {BASELINE.name}")
        return 1 if trios else 0

    baseline = load_baseline()
    if not baseline:
        # 首跑（无基线）：全部漂移项原样报错，供 --update-baseline 冻结
        for f in findings:
            print(f"- [{f['cohort']}] {f['file']}  {f['dim']}={f['value']}（多数派 {f['mode']}）")
        print(f"\n共 {len(findings)} 条漂移项——确认后用 --update-baseline 冻结为待改清单")
        return 1 if findings else 0

    base_keys = {key_of(f) for f in baseline}
    now_keys = {key_of(f) for f in findings}
    new = [f for f in findings if key_of(f) not in base_keys]
    fixed = base_keys - now_keys

    for f in new:
        print(f"FAIL（新漂移） [{f['cohort']}] {f['file']}  {f['dim']}={f['value']}（多数派 {f['mode']}）")
    for k in sorted(fixed):
        print(f"✓ 已消 [{k[0]}] {k[1]}  {k[2]} {k[3]}→{k[4]}（基线可收缩）")
    for f in findings:
        if key_of(f) in now_keys and key_of(f) in base_keys and not new:
            pass  # 静默；汇总行给出余量
    print(f"\n基线余量 {len(now_keys & base_keys)} 条待改 / 本次新漂移 {len(new)} 条 / 本轮消除 {len(fixed)} 条")
    if new:
        print("新漂移必须处理：改资产归一，或有设计理由则 --update-baseline 并补 reason")
    return 1 if (new or trios) else 0


if __name__ == "__main__":
    sys.exit(main())
