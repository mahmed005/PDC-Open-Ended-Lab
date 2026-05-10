"""Flask web front-end for the books SolrCloud collection.

Implements every feature mentioned in Task 2 of the lab brief:
    * Search bar with query support
    * Real-time search (debounced JS) + autocomplete suggestions
    * Filters and faceted navigation (category, tag, in-stock, price range)
    * Pagination
    * Sorting options
    * Responsive UI design
    * Highlighted search terms

The application is intentionally a thin layer in front of Solr: every query
hits Solr directly via /select with the parameters set in `build_solr_params`.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import urlencode

import requests
from flask import Flask, jsonify, render_template, request

SOLR_URL = "http://localhost:8983/solr/books"
PAGE_SIZE_DEFAULT = 10
SORT_OPTIONS: dict[str, str] = {
    "relevance":   "score desc, rating desc",
    "rating_desc": "rating desc, price asc",
    "price_asc":   "price asc",
    "price_desc":  "price desc",
    "newest":      "publish_date desc",
    "oldest":      "publish_date asc",
    "title_asc":   "title_str asc, title asc",
}

app = Flask(__name__)


def build_solr_params(args) -> list[tuple[str, str]]:
    """Translate the HTTP form arguments into Solr query parameters.

    Returns a list of (key, value) tuples so that repeated parameters such as
    ``fq`` and ``facet.field`` are preserved.
    """
    q = args.get("q", "").strip() or "*:*"
    page = max(1, int(args.get("page", 1) or 1))
    page_size = int(args.get("page_size", PAGE_SIZE_DEFAULT) or PAGE_SIZE_DEFAULT)
    sort_key = args.get("sort", "relevance")
    sort_value = SORT_OPTIONS.get(sort_key, SORT_OPTIONS["relevance"])

    params: list[tuple[str, str]] = [
        ("q", q),
        ("defType", "edismax"),
        ("qf", "title^4 description^2 authors^2 tags^1.5 category publisher"),
        ("pf", "title^6 description^2"),
        ("start", str((page - 1) * page_size)),
        ("rows", str(page_size)),
        ("sort", sort_value),
        ("fl", "id,title,authors,category,tags,publisher,language,pages,"
                "price,rating,in_stock,publish_date,description,score"),

        ("hl", "true"),
        ("hl.fl", "title,description"),
        ("hl.simple.pre", "<mark>"),
        ("hl.simple.post", "</mark>"),
        ("hl.fragsize", "200"),

        ("facet", "true"),
        ("facet.field", "category"),
        ("facet.field", "publisher"),
        ("facet.field", "tags"),
        ("facet.field", "in_stock"),
        ("facet.mincount", "1"),
        ("facet.limit", "30"),
        ("facet.range", "price"),
        ("f.price.facet.range.start", "0"),
        ("f.price.facet.range.end", "200"),
        ("f.price.facet.range.gap", "20"),

        ("spellcheck", "true"),
        ("spellcheck.collate", "true"),
    ]

    for cat in args.getlist("category"):
        params.append(("fq", f'category:"{cat}"'))
    for tag in args.getlist("tag"):
        params.append(("fq", f'tags:"{tag}"'))
    for pub in args.getlist("publisher"):
        params.append(("fq", f'publisher:"{pub}"'))

    if args.get("in_stock") == "true":
        params.append(("fq", "in_stock:true"))

    pmin = args.get("price_min", "").strip()
    pmax = args.get("price_max", "").strip()
    if pmin or pmax:
        lo = pmin if pmin else "*"
        hi = pmax if pmax else "*"
        params.append(("fq", f"price:[{lo} TO {hi}]"))

    rmin = args.get("rating_min", "").strip()
    if rmin:
        params.append(("fq", f"rating:[{rmin} TO *]"))

    return params


def fetch_solr(params: list[tuple[str, str]]) -> dict[str, Any]:
    url = f"{SOLR_URL}/select?{urlencode(params, doseq=True)}"
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    return resp.json()


@app.route("/")
def home():
    return render_template(
        "index.html",
        sort_options=SORT_OPTIONS,
        page_size_default=PAGE_SIZE_DEFAULT,
    )


@app.route("/api/search")
def api_search():
    try:
        params = build_solr_params(request.args)
        payload = fetch_solr(params)
    except requests.HTTPError as exc:
        return jsonify({"error": f"Solr returned {exc.response.status_code}",
                        "detail": exc.response.text}), 502
    except requests.RequestException as exc:
        return jsonify({"error": "cannot reach solr", "detail": str(exc)}), 502

    docs = payload.get("response", {}).get("docs", [])
    highlights = payload.get("highlighting", {})
    for d in docs:
        h = highlights.get(d["id"], {})
        if h.get("title"):
            d["title_hl"] = h["title"][0]
        if h.get("description"):
            d["description_hl"] = h["description"][0]

    return jsonify({
        "header": payload.get("responseHeader", {}),
        "numFound": payload.get("response", {}).get("numFound", 0),
        "start":    payload.get("response", {}).get("start", 0),
        "docs":     docs,
        "facets":   payload.get("facet_counts", {}),
        "spellcheck": payload.get("spellcheck", {}),
        "solr_url": f"{SOLR_URL}/select?{urlencode(params, doseq=True)}",
    })


@app.route("/api/suggest")
def api_suggest():
    """Autocomplete endpoint backed by the EdgeNGram `suggest` field."""
    term = request.args.get("q", "").strip()
    if not term:
        return jsonify({"suggestions": []})

    params = [
        ("q", f"suggest:{term}"),
        ("fl", "title"),
        ("rows", "8"),
        ("defType", "lucene"),
    ]
    try:
        payload = fetch_solr(params)
    except requests.RequestException:
        return jsonify({"suggestions": []})

    seen: set[str] = set()
    out: list[str] = []
    for doc in payload.get("response", {}).get("docs", []):
        title = doc.get("title")
        if title and title not in seen:
            seen.add(title)
            out.append(title)
    return jsonify({"suggestions": out})


@app.route("/api/cluster")
def api_cluster():
    """Expose live SolrCloud cluster information for the status panel."""
    try:
        resp = requests.get("http://localhost:8983/api/cluster", timeout=10)
        resp.raise_for_status()
        return jsonify(resp.json())
    except requests.RequestException as exc:
        return jsonify({"error": str(exc)}), 502


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False, threaded=True)
