"""品牌数据档案存取与项目选择；不写技能安装目录，不执行档案正文。"""

from __future__ import annotations
import argparse
from datetime import date
import json
from pathlib import Path
import re
import sys
from style_config import default_config, load_config
from reskin import DEFAULT_CONFIG

SLUG = re.compile(r"[a-z0-9][a-z0-9-]{0,63}")
FIELDS = ("colors", "fonts", "typography")


def slug(value, mutable=False):
    if not SLUG.fullmatch(value) or (mutable and value == "default"):
        raise ValueError("非法/保留档案 slug")
    return value


def profile_path(library, name):
    slug(name)
    if name == "default":
        return DEFAULT_CONFIG
    for extension in (".json", ".md"):
        path = library / (name + extension)
        if path.is_file():
            return path
    raise ValueError(f"缺少档案 {name}")


def resolve(project, library):
    marker = project / ".diagram-design"
    if not marker.exists():
        return DEFAULT_CONFIG
    source = marker.read_text()
    match = re.fullmatch(
        r"[ \t]*profile:[ \t]*([a-z0-9][a-z0-9-]{0,63})[ \t]*\n?", source
    )
    if not match:
        raise ValueError("项目标记须恰好一行 profile: <slug>")
    return profile_path(library, match[1])


def overrides(data):
    base = default_config()
    out = {"schema": 1}
    for field in FIELDS:
        if field in data:
            different = {
                k: v for k, v in data[field].items() if v != base[field].get(k)
            }
            if different:
                out[field] = different
    return out


def save(library, name, source, update=False, migrate=False):
    slug(name, True)
    target = library / (name + ".json")
    if target.exists() and not update:
        raise ValueError("档案已存在；更新须显式 update")
    if update and not target.exists():
        raise ValueError("更新目标不存在")
    data = load_config(source)
    out = overrides(data)
    old = json.loads(target.read_text()) if target.exists() else {}
    today = date.today().isoformat()
    out.update(
        {
            "name": data.get("name", old.get("name", name)),
            "slug": name,
            "created": old.get("created", data.get("created", today)),
            "updated": today,
        }
    )
    for key in ("notes", "source-url"):
        if key in data or key in old:
            out[key] = data.get(key, old.get(key))
    library.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n")
    try:
        load_config(temporary)
        temporary.replace(target)
    finally:
        if temporary.exists():
            temporary.unlink()
    return target


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "command",
        choices=[
            "resolve",
            "show",
            "list",
            "save",
            "update",
            "load",
            "switch",
            "reset",
            "delete",
            "migrate",
        ],
    )
    p.add_argument("name", nargs="?")
    p.add_argument("--source", type=Path)
    p.add_argument("--project", type=Path, default=Path.cwd())
    p.add_argument(
        "--library", type=Path, default=Path.home() / ".diagram-design/profiles"
    )
    a = p.parse_args()
    try:
        if a.command in {"resolve", "show"}:
            path = resolve(a.project, a.library)
            print(
                path
                if a.command == "resolve"
                else json.dumps(load_config(path), ensure_ascii=False, indent=2)
            )
        elif a.command == "list":
            print("default（当前技能默认）")
            if a.library.exists():
                for name in sorted(
                    {
                        x.stem
                        for x in a.library.iterdir()
                        if x.suffix in {".json", ".md"}
                        and SLUG.fullmatch(x.stem)
                        and x.stem != "default"
                    }
                ):
                    path = profile_path(a.library, name)
                    try:
                        load_config(path)
                        print(f"{name} · {path}")
                    except ValueError as exc:
                        print(f"{name} · invalid：{exc}")
        elif a.command in {"save", "update", "migrate"}:
            if not a.name or not a.source:
                raise ValueError("需要确切 slug 与 --source 数据文件/旧档案")
            print(
                save(
                    a.library,
                    a.name,
                    a.source,
                    update=a.command == "update",
                    migrate=a.command == "migrate",
                )
            )
        elif a.command in {"load", "switch", "reset"}:
            name = "default" if a.command == "reset" else a.name
            if not name:
                raise ValueError("需要确切 slug")
            source = profile_path(a.library, name)
            load_config(source)
            marker = a.project / ".diagram-design"
            marker.write_text(f"profile: {name}\n")
            print(marker)
        elif a.command == "delete":
            if not a.name:
                raise ValueError("需要确切 slug")
            slug(a.name, True)
            path = profile_path(a.library, a.name)
            if (a.project / ".diagram-design").exists() and resolve(
                a.project, a.library
            ) == path:
                raise ValueError("当前项目正在使用该档案；先显式选择其他档案")
            path.unlink()
            print(f"已删除 {path}")
        return 0
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print(f"FAIL：{exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
