const defaultsForm = document.querySelector(".defaults-form");
const entries = document.querySelector("#labor-entries");
const template = document.querySelector("#labor-entry-template");
const addButton = document.querySelector("#add-labor");
const draftKey = "business-defaults-draft";

const laborStatus = document.createElement("p");
laborStatus.className = "visually-hidden";
laborStatus.setAttribute("role", "status");
entries.before(laborStatus);

function updateLaborNames() {
  entries.querySelectorAll(".labor-entry").forEach((entry, index) => {
    entry.setAttribute("role", "group");
    entry.setAttribute("aria-label", `Default labor entry ${index + 1}`);
    entry.querySelector(".remove-labor").setAttribute(
      "aria-label", `Remove default labor entry ${index + 1}`,
    );
  });
}

function connectRemoveButton(button) {
  button.addEventListener("click", () => {
    if (entries.children.length === 1) {
      entries.querySelectorAll("input").forEach((input) => { input.value = ""; });
      entries.querySelector("input").focus();
      laborStatus.textContent = "Default labor entry cleared.";
      scheduleDraftSave();
      return;
    }
    const entry = button.closest(".labor-entry");
    const nextFocus = entry.nextElementSibling?.querySelector("input")
      ?? entry.previousElementSibling?.querySelector("input")
      ?? addButton;
    entry.remove();
    updateLaborNames();
    laborStatus.textContent = "Default labor entry removed.";
    nextFocus.focus();
    scheduleDraftSave();
  });
}

function addLaborEntry(rate = "", hours = "", focus = true) {
  const fragment = template.content.cloneNode(true);
  const entry = fragment.querySelector(".labor-entry");
  entry.querySelector('[name="labor_rate"]').value = rate;
  entry.querySelector('[name="labor_hours"]').value = hours;
  connectRemoveButton(entry.querySelector(".remove-labor"));
  entries.append(fragment);
  updateLaborNames();
  if (focus) entries.lastElementChild.querySelector("input").focus();
}

entries.querySelectorAll(".remove-labor").forEach(connectRemoveButton);
updateLaborNames();
addButton.addEventListener("click", () => {
  addLaborEntry();
  laborStatus.textContent = "Default labor entry added.";
  scheduleDraftSave();
});

const targetChoices = document.querySelectorAll('input[name="profit_target_type"]');
const amountField = document.querySelector("#profit-amount-field");
const amountInput = document.querySelector("#minimum_profit_amount");
const marginField = document.querySelector("#profit-margin-field");
const marginInput = document.querySelector("#minimum_profit_margin");

function updateProfitTarget(clearHidden = false) {
  const selected = document.querySelector(
    'input[name="profit_target_type"]:checked',
  )?.value;
  const showAmount = selected === "profit_amount";
  const showMargin = selected === "profit_margin";
  amountField.hidden = !showAmount;
  amountInput.required = showAmount;
  marginField.hidden = !showMargin;
  marginInput.required = showMargin;
  if (clearHidden && !showAmount) amountInput.value = "";
  if (clearHidden && !showMargin) marginInput.value = "";
}

targetChoices.forEach((choice) => {
  choice.addEventListener("change", () => {
    updateProfitTarget(true);
    scheduleDraftSave();
  });
});
updateProfitTarget();

const foodMethodChoice = document.querySelector("#food_cost_method_choice");
const confirmedFoodMethod = document.querySelector("#food_cost_method");
const confirmFoodMethod = document.querySelector("#confirm-food-cost-method");
const foodCostFields = {
  average_per_order: {
    container: document.querySelector("#average-food-cost-field"),
    input: document.querySelector("#average_food_cost_per_order"),
  },
  sales_percentage: {
    container: document.querySelector("#food-cost-percentage-field"),
    input: document.querySelector("#food_cost_percentage"),
  },
  typical_event_total: {
    container: document.querySelector("#typical-food-cost-field"),
    input: document.querySelector("#typical_food_cost_total"),
  },
};

function showConfirmedFoodMethod() {
  Object.entries(foodCostFields).forEach(([method, field]) => {
    const selected = confirmedFoodMethod.value === method;
    field.container.hidden = !selected;
    field.input.required = selected;
  });
}

confirmFoodMethod.addEventListener("click", () => {
  const nextMethod = foodMethodChoice.value;
  if (confirmedFoodMethod.value !== nextMethod) {
    Object.entries(foodCostFields).forEach(([method, field]) => {
      if (method !== nextMethod) field.input.value = "";
    });
  }
  confirmedFoodMethod.value = nextMethod;
  showConfirmedFoodMethod();
  foodCostFields[nextMethod].input.focus();
  scheduleDraftSave();
});
showConfirmedFoodMethod();

