# Dataset

The dataset used for this lab is a curated **technical-books catalogue** containing **40 records** of computer-science / software-engineering titles.

It exercises every field type supported in the schema:

| Field          | Type      | Purpose                                    |
| -------------- | --------- | ------------------------------------------ |
| `id`           | string    | Unique key                                 |
| `title`        | text_en   | Stemmed full-text + highlighting           |
| `description`  | text_en   | Stemmed full-text + highlighting           |
| `authors`      | string \* | Multi-valued, facet-friendly               |
| `category`     | string    | Faceting / filtering                       |
| `tags`         | string \* | Multi-valued faceting                      |
| `publisher`    | string    | Faceting / filtering                       |
| `language`     | string    | Filtering                                  |
| `pages`        | pint      | Range queries / sort                       |
| `price`        | pfloat    | Range queries / sort                       |
| `rating`       | pfloat    | Range queries / sort                       |
| `in_stock`     | boolean   | Boolean filter                             |
| `publish_date` | pdate     | Range / sort by date                       |
| `text`         | text_general | Catch-all copy field for `q=` queries   |
| `suggest`      | text_suggest | EdgeNGram copy field for autocomplete  |

\* multi-valued

The same data is supplied in two formats to demonstrate Solr's multi-format ingestion capability:

- `books.json` – primary source, indexed via the `/update` JSON handler
- `books.csv`  – flat representation, demonstrating CSV import via `/update/csv`
