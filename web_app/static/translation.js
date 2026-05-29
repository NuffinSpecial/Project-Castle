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
  const signContext = document.getElementById("video-sign-context");
  const variantControls = document.getElementById("sign-variant-controls");
  const variantPrev = document.getElementById("sign-variant-prev");
  const variantNext = document.getElementById("sign-variant-next");
  const variantLabel = document.getElementById("sign-variant-label");
  const videoScreen = document.querySelector(".video-player__screen");

  const workspace = document.getElementById("translation-workspace");
  const loggedIn = workspace?.dataset.loggedIn === "true";
  const loginUrl = workspace?.dataset.loginUrl || "/auth/login";
  const reportGlossBtn = document.getElementById("report-gloss-btn");
  const reportVideoBtn = document.getElementById("report-video-btn");
  const reportDialog = document.getElementById("report-dialog");
  const reportForm = document.getElementById("report-form");
  const reportIntro = document.getElementById("report-dialog-intro");
  const reportMessage = document.getElementById("report-message");
  const reportError = document.getElementById("report-error");
  const reportCancel = document.getElementById("report-cancel");
  const reportDialogClose = document.getElementById("report-dialog-close");
  const reportSubmit = document.getElementById("report-submit");

  let currentResult = null;
  let activeSignIndex = 0;
  let pendingReportType = null;
  let glossSelector = null;
  let glossSelectorLayoutBound = false;
  let glossLabelsReady = false;
  const variantIndexByToken = new Map();

  const GLOSS_SELECTOR_MS = 580;
  const GLOSS_SELECTOR_EASE = "cubic-bezier(0.33, 1, 0.68, 1)";
  const GLOSS_ENTRANCE_MS = 560;

  function ensureGlossSelector() {
    if (!glossSelector || !glossSelector.isConnected) {
      glossSelector = document.createElement("span");
      glossSelector.className = "gloss-tokens__selector";
      glossSelector.setAttribute("aria-hidden", "true");
      glossContainer.appendChild(glossSelector);
    }
    return glossSelector;
  }

  function ensureGlossLabelLayer() {
    let layer = glossContainer.querySelector(".gloss-tokens__labels");
    if (!layer) {
      layer = document.createElement("div");
      layer.className = "gloss-tokens__labels";
      layer.setAttribute("aria-hidden", "true");
      glossContainer.appendChild(layer);
    }
    return layer;
  }

  function revealGlossLabels() {
    glossLabelsReady = true;
    glossContainer.classList.add("gloss-tokens--labels-ready");
  }

  function resetGlossLabelLayer() {
    glossLabelsReady = false;
    glossContainer.classList.remove("gloss-tokens--labels-ready");
    glossContainer.querySelector(".gloss-tokens__labels")?.replaceChildren();
  }

  function syncGlossLabelOverlays() {
    if (!glossLabelsReady) return;

    const layer = ensureGlossLabelLayer();
    layer.innerHTML = "";

    glossContainer.querySelectorAll(".gloss-token").forEach((btn) => {
      const box = measureButtonBox(btn);
      const overlay = document.createElement("span");
      overlay.className = "gloss-token__overlay";
      overlay.dataset.tokenIndex = btn.dataset.tokenIndex;

      if (btn.classList.contains("gloss-token--active")) {
        overlay.classList.add("gloss-token__overlay--active");
      }
      if (btn.classList.contains("gloss-token--ambiguous")) {
        overlay.classList.add("gloss-token__overlay--ambiguous");
        overlay.dataset.variantCount = btn.dataset.variantCount || "";
      }
      if (btn.classList.contains("gloss-token--has-video")) {
        overlay.classList.add("gloss-token__overlay--has-video");
      }

      const label = btn.querySelector(".gloss-token__label");
      overlay.textContent = label?.textContent || "";
      overlay.style.width = `${box.width}px`;
      overlay.style.height = `${box.height}px`;
      overlay.style.transform = `translate3d(${box.x}px, ${box.y}px, 0)`;
      layer.appendChild(overlay);
    });
  }

  function whenGlossLayoutReady(callback) {
    const run = () => {
      window.setTimeout(() => {
        requestAnimationFrame(() => {
          requestAnimationFrame(callback);
        });
      }, GLOSS_ENTRANCE_MS);
    };

    if (document.body.classList.contains("is-ready")) {
      run();
      return;
    }

    const observer = new MutationObserver(() => {
      if (!document.body.classList.contains("is-ready")) return;
      observer.disconnect();
      run();
    });
    observer.observe(document.body, { attributes: true, attributeFilter: ["class"] });
  }

  function measureButtonBox(btn) {
    const containerRect = glossContainer.getBoundingClientRect();
    const btnRect = btn.getBoundingClientRect();
    return {
      x: btnRect.left - containerRect.left + glossContainer.scrollLeft,
      y: btnRect.top - containerRect.top + glossContainer.scrollTop,
      width: btnRect.width,
      height: btnRect.height,
    };
  }

  function applySelectorBox(selector, box) {
    selector.style.width = `${box.width}px`;
    selector.style.height = `${box.height}px`;
    selector.style.transform = `translate3d(${box.x}px, ${box.y}px, 0)`;
    glossContainer.classList.add("gloss-tokens--ready");
  }

  function animateSelectorBetween(from, to, onComplete) {
    const selector = ensureGlossSelector();
    selector.hidden = false;
    selector.classList.add("gloss-tokens__selector--animating");
    selector.getAnimations().forEach((animation) => animation.cancel());

    applySelectorBox(selector, from);

    const animation = selector.animate(
      [
        {
          transform: `translate3d(${from.x}px, ${from.y}px, 0)`,
          width: `${from.width}px`,
          height: `${from.height}px`,
        },
        {
          transform: `translate3d(${to.x}px, ${to.y}px, 0)`,
          width: `${to.width}px`,
          height: `${to.height}px`,
        },
      ],
      {
        duration: GLOSS_SELECTOR_MS,
        easing: GLOSS_SELECTOR_EASE,
        fill: "forwards",
      },
    );

    let finished = false;
    const finish = () => {
      if (finished) return;
      finished = true;
      selector.classList.remove("gloss-tokens__selector--animating");
      applySelectorBox(selector, to);
      syncGlossLabelOverlays();
      onComplete?.();
    };

    animation.onfinish = finish;
    animation.oncancel = finish;
    window.setTimeout(finish, GLOSS_SELECTOR_MS + 80);

    return animation;
  }

  function moveGlossSelectorToButton(btn, { instant = false, fromBox = null, onComplete } = {}) {
    const selector = ensureGlossSelector();
    if (!btn || !glossContainer.contains(btn)) {
      selector.getAnimations().forEach((animation) => animation.cancel());
      selector.classList.remove("gloss-tokens__selector--animating");
      selector.hidden = true;
      glossContainer.classList.remove("gloss-tokens--ready");
      onComplete?.();
      return;
    }

    selector.hidden = false;
    const target = measureButtonBox(btn);

    if (instant || !fromBox) {
      selector.getAnimations().forEach((animation) => animation.cancel());
      selector.classList.remove("gloss-tokens__selector--animating");
      applySelectorBox(selector, target);
      syncGlossLabelOverlays();
      onComplete?.();
      return;
    }

    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        animateSelectorBetween(fromBox, measureButtonBox(btn), onComplete);
      });
    });
  }

  function bindGlossSelectorLayout() {
    if (glossSelectorLayoutBound) return;
    glossSelectorLayoutBound = true;

    window.addEventListener("resize", () => {
      const activeBtn = glossContainer.querySelector(".gloss-token--active");
      if (activeBtn) {
        moveGlossSelectorToButton(activeBtn, { instant: true });
      } else {
        syncGlossLabelOverlays();
      }
    });
  }

  function getVariants(index) {
    const variants = currentResult?.signVariants?.[index];
    if (variants?.length) return variants;

    if (currentResult?.signAvailable?.[index] && currentResult.links?.[index]) {
      return [
        {
          videoUrl: currentResult.links[index],
          submissionId: currentResult.submissionIds?.[index] || null,
          english: currentResult.glossTokens[index],
          context: currentResult.glossTokens[index],
        },
      ];
    }
    return [];
  }

  function getVariantIndex(index) {
    const variants = getVariants(index);
    if (!variants.length) return 0;
    const stored = variantIndexByToken.get(index) ?? 0;
    return Math.min(stored, variants.length - 1);
  }

  function setVariantIndex(index, variantIndex) {
    const variants = getVariants(index);
    if (!variants.length) return;
    const wrapped =
      ((variantIndex % variants.length) + variants.length) % variants.length;
    variantIndexByToken.set(index, wrapped);
  }

  function getActiveVariant(index) {
    const variants = getVariants(index);
    if (!variants.length) return null;
    return variants[getVariantIndex(index)];
  }

  function updateVariantControls(index) {
    const variants = getVariants(index);
    if (!variantControls || !variantLabel) return;

    if (variants.length > 1) {
      const variantIndex = getVariantIndex(index);
      const current = variantIndex + 1;
      variantControls.hidden = false;
      variantLabel.textContent = `${current} of ${variants.length}`;
      if (variantPrev) {
        variantPrev.disabled = variantIndex === 0;
      }
      if (variantNext) {
        variantNext.disabled = variantIndex >= variants.length - 1;
      }
    } else {
      variantControls.hidden = true;
      variantLabel.textContent = "";
      if (variantPrev) variantPrev.disabled = true;
      if (variantNext) variantNext.disabled = true;
    }
  }

  function updateSignContext(variant) {
    if (!signContext) return;
    const text = variant?.context?.trim() || variant?.english?.trim() || "";
    if (text) {
      signContext.textContent = text;
      signContext.hidden = false;
    } else {
      signContext.textContent = "";
      signContext.hidden = true;
    }
  }

  function hideVideoExtras() {
    if (signContext) {
      signContext.textContent = "";
      signContext.hidden = true;
    }
    if (variantControls) variantControls.hidden = true;
  }

  function setActiveToken(index, options = {}) {
    const { instant = false } = options;
    let activeBtn = null;
    const previousBtn = glossContainer.querySelector(".gloss-token--active");
    const buttons = glossContainer.querySelectorAll(".gloss-token");

    buttons.forEach((btn) => {
      const tokenIndex = Number(btn.dataset.tokenIndex);
      if (tokenIndex === index) {
        activeBtn = btn;
      }
    });

    if (!activeBtn) {
      return;
    }

    const fromBox =
      !instant && previousBtn && previousBtn !== activeBtn
        ? measureButtonBox(previousBtn)
        : null;

    buttons.forEach((btn) => {
      const tokenIndex = Number(btn.dataset.tokenIndex);
      const isActive = btn === activeBtn;
      btn.classList.toggle("gloss-token--active", isActive);
      btn.setAttribute("aria-pressed", isActive ? "true" : "false");
    });

    moveGlossSelectorToButton(activeBtn, { instant: instant || !fromBox, fromBox });

    if (!glossLabelsReady) {
      revealGlossLabels();
    }
    syncGlossLabelOverlays();
  }

  function updateReportButtons() {
    if (!currentResult) {
      if (reportGlossBtn) reportGlossBtn.hidden = true;
      if (reportVideoBtn) reportVideoBtn.hidden = true;
      return;
    }
    if (reportGlossBtn) {
      reportGlossBtn.hidden = currentResult.glossTokens.length === 0;
    }
    if (reportVideoBtn) {
      const variant = getActiveVariant(activeSignIndex);
      reportVideoBtn.hidden = !(variant?.submissionId && variant?.videoUrl);
    }
  }

  function updateVideoMeta(token, variant) {
    const targets = [signLabel];
    if (variant && signContext) targets.push(signContext);
    targets.forEach((el) => el?.classList.add("is-swapping"));
    window.setTimeout(() => {
      signLabel.textContent = token;
      if (variant) {
        updateSignContext(variant);
      }
      targets.forEach((el) => el?.classList.remove("is-swapping"));
    }, 130);
  }

  function showSign(index, options = {}) {
    if (!currentResult) return;
    activeSignIndex = index;
    const token = currentResult.glossTokens[index];
    const variant = getActiveVariant(index);

    setActiveToken(index, options);
    updateVideoMeta(token, variant?.videoUrl ? variant : null);

    video.pause();
    videoScreen?.classList.add("is-loading");
    video.removeAttribute("src");
    video.load();

    if (variant?.videoUrl) {
      video.src = variant.videoUrl;
      video.addEventListener(
        "loadeddata",
        () => {
          videoScreen?.classList.remove("is-loading");
        },
        { once: true },
      );
      placeholder.hidden = true;
      missingLink.hidden = true;
      updateSignContext(variant);
      updateVariantControls(index);
    } else {
      videoScreen?.classList.remove("is-loading");
      hideVideoExtras();
      placeholder.hidden = false;
      missingLink.hidden = false;
      const submitUrl = `/submit?english=${encodeURIComponent(token)}`;
      missingLink.href = submitUrl;
      const linkLabel = missingLink.querySelector("span");
      if (linkLabel) {
        linkLabel.textContent = `No community video for “${token}” yet — submit one`;
      }
    }
    updateReportButtons();
  }

  function cycleVariant(direction) {
    const variants = getVariants(activeSignIndex);
    if (variants.length < 2) return;
    const current = getVariantIndex(activeSignIndex);
    const next = current + direction;
    if (next < 0 || next >= variants.length) return;
    variantIndexByToken.set(activeSignIndex, next);
    showSign(activeSignIndex);
  }

  function createTokenButton(token, index, result) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "gloss-token";
    btn.dataset.tokenIndex = String(index);
    btn.style.setProperty("--stagger", String(index));
    const variants = result.signVariants?.[index] || [];
    if (variants.length) {
      btn.classList.add("gloss-token--has-video");
    }
    if (variants.length > 1) {
      btn.classList.add("gloss-token--ambiguous");
      btn.dataset.variantCount = String(variants.length);
    }
    const label = document.createElement("span");
    label.className = "gloss-token__label";
    label.textContent = token;
    const bg = document.createElement("span");
    bg.className = "gloss-token__bg";
    bg.setAttribute("aria-hidden", "true");
    btn.appendChild(bg);
    btn.appendChild(label);
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
    glossSelector = null;
    glossContainer.classList.remove("gloss-tokens--ready");
    resetGlossLabelLayer();
    bindGlossSelectorLayout();
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
    variantIndexByToken.clear();
    sentenceEl.textContent = result.originalSentence;
    renderGlossTokens(result);

    updateReportButtons();
    if (result.glossTokens.length) {
      whenGlossLayoutReady(() => {
        showSign(0, { instant: true });
      });
    }
  }

  function requireLoginForReport() {
    const proceed = window.confirm(
      "Sign in to report incorrect glossing or videos. Go to the login page now?",
    );
    if (proceed) {
      window.location.href = loginUrl;
    }
    return false;
  }

  function openReportDialog(type) {
    if (!currentResult) return;
    if (!loggedIn) {
      requireLoginForReport();
      return;
    }

    pendingReportType = type;
    if (reportError) {
      reportError.hidden = true;
      reportError.textContent = "";
    }
    if (reportMessage) {
      reportMessage.value = "";
    }

    const sentence = currentResult.originalSentence;
    if (type === "gloss") {
      reportIntro.textContent = `Report incorrect ASL gloss for: “${sentence}”`;
    } else {
      const token = currentResult.glossTokens[activeSignIndex];
      reportIntro.textContent = `Report a problem with the video for “${token}”.`;
    }

    reportDialog?.showModal();
    reportMessage?.focus();
  }

  async function submitReport(event) {
    event.preventDefault();
    if (!currentResult || !pendingReportType) return;

    const message = reportMessage?.value.trim() || "";
    if (message.length < 5) {
      if (reportError) {
        reportError.textContent = "Please describe the issue in at least 5 characters.";
        reportError.hidden = false;
      }
      return;
    }

    const payload = {
      type: pendingReportType,
      originalSentence: currentResult.originalSentence,
      glossTokens: currentResult.glossTokens,
      message,
    };

    if (pendingReportType === "video") {
      const variant = getActiveVariant(activeSignIndex);
      payload.glossToken = currentResult.glossTokens[activeSignIndex];
      payload.submissionId = variant?.submissionId || null;
    }

    reportSubmit.disabled = true;
    try {
      const response = await fetch("/api/reports", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
        },
        body: JSON.stringify(payload),
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.error || "Could not submit report.");
      }
      reportDialog?.close();
      window.alert(data.message || "Thank you — your report was submitted.");
    } catch (error) {
      if (reportError) {
        reportError.textContent = error.message;
        reportError.hidden = false;
      }
    } finally {
      reportSubmit.disabled = false;
    }
  }

  variantPrev?.addEventListener("click", () => cycleVariant(-1));
  variantNext?.addEventListener("click", () => cycleVariant(1));

  reportGlossBtn?.addEventListener("click", () => openReportDialog("gloss"));
  reportVideoBtn?.addEventListener("click", () => openReportDialog("video"));
  reportForm?.addEventListener("submit", submitReport);
  reportCancel?.addEventListener("click", () => reportDialog?.close());
  reportDialogClose?.addEventListener("click", () => reportDialog?.close());

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
    setAnimatedPanel(helpPanel, open);
    helpToggle.setAttribute("aria-expanded", open ? "true" : "false");
    helpToggle.classList.toggle("help-toggle--active", open);
  }

  helpToggle?.addEventListener("click", () => {
    setHelpOpen(!helpPanel.classList.contains("is-open"));
  });

  helpClose?.addEventListener("click", () => {
    setHelpOpen(false);
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && helpPanel?.classList.contains("is-open")) {
      setHelpOpen(false);
    }
  });

  document.addEventListener("click", (event) => {
    if (!helpPanel?.classList.contains("is-open")) return;
    const target = event.target;
    if (!(target instanceof Node)) return;
    if (helpPanel.contains(target) || helpToggle?.contains(target)) return;
    setHelpOpen(false);
  });
});
