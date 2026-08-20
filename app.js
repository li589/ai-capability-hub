/* AI 能力整合包 · 展示站 — interactions
   Loads skills.json (generated from manifest.csv), renders the archive browser. */
(function () {
  "use strict";

  var TOOL_COLORS = {
    "qoder-work": "oklch(0.58 0.150 42)",   // terracotta
    "workbuddy":  "oklch(0.52 0.078 200)",  // teal
    "trae-cn":    "oklch(0.79 0.095 88)",   // gold
    "trae":       "oklch(0.55 0.060 130)",  // olive
    "qoder":      "oklch(0.52 0.100 350)",  // plum
    "qoder-cn":   "oklch(0.62 0.110 280)"   // violet
  };
  var FALLBACK = "oklch(0.6 0.05 250)";

  var PAGE = 60;
  var state = { data: null, q: "", cap: "all", rendered: 0 };

  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };

  function fmt(n) { return n.toLocaleString("en-US"); }

  function renderFigures(d) {
    var t = d.totals;
    var figs = [
      { n: fmt(t.packages), l: "能力包 Packages" },
      { n: fmt(t.files), l: "文件 Files" },
      { n: String(t.tools), l: "来源工具 Source tools" },
      { n: String(t.capabilities), l: "能力类型 Capability types" }
    ];
    $(".figures").innerHTML = figs.map(function (f) {
      return '<div class="figure"><div class="n">' + f.n + '</div><div class="l">' + f.l + "</div></div>";
    }).join("");
  }

  function renderSources(d) {
    var total = d.totals.packages;
    var bar = $(".sources-bar");
    var legend = $(".legend");
    bar.innerHTML = "";
    legend.innerHTML = "";
    d.by_source_tool.forEach(function (s) {
      var col = TOOL_COLORS[s.tool] || FALLBACK;
      var pct = (s.count / total * 100).toFixed(2);
      var seg = document.createElement("span");
      seg.style.background = col;
      seg.style.width = pct + "%";
      seg.title = s.tool + " — " + fmt(s.count);
      bar.appendChild(seg);

      var item = document.createElement("div");
      item.className = "item";
      item.innerHTML =
        '<span class="sw" style="background:' + col + '"></span>' +
        '<span class="nm">' + s.tool + '</span>' +
        '<span class="ct">' + fmt(s.count) + "</span>";
      legend.appendChild(item);
    });
  }

  function renderChips(d) {
    var box = $(".chips");
    var all = [{ cap: "all", count: d.totals.packages, label: "全部 All" }];
    var caps = d.by_capability.map(function (c) {
      return { cap: c.cap, count: c.count, label: c.cap };
    });
    box.innerHTML = "";
    all.concat(caps).forEach(function (c) {
      var b = document.createElement("button");
      b.className = "chip";
      b.setAttribute("aria-pressed", c.cap === "all" ? "true" : "false");
      b.dataset.cap = c.cap;
      b.innerHTML = c.label + ' <span class="c">' + fmt(c.count) + "</span>";
      b.addEventListener("click", function () {
        state.cap = c.cap;
        $$(".chip", box).forEach(function (x) {
          x.setAttribute("aria-pressed", x.dataset.cap === c.cap ? "true" : "false");
        });
        resetAndRender();
      });
      box.appendChild(b);
    });
  }

  function matches(p) {
    if (state.cap !== "all" && p.cap !== state.cap) return false;
    var q = state.q.trim().toLowerCase();
    if (!q) return true;
    return (p.name + " " + p.cap + " " + p.cat + " " + p.tool + " " + p.path)
      .toLowerCase().indexOf(q) !== -1;
  }

  function rowHTML(p) {
    return (
      '<a class="row" href="' + p.url + '" target="_blank" rel="noopener">' +
        '<div class="r-main">' +
          '<div class="r-name">' + escapeHTML(p.name) +
            '<span class="ext">' + escapeHTML(p.cap) + "</span></div>" +
          '<div class="r-tags">' +
            '<span class="tag cap">' + escapeHTML(p.cat) + "</span>" +
            '<span class="tag tool">' + escapeHTML(p.tool) + "</span>" +
            '<span class="tag">' + escapeHTML(p.path) + "</span>" +
          "</div>" +
        "</div>" +
        '<div class="r-go">在 GitHub 查看' +
          '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14M13 6l6 6-6 6"/></svg>' +
        "</div>" +
      "</a>"
    );
  }

  function escapeHTML(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  function resetAndRender() {
    state.rendered = 0;
    var list = state.data.packages.filter(matches);
    var box = $(".results");
    box.innerHTML = "";
    if (!list.length) {
      box.innerHTML = '<div class="empty">未找到匹配的能力包 · no matches</div>';
      $(".count-pill").innerHTML = "0 / " + fmt(state.data.totals.packages);
      var lm = $(".loadmore"); if (lm) lm.remove();
      return;
    }
    state._list = list;
    renderBatch();
    $(".count-pill").innerHTML = "<b>" + fmt(list.length) + "</b> / " + fmt(state.data.totals.packages);
  }

  function renderBatch() {
    var list = state._list;
    var box = $(".results");
    var frag = document.createDocumentFragment();
    var end = Math.min(state.rendered + PAGE, list.length);
    for (var i = state.rendered; i < end; i++) {
      var tmp = document.createElement("div");
      tmp.innerHTML = rowHTML(list[i]).trim();
      frag.appendChild(tmp.firstChild);
    }
    box.appendChild(frag);
    state.rendered = end;

    var lm = $(".loadmore");
    if (state.rendered >= list.length) { if (lm) lm.remove(); return; }
    if (!lm) {
      lm = document.createElement("button");
      lm.className = "loadmore";
      lm.textContent = "加载更多 · load more";
      lm.addEventListener("click", renderBatch);
      box.parentNode.insertBefore(lm, box.nextSibling);
    }
  }

  function wireSearch() {
    var inp = $(".search input");
    var t;
    inp.addEventListener("input", function () {
      clearTimeout(t);
      t = setTimeout(function () { state.q = inp.value; resetAndRender(); }, 120);
    });
  }

  function wireReveal() {
    var els = $$(".reveal");
    if (!("IntersectionObserver" in window)) { els.forEach(function (e) { e.classList.add("in"); }); return; }
    var io = new IntersectionObserver(function (ents) {
      ents.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add("in"); io.unobserve(e.target); } });
    }, { threshold: 0.12 });
    els.forEach(function (e) { io.observe(e); });
  }

  function fillLinks(d) {
    var repo = "https://github.com/" + d.owner + "/" + d.repo;
    var zip = repo + "/archive/refs/heads/package.zip";
    $$("[data-repo]").forEach(function (a) { a.href = repo; });
    $$("[data-zip]").forEach(function (a) { a.href = zip; });
    var gen = $(".generated"); if (gen) gen.textContent = new Date().toISOString().slice(0, 10);
  }

  function init(d) {
    state.data = d;
    renderFigures(d);
    renderSources(d);
    renderChips(d);
    wireSearch();
    fillLinks(d);
    resetAndRender();
    wireReveal();
  }

  fetch("skills.json", { cache: "no-cache" })
    .then(function (r) { if (!r.ok) throw new Error("HTTP " + r.status); return r.json(); })
    .then(init)
    .catch(function (e) {
      $(".results").innerHTML =
        '<div class="empty">无法加载 skills.json（请通过 GitHub Pages 访问，而非本地 file://）。<br>' + e + "</div>";
    });
})();
