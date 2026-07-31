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
    choices.forEach((choice) => {
      choice.closest(".selection-row")?.classList.toggle(
        "is-selected", choice.checked,
      );
    });
  }

  choices.forEach((choice) => {
    choice.addEventListener("change", () => {
      updateComparisonSelection(choice);
    });
  });
  updateComparisonSelection();
  comparisonForm.addEventListener("submit", () => {
    compareButton.disabled = true;
    compareButton.classList.add("is-loading");
    compareButton.setAttribute("aria-busy", "true");
    compareButton.textContent = "Comparing…";
  });
}

document.querySelectorAll(".management-action form").forEach((form) => {
  form.addEventListener("submit", () => {
    const button = form.querySelector('button[type="submit"]');
    if (!button) return;
    button.disabled = true;
    button.classList.add("is-loading");
    button.setAttribute("aria-busy", "true");
    button.textContent = button.textContent.trim().startsWith("Delete")
      ? "Deleting…" : "Renaming…";
  });
});

const savedWorkSearch = document.querySelector("#saved-work-search");
const savedWorkSort = document.querySelector("#saved-work-sort");
const savedEventList = document.querySelector("#saved-event-list");

if (savedWorkSearch && savedWorkSort && savedEventList) {
  const clearSearch = document.querySelector("#clear-saved-work-search");
  const clearNoResults = document.querySelector("#clear-saved-work-no-results");
  const noResults = document.querySelector("#saved-work-no-results");
  const filterStatus = document.querySelector("#saved-work-filter-status");

  function filterSavedWork() {
    const query = savedWorkSearch.value.trim().toLocaleLowerCase();
    let visibleEvents = 0;
    savedEventList.querySelectorAll(".event-library-row").forEach((event) => {
      const eventMatches = event.dataset.eventName
        .toLocaleLowerCase().includes(query);
      let matchingScenarios = 0;
      event.querySelectorAll(".scenario-row").forEach((scenario) => {
        const matches = !query || eventMatches || scenario.dataset.scenarioName
          .toLocaleLowerCase().includes(query);
        scenario.hidden = !matches;
        if (matches) matchingScenarios += 1;
      });
      event.hidden = matchingScenarios === 0;
      if (!event.hidden) visibleEvents += 1;
    });
    clearSearch.hidden = !query;
    noResults.hidden = visibleEvents !== 0 || !query;
    filterStatus.textContent = query
      ? `${visibleEvents} matching Event${visibleEvents === 1 ? "" : "s"}.`
      : "Showing all saved Events.";
  }

  function sortSavedWork() {
    const events = Array.from(savedEventList.querySelectorAll(
      ".event-library-row",
    ));
    const sort = savedWorkSort.value;
    events.sort((left, right) => {
      if (sort === "name") {
        return left.dataset.eventName.localeCompare(
          right.dataset.eventName, undefined, { sensitivity: "base" },
        );
      }
      if (sort === "event-date") {
        return right.dataset.eventDate.localeCompare(left.dataset.eventDate);
      }
      return right.dataset.modified.localeCompare(left.dataset.modified);
    });
    events.forEach((event) => savedEventList.append(event));
  }

  function resetSearch() {
    savedWorkSearch.value = "";
    filterSavedWork();
    savedWorkSearch.focus();
  }

  savedWorkSearch.addEventListener("input", filterSavedWork);
  savedWorkSort.addEventListener("change", sortSavedWork);
  clearSearch.addEventListener("click", resetSearch);
  clearNoResults.addEventListener("click", resetSearch);
  sortSavedWork();
  filterSavedWork();
}
