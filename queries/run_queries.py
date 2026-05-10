"""Run a battery of Solr queries against the books collection.

Used both for documenting the lab observations and for measuring query
latency. The output is human-readable and is also captured into
`queries/results.txt` for inclusion in the deliverable.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen

SOLR = "http://localhost:8983/solr/books/select"
HERE = Path(__file__).resolve().parent
LOG = HERE / "results.txt"

QUERIES: list[tuple[str, dict]] = [
    ("Q1  full-text 'python'",
     {"q": "python", "fl": "id,title,price", "rows": 5}),
    ("Q2  edismax 'java' boosted",
     {"q": "java", "defType": "edismax",
      "qf": "title^4 description^2 authors^2 tags",
      "fl": "id,title,score", "rows": 5}),
    ("Q3  phrase 'Definitive Guide'",
     {"q": 'title:"Definitive Guide"', "fl": "id,title", "rows": 10}),
    ("Q4  wildcard title:Pyth*",
     {"q": "title:Pyth*", "fl": "id,title"}),
    ("Q5  numeric range price [20..50]",
     {"q": "*:*", "fq": "price:[20 TO 50]",
      "fl": "id,title,price", "rows": 20, "sort": "price asc"}),
    ("Q6  date range publish_date>=2018",
     {"q": "*:*",
      "fq": "publish_date:[2018-01-01T00:00:00Z TO NOW]",
      "sort": "publish_date desc",
      "fl": "id,title,publish_date", "rows": 10}),
    ("Q7  boolean filter in_stock:true && rating>=4.5",
     {"q": "*:*", "fq": ["in_stock:true", "rating:[4.5 TO *]"],
      "fl": "id,title,rating", "rows": 20}),
    ("Q8  facets per category & publisher",
     {"q": "*:*", "rows": 0, "facet": "true",
      "facet.field": ["category", "publisher", "tags"],
      "facet.mincount": 1, "facet.limit": 20}),
    ("Q9  range facet on price",
     {"q": "*:*", "rows": 0, "facet": "true",
      "facet.range": "price",
      "facet.range.start": 0, "facet.range.end": 200, "facet.range.gap": 20}),
    ("Q10 highlight 'design'",
     {"q": "design", "hl": "true", "hl.fl": "title,description",
      "hl.simple.pre": "<mark>", "hl.simple.post": "</mark>",
      "fl": "id,title", "rows": 5}),
    ("Q11 sorting by rating desc, price asc",
     {"q": "*:*", "sort": "rating desc, price asc",
      "fl": "id,title,rating,price", "rows": 5}),
    ("Q12 grouping by category",
     {"q": "*:*", "group": "true", "group.field": "category",
      "group.limit": 2, "fl": "id,title,category"}),
    ("Q13 stats on price",
     {"q": "*:*", "rows": 0, "stats": "true",
      "stats.field": "{!min=true max=true mean=true sum=true}price"}),
    ("Q14 shard info",
     {"q": "*:*", "rows": 0, "shards.info": "true"}),
    ("Q15 combined UI-style query",
     {"q": "systems", "defType": "edismax",
      "qf": "title^4 description^2 authors^2 tags^1.5 category",
      "fq": ["in_stock:true", "price:[* TO 60]"],
      "facet": "true", "facet.field": ["category", "publisher"],
      "facet.range": "price", "facet.range.start": 0,
      "facet.range.end": 200, "facet.range.gap": 20,
      "hl": "true", "hl.fl": "title,description",
      "hl.simple.pre": "<mark>", "hl.simple.post": "</mark>",
      "sort": "score desc, rating desc",
      "start": 0, "rows": 5}),
]


def _flatten(params: dict) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for k, v in params.items():
        if isinstance(v, list):
            for item in v:
                out.append((k, str(item)))
        else:
            out.append((k, str(v)))
    return out


def run(label: str, params: dict, log) -> None:
    flat = _flatten(params)
    url = f"{SOLR}?{urlencode(flat, doseq=False)}"
    started = time.perf_counter()
    with urlopen(url, timeout=30) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    elapsed_ms = (time.perf_counter() - started) * 1000
    qtime = payload.get("responseHeader", {}).get("QTime")
    n = payload.get("response", {}).get("numFound")
    grouped = payload.get("grouped")
    line = (
        f"\n--- {label} ---\n"
        f"URL     : {url}\n"
        f"QTime   : {qtime} ms (server)   wall: {elapsed_ms:7.2f} ms\n"
        f"numFound: {n}{'  (grouped)' if grouped else ''}\n"
    )
    print(line)
    log.write(line)
    log.write(json.dumps(payload, indent=2)[:2000])
    log.write("\n... [truncated] ...\n" if len(json.dumps(payload)) > 2000 else "\n")


def main() -> None:
    with LOG.open("w", encoding="utf-8") as log:
        log.write("# Solr query results\n")
        for label, params in QUERIES:
            try:
                run(label, params, log)
            except Exception as exc:
                msg = f"\n--- {label} ---\nERROR: {exc!r}\n"
                print(msg)
                log.write(msg)
    print(f"\nWrote detailed results to {LOG}")


if __name__ == "__main__":
    main()
