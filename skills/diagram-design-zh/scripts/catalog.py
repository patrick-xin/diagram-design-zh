"""按类型/变体名称发现参考与示例；不加载无关正文。"""

import argparse
import json
from pathlib import Path

CATALOG = Path(__file__).resolve().parent.parent / "references/catalog.json"


def search(query):
    data = json.loads(CATALOG.read_text())
    terms = query.casefold().split()
    return [
        item
        for item in data["types"]
        if all(
            term
            in " ".join(
                [item["name"], item["id"], *item["aliases"], *item["variants"]]
            ).casefold()
            for term in terms
        )
    ]


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("query", nargs="?", default="")
    a = p.parse_args()
    print(json.dumps(search(a.query), ensure_ascii=False, indent=2))
