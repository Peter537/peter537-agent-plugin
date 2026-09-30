const approve = document.querySelector("[data-testid='approve']");
const reject = document.querySelector("[data-testid='reject']");
const reason = document.querySelector("#reason");
const error = document.querySelector("[data-testid='decision-error']");
const caseTitle = document.querySelector("[data-testid='case-title']");
if (new URLSearchParams(location.search).get("content") === "short") {
  caseTitle.textContent = "Leverandørens erklæring";
}

approve.addEventListener("click", () => { error.hidden = true; });
reject.addEventListener("click", () => { error.hidden = Boolean(reason.value.trim()); });
document.addEventListener("keydown", event => {
  if (event.altKey && event.key === "a") approve.click();
  if (event.altKey && event.key === "r") reject.click();
});
