"""Convert the canonical books.json dataset into Solr-friendly CSV.

Multi-valued fields (authors, tags) are joined with a pipe character so that
they can be re-split during indexing using f.authors.split=true&f.authors.separator=|.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE / "books.json"
DEST = HERE / "books.csv"

MULTI_VALUED = {"authors", "tags"}
SEPARATOR = "|"

with SRC.open(encoding="utf-8") as f:
    rows = json.load(f)

fieldnames = [
    "id", "title", "authors", "category", "tags", "publisher", "language",
    "pages", "price", "rating", "in_stock", "publish_date", "description",
]

with DEST.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL)
    writer.writeheader()
    for row in rows:
        flat = {}
        for k in fieldnames:
            v = row.get(k, "")
            if k in MULTI_VALUED and isinstance(v, list):
                v = SEPARATOR.join(v)
            flat[k] = v
        writer.writerow(flat)

print(f"Wrote {len(rows)} rows -> {DEST}")
