const entries = document.querySelector("#labor-entries");
const template = document.querySelector("#labor-entry-template");
const addButton = document.querySelector("#add-labor");
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
    const entry = button.closest(".labor-entry");
    const nextFocus = entry.nextElementSibling?.querySelector("input")
      ?? entry.previousElementSibling?.querySelector("input")
      ?? addButton;
    entry.remove();
    updateLaborNames();
    laborStatus.textContent = "Default labor entry removed.";
    nextFocus.focus();
  });
}

entries.querySelectorAll(".remove-labor").forEach(connectRemoveButton);
updateLaborNames();

addButton.addEventListener("click", () => {
  const entry = template.content.cloneNode(true);
  connectRemoveButton(entry.querySelector(".remove-labor"));
  entries.append(entry);
  updateLaborNames();
  entries.lastElementChild.querySelector("input").focus();
  laborStatus.textContent = "Default labor entry added.";
});

const targetChoices = document.querySelectorAll(
  'input[name="profit_target_type"]',
);
const amountField = document.querySelector("#profit-amount-field");
const amountInput = document.querySelector("#minimum_profit_amount");
const marginField = document.querySelector("#profit-margin-field");
const marginInput = document.querySelector("#minimum_profit_margin");

function updateProfitTarget() {
  const selected = document.querySelector(
    'input[name="profit_target_type"]:checked',
  )?.value;
  const showAmount = selected === "profit_amount";
  const showMargin = selected === "profit_margin";

  amountField.hidden = !showAmount;
  amountInput.required = showAmount;
  marginField.hidden = !showMargin;
  marginInput.required = showMargin;

  if (!showAmount) {
    amountInput.value = "";
  }
  if (!showMargin) {
    marginInput.value = "";
  }
}

targetChoices.forEach((choice) => {
  choice.addEventListener("change", updateProfitTarget);
});
updateProfitTarget();

const foodMethodChoice = document.querySelector("#food_cost_method_choice");
const confirmedFoodMethod = document.querySelector("#food_cost_method");
const confirmFoodMethod = document.querySelector(
  "#confirm-food-cost-method",
);
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
      if (method !== nextMethod) {
        field.input.value = "";
      }
    });
  }
  confirmedFoodMethod.value = nextMethod;
  showConfirmedFoodMethod();
});

showConfirmedFoodMethod();

document.querySelector(".error-summary")?.focus();
document.querySelectorAll('[aria-invalid="true"]').forEach((input, index) => {
  const error = input.closest(".form-field, fieldset")?.querySelector(".field-error");
  if (!error) return;
  error.id ||= `defaults-field-error-${index + 1}`;
  const describedBy = new Set((input.getAttribute("aria-describedby") ?? "").split(" ").filter(Boolean));
  describedBy.add(error.id);
  input.setAttribute("aria-describedby", Array.from(describedBy).join(" "));
});

const defaultsNavigation = document.querySelector("[data-defaults-navigation]");
const defaultsSections = Array.from(
  document.querySelectorAll("[data-defaults-section]"),
);

