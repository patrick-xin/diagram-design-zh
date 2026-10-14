"""公开 checkout 可复现的结构、资源、样式、家族与工具回归检查入口。"""

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys

PUBLIC = Path(__file__).resolve().parent.parent
ROOT = PUBLIC / "skills/diagram-design-zh"
sys.path.insert(0, str(ROOT / "scripts"))
from self_check import verify
from style_config import load_config
from embed_fonts import EMBED_RE
import build_gallery


def structural_checks():
    errors = []
    warnings = []
    for path in sorted((ROOT / "assets").glob("*.html")):
        mode = (
            "gallery"
            if path.name == "index.html"
            else "decorative" if path.name == "icons.html" else "diagram"
        )
        e, w = verify(
            path, mode=mode, gallery_template=PUBLIC / "tools/gallery_template.html"
        )
        errors.extend(f"{path.name}：{x}" for x in e)
        warnings.extend(f"{path.name}：{x}" for x in w)
    catalog = json.loads((ROOT / "references/catalog.json").read_text())
    ids = [x["id"] for x in catalog["types"]]
    if len(ids) != len(set(ids)):
        errors.append("类型清单 ID 重复")
    entry = (ROOT / "SKILL.md").read_text()
    routed = set(re.findall(r"references/type-([\w-]+)\.md", entry))
    if routed != set(ids):
        errors.append(f"入口与资源清单类型不符：{sorted(routed^set(ids))}")
    readme = (PUBLIC / "README.md").read_text()
    declared = re.findall(r"badge/types-(\d+)-|(?<!\d)(\d+)\s*种(?:图表)?类型", readme)
    if any(int(a or b) != len(ids) for a, b in declared):
        errors.append("README 类型计数与资源清单不同步")
    heading = re.search(r"类型路由（(\d+) 内置）", entry)
    if not heading or int(heading[1]) != len(ids):
        errors.append("入口类型计数与资源清单不同步")
    for item in catalog["types"]:
        for key in ("reference", "example"):
            if not (ROOT / item[key]).is_file():
                errors.append("资源缺失：" + item[key])
        for name in item["variants"]:
            if not (ROOT / "assets" / ("example-" + name + ".html")).is_file():
                errors.append("变体缺失：" + name)
    for path in PUBLIC.rglob("*.md"):
        for target in re.findall(r"(?<!!)\[[^\]]*\]\(([^)]+)\)", path.read_text()):
            local = target.split("#")[0]
            if not local or re.match(r"[a-z][a-z0-9+.-]*:", local):
                continue
            if not (path.parent / local).exists():
                errors.append(f"{path.relative_to(PUBLIC)} 链接失效：{target}")
    data = load_config(ROOT / "styles/default.json")
    guide = load_config(ROOT / "references/style-guide.md")
    for key in ("colors", "fonts", "typography"):
        if data[key] != guide[key]:
            errors.append("指南与默认配置不同步：" + key)
    existing = (ROOT / "assets/index.html").read_text()

    def normalize(s):
        return EMBED_RE.sub("", s).strip()

    if normalize(existing) != normalize(build_gallery.build()):
        errors.append("画廊与生成源不同步，请重建并内嵌字体")
    return errors, warnings


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--tests", action="store_true")
    a = p.parse_args()
    try:
        errors, warnings = structural_checks()
    except (OSError, ValueError, KeyError) as exc:
        errors = [str(exc)]
        warnings = []
    for message in errors:
        print("FAIL " + message)
    for message in warnings:
        print("WARN " + message)
    if errors:
        return 1
    for script in ("family_check.py", "contrast_check.py"):
        run = subprocess.run(
            [sys.executable, str(PUBLIC / "tools" / script)],
            cwd=PUBLIC,
            capture_output=True,
            text=True,
        )
        if run.returncode:
            print(run.stdout + run.stderr)
            return 1
        print(run.stdout.strip())
    if a.tests:
        run = subprocess.run(
            [
                sys.executable,
                "-m",
                "unittest",
                "discover",
                "-s",
                str(PUBLIC / "tests"),
                "-v",
            ],
            cwd=PUBLIC,
        )
        if run.returncode:
            return run.returncode
    print(
        f'OK 项目检查：{len(list((ROOT/"assets").glob("*.html")))} HTML，{len(warnings)} 警告'
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
