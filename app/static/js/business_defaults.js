const entries = document.querySelector("#labor-entries");
const template = document.querySelector("#labor-entry-template");
const addButton = document.querySelector("#add-labor");

function connectRemoveButton(button) {
  button.addEventListener("click", () => {
    button.closest(".labor-entry").remove();
  });
}

entries.querySelectorAll(".remove-labor").forEach(connectRemoveButton);

addButton.addEventListener("click", () => {
  const entry = template.content.cloneNode(true);
  connectRemoveButton(entry.querySelector(".remove-labor"));
  entries.append(entry);
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

const defaultsNavigation = document.querySelector("[data-defaults-navigation]");
const defaultsSections = Array.from(
  document.querySelectorAll("[data-defaults-section]"),
);

if (defaultsNavigation && defaultsSections.length) {
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
  const initial = Number(
    defaultsSections.find((section) => section.querySelector('[aria-invalid="true"]'))
      ?.dataset.defaultsSection ?? 1,
  );
  function showDefaultsSection(number) {
    defaultsSections.forEach((section) => {
      section.hidden = Number(section.dataset.defaultsSection) !== number;
    });
    buttons.forEach((button) => {
      const active = Number(button.dataset.defaultsTarget) === number;
      button.classList.toggle("is-active", active);
      button.setAttribute("aria-current", active ? "page" : "false");
    });
  }
  defaultsSections.forEach((section) => {
    if (section.querySelector('[aria-invalid="true"]')) {
      buttons.find((button) => (
        button.dataset.defaultsTarget === section.dataset.defaultsSection
      ))?.classList.add("has-error");
    }
  });
  buttons.forEach((button) => {
    button.addEventListener("click", () => {
      showDefaultsSection(Number(button.dataset.defaultsTarget));
    });
  });
  showDefaultsSection(initial);
}
