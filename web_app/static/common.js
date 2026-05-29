/** Shared storage keys and theme/search utilities for Project Castle. */
const CastleStorage = {
  PHRASE: "castle.phrase",
  TRANSLATION: "castle.translation",
  HISTORY: "castle.searchHistory",
  THEME: "castle.theme",
  MAX_HISTORY: 10,
};

function getTheme() {
  const stored = localStorage.getItem(CastleStorage.THEME);
  if (stored === "dark" || stored === "light") {
    return stored;
  }
  const current = document.documentElement.getAttribute("data-theme");
  if (current === "dark" || current === "light") {
    return current;
  }
  return "light";
}

const THEME_SLIDER_MS = 650;

function syncHeaderThemeToggle(themeOverride, options = {}) {
  const { animate = false } = options;
  const toggle = document.getElementById("header-theme-toggle");
  if (!toggle) return;

  const theme =
    themeOverride === "dark" || themeOverride === "light" ? themeOverride : getTheme();
  const isDark = theme === "dark";
  const wasDark = toggle.classList.contains("theme-slider--dark");
  const menu = toggle.closest(".user-menu");
  const thumb = toggle.querySelector(".theme-slider__thumb");

  toggle.setAttribute("aria-checked", isDark ? "true" : "false");
  toggle.setAttribute("aria-label", isDark ? "Dark mode" : "Light mode");
  toggle.title = isDark ? "Switch to light mode" : "Switch to dark mode";

  if (thumb) {
    thumb.style.removeProperty("left");
  }

  const applyPosition = () => {
    toggle.classList.toggle("theme-slider--dark", isDark);
  };

  if (!animate || wasDark === isDark) {
    toggle.classList.add("theme-slider--instant");
    applyPosition();
    requestAnimationFrame(() => {
      toggle.classList.remove("theme-slider--instant");
    });
    return;
  }

  menu?.classList.add("user-menu--theme-sliding");

  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      applyPosition();
    });
  });

  if (!thumb) {
    menu?.classList.remove("user-menu--theme-sliding");
    return;
  }

  const finish = () => {
    menu?.classList.remove("user-menu--theme-sliding");
  };

  thumb.addEventListener(
    "transitionend",
    (event) => {
      if (event.propertyName === "left") {
        finish();
      }
    },
    { once: true },
  );
  window.setTimeout(finish, THEME_SLIDER_MS + 100);
}

function commitTheme(next) {
  document.documentElement.setAttribute("data-theme", next);
  localStorage.setItem(CastleStorage.THEME, next);
}

function fadeThemeWithOverlay(next) {
  let overlay = document.getElementById("theme-fade-overlay");
  if (!overlay) {
    overlay = document.createElement("div");
    overlay.id = "theme-fade-overlay";
    overlay.className = "theme-fade-overlay";
    overlay.setAttribute("aria-hidden", "true");
    document.body.appendChild(overlay);
  }

  overlay.style.background = getComputedStyle(document.body).backgroundColor;
  requestAnimationFrame(() => {
    overlay.classList.add("theme-fade-overlay--visible");
  });

  window.setTimeout(() => {
    commitTheme(next);
    overlay.style.background = getComputedStyle(document.body).backgroundColor;
    overlay.classList.remove("theme-fade-overlay--visible");
  }, 280);
}

function applyTheme(theme, options = {}) {
  const { animate = true } = options;
  const next = theme === "dark" ? "dark" : "light";
  if (getTheme() === next) {
    syncHeaderThemeToggle(next, { animate: false });
    return;
  }

  if (!animate) {
    commitTheme(next);
    syncHeaderThemeToggle(next, { animate: false });
    return;
  }

  syncHeaderThemeToggle(next, { animate: true });

  const prefersReduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (prefersReduced) {
    commitTheme(next);
    return;
  }

  // Let the slider move on screen before the page fade covers it.
  window.setTimeout(() => fadeThemeWithOverlay(next), 280);
}

function getPhrase() {
  return sessionStorage.getItem(CastleStorage.PHRASE) || "";
}

function setPhrase(phrase) {
  sessionStorage.setItem(CastleStorage.PHRASE, phrase);
}

