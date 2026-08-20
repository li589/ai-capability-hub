/* AI 能力包 · 检索站 — interactions (v2.2)
   Loads skills.json, renders an icon-rich card gallery with search, filter & pagination. */
(function () {
  "use strict";

  var PER_PAGE = 48;
  var state = { data: null, q: "", cap: "all", list: null, page: 1 };

  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };

  var ICONS = {
    skills: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3l1.8 4.7L18.5 9.5l-4.7 1.8L12 16l-1.8-4.7L5.5 9.5l4.7-1.8z"/><path d="M19 14l.8 2.2L22 17l-2.2.8L19 20l-.8-2.2L16 17l2.2-.8z"/></svg>',
    plugins: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7" rx="1.6"/><rect x="14" y="3" width="7" height="7" rx="1.6"/><rect x="3" y="14" width="7" height="7" rx="1.6"/><rect x="14" y="14" width="7" height="7" rx="1.6"/></svg>',
    connectors: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"><path d="M9 17H7A5 5 0 0 1 7 7h2"/><path d="M15 7h2a5 5 0 0 1 0 10h-2"/><path d="M8 12h8"/></svg>',
    experts: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"><circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/></svg>',
    mcps: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round"><path d="M12 3l8 4.5v9L12 21l-8-4.5v-9z"/><path d="M12 3v18M4 7.5l8 4.5 8-4.5"/></svg>',
    canvas: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M4 20h4L19 9a2 2 0 0 0-3-3L5 17z"/><path d="M14 7l3 3"/></svg>',
    design_libraries: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round"><path d="M12 3l9 5-9 5-9-5z"/><path d="M3 13l9 5 9-5"/></svg>',
    knowledges: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M5 4h11a3 3 0 0 1 3 3v13H8a3 3 0 0 1-3-3z"/><path d="M5 4v13"/></svg>',
    commands: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M5 8l4 4-4 4"/><path d="M13 16h6"/></svg>',
    _default: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round"><path d="M3 7l9-4 9 4v10l-9 4-9-4z"/><path d="M3 7l9 4 9-4M12 11v10"/></svg>'
  };
  var CAP_ZH = { skills: "技能", plugins: "插件", connectors: "连接器", experts: "专家", mcps: "MCP", canvas: "画布", design_libraries: "设计库", knowledges: "知识库", commands: "命令" };
  var GO_SVG = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M13 6l6 6-6 6"/></svg>';

  function fmt(n) { return n.toLocaleString("en-US"); }
  function esc(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

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

  function renderChips(d) {
    var box = $(".chips");
    var all = [{ cap: "all", count: d.totals.packages, label: "全部" }];
    var caps = d.by_capability.map(function (c) { return { cap: c.cap, count: c.count, label: c.cap }; });
    box.innerHTML = "";
    all.concat(caps).forEach(function (c) {
      var b = document.createElement("button");
      b.className = "chip";
      b.setAttribute("aria-pressed", c.cap === "all" ? "true" : "false");
      b.dataset.cap = c.cap;
      b.innerHTML = (CAP_ZH[c.cap] || c.label) + ' <span class="c">' + fmt(c.count) + "</span>";
      b.addEventListener("click", function () {
        state.cap = c.cap;
        $$(".chip", box).forEach(function (x) { x.setAttribute("aria-pressed", x.dataset.cap === c.cap ? "true" : "false"); });
        resetAndRender();
      });
      box.appendChild(b);
    });
  }

  function matches(p) {
    if (state.cap !== "all" && p.cap !== state.cap) return false;
    var q = state.q.trim().toLowerCase();
    if (!q) return true;
    return (p.name + " " + (p.title || "") + " " + p.desc + " " + p.cap + " " + p.cat + " " + p.tool).toLowerCase().indexOf(q) !== -1;
  }

  function cardHTML(p) {
    var ic = ICONS[p.cap] || ICONS._default;
    return (
      '<div class="card-top">' +
        '<span class="ico">' + ic + "</span>" +
        '<span class="tool-sub">' + esc(p.tool) + "</span>" +
      "</div>" +
      '<h3 class="card-title">' + esc(p.title || p.name) + "</h3>" +
      '<p class="card-desc">' + esc(p.desc) + "</p>" +
      '<div class="card-foot">' +
        '<span class="tag-cat">' + esc(CAP_ZH[p.cap] || p.cap) + "</span>" + '<span class="cat-sub">' + esc(p.cat) + "</span>" +
        '<span class="go">在 GitHub 查看 ' + GO_SVG + "</span>" +
      "</div>"
    );
  }

  function totalPages() {
    return Math.max(1, Math.ceil((state.list ? state.list.length : 0) / PER_PAGE));
  }

  function pageList(cur, total) {
    var out = [], set = {}, i, p, prev = 0;
    set[1] = true; set[total] = true;
    for (i = cur - 1; i <= cur + 1; i++) if (i >= 1 && i <= total) set[i] = true;
    for (p = 1; p <= total; p++) {
      if (set[p]) {
        if (prev && p - prev > 1) out.push("…");
        out.push(p); prev = p;
      }
    }
    return out;
  }

  function renderPage() {
    var list = state.list; if (!list) return;
    var grid = $(".grid");
    var startI = (state.page - 1) * PER_PAGE;
    var endI = Math.min(startI + PER_PAGE, list.length);
    var frag = document.createDocumentFragment();
    for (var i = startI; i < endI; i++) {
      var p = list[i];
      var a = document.createElement("a");
      a.className = "card";
      a.href = p.url; a.target = "_blank"; a.rel = "noopener";
      a.style.animationDelay = ((i - startI) * 35) + "ms";
      a.innerHTML = cardHTML(p);
      frag.appendChild(a);
    }
    grid.innerHTML = "";
    grid.appendChild(frag);
  }

  function renderPager() {
    var pager = $(".pager");
    var total = totalPages();
    if (!state.list || !state.list.length || total <= 1) { pager.innerHTML = ""; return; }
    var nums = pageList(state.page, total).map(function (p) {
      if (p === "…") return '<span class="pg-ell">…</span>';
      return '<button class="pg-num' + (p === state.page ? " cur" : "") + '" data-pg="' + p + '">' + p + "</button>";
    }).join("");
    pager.innerHTML =
      '<button class="pg" data-pg="prev"' + (state.page <= 1 ? " disabled" : "") + ">‹ 上一页</button>" +
      '<span class="pg-info">第 ' + state.page + " / " + total + " 页</span>" +
      '<div class="pg-nums">' + nums + "</div>" +
      '<button class="pg" data-pg="next"' + (state.page >= total ? " disabled" : "") + ">下一页 ›</button>";
    $$(".pg-num", pager).forEach(function (b) { b.addEventListener("click", function () { goToPage(+b.dataset.pg); }); });
    var prev = $(".pg[data-pg=prev]", pager), next = $(".pg[data-pg=next]", pager);
    if (prev && !prev.disabled) prev.addEventListener("click", function () { goToPage(state.page - 1); });
    if (next && !next.disabled) next.addEventListener("click", function () { goToPage(state.page + 1); });
  }

  function goToPage(n) {
    var total = totalPages();
    n = Math.min(total, Math.max(1, n | 0));
    if (n === state.page) return;
    state.page = n;
    renderPage();
    renderPager();
    var grid = $(".grid");
    if (grid) grid.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function resetAndRender() {
    state.list = state.data.packages.filter(matches);
    state.page = 1;
    if (!state.list.length) {
      $(".grid").innerHTML = '<div class="empty">未找到匹配的能力包 · no matches</div>';
      $(".pager").innerHTML = "";
      $(".count-pill").innerHTML = "0 / " + fmt(state.data.totals.packages);
      return;
    }
    renderPage();
    renderPager();
    $(".count-pill").innerHTML = "<b>" + fmt(state.list.length) + "</b> / " + fmt(state.data.totals.packages);
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
      $(".grid").innerHTML = '<div class="empty">无法加载 skills.json（请通过 GitHub Pages 访问，而非本地 file://）。<br>' + e + "</div>";
    });
})();