document.querySelector(".error-summary")?.focus();
document.querySelectorAll('[aria-invalid="true"]').forEach((input, index) => {
  const error = input.closest(".form-field, fieldset")?.querySelector(".field-error");
  if (!error) return;
  error.id ||= `defaults-field-error-${index + 1}`;
  const describedBy = new Set(
    (input.getAttribute("aria-describedby") ?? "").split(" ").filter(Boolean),
  );
  describedBy.add(error.id);
  input.setAttribute("aria-describedby", Array.from(describedBy).join(" "));
});

const defaultsNavigation = document.querySelector("[data-defaults-navigation]");
const defaultsSections = Array.from(document.querySelectorAll("[data-defaults-section]"));
const defaultsPage = document.querySelector(".defaults-page");
const buttons = Array.from(defaultsNavigation.querySelectorAll("[data-defaults-target]"));
const backButton = document.querySelector("#defaults-back");
const continueButton = document.querySelector("#defaults-continue");
const saveButton = document.querySelector("#save-defaults");
const finishLaterButton = document.querySelector("#defaults-finish-later");
const saveStatus = document.querySelector("#defaults-save-status");
const wizardStep = document.querySelector("#wizard_step");
const initialSetup = defaultsPage.dataset.initialSetup === "true";
let activeSection = Number(defaultsPage.dataset.initialStep || 1);
let completedThrough = initialSetup ? 0 : 4;
let saveTimer;

const operatingSection = document.querySelector('[data-defaults-section="4"]');
operatingSection.append(
  document.querySelector("#card_processing_percentage").closest(".form-field"),
  document.querySelector("#default_travel_cost").closest(".form-field"),
);

function sectionFields(number) {
  return defaultsSections
    .filter((section) => Number(section.dataset.defaultsSection) === number)
    .flatMap((section) => Array.from(section.querySelectorAll("input, select, textarea")));
}

function draftData() {
  const fields = {};
  new FormData(defaultsForm).forEach((value, name) => {
    if (name === "labor_rate" || name === "labor_hours") return;
    fields[name] = value;
  });
  return {
    fields,
    laborRates: Array.from(defaultsForm.querySelectorAll('[name="labor_rate"]'), (input) => input.value),
    laborHours: Array.from(defaultsForm.querySelectorAll('[name="labor_hours"]'), (input) => input.value),
    activeSection,
    completedThrough,
  };
}

function saveDraft() {
  window.localStorage.setItem(draftKey, JSON.stringify(draftData()));
  saveStatus.textContent = "Progress saved automatically";
}

function scheduleDraftSave() {
  window.clearTimeout(saveTimer);
  saveStatus.textContent = "Saving progress…";
  saveTimer = window.setTimeout(saveDraft, 350);
}

function restoreDraft() {
  if (!initialSetup || document.querySelector('[aria-invalid="true"], .field-error')) return;
  const raw = window.localStorage.getItem(draftKey);
  if (!raw) return;
  try {
    const draft = JSON.parse(raw);
    Object.entries(draft.fields ?? {}).forEach(([name, value]) => {
      const controls = defaultsForm.elements.namedItem(name);
      if (!controls) return;
      if (controls instanceof RadioNodeList) {
        Array.from(controls).forEach((control) => { control.checked = control.value === value; });
      } else {
        controls.value = value;
      }
    });
    if (draft.laborRates?.length) {
      entries.replaceChildren();
      draft.laborRates.forEach((rate, index) => {
        addLaborEntry(rate, draft.laborHours?.[index] ?? "", false);
      });
    }
    activeSection = Number(draft.activeSection || 1);
    completedThrough = Number(draft.completedThrough || 0);
    updateProfitTarget();
    showConfirmedFoodMethod();
  } catch {
    window.localStorage.removeItem(draftKey);
  }
}

function fieldSummary(field) {
  if (!field.name || !field.value || field.closest("[hidden]")) return null;
  if (field.type === "radio" && !field.checked) return null;
  if (["hidden", "button", "submit"].includes(field.type)) return null;
  const label = field.labels?.[0]?.textContent.trim();
  return label ? `${label}: ${field.value}` : null;
}

