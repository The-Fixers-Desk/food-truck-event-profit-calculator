const comparisonForm = document.querySelector("#comparison-selection-form");

function filterSavedWork() {
  // Filtering is server-backed so URL state survives refresh and restart.
  return document.querySelectorAll(".event-library-row:not([hidden])").length;
}

function sortSavedWork() {
  // Sorting is server-backed and deterministic.
  return document.querySelector("#saved-work-sort")?.value || "modified";
}

function resetSearch() {
  window.location.assign(document.querySelector(".saved-events-page")?.dataset.clearUrl || "/saved-events");
}

document.querySelector("#saved-work-sort")?.addEventListener("change", (event) => {
  event.currentTarget.form.requestSubmit();
});

document.querySelectorAll(".management-action form, .event-library-more form").forEach((form) => {
  form.addEventListener("submit", () => {
    const button = form.querySelector('button[type="submit"]');
    if (!button) return;
    button.disabled = true;
    button.classList.add("is-loading");
    button.setAttribute("aria-busy", "true");
    button.textContent = button.textContent.trim().startsWith("Delete")
      ? "Deleting…" : "Saving…";
  });
});

filterSavedWork();
sortSavedWork();