if (defaultsNavigation && defaultsSections.length) {
  const defaultsForm = document.querySelector(".defaults-form");
  const paymentSection = document.querySelector('[data-defaults-section="2"]');
  const laborCostSection = document.querySelector('[data-defaults-section="3"]');
  ["card_sales_percentage", "card_processing_percentage"].forEach((id) => {
    paymentSection.append(document.querySelector(`#${id}`).closest(".form-field"));
  });
  laborCostSection.append(
    document.querySelector("#default_travel_cost").closest(".form-field"),
  );
  const buttons = Array.from(
    defaultsNavigation.querySelectorAll("[data-defaults-target]"),
  );
  const backButton = document.querySelector("#defaults-back");
  const continueButton = document.querySelector("#defaults-continue");
  const saveButton = document.querySelector("#save-defaults");
  const progress = document.querySelector("#defaults-progress");
  let activeSection = Number(
    defaultsSections.find((section) => section.querySelector(
      '[aria-invalid="true"], .field-error',
    ))
      ?.dataset.defaultsSection ?? 1,
  );
  let completedThrough = document.querySelector(
    '[aria-invalid="true"], .field-error',
  )
    ? Math.max(0, activeSection - 1) : 0;

  function sectionFields(number) {
    return defaultsSections
      .filter((section) => Number(section.dataset.defaultsSection) === number)
      .flatMap((section) => Array.from(section.querySelectorAll(
        "input, select, textarea",
      )));
  }

  function updateDefaultsReview() {
    const review = document.querySelector("#defaults-review-summary");
    if (!review) return;
    review.replaceChildren();
    for (let number = 1; number <= 4; number += 1) {
      const summarySection = document.createElement("section");
      summarySection.className = "review-section";
      const heading = document.createElement("h3");
      heading.textContent = buttons[number - 1].textContent.trim();
      const values = sectionFields(number)
        .filter((field) => (
          field.name && field.type !== "hidden" && field.value
          && !field.closest("[hidden]")
          && (field.type !== "radio" || field.checked)
        ))
        .slice(0, 4)
        .map((field) => {
          const label = field.labels?.[0]?.textContent.trim();
          return label ? `${label}: ${field.value}` : field.value;
        });
      const summary = document.createElement("p");
      summary.textContent = values.length
        ? values.join(" · ") : "No optional value entered.";
      const edit = document.createElement("button");
      edit.type = "button";
      edit.className = "button-secondary";
      edit.textContent = "Edit";
      edit.addEventListener("click", () => showDefaultsSection(number));
      summarySection.append(heading, summary, edit);
      review.append(summarySection);
    }
  }

  function showDefaultsSection(number) {
    activeSection = number;
    defaultsSections.forEach((section) => {
      section.hidden = Number(section.dataset.defaultsSection) !== number;
    });
    buttons.forEach((button) => {
      const target = Number(button.dataset.defaultsTarget);
      const active = target === number;
      button.classList.toggle("is-active", active);
      button.classList.toggle("is-complete", target <= completedThrough);
      button.setAttribute("aria-current", active ? "step" : "false");
      button.disabled = target > completedThrough + 1 && !active;
    });
    backButton.hidden = number === 1;
    continueButton.hidden = number === 5;
    saveButton.hidden = number !== 5;
    progress.textContent = `Step ${number} of 5`;
    if (number === 5) updateDefaultsReview();
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
    buttons.find((button) => (
      Number(button.dataset.defaultsTarget) === activeSection
    ))?.classList.add("has-error");
    return false;
  }
  defaultsSections.forEach((section) => {
    if (section.querySelector('[aria-invalid="true"], .field-error')) {
      buttons.find((button) => (
        button.dataset.defaultsTarget === section.dataset.defaultsSection
      ))?.classList.add("has-error");
    }
  });
  buttons.forEach((button) => {
    button.addEventListener("click", () => {
      const target = Number(button.dataset.defaultsTarget);
      if (target <= completedThrough + 1) showDefaultsSection(target);
    });
  });
  backButton.addEventListener("click", () => {
    showDefaultsSection(activeSection - 1);
  });
  continueButton.addEventListener("click", () => {
    if (!validateDefaultsSection()) return;
    completedThrough = Math.max(completedThrough, activeSection);
    showDefaultsSection(activeSection + 1);
  });
  defaultsForm.addEventListener("submit", (event) => {
    if (activeSection === 5) return;
    event.preventDefault();
    if (completedThrough >= 4) showDefaultsSection(5);
  });
  showDefaultsSection(activeSection);
}

const firstDefaultsError = document.querySelector('[aria-invalid="true"]')
  ?? document.querySelector("[data-defaults-section] .field-error")
    ?.closest("[data-defaults-section]")?.querySelector("input, select");
if (firstDefaultsError) window.requestAnimationFrame(() => firstDefaultsError.focus());
