// Supplied synthetic records; no service or persistence is represented.
const records = [
  {id: "R-101", severity: "Critical", owner: "Relay", age: 48, evidence: "Acknowledgements delayed"},
  {id: "R-102", severity: "Warning", owner: "Storage", age: 42, evidence: "Archive queue above threshold"},
  {id: "R-103", severity: "Critical", owner: "Relay", age: 37, evidence: "Repeated delivery timeout"},
  {id: "R-104", severity: "Warning", owner: "Storage", age: 31, evidence: "Index refresh pending"},
  {id: "R-105", severity: "Warning", owner: "Relay", age: 26, evidence: "Retry budget nearly exhausted"},
  {id: "R-106", severity: "Warning", owner: "Storage", age: 23, evidence: "Snapshot awaiting validation"},
  {id: "R-107", severity: "Critical", owner: "Relay", age: 18, evidence: "Delivery workers unavailable"},
  {id: "R-108", severity: "Warning", owner: "Storage", age: 14, evidence: "Export queue delayed"},
  {id: "R-109", severity: "Warning", owner: "Relay", age: 11, evidence: "Receiver confirmation pending"},
  {id: "R-110", severity: "Warning", owner: "Storage", age: 9, evidence: "Compaction queued"},
  {id: "R-111", severity: "Warning", owner: "Relay", age: 6, evidence: "Transient connection failure"},
  {id: "R-112", severity: "Warning", owner: "Storage", age: 3, evidence: "Integrity check pending"}
];
const selected = new Set();
const filter = document.querySelector("#filter");
const sort = document.querySelector("#sort");
let oldest = true;
function render() {
  const visible = records.filter(row => filter.value === "all" || row.owner === filter.value).sort((a,b) => oldest ? b.age-a.age : a.age-b.age);
  document.querySelector("#rows").innerHTML = visible.map(row => `<tr data-record="${row.id}"><td><input type="checkbox" aria-label="Select ${row.id}" data-select="${row.id}" ${selected.has(row.id) ? "checked" : ""}></td><th scope="row">${row.id}</th><td>${row.severity}</td><td>${row.owner}</td><td>${row.age}</td><td><button type="button" data-open="${row.id}">Open ${row.id}</button></td></tr>`).join("");
  document.querySelector("#selection").textContent = selected.size ? `${selected.size} relay selected.` : "No relay selected.";
  sort.textContent = oldest ? "Oldest first" : "Newest first";
  document.querySelector("#age-heading").setAttribute("aria-sort", oldest ? "descending" : "ascending");
}
filter.addEventListener("change", render);
sort.addEventListener("click", () => { oldest = !oldest; render(); });
document.querySelector("#rows").addEventListener("change", event => {
  const id = event.target.dataset.select;
  if (id) { event.target.checked ? selected.add(id) : selected.delete(id); document.querySelector("#selection").textContent = selected.size ? `${selected.size} relay selected.` : "No relay selected."; }
});
document.querySelector("#rows").addEventListener("click", event => {
  const row = records.find(item => item.id === event.target.dataset.open);
  if (row) document.querySelector("[data-testid='evidence-detail']").textContent = `${row.id}: ${row.evidence}`;
});
render();
