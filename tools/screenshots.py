"""按源内容哈希更新公开截图；默认跳过未变示例，支持 --only 与 --force。"""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

PUBLIC = Path(__file__).resolve().parent.parent
SKILL = PUBLIC / "skills/diagram-design-zh"


def fingerprint(path):
    digest = hashlib.sha256(path.read_bytes())
    for helper in ("export.py", "html_tools.py"):
        digest.update((SKILL / "scripts" / helper).read_bytes())
    digest.update(b"whole-page-scale-1")
    return digest.hexdigest()


def export(only=None, force=False, browser=None):
    catalog = json.loads((SKILL / "references/catalog.json").read_text())
    available = {item["id"] for item in catalog["types"]}
    if only and not set(only) <= available:
        raise ValueError("未知类型：" + str(sorted(set(only) - available)))
    directory = PUBLIC / "screenshots"
    directory.mkdir(exist_ok=True)
    manifest = directory / "source-hashes.json"
    cache = json.loads(manifest.read_text()) if manifest.exists() else {}
    for item in catalog["types"]:
        name = item["id"]
        if only and name not in only:
            continue
        source = SKILL / item["example"]
        target = directory / (name + ".png")
        key = fingerprint(source)
        if not force and target.exists() and cache.get(name) == key:
            print("跳过未变示例 " + name)
            continue
        args = [
            sys.executable,
            str(SKILL / "scripts/export.py"),
            str(source),
            "--format",
            "png",
            "--page",
            "--scale",
            "1",
            "-o",
            str(target),
        ]
        if browser:
            args += ["--browser-executable", browser]
        subprocess.run(args, check=True)
        cache[name] = key
        temporary = manifest.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(cache, indent=2) + "\n")
        temporary.replace(manifest)
    return cache


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--only", nargs="+")
    p.add_argument("--force", action="store_true")
    p.add_argument("--browser-executable")
    a = p.parse_args()
    try:
        export(a.only, a.force, a.browser_executable)
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        print("FAIL：" + str(exc))
        sys.exit(1)
