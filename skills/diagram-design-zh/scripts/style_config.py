"""读取生效样式指南的颜色表；只解析数据，不执行 Markdown 或元数据。"""

from __future__ import annotations

from pathlib import Path
import re
import json
from copy import deepcopy

import reskin

REQUIRED = {
    "paper",
    "paper-2",
    "ink",
    "muted",
    "soft",
    "rule",
    "accent",
    "accent-tint",
    "link",
}
DARK_NAMES = {
    "paper": "dark-bg",
    "paper-2": "paper-2-dark",
    "ink": "paper-dark",
    "muted": "muted-dark",
    "soft": "soft-dark",
    "accent": "accent-dark",
    "link": "link-dark",
}
COLOR_RE = re.compile(r"#[0-9a-fA-F]{6}\b|rgba?\([^)]*\)")


def markdown_colors(path: Path) -> dict[str, tuple[str, tuple[int, int, int]]]:
    """从角色色板读取浅深值；语义族和系列族只接受既有已登记值。"""
    source = path.read_text(encoding="utf-8")
    found, colors, alphas = set(), {}, {}
    section, fenced = "", False
    for line in source.splitlines():
        if re.match(r"^\s*```", line):
            fenced = not fenced
            continue
        if fenced:
            continue
        if line.startswith("## "):
            section = line[3:].strip()
        if section != "色板（语义角色）":
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if not line.startswith("|") or len(cells) < 4:
            continue
        role = cells[0].strip("` ")
        if role not in REQUIRED:
            continue
        if role in found:
            raise ValueError(f"样式指南角色重复：{role}")
        found.add(role)
        for index, mode in ((2, "light"), (3, "dark")):
            match = COLOR_RE.search(cells[index])
            if not match:
                raise ValueError(f"样式指南 {role} 的 {mode} 列缺有效颜色")
            value = reskin.parse_color(match.group())
            slot = role if mode == "light" else DARK_NAMES.get(role, role + "-dark")
            colors[slot] = value
            raw = match.group()
            alpha = (
                float(raw.rstrip(")").split(",")[-1])
                if raw.startswith("rgba(")
                else 1.0
            )
            if not 0 <= alpha <= 1:
                raise ValueError(f"样式指南 {role} 的透明度不在 0..1")
            alphas[slot] = alpha
    if missing := REQUIRED - found:
        raise ValueError(f"样式指南缺颜色角色：{sorted(missing)}")
    return validate_colors(colors)


def validate_colors(colors):
    alphas = {
        k: float(v[0].rstrip(")").split(",")[-1]) if v[0].startswith("rgba(") else 1.0
        for k, v in colors.items()
    }
    if any(not 0 <= a <= 1 for a in alphas.values()):
        raise ValueError("颜色透明度须在 0..1")
    for background in ("paper", "dark-bg"):
        if alphas[background] != 1:
            raise ValueError(
                f"样式指南 {background} 须为不透明纸面，不能假定未声明的背板色"
            )

    def ratio_on(foreground, background):
        fore, back = colors[foreground][1], colors[background][1]
        alpha = alphas[foreground]
        composite = tuple(alpha * f + (1 - alpha) * b for f, b in zip(fore, back))
        return reskin.contrast(composite, back)

    for foreground, background in [
        ("ink", "paper"),
        ("muted", "paper"),
        ("paper-dark", "dark-bg"),
        ("muted-dark", "dark-bg"),
    ]:
        ratio = ratio_on(foreground, background)
        if ratio < 4.5:
            raise ValueError(
                f"样式指南 {foreground} 对 {background} 对比度 {ratio:.2f} < 4.5"
            )
    for foreground, background in [("accent", "paper"), ("accent-dark", "dark-bg")]:
        if colors[foreground][1] in {
            colors["ink" if background == "paper" else "paper-dark"][1],
            colors["muted" if background == "paper" else "muted-dark"][1],
        }:
            raise ValueError(f"样式指南 {foreground} 与文本角色撞色")
        ratio = ratio_on(foreground, background)
        if ratio < 3:
            raise ValueError(
                f"样式指南 {foreground} 对 {background} 图形对比度 {ratio:.2f} < 3"
            )
    return colors


def default_config():
    return deepcopy(reskin.DEFAULT_DATA)


