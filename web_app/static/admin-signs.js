document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".admin-delete-form").forEach((form) => {
    form.addEventListener("submit", (event) => {
      const gloss = form.dataset.gloss || "this submission";
      const ok = window.confirm(
        `Permanently delete “${gloss}”? This removes the video and cannot be undone.`,
      );
      if (!ok) {
        event.preventDefault();
      }
    });
  });
});
