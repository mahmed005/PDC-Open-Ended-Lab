/* SolrShelf front-end controller.
 *
 * Listens for user input, calls /api/search and /api/suggest, and renders the
 * results, facet sidebar, range histogram and pagination. Keeps a single
 * `state` object that mirrors the Solr query so the UI is one rendering pass
 * away from "share-able" search permalinks.
 */

const state = {
  q: "",
  page: 1,
  page_size: window.PAGE_SIZE_DEFAULT || 10,
  sort: "relevance",
  category: new Set(),
  publisher: new Set(),
  tag: new Set(),
  in_stock: false,
  price_min: "",
  price_max: "",
  rating_min: 0,
};

let suggestTimer = null;
let searchTimer = null;
let lastResponse = null;

function $(id) { return document.getElementById(id); }

function buildQS() {
  const p = new URLSearchParams();
  if (state.q) p.set("q", state.q);
  p.set("page", state.page);
  p.set("page_size", state.page_size);
  p.set("sort", state.sort);
  if (state.in_stock) p.set("in_stock", "true");
  if (state.price_min !== "") p.set("price_min", state.price_min);
  if (state.price_max !== "") p.set("price_max", state.price_max);
  if (state.rating_min > 0) p.set("rating_min", state.rating_min);
  state.category.forEach(v => p.append("category", v));
  state.publisher.forEach(v => p.append("publisher", v));
  state.tag.forEach(v => p.append("tag", v));
  return p.toString();
}

async function search() {
  try {
    const r = await fetch("/api/search?" + buildQS());
    const data = await r.json();
    lastResponse = data;
    render(data);
  } catch (err) {
    $("hits").innerHTML = `<li class="hit"><h3 class="hit-title">Search failed</h3><div class="hit-desc">${err}</div></li>`;
  }
}

function debouncedSearch() {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(search, 200);
}

/* ----- rendering ----- */

