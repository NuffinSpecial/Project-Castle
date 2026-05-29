document.addEventListener("DOMContentLoaded", () => {
  const glossContainer = document.getElementById("gloss-tokens");
  const glossLegend = document.getElementById("gloss-legend");
  const sentenceEl = document.getElementById("original-sentence");
  const signLabel = document.getElementById("video-sign-label");
  const video = document.getElementById("sign-video");
  const placeholder = document.getElementById("video-placeholder");
  const missingLink = document.getElementById("sign-missing-link");
  const playBtn = document.getElementById("video-play");
  const pauseBtn = document.getElementById("video-pause");
  const replayBtn = document.getElementById("video-replay");
  const speedSelect = document.getElementById("video-speed");

  let currentResult = null;

  function setActiveToken(index) {
    const buttons = glossContainer.querySelectorAll(".gloss-token");
    buttons.forEach((btn) => {
      const tokenIndex = Number(btn.dataset.tokenIndex);
      btn.classList.toggle("gloss-token--active", tokenIndex === index);
      btn.setAttribute("aria-pressed", tokenIndex === index ? "true" : "false");
    });
  }

  function showSign(index) {
    if (!currentResult) return;
    const token = currentResult.glossTokens[index];
    const videoUrl = currentResult.links[index];
    const available = currentResult.signAvailable?.[index];

    setActiveToken(index);
    signLabel.textContent = token;

    video.pause();
    video.removeAttribute("src");
    video.load();

    if (available && videoUrl) {
      video.src = videoUrl;
      placeholder.hidden = true;
      missingLink.hidden = true;
    } else {
      placeholder.hidden = false;
      missingLink.hidden = false;
      const submitUrl = `/submit?english=${encodeURIComponent(token)}`;
      missingLink.href = submitUrl;
      const linkLabel = missingLink.querySelector("span");
      if (linkLabel) {
        linkLabel.textContent = `No community video for “${token}” yet — submit one`;
      }
    }
  }

  function createTokenButton(token, index, result) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "gloss-token";
    btn.dataset.tokenIndex = String(index);
    if (result.signAvailable?.[index]) {
      btn.classList.add("gloss-token--has-video");
    }
    btn.textContent = token;
    btn.setAttribute("aria-pressed", "false");
    btn.addEventListener("click", () => showSign(index));
    return btn;
  }

  function buildIndexToGroupMap(mutableGroups) {
    const map = new Map();
    (mutableGroups || []).forEach((group, groupId) => {
      group.indices.forEach((idx) => map.set(idx, groupId));
    });
    return map;
  }

  function renderGlossTokens(result) {
    glossContainer.innerHTML = "";
    const tokens = result.glossTokens || [];
    const mutableGroups = result.mutableGroups || [];
    const indexToGroup = buildIndexToGroupMap(mutableGroups);

    if (glossLegend) {
      glossLegend.hidden = mutableGroups.length === 0;
    }

    let index = 0;
    while (index < tokens.length) {
      const groupId = indexToGroup.get(index);
      if (groupId === undefined) {
        glossContainer.appendChild(createTokenButton(tokens[index], index, result));
        index += 1;
        continue;
      }

      const group = mutableGroups[groupId];
      const groupEl = document.createElement("span");
      groupEl.className = "gloss-mutable-group";
      groupEl.title = group.note || "These signs may appear in either order.";

      group.indices.forEach((tokenIndex, position) => {
        if (position > 0) {
          const swap = document.createElement("span");
          swap.className = "gloss-mutable-group__swap";
          swap.setAttribute("aria-hidden", "true");
          swap.textContent = "↔";
          groupEl.appendChild(swap);
        }
        groupEl.appendChild(createTokenButton(tokens[tokenIndex], tokenIndex, result));
      });

      glossContainer.appendChild(groupEl);
      index = Math.max(...group.indices) + 1;
    }
  }

  function renderTranslation(data) {
    const result = data.results[0];
    currentResult = result;
    sentenceEl.textContent = result.originalSentence;
    renderGlossTokens(result);

    if (result.glossTokens.length) {
      showSign(0);
    }
  }

  async function loadOrTranslate(phrase) {
    const cached = getTranslationCache();
    if (cached && cached.sentences?.[0] === phrase && cached.results?.length) {
      renderTranslation(cached);
      return;
    }
    const data = await fetchTranslation(phrase);
    setTranslationCache(data);
    renderTranslation(data);
  }

  initPhraseBar({
    autoTranslateOnHistoryClick: true,
    onTranslate: async (phrase) => {
      const button = document.getElementById("translate-button");
      const label = button.querySelector("span");
      button.disabled = true;
      if (label) label.textContent = "Translating…";
      glossContainer.innerHTML = '<p class="loading-inline">Translating…</p>';
      if (glossLegend) glossLegend.hidden = true;
      try {
        await loadOrTranslate(phrase);
      } catch (error) {
        const errorEl = document.getElementById("phrase-error");
        if (errorEl) {
          errorEl.textContent = error.message;
          errorEl.hidden = false;
        }
        glossContainer.innerHTML = "";
      } finally {
        button.disabled = false;
        if (label) label.textContent = "Translate";
      }
    },
  });

  playBtn.addEventListener("click", () => {
    if (video.src) video.play();
  });
  pauseBtn.addEventListener("click", () => video.pause());
  replayBtn.addEventListener("click", () => {
    if (!video.src) return;
    video.currentTime = 0;
    video.play();
  });
  speedSelect.addEventListener("change", () => {
    video.playbackRate = Number(speedSelect.value);
  });

  const phrase = getPhrase();
  if (!phrase) {
    window.location.href = "/";
    return;
  }

  const cached = getTranslationCache();
  if (cached && cached.results?.length) {
    renderTranslation(cached);
  } else {
    loadOrTranslate(phrase).catch((error) => {
      const errorEl = document.getElementById("phrase-error");
      if (errorEl) {
        errorEl.textContent = error.message;
        errorEl.hidden = false;
      }
    });
  }

  const helpToggle = document.getElementById("help-toggle");
  const helpPanel = document.getElementById("help-panel");
  const helpClose = document.getElementById("help-close");

  function setHelpOpen(open) {
    if (!helpPanel || !helpToggle) return;
    helpPanel.hidden = !open;
    helpToggle.setAttribute("aria-expanded", open ? "true" : "false");
    helpToggle.classList.toggle("help-toggle--active", open);
  }

  helpToggle?.addEventListener("click", () => {
    setHelpOpen(helpPanel.hidden);
  });

  helpClose?.addEventListener("click", () => {
    setHelpOpen(false);
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && helpPanel && !helpPanel.hidden) {
      setHelpOpen(false);
    }
  });

  document.addEventListener("click", (event) => {
    if (!helpPanel || helpPanel.hidden) return;
    const target = event.target;
    if (!(target instanceof Node)) return;
    if (helpPanel.contains(target) || helpToggle?.contains(target)) return;
    setHelpOpen(false);
  });
});
