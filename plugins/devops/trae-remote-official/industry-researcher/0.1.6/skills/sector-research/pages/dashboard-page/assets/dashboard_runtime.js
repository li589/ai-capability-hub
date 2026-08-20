(function () {
  function parseDate(value) {
    if (!value) return null;
    const date = new Date(`${value}T00:00:00`);
    return Number.isNaN(date.getTime()) ? null : date;
  }

  function isoDate(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const day = String(date.getDate()).padStart(2, "0");
    return `${year}-${month}-${day}`;
  }

  function daysAgo(latestDate, days) {
    const date = new Date(latestDate);
    date.setDate(date.getDate() - (days - 1));
    return date;
  }

  function computeRange(preset, dates) {
    if (!dates.length) return { start: "", end: "" };
    const first = parseDate(dates[0]);
    const latest = parseDate(dates[dates.length - 1]);
    if (!first || !latest) return { start: "", end: "" };
    const year = latest.getFullYear();
    const month = latest.getMonth();
    const quarterStartMonth = Math.floor(month / 3) * 3;
    let start = first;
    if (preset === "7D") start = daysAgo(latest, 7);
    if (preset === "30D") start = daysAgo(latest, 30);
    if (preset === "MTD") start = new Date(year, month, 1);
    if (preset === "QTD") start = new Date(year, quarterStartMonth, 1);
    if (preset === "YTD") start = new Date(year, 0, 1);
    if (start < first || preset === "ALL") start = first;
    return { start: isoDate(start), end: isoDate(latest) };
  }

  function withinRange(row, state) {
    const value = row.date || row.snapshot_date;
    if (!value) return true;
    if (state.start && value < state.start) return false;
    if (state.end && value > state.end) return false;
    return true;
  }

  window.setupDashboardRuntime = function setupDashboardRuntime(config) {
    const chartFactories = config.chartFactories || {};
    const sourceMap = config.sourceMap || {};
    const tables = config.tables || {};
    const allDates = (config.availableDates || []).slice().sort();
    const chartState = {};
    const state = {
      preset: config.defaultRange || "30D",
      ...computeRange(config.defaultRange || "30D", allDates),
    };

    function filteredRows(key) {
      const rows = (config.datasets && config.datasets[key]) || [];
      return rows.filter((row) => withinRange(row, state));
    }

    function setRangeLabel() {
      const label = document.getElementById("activeRangeLabel");
      if (!label) return;
      label.textContent = state.start && state.end ? `${state.start} to ${state.end}` : "No dated rows";
    }

    function setDateInputs() {
      const start = document.getElementById("rangeStart");
      const end = document.getElementById("rangeEnd");
      if (start) start.value = state.start || "";
      if (end) end.value = state.end || "";
    }

    function setActivePreset() {
      document.querySelectorAll("[data-range-preset]").forEach((button) => {
        button.classList.toggle("active", button.dataset.rangePreset === state.preset);
      });
    }

    function initChart(id, type) {
      const el = document.getElementById(id);
      if (!el || !chartFactories[id]) return;
      const chart = echarts.init(el, null, { renderer: "canvas" });
      chartState[id] = { chart, type };
      chart.setOption(chartFactories[id](type, filteredRows), true);
    }

    function updateCharts() {
      Object.entries(chartState).forEach(([id, entry]) => {
        if (chartFactories[id]) entry.chart.setOption(chartFactories[id](entry.type, filteredRows), true);
      });
    }

    function updateTables() {
      Object.entries(tables).forEach(([id, tableConfig]) => {
        const body = document.querySelector(`#${id} tbody`);
        if (!body) return;
        const rows = filteredRows(tableConfig.dataset).slice();
        if (tableConfig.sortField) {
          rows.sort((a, b) => {
            const left = a[tableConfig.sortField];
            const right = b[tableConfig.sortField];
            if (typeof left === "number" && typeof right === "number") {
              return tableConfig.sortDirection === "asc" ? left - right : right - left;
            }
            return tableConfig.sortDirection === "asc"
              ? String(left).localeCompare(String(right))
              : String(right).localeCompare(String(left));
          });
        }
        const limited = rows.slice(0, tableConfig.limit || 12);
        body.replaceChildren(
          ...limited.map((row) => {
            const tr = document.createElement("tr");
            tableConfig.columns.forEach((column) => {
              const td = document.createElement("td");
              td.textContent = row[column.field] == null ? "" : String(row[column.field]);
              if (column.numeric) td.className = "num";
              tr.appendChild(td);
            });
            return tr;
          })
        );
      });
    }

    function refresh() {
      setRangeLabel();
      setDateInputs();
      setActivePreset();
      updateCharts();
      updateTables();
    }

    window.setDashboardRange = function setDashboardRange(preset) {
      state.preset = preset;
      const next = computeRange(preset, allDates);
      state.start = next.start;
      state.end = next.end;
      refresh();
    };

    window.setCustomDashboardRange = function setCustomDashboardRange() {
      const start = document.getElementById("rangeStart");
      const end = document.getElementById("rangeEnd");
      state.preset = "CUSTOM";
      state.start = start ? start.value : "";
      state.end = end ? end.value : "";
      refresh();
    };

    window.setChartType = function setChartType(id, type) {
      if (!chartState[id] || !chartFactories[id]) return;
      chartState[id].type = type;
      chartState[id].chart.setOption(chartFactories[id](type, filteredRows), true);
    };

    window.toggleMenu = function toggleMenu(id) {
      document.querySelectorAll(".menu").forEach((menu) => {
        if (menu.id !== `menu-${id}`) menu.classList.remove("open");
      });
      const menu = document.getElementById(`menu-${id}`);
      if (menu) menu.classList.toggle("open");
    };

    window.toggleEdit = function toggleEdit(id) {
      const menu = document.getElementById(`menu-${id}`);
      const panel = document.getElementById(`edit-${id}`);
      if (menu) menu.classList.remove("open");
      if (panel) panel.classList.toggle("open");
    };

    window.viewSource = function viewSource(id) {
      const menu = document.getElementById(`menu-${id}`);
      if (menu) menu.classList.remove("open");
      document.getElementById("modalTitle").textContent = "Data Source";
      document.getElementById("modalSubtitle").textContent =
        (config.modalSubtitlePrefix || "Dashboard transform for ") + id + ".";
      document.getElementById("modalSnippet").textContent = sourceMap[id] || "";
      document.getElementById("modalCode").textContent = config.fullScript || "";
      document.getElementById("modalBackdrop").classList.add("open");
    };

    window.closeModal = function closeModal() {
      document.getElementById("modalBackdrop").classList.remove("open");
    };

    window.copyCode = async function copyCode(codeId, button) {
      const text = document.getElementById(codeId).textContent || "";
      try {
        await navigator.clipboard.writeText(text);
      } catch (err) {
        const textarea = document.createElement("textarea");
        textarea.value = text;
        textarea.setAttribute("readonly", "");
        textarea.style.position = "fixed";
        textarea.style.opacity = "0";
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand("copy");
        document.body.removeChild(textarea);
      }
      const previousLabel = button.getAttribute("aria-label") || "Copy";
      button.classList.add("copied");
      button.setAttribute("aria-label", "Copied");
      button.setAttribute("title", "Copied");
      setTimeout(() => {
        button.classList.remove("copied");
        button.setAttribute("aria-label", previousLabel);
        button.removeAttribute("title");
      }, 1200);
    };

    (config.initialCharts || []).forEach((item) => initChart(item.id, item.type));
    refresh();

    document.querySelectorAll("[data-range-preset]").forEach((button) => {
      button.addEventListener("click", () => window.setDashboardRange(button.dataset.rangePreset));
    });
    document.querySelectorAll("[data-range-input]").forEach((input) => {
      input.addEventListener("change", window.setCustomDashboardRange);
    });
    document.addEventListener("click", (event) => {
      if (!event.target.closest(".toolbox")) {
        document.querySelectorAll(".menu").forEach((menu) => menu.classList.remove("open"));
      }
    });
    window.addEventListener("resize", () => {
      Object.values(chartState).forEach((entry) => entry.chart.resize());
    });
  };
})();