function getTranslationCache() {
  const raw = sessionStorage.getItem(CastleStorage.TRANSLATION);
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

function setTranslationCache(payload) {
  sessionStorage.setItem(CastleStorage.TRANSLATION, JSON.stringify(payload));
}

function getSearchHistory() {
  try {
    const raw = localStorage.getItem(CastleStorage.HISTORY);
    const list = raw ? JSON.parse(raw) : [];
    return Array.isArray(list) ? list.filter((item) => typeof item === "string") : [];
  } catch {
    return [];
  }
}

function addSearchHistory(phrase) {
  const trimmed = phrase.trim();
  if (!trimmed) return;
  const history = getSearchHistory().filter((item) => item !== trimmed);
  history.unshift(trimmed);
  localStorage.setItem(
    CastleStorage.HISTORY,
    JSON.stringify(history.slice(0, CastleStorage.MAX_HISTORY)),
  );
}

function initPhraseBar(options = {}) {
  const { onTranslate, autoTranslateOnHistoryClick = false } = options;
  const input = document.getElementById("phrase-input");
  const button = document.getElementById("translate-button");
  const dropdown = document.getElementById("search-history-dropdown");
  const errorEl = document.getElementById("phrase-error");

  if (!input || !button || !dropdown) return null;

  const savedPhrase = getPhrase();
  if (savedPhrase) {
    input.value = savedPhrase;
  }

  function showError(message) {
    if (!errorEl) return;
    if (message) {
      errorEl.textContent = message;
      errorEl.hidden = false;
    } else {
      errorEl.hidden = true;
      errorEl.textContent = "";
    }
  }

  function renderHistoryDropdown() {
    const history = getSearchHistory();
    dropdown.innerHTML = "";
    if (!history.length) {
      dropdown.hidden = true;
      input.setAttribute("aria-expanded", "false");
      return;
    }

    history.forEach((entry) => {
      const item = document.createElement("li");
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "search-history__item";
      btn.textContent = entry;
      btn.addEventListener("click", () => {
        input.value = entry;
        setPhrase(entry);
        closeHistoryDropdown();
        if (autoTranslateOnHistoryClick && onTranslate) {
          onTranslate(entry);
        }
      });
      item.appendChild(btn);
      dropdown.appendChild(item);
    });
  }

  function openHistoryDropdown() {
    renderHistoryDropdown();
    if (!dropdown.children.length) return;
    dropdown.hidden = false;
    requestAnimationFrame(() => dropdown.classList.add("is-open"));
    input.setAttribute("aria-expanded", "true");
  }

  function closeHistoryDropdown() {
    dropdown.classList.remove("is-open");
    const duration = window.matchMedia("(prefers-reduced-motion: reduce)").matches ? 0 : 520;
    window.setTimeout(() => {
      if (!dropdown.classList.contains("is-open")) {
        dropdown.hidden = true;
      }
    }, duration);
    input.setAttribute("aria-expanded", "false");
  }

  async function runTranslate() {
    const phrase = input.value.trim();
    if (!phrase) {
      showError("Please enter a phrase to translate.");
      return;
    }
    showError("");
    setPhrase(phrase);
    addSearchHistory(phrase);
    if (onTranslate) {
      await onTranslate(phrase);
    }
  }

  input.addEventListener("focus", openHistoryDropdown);
  input.addEventListener("click", openHistoryDropdown);
  input.addEventListener("keydown", (event) => {
    if (event.key === "Escape") closeHistoryDropdown();
  });

  document.addEventListener("click", (event) => {
    if (!event.target.closest("[data-phrase-bar]")) {
      closeHistoryDropdown();
    }
  });

  button.addEventListener("click", runTranslate);
  input.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      runTranslate();
    }
  });

  return { input, runTranslate, showError, closeHistoryDropdown };
}

async function fetchTranslation(phrase) {
  const response = await fetch("/translate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ sentences: [phrase] }),
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || "Translation failed. Please try again.");
  }
  return data;
}

function setAnimatedPanel(panel, open, visibleClass = "is-open") {
  if (!panel) return;
  const duration = window.matchMedia("(prefers-reduced-motion: reduce)").matches ? 0 : 520;

  if (open) {
    panel.hidden = false;
    requestAnimationFrame(() => panel.classList.add(visibleClass));
    return;
  }

  panel.classList.remove(visibleClass);
  window.setTimeout(() => {
    if (!panel.classList.contains(visibleClass)) {
      panel.hidden = true;
    }
  }, duration);
}

function initUserMenu() {
  const menu = document.querySelector("[data-user-menu]");
  const trigger = document.getElementById("user-menu-trigger");
  const panel = document.getElementById("user-menu-panel");
  if (!menu || !trigger || !panel) return;

  function setOpen(open) {
    setAnimatedPanel(panel, open);
    trigger.setAttribute("aria-expanded", open ? "true" : "false");
  }

  trigger.addEventListener("click", (event) => {
    event.stopPropagation();
    setOpen(!panel.classList.contains("is-open"));
  });

  document.addEventListener("click", (event) => {
    if (!menu.contains(event.target)) {
      setOpen(false);
    }
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      setOpen(false);
    }
  });
}

document.addEventListener("DOMContentLoaded", () => {
  const initialTheme = getTheme();
  applyTheme(initialTheme, { animate: false });
  initUserMenu();

  document.getElementById("header-theme-toggle")?.addEventListener("click", (event) => {
    event.stopPropagation();
    const next = getTheme() === "dark" ? "light" : "dark";
    applyTheme(next);
  });

  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      document.body.classList.add("is-ready");
    });
  });
});