def load_config(path: Path):
    """数据档案叠加当前默认；旧 Markdown 只提取数据，正文规则不载入。"""
    data = default_config()
    if path.suffix.lower() == ".json" or path.name.endswith(".json.tmp"):
        override = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(override, dict) or (
            type(override.get("schema")) is not int or override.get("schema") != 1
        ):
            raise ValueError("不支持的样式 schema")
        allowed = {
            "schema",
            "name",
            "slug",
            "created",
            "updated",
            "notes",
            "source-url",
            "colors",
            "fonts",
            "typography",
        }
        if path.resolve() == reskin.DEFAULT_CONFIG.resolve():
            allowed |= {"pinned", "skin_slots", "terminal_neutrals"}
        if set(override) - allowed:
            raise ValueError(
                "样式档案包含非数据字段：" + str(sorted(set(override) - allowed))
            )
        for field in ("colors", "fonts", "typography"):
            values = override.get(field, {})
            if not isinstance(values, dict) or set(values) - set(data[field]):
                raise ValueError(f"未知 {field} 角色")
            data[field].update(values)
        for key in ("name", "slug", "created", "updated", "notes", "source-url"):
            if key in override:
                if not isinstance(override[key], str) or any(
                    c in override[key] for c in "\r\n"
                ):
                    raise ValueError(f"元数据 {key} 必须是单行文本")
                data[key] = override[key]
    else:
        data["colors"].update({k: v[0] for k, v in markdown_colors(path).items()})
        source = path.read_text(encoding="utf-8")
        header = re.search(r"<!--\s*diagram-design-profile\s*\n(.*?)-->", source, re.S)
        if header:
            for line in header[1].splitlines():
                key, separator, value = line.partition(":")
                if separator and key.strip() in {
                    "name",
                    "slug",
                    "created",
                    "updated",
                    "notes",
                    "source-url",
                }:
                    data[key.strip()] = value.strip()
        role_section = (
            source.split("## 排版角色表", 1)[-1].split("## ", 1)[0]
            if "## 排版角色表" in source
            else ""
        )
        for line in role_section.splitlines():
            cells = [v.strip().strip("`") for v in line.strip("|").split("|")]
            if (
                len(cells) == 6
                and cells[0] in data["typography"]
                and re.fullmatch(r"\d+", cells[3])
            ):
                data["typography"][cells[0]] = {
                    "stack": cells[1].split()[0],
                    "sizes": re.findall(
                        r"\d+(?:\.\d+)?(?:[–-]\d+(?:\.\d+)?)?(?:px|rem|em)", cells[2]
                    ),
                    "weight": int(cells[3]),
                    "tracking": cells[4].split("+")[0].strip(),
                    "uppercase": "uppercase" in cells[4],
                }
        for role in data["fonts"]:
            values = re.findall(r"--font-" + role + r"\s*:\s*([^;\n]+)", source)
            if values:
                data["fonts"][role] = values[0].strip()
    if any(not isinstance(v, str) for v in data["colors"].values()):
        raise ValueError("颜色角色值必须是颜色字符串")
    base = default_config()
    for role, parent in [
        ("rule", "ink"),
        ("rule-dark", "paper-dark"),
        ("accent-tint", "accent"),
        ("accent-tint-dark", "accent-dark"),
    ]:
        if (
            data["colors"][role] == base["colors"][role]
            and data["colors"][parent] != base["colors"][parent]
        ):
            _, rgb = reskin.parse_color(data["colors"][parent])
            alpha = base["colors"][role].rstrip(")").split(",")[-1]
            data["colors"][role] = f"rgba({rgb[0]},{rgb[1]},{rgb[2]},{alpha})"
    for role, value in data["fonts"].items():
        if (
            not isinstance(value, str)
            or not value.strip()
            or re.search(r"[;{}<>\r\n]", value)
        ):
            raise ValueError(f"非法 {role} 字体栈")
    for role, values in data["typography"].items():
        if not isinstance(values, dict) or set(values) != {
            "stack",
            "sizes",
            "weight",
            "tracking",
            "uppercase",
        }:
            raise ValueError(f"非法排版角色 {role}")
        if (
            values["stack"] not in {"sans", "serif", "mono"}
            or type(values["weight"]) is not int
            or not 100 <= values["weight"] <= 900
        ):
            raise ValueError("非法排版栈或字重")
        if (
            not isinstance(values["sizes"], list)
            or not values["sizes"]
            or any(
                not isinstance(v, str)
                or not re.fullmatch(
                    r"\d+(?:\.\d+)?(?:[–-]\d+(?:\.\d+)?)?(?:px|rem|em)", v
                )
                for v in values["sizes"]
            )
        ):
            raise ValueError("非法字号")
        if (
            not isinstance(values["tracking"], str)
            or not re.fullmatch(
                r"[+-]?(?:\d+(?:\.\d+)?|\.\d+)(?:px|em|rem)?", values["tracking"]
            )
            or type(values["uppercase"]) is not bool
        ):
            raise ValueError("非法字距/大小写数据")
    if any(not isinstance(v, str) for v in data["colors"].values()):
        raise ValueError("颜色角色值必须是颜色字符串")
    parsed = {k: reskin.parse_color(v) for k, v in data["colors"].items()}
    validate_colors(parsed)
    return data


def load_style_colors(path: Path):
    return {k: reskin.parse_color(v) for k, v in load_config(path)["colors"].items()}
