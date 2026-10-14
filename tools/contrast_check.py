#!/usr/bin/env python3
"""对比度闸——style-guide token 契约的实算守卫。

契约出处 style-guide「质量门」节：ink 对 paper 须达 WCAG AA（4.5:1）、
muted 对 paper 在 11px+ 文本上须达 AA；accent / link 属关键标记，下限 3:1。
token 值从 style-guide.md 的表里实时解析（颜色唯一权威），表结构变了这里
会报缺——改表要连带过闸。

soft 两档是契约外角色（子标签/边界标签，浅档 3.00:1、终端档 2.76:1），
只打印实算值不拦截；是否纳入契约或调值属设计决策，待拍板后把对应
配对挪进 CONTRACT 即可。

用法：python3 tools/contrast_check.py   （在仓库根目录）
与 family_check.py 并跑，作为资产验收的第三道程序闸。
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent / "skills/diagram-design-zh"
STYLE_GUIDE = REPO / "references" / "style-guide.md"

AA_TEXT = 4.5
MARKS = 3.0

# (前景 token, 背景 token, 下限, 语义说明) —— soft 不在契约里，见模块 docstring
CONTRACT = [
    ("ink", "paper", AA_TEXT, "主文本/主描边"),
    ("muted", "paper", AA_TEXT, "次文本（11px+ 文本 AA）"),
    ("accent", "paper", MARKS, "焦点关键标记"),
    ("link", "paper", MARKS, "HTTP/API 关键标记"),
]
INFO_ONLY = [("soft", "paper", "子标签/边界标签——契约外，是否纳入待拍板")]

TERMINAL_CONTRACT = [
    ("terminal-ink", "terminal-paper", AA_TEXT, "终端主文本"),
    ("terminal-muted", "terminal-paper", AA_TEXT, "终端次文本"),
    ("terminal-accent", "terminal-paper", MARKS, "终端焦点标记"),
]
TERMINAL_INFO = [("terminal-soft", "terminal-paper", "终端三级（非活动装饰点）——契约外")]


def luminance(hex_color: str) -> float:
    value = hex_color.lstrip("#")
    channels = [int(value[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    linear = [v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4 for v in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def contrast(fore: str, back: str) -> float:
    lf, lb = luminance(fore), luminance(back)
    hi, lo = max(lf, lb), min(lf, lb)
    return (hi + 0.05) / (lo + 0.05)


def parse_tokens() -> tuple[dict[tuple[str, str], str], list[str]]:
    """从 style-guide 表解析 token 值。

    返回 {(token, 档位): hex}，档位 light/dark 取自九角色表的两值列，
    terminal 取自终端表的单值列。缺 token 记入第二返回值。
    """
    text = STYLE_GUIDE.read_text(encoding="utf-8")
    values: dict[tuple[str, str], str] = {}
    missing: list[str] = []
    for line in text.splitlines():
        row = re.match(r"^\|\s*`([\w-]+)`\s*\|", line)
        if not row:
            continue
        token = row.group(1)
        hexes = re.findall(r"#([0-9a-fA-F]{6})\b", line)
        if token in {"paper", "paper-2", "ink", "muted", "soft", "accent", "link"}:
            if len(hexes) >= 2:
                values[(token, "light")], values[(token, "dark")] = "#" + hexes[0], "#" + hexes[1]
        elif token.startswith("terminal-"):
            if hexes:
                values[(token, "terminal")] = "#" + hexes[0]
    for token in ("paper", "ink", "muted", "soft", "accent", "link"):
        for scheme in ("light", "dark"):
            if (token, scheme) not in values:
                missing.append(f"{token}（{scheme}）")
    for token in ("terminal-paper", "terminal-ink", "terminal-muted", "terminal-soft", "terminal-accent"):
        if (token, "terminal") not in values:
            missing.append(token)
    return values, missing


def report(scheme: str, contract: list, info: list, values: dict, failures: list[str]) -> None:
    label = {"light": "浅色档", "dark": "深色档", "terminal": "终端档"}[scheme]
    print(f"\n== {label} ==")
    for fore, back, floor, why in contract:
        ratio = contrast(values[(fore, scheme)], values[(back, scheme)])
        ok = ratio >= floor
        mark = "PASS" if ok else "FAIL"
        print(f"  {mark}  {fore:16s} on {back:16s} {ratio:5.2f}:1  (下限 {floor}:1，{why})")
        if not ok:
            failures.append(f"{label} {fore} 对 {back} = {ratio:.2f}:1，低于下限 {floor}:1（{why}）")
    for fore, back, why in info:
        ratio = contrast(values[(fore, scheme)], values[(back, scheme)])
        print(f"  INFO  {fore:16s} on {back:16s} {ratio:5.2f}:1  ({why})")


def main() -> int:
    if not STYLE_GUIDE.is_file():
        print(f"找不到 style-guide：{STYLE_GUIDE}")
        return 1
    values, missing = parse_tokens()
    if missing:
        print(f"style-guide 表缺 token，先修 SOT 再过闸：{missing}")
        return 1
    failures: list[str] = []
    for scheme in ("light", "dark"):
        report(scheme, CONTRACT, INFO_ONLY, values, failures)
    report("terminal", TERMINAL_CONTRACT, TERMINAL_INFO, values, failures)
    print("\n" + ("对比度闸：全过" if not failures else "对比度闸：FAIL"))
    for failure in failures:
        print("  - " + failure)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
