(() => {
  "use strict";

  const root = document.documentElement;
  const nav = document.querySelector("[data-report-nav]");
  const sections = [...document.querySelectorAll("[data-report-section][id]")];
  const triggers = [...document.querySelectorAll("[data-signal-trigger][data-signal-id]")];
  const cards = [...document.querySelectorAll("[data-signal-card][data-signal-id]")];
  const details = [...document.querySelectorAll("[data-signal-detail][data-signal-id]")];
  const live = document.querySelector("[data-radar-live]");
  let activeSignal = "";
  let invokingTrigger = null;
  let expandedSignal = "";

  function setCurrentChapter(id) {
    if (!nav || !id) return;
    nav.querySelectorAll("a[href^='#']").forEach((link) => {
      const current = link.getAttribute("href") === `#${id}`;
      if (current) link.setAttribute("aria-current", "location");
      else link.removeAttribute("aria-current");
    });
  }

  if (nav && sections.length && "IntersectionObserver" in window) {
    const observer = new IntersectionObserver(
      (entries) => {
        const visible = entries
          .filter((entry) => entry.isIntersecting)
          .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
        if (visible) setCurrentChapter(visible.target.id);
      },
      { rootMargin: "-16% 0px -68% 0px", threshold: [0.05, 0.3, 0.6] }
    );
    sections.forEach((section) => observer.observe(section));
    nav.querySelectorAll("a[href^='#']").forEach((link) => {
      link.addEventListener("click", () => {
        setCurrentChapter(link.getAttribute("href").slice(1));
      });
    });
  }

  function selectSignal(id, options = {}) {
    if (!id || id === activeSignal) {
      if (options.expand) openDetail(id, options.trigger);
      return;
    }

    activeSignal = id;
    root.dataset.activeSignal = id;

    cards.forEach((card) => {
      card.classList.toggle("is-selected", card.dataset.signalId === id);
    });
    triggers.forEach((trigger) => {
      trigger.setAttribute("aria-pressed", String(trigger.dataset.signalId === id));
    });
    if (!options.expand) {
      expandedSignal = "";
      details.forEach((detail) => {
        detail.hidden = true;
      });
      triggers.forEach((trigger) => {
        if (trigger.hasAttribute("aria-expanded")) {
          trigger.setAttribute("aria-expanded", "false");
        }
      });
    }

    if (live) live.textContent = `Selected signal ${id}`;
    window.dispatchEvent(
      new CustomEvent("radar:signalchange", {
        detail: { id, source: options.source || "interface" }
      })
    );

    if (options.expand) openDetail(id, options.trigger);
  }

  function openDetail(id, trigger) {
    const detail = details.find((item) => item.dataset.signalId === id);
    if (!detail) return;
    expandedSignal = id;
    invokingTrigger = trigger || invokingTrigger;
    details.forEach((item) => {
      item.hidden = item !== detail;
    });
    triggers.forEach((item) => {
      if (item.hasAttribute("aria-expanded")) {
        item.setAttribute("aria-expanded", String(item.dataset.signalId === id));
      }
    });
    detail.focus({ preventScroll: true });
    const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    detail.scrollIntoView({ block: "nearest", behavior: reduceMotion ? "auto" : "smooth" });
  }

  function closeDetails() {
    expandedSignal = "";
    details.forEach((detail) => {
      detail.hidden = true;
    });
    triggers.forEach((trigger) => {
      if (trigger.hasAttribute("aria-expanded")) {
        trigger.setAttribute("aria-expanded", "false");
      }
    });
    if (invokingTrigger) invokingTrigger.focus();
  }

  triggers.forEach((trigger) => {
    trigger.addEventListener("click", () => {
      selectSignal(trigger.dataset.signalId, {
        source: "card",
        expand: trigger.hasAttribute("aria-controls"),
        trigger
      });
    });
  });

  window.addEventListener("radar:select-signal", (event) => {
    selectSignal(event.detail?.id, { source: event.detail?.source || "chart" });
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") closeDetails();
  });

  const initial =
    root.dataset.activeSignal ||
    triggers.find((trigger) => trigger.getAttribute("aria-pressed") === "true")?.dataset.signalId ||
    triggers[0]?.dataset.signalId;
  if (initial) selectSignal(initial, { source: "initial" });
})();
