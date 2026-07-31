const weatherOutlook = document.querySelector("#weather_outlook");
const customWeatherField = document.querySelector("#custom-weather-field");
const customWeatherInput = document.querySelector(
  "#custom_weather_reduction",
);
const protectionField = document.querySelector("#event-protection-field");
const protectionChoices = document.querySelectorAll(
  'input[name="event_protection"]',
);

const weatherReductions = {
  favorable: 0,
  minor_concern: 5,
  moderate_adverse: 15,
  significant_adverse: 30,
  severe_disruption: 50,
};
const protectionFactors = {
  fully_indoors: 0.15,
  covered_reliable_seating: 0.5,
  partially_covered: 0.75,
  fully_outdoors: 1,
};

function selectedWeatherReduction() {
  if (weatherOutlook.value === "custom") {
    const customValue = Number(customWeatherInput.value);
    if (
      customWeatherInput.value === ""
      || !Number.isFinite(customValue)
      || customValue < 0
      || customValue > 100
    ) {
      return null;
    }
    return customValue;
  }
  return weatherReductions[weatherOutlook.value] ?? null;
}

function formatPercentage(value) {
  return String(Math.round(value * 100) / 100);
}

function updateWeatherControls() {
  const isCustom = weatherOutlook.value === "custom";
  customWeatherField.hidden = !isCustom;
  customWeatherInput.required = isCustom;
  if (!isCustom) {
    customWeatherInput.value = "";
  }

  const reduction = selectedWeatherReduction();
  protectionField.hidden = reduction === null;
  protectionChoices.forEach((choice) => {
    choice.required = reduction !== null;
    if (reduction === null) {
      choice.checked = false;
    }
  });

  if (reduction !== null) {
    Object.entries(protectionFactors).forEach(([protection, factor]) => {
      document.querySelector(`[data-protection="${protection}"]`).textContent =
        formatPercentage(reduction * factor);
    });
  }
}

weatherOutlook.addEventListener("change", updateWeatherControls);
customWeatherInput.addEventListener("input", updateWeatherControls);
updateWeatherControls();

const revenueMethod = document.querySelector("#revenue_method");
const useCustomSales = document.querySelector("#use-custom-sales");
const customSalesField = document.querySelector("#custom-sales-field");
const expectedSalesAmount = document.querySelector("#expected_sales_amount");
const useCalculatedSales = document.querySelector("#use-calculated-sales");

function updateSalesControls() {
  const customIsActive = revenueMethod.value === "manual_sales";
  useCustomSales.hidden = customIsActive;
  customSalesField.hidden = !customIsActive;
  expectedSalesAmount.required = customIsActive;
  if (!customIsActive) {
    expectedSalesAmount.value = "";
  }
}

useCustomSales.addEventListener("click", () => {
  revenueMethod.value = "manual_sales";
  updateSalesControls();
});

useCalculatedSales.addEventListener("click", () => {
  revenueMethod.value = "attendance";
  updateSalesControls();
});

updateSalesControls();

const eventFoodMethodChoice = document.querySelector(
  "#event_food_cost_method_choice",
);
const confirmedEventFoodMethod = document.querySelector(
  "#event_food_cost_method",
);
const confirmEventFoodMethod = document.querySelector(
  "#confirm-event-food-cost-method",
);
const eventFoodCostFields = {
  average_per_order: {
    container: document.querySelector("#event-average-food-cost-field"),
    input: document.querySelector("#event_average_food_cost_per_order"),
  },
  sales_percentage: {
    container: document.querySelector("#event-food-cost-percentage-field"),
    input: document.querySelector("#event_food_cost_percentage"),
  },
  manual_event_total: {
    container: document.querySelector("#event-manual-food-cost-field"),
    input: document.querySelector("#event_manual_food_cost_total"),
  },
};

function showConfirmedEventFoodMethod() {
  Object.entries(eventFoodCostFields).forEach(([method, field]) => {
    const selected = confirmedEventFoodMethod.value === method;
    field.container.hidden = !selected;
    field.input.required = selected;
  });
  updateFoodDefaultIndicator();
}

confirmEventFoodMethod.addEventListener("click", () => {
  const nextMethod = eventFoodMethodChoice.value;
  if (confirmedEventFoodMethod.value !== nextMethod) {
    Object.entries(eventFoodCostFields).forEach(([method, field]) => {
      if (method !== nextMethod) {
        field.input.value = "";
      }
    });
  }
  confirmedEventFoodMethod.value = nextMethod;
  showConfirmedEventFoodMethod();
});

showConfirmedEventFoodMethod();

function setIndicator(indicator, unchanged) {
  if (indicator) {
    indicator.textContent = unchanged
      ? "From defaults"
      : "Changed for this event";
  }
}

function updateTrackedInputIndicator(input) {
  const indicator = document.querySelector(
    `[data-indicator-for="${input.id}"]`,
  );
  setIndicator(indicator, input.value === input.dataset.defaultValue);
}

