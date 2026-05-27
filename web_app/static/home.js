function setTranslateButtonLoading(button, loading) {
  const label = button.querySelector("span");
  button.disabled = loading;
  if (label) {
    label.textContent = loading ? "Translating…" : "Translate";
  }
}

document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".phrase-chip").forEach((chip) => {
    chip.addEventListener("click", () => {
      const input = document.getElementById("phrase-input");
      const phrase = chip.dataset.phrase;
      if (input && phrase) {
        input.value = phrase;
        setPhrase(phrase);
        document.getElementById("translate-button")?.click();
      }
    });
  });

  initPhraseBar({
    onTranslate: async (phrase) => {
      const button = document.getElementById("translate-button");
      setTranslateButtonLoading(button, true);

      try {
        const data = await fetchTranslation(phrase);
        setTranslationCache(data);
        window.location.href = "/translation";
      } catch (error) {
        const errorEl = document.getElementById("phrase-error");
        if (errorEl) {
          errorEl.textContent = error.message || "Something went wrong.";
          errorEl.hidden = false;
        }
      } finally {
        setTranslateButtonLoading(button, false);
      }
    },
  });
});