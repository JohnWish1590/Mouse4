(() => {
  const buttons = document.querySelectorAll("[data-theme-choice]");

  buttons.forEach((button) => {
    button.addEventListener("click", () => {
      const theme = button.dataset.themeChoice;
      document.body.dataset.theme = theme;
      buttons.forEach((item) => item.classList.toggle("is-active", item === button));
    });
  });
})();
