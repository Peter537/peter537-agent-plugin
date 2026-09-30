const allowed = new URLSearchParams(location.search).get("state") !== "denied";
const action = document.querySelector("#quarantine");
const dialog = document.querySelector("#confirmation");
const note = document.querySelector("#permission-note");
action.disabled = !allowed;
note.textContent = allowed ? "You may record a quarantine decision." : "You have read-only access. You may inspect evidence; contact the shift lead to request decision permission.";
function requestDecision() { if (allowed) dialog.showModal(); }
action.addEventListener("click", requestDecision);
document.addEventListener("keydown", event => {
  if (event.altKey && event.key.toLowerCase() === "q") { event.preventDefault(); requestDecision(); }
});
document.querySelector("#cancel").addEventListener("click", () => { dialog.close(); action.focus(); });
document.querySelector("#confirm").addEventListener("click", () => {
  if (!allowed) return;
  document.querySelector("#decision-result").textContent = "Demonstration decision: S-42 quarantined.";
  dialog.close(); action.focus();
});
