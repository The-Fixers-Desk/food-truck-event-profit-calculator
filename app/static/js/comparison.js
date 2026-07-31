const baselineChoices = document.querySelectorAll(
  'input[name="comparison_baseline"]',
);
const baselineStatus = document.querySelector("#baseline-status");
const differencesOnly = document.querySelector("#show-differences-only");

function updateBaseline() {
  const selected = document.querySelector(
    'input[name="comparison_baseline"]:checked',
  );
  if (!selected) {
    return;
  }
  document.querySelectorAll(".comparison-difference").forEach((difference) => {
    difference.hidden = difference.dataset.baseline !== selected.value;
  });
  document.querySelectorAll(".comparison-identity").forEach((identity) => {
    identity.querySelector(".baseline-label").hidden =
      identity.dataset.scenarioId !== selected.value;
  });
  baselineStatus.textContent =
    `Baseline: ${selected.parentElement.textContent.trim()}`;
}

function updateDifferencesOnly() {
  document.querySelectorAll("[data-assumption-row]").forEach((row) => {
    row.hidden = differencesOnly.checked && row.dataset.identical === "true";
  });
}

baselineChoices.forEach((choice) => {
  choice.addEventListener("change", updateBaseline);
});
differencesOnly.addEventListener("change", updateDifferencesOnly);
updateBaseline();
updateDifferencesOnly();
