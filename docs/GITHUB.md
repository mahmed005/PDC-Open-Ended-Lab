# Pushing this lab to GitHub

Step-by-step instructions to publish `pdc-open-ended-lab` to your GitHub
account and include the resulting URL in the report.

## 0. Prerequisites

* `git` installed and on PATH (`git --version` should print 2.x).
* A GitHub account.
* A new (empty) repository on GitHub. Suggested settings:
  * **Name:** `pdc-open-ended-lab` (or `cs347-lab13-solr`)
  * **Visibility:** Public (the lab brief asks for a shareable link)
  * **Initialise with README:** No (we already have one)
  * **.gitignore / license:** None (we will add manually if needed)

## 1. Create a `.gitignore` (one-time)

From PowerShell, in the project root:

```powershell
@'
__pycache__/
*.pyc
.venv/
.idea/
.vscode/
node_modules/

# Solr runtime artefacts (we keep configset/, but not generated indexes)
*.log
solr.log*
*-console.log
**/data/
**/zoo_data/
**/*_replica_*/

# Python / pip cache
.pytest_cache/

# OS junk
Thumbs.db
.DS_Store
'@ | Set-Content .gitignore -Encoding UTF8
```

## 2. Initialise the repo and make the first commit

```powershell
cd C:\Users\PMLS\Desktop\pdc-open-ended-lab

git init
git branch -M main
git add .
git commit -m "Lab 13: Apache Solr indexing, search and Flask web UI"
```

If `git config user.name` / `user.email` are not set yet, git will prompt
you. Configure once with:

```powershell
git config --global user.name  "Your Name"
git config --global user.email "your.email@example.com"
```

## 3. Connect the local repo to GitHub

Replace `<YOUR-USERNAME>` and `<REPO-NAME>` with your values:

```powershell
git remote add origin https://github.com/<YOUR-USERNAME>/<REPO-NAME>.git
git push -u origin main
```

If GitHub asks for a password, use a **personal access token** (Settings ->
Developer Settings -> Personal access tokens -> Fine-grained tokens) with
`repo: contents: read & write` scope.

## 4. (Optional) Enable GitHub Actions to keep the report in sync

Not required by the brief, but helpful: add a workflow that re-runs
`docs/generate_report.py` whenever `screenshots/` or `dataset/` changes. A
minimal example would live at `.github/workflows/report.yml`.

## 5. Take the link

After `git push`, the repository will be browsable at:

```
https://github.com/<YOUR-USERNAME>/<REPO-NAME>
```

Paste that URL into:

* the report's **§9 Repository Layout** section (just below the directory tree), and
* the LMS submission text alongside the `Lab_13_Report.docx` upload.

## 6. Verify the deliverable

* `git status` should print "nothing to commit, working tree clean".
* On GitHub, the README.md should render and screenshots should be visible
  under `screenshots/`.
* Click `Lab_13_Report.docx` in GitHub; the file should download.

## What NOT to commit

The repo intentionally excludes:

* `*-console.log`, `solr.log*` - Solr runtime logs
* `**/data/`, `**/zoo_data/` - on-disk Lucene index + ZooKeeper state
* `**/*_replica_*` - per-node replica directories Solr writes when a
  collection is created

Your `.gitignore` (created in step 1) takes care of all of these.
