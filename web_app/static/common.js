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

function applyTheme(theme) {
  const next = theme === "dark" ? "dark" : "light";
  document.documentElement.setAttribute("data-theme", next);
  localStorage.setItem(CastleStorage.THEME, next);
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
    input.setAttribute("aria-expanded", "true");
  }

  function closeHistoryDropdown() {
    dropdown.hidden = true;
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

document.addEventListener("DOMContentLoaded", () => {
  applyTheme(getTheme());
  requestAnimationFrame(() => {
    document.body.classList.add("is-ready");
  });
});
