const comparisonForm = document.querySelector(
  "#comparison-selection-form",
);

if (comparisonForm) {
  const choices = document.querySelectorAll(
    'input[name="scenario_id"][form="comparison-selection-form"]',
  );
  const compareButton = document.querySelector("#compare-selected");
  const status = document.querySelector("#comparison-selection-status");

  function updateComparisonSelection(changedChoice = null) {
    let selected = Array.from(choices).filter((choice) => choice.checked);
    if (selected.length > 4 && changedChoice) {
      changedChoice.checked = false;
      selected = Array.from(choices).filter((choice) => choice.checked);
      status.textContent = "Select no more than four Scenarios.";
    } else if (selected.length < 2) {
      status.textContent = "Select two to four Scenarios.";
    } else {
      status.textContent = `${selected.length} Scenarios selected.`;
    }
    compareButton.disabled = selected.length < 2 || selected.length > 4;
  }

  choices.forEach((choice) => {
    choice.addEventListener("change", () => {
      updateComparisonSelection(choice);
    });
  });
  updateComparisonSelection();
}