document.querySelectorAll("[data-indicator-for]").forEach((indicator) => {
  const input = document.querySelector(`#${indicator.dataset.indicatorFor}`);
  if (input) {
    input.addEventListener("input", () => {
      updateTrackedInputIndicator(input);
    });
    updateTrackedInputIndicator(input);
  }
});

function updateFoodDefaultIndicator() {
  const indicator = document.querySelector("#food-cost-default-indicator");
  if (!indicator) {
    return;
  }
  const tracked = [
    confirmedEventFoodMethod,
    ...Object.values(eventFoodCostFields).map((field) => field.input),
  ];
  setIndicator(
    indicator,
    tracked.every((input) => input.value === input.dataset.defaultValue),
  );
}

Object.values(eventFoodCostFields).forEach((field) => {
  field.input.addEventListener("input", updateFoodDefaultIndicator);
});
updateFoodDefaultIndicator();

const employeeLaborEntries = document.querySelector(
  "#event-employee-labor-entries",
);
const employeeLaborTemplate = document.querySelector(
  "#event-employee-labor-template",
);
const addEmployeeLabor = document.querySelector("#add-event-labor");

function connectEventLaborRemove(button) {
  button.addEventListener("click", () => {
    button.closest(".labor-entry").remove();
  });
}

function connectLaborIndicator(entry) {
  const indicator = entry.querySelector(".labor-default-indicator");
  if (!indicator) {
    return;
  }
  const inputs = entry.querySelectorAll("[data-default-value]");
  const update = () => {
    setIndicator(
      indicator,
      Array.from(inputs).every(
        (input) => input.value === input.dataset.defaultValue,
      ),
    );
  };
  inputs.forEach((input) => input.addEventListener("input", update));
  update();
}

employeeLaborEntries
  .querySelectorAll(".remove-event-labor")
  .forEach(connectEventLaborRemove);
employeeLaborEntries
  .querySelectorAll(".labor-entry")
  .forEach(connectLaborIndicator);

addEmployeeLabor.addEventListener("click", () => {
  const entry = employeeLaborTemplate.content.cloneNode(true);
  connectEventLaborRemove(entry.querySelector(".remove-event-labor"));
  employeeLaborEntries.append(entry);
});

const profitTargetChoices = document.querySelectorAll(
  'input[name="profit_target_type"]',
);
const eventProfitAmountField = document.querySelector(
  "#event-profit-amount-field",
);
const eventProfitAmount = document.querySelector(
  "#event_minimum_profit_amount",
);
const eventProfitMarginField = document.querySelector(
  "#event-profit-margin-field",
);
const eventProfitMargin = document.querySelector(
  "#event_minimum_profit_margin",
);

function updateProfitDefaultIndicator() {
  const indicator = document.querySelector("#profit-target-default-indicator");
  if (!indicator) {
    return;
  }
  const selected = document.querySelector(
    'input[name="profit_target_type"]:checked',
  )?.value ?? "";
  const baselineType = document.querySelector(
    'input[name="baseline_profit_target_type"]',
  ).value;
  setIndicator(
    indicator,
    selected === baselineType
      && eventProfitAmount.value === eventProfitAmount.dataset.defaultValue
      && eventProfitMargin.value === eventProfitMargin.dataset.defaultValue,
  );
}

function updateEventProfitTarget(clearUnselected = false) {
  const selected = document.querySelector(
    'input[name="profit_target_type"]:checked',
  )?.value;
  const showAmount = selected === "profit_amount";
  const showMargin = selected === "profit_margin";
  eventProfitAmountField.hidden = !showAmount;
  eventProfitMarginField.hidden = !showMargin;
  eventProfitAmount.required = showAmount;
  eventProfitMargin.required = showMargin;
  if (clearUnselected && !showAmount) {
    eventProfitAmount.value = "";
  }
  if (clearUnselected && !showMargin) {
    eventProfitMargin.value = "";
  }
  updateProfitDefaultIndicator();
}

profitTargetChoices.forEach((choice) => {
  choice.addEventListener("change", () => updateEventProfitTarget(true));
});
eventProfitAmount.addEventListener("input", updateProfitDefaultIndicator);
eventProfitMargin.addEventListener("input", updateProfitDefaultIndicator);
updateEventProfitTarget();

const additionalCostEntries = document.querySelector(
  "#event-additional-cost-entries",
);
const additionalCostTemplate = document.querySelector(
  "#event-additional-cost-template",
);
const addAdditionalCost = document.querySelector("#add-additional-cost");

function connectAdditionalCostRemove(button) {
  button.addEventListener("click", () => {
    button.closest(".additional-cost-entry").remove();
  });
}

additionalCostEntries
  .querySelectorAll(".remove-additional-cost")
  .forEach(connectAdditionalCostRemove);

addAdditionalCost.addEventListener("click", () => {
  const entry = additionalCostTemplate.content.cloneNode(true);
  connectAdditionalCostRemove(
    entry.querySelector(".remove-additional-cost"),
  );
  additionalCostEntries.append(entry);
});
