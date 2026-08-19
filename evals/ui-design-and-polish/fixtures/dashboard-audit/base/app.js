const status = document.querySelector("#status");
const rows = document.querySelector("#rows");

function render(state) {
  status.textContent = "";
  rows.replaceChildren();
  if (state === "loading") status.textContent = "Loading relay state…";
  if (state === "empty") status.textContent = "No relays need attention.";
  if (state === "error") status.textContent = "Relay state is unavailable. Try again.";
  if (state === "ready") rows.innerHTML = "<tr><td>North</td><td>Delayed</td><td>12 min</td></tr>";
}

document.querySelector("#refresh").addEventListener("click", () => render("loading"));
render(new URLSearchParams(location.search).get("state") || "ready");
