"""核对源值→SVG 属性与导入 ID→成品映射；不推断图的叙事，不执行表达式。"""

from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
import sys
from xml.etree import ElementTree as ET
from html_tools import select_svg

NUMERIC_ATTRIBUTES = {
    "x",
    "y",
    "x1",
    "x2",
    "y1",
    "y2",
    "cx",
    "cy",
    "r",
    "width",
    "height",
}


def number(value):
    if isinstance(value, bool):
        raise ValueError("布尔值不是数值")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError("数值须有限")
    return result


def verify(html, model, source_ir=None):
    if model.get("schema") != 1:
        raise ValueError("不支持的内容模型 schema")
    tree = ET.fromstring(select_svg(html).source)
    elements = {}
    errors = []
    for element in tree.iter():
        key = element.get("id")
        if key:
            if key in elements:
                errors.append(f"重复成品 id：{key}")
            elements[key] = element
    for mapping in model.get("encodings", []):
        element = elements.get(mapping["element"])
        attr = mapping["attribute"]
        key = mapping["key"]
        if element is None:
            errors.append(f'缺少数值元素 {mapping["element"]}')
            continue
        expected = number(model["values"][key]) * number(
            mapping.get("scale", 1)
        ) + number(mapping.get("offset", 0))
        if attr == "text":
            text = "".join(element.itertext()).strip()
            prefix, suffix = mapping.get("prefix", ""), mapping.get("suffix", "")
            if not text.startswith(prefix) or (suffix and not text.endswith(suffix)):
                errors.append(f"{key} 数值标签单位/前缀不符")
                continue
            raw = text[len(prefix) : len(text) - len(suffix) if suffix else None]
        elif attr in NUMERIC_ATTRIBUTES:
            raw = element.get(attr)
        else:
            raise ValueError(f"不支持的数值属性 {attr}")
        try:
            actual = number(raw)
        except (TypeError, ValueError):
            errors.append(f"{key} 的 {attr} 不是有限数值")
            continue
        # SVG coordinate rounding has a declared, bounded tolerance; no arbitrary evaluator.
        tolerance = number(mapping.get("tolerance", 0.01))
        if not 0 <= tolerance <= 1:
            raise ValueError("容差须在 0..1 SVG 单位")
        if abs(actual - expected) > tolerance:
            errors.append(
                f"{key} 的 {attr}：实测 {actual:g}，源值映射应为 {expected:g}"
            )
    if source_ir is not None:
        pages = source_ir.get("diagrams", source_ir.get("pages", []))
        if len(pages) != 1:
            raise ValueError("内容对账每次只接受一个已选图/页")
        source = pages[0]
        nodes = {x["id"]: x for x in source["nodes"]}
        edges = {x["id"]: x for x in source["edges"]}
        mapped_nodes = {}
        covered = {"node": set(), "edge": set()}
        for kind, collection in [("node", "nodes"), ("edge", "edges")]:
            inventory = nodes if kind == "node" else edges
            for record in model.get(collection, []):
                target = elements.get(record["element"])
                if target is None:
                    errors.append(f'缺少映射元素 {record["element"]}')
                    continue
                ids = record["source_ids"]
                if not ids:
                    errors.append("映射需要源 ID")
                if len(ids) > 1 and not record.get("reason"):
                    errors.append("合并映射缺少理由")
                for ident in ids:
                    if ident not in inventory:
                        errors.append(f"未知源 {kind} {ident}")
                        continue
                    if ident in covered[kind]:
                        errors.append(f"源 {kind} {ident} 重复登记")
                    covered[kind].add(ident)
                    if kind == "node":
                        mapped_nodes[ident] = record["element"]
        for record in model.get("omitted", []):
            kind = record["kind"]
            ident = record["id"]
            if kind not in covered or ident not in (nodes if kind == "node" else edges):
                errors.append("省略项不在源清单")
                continue
            if not record.get("reason"):
                errors.append(f"省略 {ident} 缺少理由")
            if ident in covered[kind]:
                errors.append(f"{ident} 同时映射和省略")
            covered[kind].add(ident)
        for kind, inventory in [("node", nodes), ("edge", edges)]:
            missing = set(inventory) - covered[kind]
            if missing:
                errors.append(f"未交代的源 {kind}：{sorted(missing)}")
        for record in model.get("edges", []):
            target = elements.get(record["element"])
            if target is None:
                continue
            for ident in record["source_ids"]:
                original = edges.get(ident)
                if original is None:
                    continue
                for attr in ("source", "target"):
                    expected = mapped_nodes.get(original[attr])
                    if expected is None or target.get("data-" + attr) != expected:
                        errors.append(f"关系 {ident} 的 {attr} 不符")
                if original.get("label"):
                    label = elements.get(record.get("label_element", ""))
                    expected = record.get("display_label", original["label"])
                    if label is None or "".join(label.itertext()).strip() != expected:
                        errors.append(f"关系 {ident} 缺可见标签/标签不符")
                    if expected != original["label"] and not record.get("reason"):
                        errors.append(f"关系 {ident} 改写标签缺理由")
        # Sequence fragments, notes, ER fields and guards require their own visible review.
        facts = model.get("source_facts")
        expected = {key: source.get(key, []) for key in ("fragments", "notes")}
        expected["fields"] = {
            key: node["fields"] for key, node in nodes.items() if node.get("fields")
        }
        if any(expected.values()) and facts != expected:
            errors.append("片段/备注/字段未完整进入 source_facts 核对记录")
    if not model.get("encodings") and source_ir is None:
        raise ValueError("空模型不能证明内容正确")
    return errors


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("html", type=Path)
    p.add_argument("--model", type=Path, required=True)
    p.add_argument("--source-ir", type=Path)
    a = p.parse_args()
    try:
        errors = verify(
            a.html.read_text(),
            json.loads(a.model.read_text()),
            json.loads(a.source_ir.read_text()) if a.source_ir else None,
        )
        for error in errors:
            print("FAIL：" + error)
        if not errors:
            print("OK 内容映射（语义取舍与真实可读性仍须审核）")
        return bool(errors)
    except (ValueError, TypeError, KeyError, OSError, ET.ParseError) as exc:
        print("FAIL：" + str(exc))
        return 1


if __name__ == "__main__":
    sys.exit(main())
