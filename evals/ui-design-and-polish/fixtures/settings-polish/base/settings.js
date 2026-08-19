const form = document.querySelector("[data-testid='account-settings']");
const nameInput = document.querySelector("[data-testid='display-name']");
const error = document.querySelector("#display-name-error");
const save = document.querySelector("[data-testid='save-settings']");
const status = document.querySelector("[data-testid='save-status']");

form.addEventListener("submit", event => {
  event.preventDefault();
  error.hidden = Boolean(nameInput.value.trim());
  if (!error.hidden) return;
  save.disabled = true;
  status.textContent = "Saving…";
  setTimeout(() => {
    save.disabled = false;
    status.textContent = "Settings saved.";
  }, 50);
});