function updateDefaultsReview() {
  const review = document.querySelector("#defaults-review-summary");
  review.replaceChildren();
  for (let number = 1; number <= 4; number += 1) {
    const summarySection = document.createElement("section");
    summarySection.className = "review-section";
    const heading = document.createElement("h3");
    heading.textContent = buttons[number - 1].querySelector("strong").textContent;
    const values = sectionFields(number).map(fieldSummary).filter(Boolean);
    const summary = document.createElement("p");
    summary.textContent = values.length ? values.join(" · ") : "No optional value entered.";
    const edit = document.createElement("button");
    edit.type = "button";
    edit.className = "button-secondary button--small";
    edit.textContent = "Edit";
    edit.addEventListener("click", () => showDefaultsSection(number));
    summarySection.append(heading, summary, edit);
    review.append(summarySection);
  }
}

function showDefaultsSection(number) {
  activeSection = Math.max(1, Math.min(5, number));
  wizardStep.value = String(activeSection);
  defaultsSections.forEach((section) => {
    section.hidden = Number(section.dataset.defaultsSection) !== activeSection;
  });
  buttons.forEach((button) => {
    const target = Number(button.dataset.defaultsTarget);
    const active = target === activeSection;
    button.classList.toggle("is-active", active);
    button.classList.toggle("is-complete", target <= completedThrough);
    button.setAttribute("aria-current", active ? "step" : "false");
    button.disabled = target > completedThrough + 1 && !active;
    const marker = button.querySelector(".stage-completion-indicator");
    marker.textContent = target <= completedThrough ? "✓" : String(target);
  });
  backButton.hidden = activeSection === 1;
  continueButton.hidden = activeSection === 5;
  saveButton.hidden = activeSection !== 5;
  if (activeSection === 5) updateDefaultsReview();
}

function validateDefaultsSection() {
  if (activeSection === 2 && !confirmedFoodMethod.value) {
    foodMethodChoice.setCustomValidity("Confirm a food cost method.");
    foodMethodChoice.reportValidity();
    foodMethodChoice.focus();
    return false;
  }
  foodMethodChoice.setCustomValidity("");
  const invalid = sectionFields(activeSection).find((field) => (
    !field.closest("[hidden]") && !field.checkValidity()
  ));
  if (!invalid) return true;
  invalid.reportValidity();
  invalid.focus();
  buttons.find((button) => Number(button.dataset.defaultsTarget) === activeSection)
    ?.classList.add("has-error");
  return false;
}

restoreDraft();
defaultsSections.forEach((section) => {
  if (section.querySelector('[aria-invalid="true"], .field-error')) {
    activeSection = Number(section.dataset.defaultsSection);
    completedThrough = Math.max(0, activeSection - 1);
    buttons.find((button) => button.dataset.defaultsTarget === section.dataset.defaultsSection)
      ?.classList.add("has-error");
  }
});

buttons.forEach((button) => {
  button.addEventListener("click", () => {
    const target = Number(button.dataset.defaultsTarget);
    if (target <= completedThrough + 1) {
      showDefaultsSection(target);
      saveDraft();
    }
  });
});
backButton.addEventListener("click", () => {
  showDefaultsSection(activeSection - 1);
  saveDraft();
});
continueButton.addEventListener("click", () => {
  if (!validateDefaultsSection()) return;
  completedThrough = Math.max(completedThrough, activeSection);
  showDefaultsSection(activeSection + 1);
  saveDraft();
});

defaultsForm.addEventListener("input", scheduleDraftSave);
defaultsForm.addEventListener("change", scheduleDraftSave);
defaultsForm.addEventListener("focusout", (event) => {
  if (event.target.matches("input, select, textarea")) saveDraft();
});
defaultsForm.addEventListener("submit", (event) => {
  if (activeSection !== 5) {
    event.preventDefault();
    return;
  }
  window.localStorage.removeItem(draftKey);
});

finishLaterButton.addEventListener("click", async () => {
  saveDraft();
  finishLaterButton.disabled = true;
  saveStatus.textContent = "Saving progress…";
  try {
    const response = await fetch(defaultsForm.dataset.finishLaterUrl, { method: "POST" });
    window.location.assign(response.url);
  } catch {
    finishLaterButton.disabled = false;
    saveStatus.textContent = "Progress is saved on this device. Try returning to the Dashboard again.";
  }
});

showDefaultsSection(activeSection);
const firstDefaultsError = document.querySelector('[aria-invalid="true"]');
if (firstDefaultsError) window.requestAnimationFrame(() => firstDefaultsError.focus());
