const approve = document.querySelector("[data-testid='approve']");
const reject = document.querySelector("[data-testid='reject']");
const reason = document.querySelector("#reason");
const error = document.querySelector("[data-testid='decision-error']");

approve.addEventListener("click", () => { error.hidden = true; });
reject.addEventListener("click", () => { error.hidden = Boolean(reason.value.trim()); });
document.addEventListener("keydown", event => {
  if (event.altKey && event.key === "a") approve.click();
  if (event.altKey && event.key === "r") reject.click();
});
