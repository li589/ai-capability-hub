(function () {
  'use strict';

  function emit(name, detail) {
    document.dispatchEvent(new CustomEvent(name, { detail: detail || {} }));
  }

  function prefersReducedMotion() {
    return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  }

  function initReportNavigation() {
    document.querySelectorAll('[data-pui-report-nav]').forEach(function (nav) {
      var links = Array.prototype.slice.call(nav.querySelectorAll('a[href^="#"]'));
      var pairs = links.map(function (link) {
        var id = decodeURIComponent(link.getAttribute('href').slice(1));
        var section = id ? document.getElementById(id) : null;
        return section && section.hasAttribute('data-pui-section')
          ? { link: link, section: section }
          : null;
      }).filter(Boolean);
      var activeId = null;
      var ticking = false;

      if (!pairs.length) return;

      function update(pair, announce) {
        if (!pair || pair.section.id === activeId) return;
        activeId = pair.section.id;
        pairs.forEach(function (candidate) {
          if (candidate === pair) candidate.link.setAttribute('aria-current', 'true');
          else candidate.link.removeAttribute('aria-current');
        });
        if (nav.scrollWidth > nav.clientWidth) {
          var targetLeft = pair.link.offsetLeft - ((nav.clientWidth - pair.link.offsetWidth) / 2);
          nav.scrollTo({
            left: Math.max(0, targetLeft),
            behavior: prefersReducedMotion() ? 'auto' : 'smooth'
          });
        }
        if (announce) {
          emit('pui:chapterchange', {
            id: pair.section.id,
            link: pair.link,
            section: pair.section,
            root: nav
          });
        }
      }

      function selectFromViewport() {
        var marker = Math.max(96, window.innerHeight * 0.28);
        var current = pairs[0];
        var nearestDistance = Infinity;
        pairs.forEach(function (pair) {
          var top = pair.section.getBoundingClientRect().top;
          if (top <= marker) current = pair;
          else if (current === pairs[0] && Math.abs(top - marker) < nearestDistance) {
            current = pair;
            nearestDistance = Math.abs(top - marker);
          }
        });
        update(current, true);
        ticking = false;
      }

      function scheduleViewportSelection() {
        if (ticking) return;
        ticking = true;
        window.requestAnimationFrame(selectFromViewport);
      }

      pairs.forEach(function (pair) {
        pair.link.addEventListener('click', function (event) {
          event.preventDefault();
          pair.section.scrollIntoView({
            behavior: prefersReducedMotion() ? 'auto' : 'smooth',
            block: 'start'
          });
          if (window.history && window.history.pushState) {
            window.history.pushState(null, '', '#' + encodeURIComponent(pair.section.id));
          } else {
            window.location.hash = pair.section.id;
          }
          update(pair, true);
        });
      });

      window.addEventListener('scroll', scheduleViewportSelection, { passive: true });
      window.addEventListener('resize', scheduleViewportSelection);
      selectFromViewport();
    });
  }

  function initCarousels() {
    document.querySelectorAll('[data-pui-carousel]').forEach(function (root) {
      var track = root.querySelector('[data-pui-carousel-track]');
      var items = Array.prototype.slice.call(root.querySelectorAll('[data-pui-carousel-item]'));
      var previous = root.querySelector('[data-pui-carousel-prev]');
      var next = root.querySelector('[data-pui-carousel-next]');
      var status = root.querySelector('[data-pui-carousel-status]');
      var activeIndex = 0;

      if (!track || !items.length) return;

      function nearestIndex() {
        var trackRect = track.getBoundingClientRect();
        var nearest = 0;
        var nearestDistance = Infinity;
        items.forEach(function (item, index) {
          var distance = Math.abs(item.getBoundingClientRect().left - trackRect.left);
          if (distance < nearestDistance) {
            nearest = index;
            nearestDistance = distance;
          }
        });
        return nearest;
      }

      function update(index, announce) {
        activeIndex = Math.max(0, Math.min(index, items.length - 1));
        items.forEach(function (item, itemIndex) {
          item.toggleAttribute('data-pui-active', itemIndex === activeIndex);
          item.setAttribute('aria-current', itemIndex === activeIndex ? 'true' : 'false');
        });
        if (previous) previous.disabled = activeIndex === 0;
        if (next) next.disabled = activeIndex === items.length - 1;
        if (status) status.textContent = String(activeIndex + 1) + ' / ' + String(items.length);
        if (announce) emit('pui:panelchange', { type: 'carousel', index: activeIndex, root: root });
      }

      function go(index) {
        var target = Math.max(0, Math.min(index, items.length - 1));
        items[target].scrollIntoView({
          behavior: prefersReducedMotion() ? 'auto' : 'smooth',
          block: 'nearest',
          inline: 'start'
        });
        update(target, true);
      }

      if (previous) previous.addEventListener('click', function () { go(activeIndex - 1); });
      if (next) next.addEventListener('click', function () { go(activeIndex + 1); });

      track.addEventListener('keydown', function (event) {
        if (event.key === 'ArrowLeft') {
          event.preventDefault();
          go(activeIndex - 1);
        } else if (event.key === 'ArrowRight') {
          event.preventDefault();
          go(activeIndex + 1);
        } else if (event.key === 'Home') {
          event.preventDefault();
          go(0);
        } else if (event.key === 'End') {
          event.preventDefault();
          go(items.length - 1);
        }
      });

      var scrollTimer;
      track.addEventListener('scroll', function () {
        window.clearTimeout(scrollTimer);
        scrollTimer = window.setTimeout(function () {
          update(nearestIndex(), false);
        }, 80);
      }, { passive: true });

      update(0, false);
    });
  }

  function initSwitches() {
    var supportsHover = window.matchMedia('(hover: hover) and (pointer: fine)');

    document.querySelectorAll('[data-pui-switch]').forEach(function (root) {
      var toggle = root.querySelector('[data-pui-switch-toggle]');
      var front = root.querySelector('[data-pui-switch-front]');
      var back = root.querySelector('[data-pui-switch-back]');
      var pinned = false;
      var hovered = false;
      var focused = false;

      if (!toggle || !front || !back) return;

      front.removeAttribute('hidden');
      back.removeAttribute('hidden');

      function render(announce) {
        var open = pinned || hovered || focused;
        front.setAttribute('aria-hidden', open ? 'true' : 'false');
        back.setAttribute('aria-hidden', open ? 'false' : 'true');
        if ('inert' in front) {
          front.inert = open;
          back.inert = !open;
        }
        toggle.setAttribute('aria-pressed', pinned ? 'true' : 'false');
        root.toggleAttribute('data-pui-open', open);
        if (announce) emit('pui:panelchange', { type: 'switch', open: open, pinned: pinned, root: root });
      }

      toggle.addEventListener('click', function () {
        pinned = !pinned;
        render(true);
      });
      if (supportsHover.matches) {
        root.addEventListener('mouseenter', function () {
          hovered = true;
          render(false);
        });
        root.addEventListener('mouseleave', function () {
          hovered = false;
          render(false);
        });
      }
      root.addEventListener('focusin', function () {
        focused = true;
        render(false);
      });
      root.addEventListener('focusout', function (event) {
        if (!root.contains(event.relatedTarget)) {
          focused = false;
          render(false);
        }
      });
      render(false);
    });
  }

  function initTabs() {
    document.querySelectorAll('[data-pui-tabs]').forEach(function (root) {
      var tabs = Array.prototype.slice.call(root.querySelectorAll('[role="tab"]'));
      if (!tabs.length) return;

      function activate(tab, moveFocus) {
        tabs.forEach(function (candidate) {
          var selected = candidate === tab;
          var panelId = candidate.getAttribute('aria-controls');
          var panel = panelId ? document.getElementById(panelId) : null;
          candidate.setAttribute('aria-selected', selected ? 'true' : 'false');
          candidate.tabIndex = selected ? 0 : -1;
          if (panel) panel.hidden = !selected;
        });
        if (moveFocus) tab.focus();
        emit('pui:panelchange', {
          type: 'tab',
          tab: tab,
          panelId: tab.getAttribute('aria-controls'),
          root: root
        });
      }

      tabs.forEach(function (tab, index) {
        tab.addEventListener('click', function () { activate(tab, false); });
        tab.addEventListener('keydown', function (event) {
          var targetIndex = index;
          if (event.key === 'ArrowLeft' || event.key === 'ArrowUp') targetIndex = (index - 1 + tabs.length) % tabs.length;
          else if (event.key === 'ArrowRight' || event.key === 'ArrowDown') targetIndex = (index + 1) % tabs.length;
          else if (event.key === 'Home') targetIndex = 0;
          else if (event.key === 'End') targetIndex = tabs.length - 1;
          else return;
          event.preventDefault();
          activate(tabs[targetIndex], true);
        });
      });

      activate(tabs.find(function (tab) {
        return tab.getAttribute('aria-selected') === 'true';
      }) || tabs[0], false);
    });
  }

  function initMasterDetails() {
    document.querySelectorAll('[data-pui-master-detail]').forEach(function (root) {
      var items = Array.prototype.slice.call(root.querySelectorAll('[data-pui-master-item]'));
      if (!items.length) return;

      function activate(item, moveFocus) {
        items.forEach(function (candidate) {
          var selected = candidate === item;
          var panelId = candidate.getAttribute('aria-controls');
          var panel = panelId ? document.getElementById(panelId) : null;
          candidate.setAttribute('aria-selected', selected ? 'true' : 'false');
          candidate.tabIndex = selected ? 0 : -1;
          if (panel) panel.hidden = !selected;
        });
        if (moveFocus) item.focus();
        emit('pui:panelchange', {
          type: 'master-detail',
          key: item.getAttribute('data-pui-key') || null,
          panelId: item.getAttribute('aria-controls'),
          root: root
        });
      }

      items.forEach(function (item, index) {
        item.addEventListener('click', function () { activate(item, false); });
        item.addEventListener('keydown', function (event) {
          var targetIndex = index;
          if (event.key === 'ArrowLeft' || event.key === 'ArrowUp') targetIndex = (index - 1 + items.length) % items.length;
          else if (event.key === 'ArrowRight' || event.key === 'ArrowDown') targetIndex = (index + 1) % items.length;
          else if (event.key === 'Home') targetIndex = 0;
          else if (event.key === 'End') targetIndex = items.length - 1;
          else return;
          event.preventDefault();
          activate(items[targetIndex], true);
        });
      });

      activate(items.find(function (item) {
        return item.getAttribute('aria-selected') === 'true';
      }) || items[0], false);
    });
  }

  function initHelpPopovers() {
    var supportsHover = window.matchMedia('(hover: hover) and (pointer: fine)');

    document.querySelectorAll('[data-pui-help]').forEach(function (root) {
      var trigger = root.querySelector('[data-pui-help-trigger]');
      var popover = root.querySelector('[data-pui-help-popover]');
      var pinned = false;
      var hovered = false;
      var focused = false;
      if (!trigger || !popover) return;

      function render() {
        var open = pinned || hovered || focused;
        popover.hidden = !open;
        trigger.setAttribute('aria-expanded', open ? 'true' : 'false');
        root.toggleAttribute('data-pui-open', open);
      }

      trigger.addEventListener('click', function () {
        pinned = !pinned;
        render();
      });
      if (supportsHover.matches) {
        root.addEventListener('mouseenter', function () {
          hovered = true;
          render();
        });
        root.addEventListener('mouseleave', function () {
          hovered = false;
          render();
        });
      }
      root.addEventListener('focusin', function () {
        focused = true;
        render();
      });
      root.addEventListener('focusout', function (event) {
        if (!root.contains(event.relatedTarget)) {
          focused = false;
          render();
        }
      });
      document.addEventListener('pointerdown', function (event) {
        if (pinned && !root.contains(event.target)) {
          pinned = false;
          render();
        }
      });
      document.addEventListener('keydown', function (event) {
        if (event.key === 'Escape' && (pinned || hovered || focused)) {
          pinned = false;
          hovered = false;
          render();
        }
      });
      render();
    });
  }

  function initLinkedKeys() {
    var keyed = Array.prototype.slice.call(document.querySelectorAll('[data-pui-key]'));
    var pinnedKey = null;

    if (!keyed.length) return;

    function apply(key, pinned) {
      keyed.forEach(function (element) {
        var matches = Boolean(key) && element.getAttribute('data-pui-key') === key;
        element.classList.toggle('pui-is-linked', matches);
        element.classList.toggle('pui-is-pinned', matches && pinned);
      });
      emit('pui:keychange', { key: key, pinned: pinned });
    }

    keyed.forEach(function (element) {
      var key = element.getAttribute('data-pui-key');
      element.addEventListener('mouseenter', function () {
        if (!pinnedKey) apply(key, false);
      });
      element.addEventListener('mouseleave', function () {
        if (!pinnedKey) apply(null, false);
      });
      element.addEventListener('focusin', function () {
        if (!pinnedKey) apply(key, false);
      });
      element.addEventListener('focusout', function () {
        if (!pinnedKey) apply(null, false);
      });
      element.addEventListener('click', function () {
        pinnedKey = pinnedKey === key ? null : key;
        apply(pinnedKey, Boolean(pinnedKey));
      });
      element.addEventListener('keydown', function (event) {
        if (event.key !== 'Enter' && event.key !== ' ') return;
        event.preventDefault();
        pinnedKey = pinnedKey === key ? null : key;
        apply(pinnedKey, Boolean(pinnedKey));
      });
    });

    document.addEventListener('procurement:charthover', function (event) {
      if (!pinnedKey && event.detail) apply(event.detail.key || null, false);
    });
    document.addEventListener('procurement:chartleave', function () {
      if (!pinnedKey) apply(null, false);
    });
    document.addEventListener('procurement:chartselect', function (event) {
      pinnedKey = event.detail && event.detail.key ? String(event.detail.key) : null;
      apply(pinnedKey, Boolean(pinnedKey));
    });

    document.addEventListener('keydown', function (event) {
      if (event.key === 'Escape' && pinnedKey) {
        pinnedKey = null;
        apply(null, false);
      }
    });
  }

  function init() {
    initReportNavigation();
    initCarousels();
    initSwitches();
    initTabs();
    initMasterDetails();
    initHelpPopovers();
    initLinkedKeys();
    document.documentElement.setAttribute('data-pui-ready', 'true');
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init, { once: true });
  } else {
    init();
  }
})();