function escapeHtml(s) {
  return String(s)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function renderHits(data) {
  const ul = $("hits");
  if (!data.docs.length) {
    ul.innerHTML = `<li class="hit"><h3 class="hit-title">No matches</h3>
      <div class="hit-desc">Try adjusting filters or simplifying your query.</div></li>`;
    return;
  }
  ul.innerHTML = data.docs.map(d => {
    const title = d.title_hl || escapeHtml(d.title || "");
    const desc  = d.description_hl || escapeHtml((d.description || "").slice(0, 240));
    const authors = (d.authors || []).map(escapeHtml).join(", ");
    const tags = (d.tags || []).slice(0, 6)
      .map(t => `<span class="pill tag">#${escapeHtml(t)}</span>`).join("");
    const stockPill = d.in_stock
      ? `<span class="pill in-stock">In stock</span>`
      : `<span class="pill out-stock">Out of stock</span>`;
    const date = (d.publish_date || "").slice(0, 10);
    return `
      <li class="hit">
        <div class="hit-header">
          <div style="flex:1; min-width:0;">
            <h3 class="hit-title">${title}</h3>
            <div class="hit-authors">${authors}</div>
            <div class="hit-desc">${desc}</div>
            <div class="hit-meta">
              <span class="pill">${escapeHtml(d.category || "")}</span>
              <span class="pill">${escapeHtml(d.publisher || "")}</span>
              <span class="pill">${d.pages || 0} pages</span>
              <span class="pill">${escapeHtml(date)}</span>
              ${stockPill}
              ${tags}
            </div>
          </div>
          <div class="hit-side">
            <span class="hit-price">$${(d.price || 0).toFixed(2)}</span>
            <span class="hit-rating">★ ${(d.rating || 0).toFixed(1)}</span>
            <span style="font-size:11px;color:var(--muted)">${escapeHtml(d.id)}</span>
          </div>
        </div>
      </li>`;
  }).join("");
}

function renderFacet(name, fcCounts, container, selectedSet, label) {
  const el = $(container);
  const flat = [];
  for (let i = 0; i < (fcCounts || []).length; i += 2) {
    flat.push([fcCounts[i], fcCounts[i + 1]]);
  }
  if (!flat.length) { el.innerHTML = `<li><em style="color:var(--muted)">no values</em></li>`; return; }
  el.innerHTML = flat.map(([val, n]) => {
    const active = selectedSet.has(val) ? "active" : "";
    return `<li class="${active}" data-val="${escapeHtml(val)}">
      <span>${escapeHtml(val)}</span><span class="count">${n}</span>
    </li>`;
  }).join("");
  el.querySelectorAll("li").forEach(li => {
    li.addEventListener("click", () => {
      const v = li.dataset.val;
      if (selectedSet.has(v)) selectedSet.delete(v);
      else selectedSet.add(v);
      state.page = 1;
      search();
    });
  });
}

function renderPriceHistogram(facet) {
  const el = $("priceBars");
  const r = (facet.facet_ranges || {}).price;
  if (!r || !r.counts || !r.counts.length) {
    $("rangeFacet").hidden = true;
    return;
  }
  $("rangeFacet").hidden = false;
  const pairs = [];
  for (let i = 0; i < r.counts.length; i += 2) pairs.push([r.counts[i], r.counts[i + 1]]);
  const max = Math.max(1, ...pairs.map(p => p[1]));
  el.innerHTML = pairs.map(([from, n]) => {
    const next = Number(from) + Number(r.gap);
    const pct = Math.round((n / max) * 100);
    return `<div class="bar" style="height:${Math.max(4, pct)}%"
                  data-label="$${from}-$${next}: ${n}"></div>`;
  }).join("");
}

function renderPager(numFound) {
  const total = Math.ceil(numFound / state.page_size);
  const cur = state.page;
  if (total <= 1) { $("pager").innerHTML = ""; return; }
  const buttons = [];
  buttons.push(`<button ${cur === 1 ? "disabled" : ""} data-p="${cur - 1}">Prev</button>`);
  const window_ = 2;
  const start = Math.max(1, cur - window_);
  const end   = Math.min(total, cur + window_);
  if (start > 1) buttons.push(`<button data-p="1">1</button>${start > 2 ? "<span style='color:var(--muted)'>...</span>" : ""}`);
  for (let i = start; i <= end; i++) {
    buttons.push(`<button class="${i === cur ? "active" : ""}" data-p="${i}">${i}</button>`);
  }
  if (end < total) buttons.push(`${end < total - 1 ? "<span style='color:var(--muted)'>...</span>" : ""}<button data-p="${total}">${total}</button>`);
  buttons.push(`<button ${cur === total ? "disabled" : ""} data-p="${cur + 1}">Next</button>`);
  $("pager").innerHTML = buttons.join("");
  $("pager").querySelectorAll("button[data-p]").forEach(b =>
    b.addEventListener("click", () => { state.page = Number(b.dataset.p); search(); }));
}

function renderSpell(spell) {
  const collations = ((spell || {}).collations) || [];
  const c = collations.find(x => typeof x === "string" && x !== "collation") || null;
  // Solr returns ["collation","corrected text", ...] in NamedList format.
  let suggestion = null;
  for (let i = 0; i < collations.length; i++) {
    if (collations[i] === "collation" && typeof collations[i + 1] === "string") {
      suggestion = collations[i + 1]; break;
    }
    if (collations[i] && typeof collations[i] === "object" && collations[i].collationQuery) {
      suggestion = collations[i].collationQuery; break;
    }
  }
  if (suggestion && lastResponse && lastResponse.numFound === 0 && state.q) {
    $("spell").hidden = false;
    $("spell").innerHTML = `Did you mean <a href="#" id="spellLink">${escapeHtml(suggestion)}</a>?`;
    $("spellLink").addEventListener("click", e => {
      e.preventDefault();
      $("q").value = suggestion;
      state.q = suggestion;
      state.page = 1;
      search();
    });
  } else {
    $("spell").hidden = true;
  }
}

function render(data) {
  const qt = (data.header || {}).QTime;
  $("meta").textContent = `${data.numFound} results in ${qt} ms (Solr QTime)`;
  $("rawSolrLink").href = data.solr_url;
  renderHits(data);
  renderPager(data.numFound);
  renderSpell(data.spellcheck);
  renderPriceHistogram(data.facets || {});
  const ff = (data.facets || {}).facet_fields || {};
  renderFacet("category",  ff.category,  "facet-category",  state.category, "Category");
  renderFacet("publisher", ff.publisher, "facet-publisher", state.publisher, "Publisher");
  renderFacet("tags",      ff.tags,      "facet-tags",      state.tag, "Tag");
}

/* ----- autocomplete ----- */

async function suggest(term) {
  if (!term) { $("suggest").hidden = true; return; }
  try {
    const r = await fetch("/api/suggest?q=" + encodeURIComponent(term));
    const data = await r.json();
    const list = data.suggestions || [];
    if (!list.length) { $("suggest").hidden = true; return; }
    $("suggest").innerHTML = list.map(t => `<li data-v="${escapeHtml(t)}">${escapeHtml(t)}</li>`).join("");
    $("suggest").hidden = false;
    $("suggest").querySelectorAll("li").forEach(li => {
      li.addEventListener("click", () => {
        $("q").value = li.dataset.v;
        state.q = li.dataset.v;
        state.page = 1;
        $("suggest").hidden = true;
        search();
      });
    });
  } catch (e) { $("suggest").hidden = true; }
}

/* ----- cluster status ----- */

async function loadCluster() {
  try {
    const r = await fetch("/api/cluster");
    const data = await r.json();
    const live = (data.cluster || {}).live_nodes || [];
    const colls = Object.keys((data.cluster || {}).collections || {});
    $("cluster").innerHTML =
      `<span class="ok">&#9679; SolrCloud</span>\n` +
      `${live.length} live nodes\n` +
      `${colls.length} collection(s)`;
  } catch {
    $("cluster").innerHTML = `<span class="err">&#9679; Solr offline</span>`;
  }
}

/* ----- wire up ----- */

window.addEventListener("DOMContentLoaded", () => {
  loadCluster();
  setInterval(loadCluster, 15000);

  $("q").addEventListener("input", e => {
    state.q = e.target.value.trim();
    state.page = 1;
    clearTimeout(suggestTimer);
    suggestTimer = setTimeout(() => suggest(state.q), 120);
    debouncedSearch();
  });
  $("q").addEventListener("blur", () => setTimeout(() => $("suggest").hidden = true, 150));

  $("searchBtn").addEventListener("click", search);
  $("q").addEventListener("keydown", e => {
    if (e.key === "Enter") { $("suggest").hidden = true; search(); }
    if (e.key === "Escape") { $("suggest").hidden = true; }
  });

  $("sort").addEventListener("change", e => { state.sort = e.target.value; state.page = 1; search(); });
  $("pageSize").addEventListener("change", e => { state.page_size = Number(e.target.value); state.page = 1; search(); });
  $("inStock").addEventListener("change", e => { state.in_stock = e.target.checked; state.page = 1; search(); });
  $("priceMin").addEventListener("change", e => { state.price_min = e.target.value; state.page = 1; search(); });
  $("priceMax").addEventListener("change", e => { state.price_max = e.target.value; state.page = 1; search(); });
  $("ratingMin").addEventListener("input", e => {
    state.rating_min = e.target.value;
    $("ratingMinLabel").textContent = Number(e.target.value).toFixed(1);
    state.page = 1;
    debouncedSearch();
  });
  $("resetBtn").addEventListener("click", () => {
    state.category.clear(); state.publisher.clear(); state.tag.clear();
    state.in_stock = false; state.price_min = ""; state.price_max = "";
    state.rating_min = 0; state.q = ""; state.page = 1;
    $("q").value = ""; $("inStock").checked = false;
    $("priceMin").value = ""; $("priceMax").value = "";
    $("ratingMin").value = 0; $("ratingMinLabel").textContent = "0.0";
    $("sort").value = "relevance"; state.sort = "relevance";
    search();
  });

  search();
});

// Test / automation hooks - allow Playwright (and the browser console) to
// drive the UI without racing the input-event listeners.
window.SolrShelf = {
  state,
  search,
  setQuery(term) { state.q = term; state.page = 1; document.getElementById("q").value = term; search(); },
};
