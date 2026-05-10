# Example Solr Queries (Books Collection)

All examples target the `books` collection running on the local SolrCloud
cluster (`localhost:8983` + `localhost:7574`, sharded into 2 shards × 2
replicas).

> Tip: the request handler is `/select`. JSON output shown below was captured
> from a live cluster.

---

## 1. Basic full-text query (default search field)

```http
GET http://localhost:8983/solr/books/select?q=python&rows=5&fl=id,title,price
```

The `text` catch-all field is the default `df`, so `q=python` matches across
title, description, tags, authors, category and publisher.

---

## 2. eDisMax with field boosting

```http
GET http://localhost:8983/solr/books/select?
       q=java
      &defType=edismax
      &qf=title^4 description^2 authors^2 tags
      &fl=id,title,authors,score
      &rows=5
```

`title` matches are weighted 4× higher than tag matches via `qf`.

---

## 3. Phrase query

```http
GET http://localhost:8983/solr/books/select?q=title:"Definitive Guide"&rows=10&fl=id,title
```

Exact-phrase match against the analysed title field.

---

## 4. Wildcard / prefix query

```http
GET http://localhost:8983/solr/books/select?q=title:Pyth*&fl=id,title
```

---

## 5. Range query (numeric)

```http
GET http://localhost:8983/solr/books/select?q=*:*&fq=price:[20 TO 50]&fl=id,title,price&rows=20
```

---

## 6. Range query (date)

```http
GET http://localhost:8983/solr/books/select?q=*:*&fq=publish_date:[2018-01-01T00:00:00Z TO NOW]&sort=publish_date desc&fl=id,title,publish_date
```

---

## 7. Boolean filter

```http
GET http://localhost:8983/solr/books/select?q=*:*&fq=in_stock:true&fq=rating:[4.5 TO *]&fl=id,title,rating
```

---

## 8. Multiple filter queries (cached separately)

```http
GET http://localhost:8983/solr/books/select?
       q=*:*
      &fq=category:"Software Engineering"
      &fq=in_stock:true
      &fq=price:[* TO 50]
      &fl=id,title,price,category
```

Each `fq` is independently cached in the filter cache, making complex multi-
predicate queries fast.

---

## 9. Sorting

```http
GET http://localhost:8983/solr/books/select?q=*:*&sort=rating desc, price asc&fl=id,title,rating,price&rows=10
```

---

## 10. Faceted search (field facets)

```http
GET http://localhost:8983/solr/books/select?
       q=*:*
      &rows=0
      &facet=true
      &facet.field=category
      &facet.field=publisher
      &facet.field=in_stock
      &facet.field=tags
      &facet.mincount=1
      &facet.limit=20
```

Returns counts per category, publisher, stock status, and tag.

---

## 11. Range facets (price histogram)

```http
GET http://localhost:8983/solr/books/select?
       q=*:*
      &rows=0
      &facet=true
      &facet.range=price
      &facet.range.start=0
      &facet.range.end=200
      &facet.range.gap=20
```

---

## 12. Hit highlighting

```http
GET http://localhost:8983/solr/books/select?
       q=design
      &hl=true
      &hl.fl=title,description
      &hl.simple.pre=<mark>
      &hl.simple.post=</mark>
      &fl=id,title
```

`<mark>...</mark>` snippets are returned next to each matched document.

---

## 13. Pagination (start / rows)

```http
GET http://localhost:8983/solr/books/select?q=*:*&start=10&rows=10&fl=id,title
```

---

## 14. Cursor-mark deep paging (production-grade)

```http
GET http://localhost:8983/solr/books/select?
       q=*:*
      &sort=id asc
      &rows=10
      &cursorMark=*
```

The response includes `nextCursorMark` to paginate beyond 10 000 docs without
the deep-paging penalty of `start=`.

---

## 15. Grouping by category

```http
GET http://localhost:8983/solr/books/select?
       q=*:*
      &group=true
      &group.field=category
      &group.limit=3
      &fl=id,title,category
```

---

## 16. Stats component

```http
GET http://localhost:8983/solr/books/select?
       q=*:*
      &rows=0
      &stats=true
      &stats.field={!min=true max=true mean=true sum=true}price
      &stats.field={!mean=true}rating
```

---

## 17. Spell-checking / suggestions

```http
GET http://localhost:8983/solr/books/select?
       q=algorthm
      &spellcheck=true
      &spellcheck.collate=true
```

`/select` already wires the `default` spellchecker (`_text_` / `text` field).

---

## 18. Autocomplete (edge-ngram)

```http
GET http://localhost:8983/solr/books/select?
       q=suggest:rust
      &fl=id,title
      &rows=5
```

The `suggest` field is an EdgeNGram-tokenised copy of title, authors, tags,
and category; it powers the type-ahead box in the Flask UI.

---

## 19. Distributed shard inspection

```http
GET http://localhost:8983/solr/books/select?q=*:*&rows=0&shards.info=true
```

Shows per-shard QTime and elapsed time for the request — useful for verifying
that both shards participate in a query.

---

## 20. Combined "real-world" query (UI-style)

```http
GET http://localhost:8983/solr/books/select?
       q=systems
      &defType=edismax
      &qf=title^4 description^2 authors^2 tags^1.5 category
      &fq=in_stock:true
      &fq=price:[* TO 60]
      &facet=true
      &facet.field=category
      &facet.field=publisher
      &facet.range=price&facet.range.start=0&facet.range.end=200&facet.range.gap=20
      &hl=true&hl.fl=title,description&hl.simple.pre=<mark>&hl.simple.post=</mark>
      &sort=score desc, rating desc
      &start=0&rows=10
```

This query exercises eDisMax + multiple filter queries + faceting + range
facet + highlighting + pagination + sorting in one request — exactly what the
Flask web UI issues on every search.
