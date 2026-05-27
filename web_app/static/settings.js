document.addEventListener("DOMContentLoaded", () => {
  const lightBtn = document.getElementById("theme-light");
  const darkBtn = document.getElementById("theme-dark");

  function syncButtons() {
    const theme = getTheme();
    lightBtn.classList.toggle("theme-toggle__btn--active", theme === "light");
    darkBtn.classList.toggle("theme-toggle__btn--active", theme === "dark");
  }

  lightBtn.addEventListener("click", () => {
    applyTheme("light");
    syncButtons();
  });

  darkBtn.addEventListener("click", () => {
    applyTheme("dark");
    syncButtons();
  });

  syncButtons();
});
