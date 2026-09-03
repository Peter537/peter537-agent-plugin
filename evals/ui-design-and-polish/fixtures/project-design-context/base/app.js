const panels = [...document.querySelectorAll("[data-state-panel]")];
const requestedState = new URLSearchParams(window.location.search).get("state") || "populated";
const activeState = panels.some(panel => panel.dataset.statePanel === requestedState) ? requestedState : "populated";

for (const panel of panels) {
  panel.hidden = panel.dataset.statePanel !== activeState;
}

for (const stateLink of document.querySelectorAll("[data-state-link]")) {
  if (stateLink.dataset.stateLink === activeState) {
    stateLink.setAttribute("aria-current", "page");
  } else {
    stateLink.removeAttribute("aria-current");
  }
}

const quarantine = document.querySelector("[data-testid='quarantine']");
const dialog = document.querySelector("[data-testid='quarantine-dialog']");

if (quarantine && activeState === "populated") {
  quarantine.addEventListener("click", () => dialog.showModal());
  document.addEventListener("keydown", event => {
    if (event.altKey && event.key.toLowerCase() === "q") {
      event.preventDefault();
      quarantine.focus();
    }
  });
}
