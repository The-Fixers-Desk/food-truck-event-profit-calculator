const baselineChoices = document.querySelectorAll(
  'input[name="comparison_baseline"]',
);
const baselineStatus = document.querySelector("#baseline-status");
const differencesOnly = document.querySelector("#show-differences-only");
const visibleDifferencesOnly = document.querySelector(
  "#show-differences-only-visible",
);
const scenarioCards = Array.from(document.querySelectorAll(
  ".comparison-identity",
));
const mobileTabs = Array.from(document.querySelectorAll(
  "[data-mobile-scenario]",
));
let selectedScenario = scenarioCards[0]?.dataset.scenarioId;

function updateBaseline() {
  const selected = document.querySelector(
    'input[name="comparison_baseline"]:checked',
  );
  if (!selected) return;
  document.querySelectorAll(".comparison-difference").forEach((difference) => {
    difference.hidden = difference.dataset.baseline !== selected.value;
  });
  scenarioCards.forEach((identity) => {
    identity.querySelector(".baseline-label").hidden =
      identity.dataset.scenarioId !== selected.value;
  });
  baselineStatus.textContent = `Baseline: ${selected.parentElement.textContent.trim()}`;
}

function updateDifferencesOnly(checked = visibleDifferencesOnly.checked) {
  differencesOnly.checked = checked;
  visibleDifferencesOnly.checked = checked;
  document.querySelectorAll("[data-assumption-row]").forEach((row) => {
    row.hidden = checked && row.dataset.identical === "true";
  });
}

function selectScenario(scenarioId) {
  selectedScenario = scenarioId;
  scenarioCards.forEach((card) => {
    const selected = card.dataset.scenarioId === scenarioId;
    card.classList.toggle("is-selected", selected);
    card.setAttribute("aria-pressed", String(selected));
  });
  mobileTabs.forEach((tab) => {
    const selected = tab.dataset.mobileScenario === scenarioId;
    tab.setAttribute("aria-selected", String(selected));
  });
  document.querySelectorAll("[data-scenario-cell]").forEach((cell) => {
    cell.classList.toggle(
      "is-mobile-selected",
      cell.dataset.scenarioCell === scenarioId,
    );
  });
  document.querySelectorAll(".comparison-warning-grid [data-scenario-id]")
    .forEach((warning) => warning.classList.toggle(
      "is-mobile-selected",
      warning.dataset.scenarioId === scenarioId,
    ));
}

baselineChoices.forEach((choice) => {
  choice.addEventListener("change", updateBaseline);
});
visibleDifferencesOnly.addEventListener(
  "change",
  () => updateDifferencesOnly(visibleDifferencesOnly.checked),
);
scenarioCards.forEach((card) => {
  card.addEventListener("click", (event) => {
    if (!event.target.closest("a")) selectScenario(card.dataset.scenarioId);
  });
  card.addEventListener("keydown", (event) => {
    if (["Enter", " "].includes(event.key)) {
      event.preventDefault();
      selectScenario(card.dataset.scenarioId);
    }
  });
});
mobileTabs.forEach((tab) => {
  tab.addEventListener("click", () => selectScenario(tab.dataset.mobileScenario));
});
document.querySelector("#keep-selected-scenario")?.addEventListener(
  "click",
  () => {
    const card = scenarioCards.find(
      (item) => item.dataset.scenarioId === selectedScenario,
    );
    const destination = card?.querySelector("a[href]")?.href;
    if (destination) window.location.assign(destination);
  },
);

updateBaseline();
updateDifferencesOnly(false);
if (selectedScenario) selectScenario(selectedScenario);
