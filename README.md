# Lab 13: Indexing, Importing and Searching data in Apache Solr

End-to-end implementation of CS-347 Lab 13 (Open-Ended): Apache Solr 10
SolrCloud cluster, custom dataset, faceted/highlighted search and a Flask web
front-end.

## Topology

* SolrCloud, two nodes (`localhost:8983` + `localhost:7574`), embedded ZooKeeper.
* `books` collection: 2 shards × 2 replicas, custom `books_config` configset.
* 40 indexed documents (custom technical-books catalogue).
* Flask web UI on `http://127.0.0.1:5000`.

## Quick start

### Prerequisites

| Software            | Tested version |
| ------------------- | -------------- |
| Apache Solr         | 10.0.0         |
| Java (JDK)          | 21             |
| Python              | 3.12+          |

### 1. Start the SolrCloud cluster

```powershell
$env:JAVA_HOME = "C:\Program Files\Eclipse Adoptium\jdk-21.0.3.9-hotspot"

# Node 1 (leader) - launches embedded ZooKeeper on 9983
C:\solr-10.0.0\bin\solr.cmd start -p 8983 -s C:\solrdata\node1\solr

# Node 2 - joins the same ZooKeeper
C:\solr-10.0.0\bin\solr.cmd start -p 7574 -s C:\solrdata\node2\solr -z localhost:9983
```

Verify both nodes are live:

```powershell
(Invoke-WebRequest "http://localhost:8983/api/cluster" -UseBasicParsing).Content
```

### 2. Upload configset and create collection

```powershell
C:\solr-10.0.0\bin\solr.cmd zk upconfig `
    -d configset\conf -n books_config -z localhost:9983

Invoke-WebRequest "http://localhost:8983/solr/admin/collections?action=CREATE&name=books&numShards=2&replicationFactor=2&maxShardsPerNode=2&collection.configName=books_config" -UseBasicParsing
```

### 3. Index the dataset

```powershell
$body = Get-Content dataset\books.json -Raw
Invoke-WebRequest "http://localhost:8983/solr/books/update?commit=true" `
  -Method POST -Body $body -ContentType "application/json" -UseBasicParsing
```

Expect `numFound = 40` from `q=*:*`.

### 4. Run the example queries

```powershell
python queries\run_queries.py
```

Outputs URL, server QTime, wall-clock latency, and `numFound` for 15 representative queries (filtering, sorting, faceting, highlighting, grouping, stats, range, etc.).

### 5. Start the web UI

```powershell
python -m pip install -r web_app\requirements.txt
python web_app\app.py
# -> http://127.0.0.1:5000
```

The UI provides: search bar, real-time results, autocomplete, filters & faceted navigation (category / publisher / tag / price / rating / availability), pagination, sorting, responsive layout, and `<mark>` highlighted matches.

## Project layout

```
pdc-open-ended-lab/
├── Lab_13_Open_Ended_Lab.docx     # original problem statement (provided)
├── Lab_13_Report.docx             # final deliverable report
├── dataset/                       # JSON + CSV catalogue (40 books)
├── configset/conf/                # explicit managed-schema + solrconfig
├── queries/                       # 20 documented query patterns + harness
├── web_app/                       # Flask + vanilla JS front-end
```

## Deliverables checklist

| Item                                           | Location                          |
| ---------------------------------------------- | --------------------------------- |
| Problem statement                              | `Lab_13_Report.docx`           |
| Dataset description                            | `Lab_13_Report.docx` + `dataset/README.md` |
| Configuration details                          | `Lab_13_Report.docx` + `configset/`         |
| Implementation steps (commands + code)         | `Lab_13_Report.docx` + `queries/queries.md` |
| Observations and analysis                      | `Lab_13_Report.docx`           |
| Challenges and solutions                       | `Lab_13_Report.docx`         |
| Conclusion                                     | `Lab_13_Report.docx`        |
| GitHub repository
