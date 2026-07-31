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

const demandPreview = document.querySelector("#demand-preview");
const demandPreviewStatus = document.querySelector(
  "#demand-preview-status",
);
const demandPreviewValues = document.querySelector(
  "#demand-preview-values",
);
const demandPreviewSummary = document.querySelector(
  "#demand-preview-summary",
);
const demandPreviewBreakEven = document.querySelector(
  "#demand-preview-break-even",
);
const eventInputsForm = demandPreview?.closest("form");
let demandPreviewTimer;
let demandPreviewRequest;

function setDemandValue(name, value) {
  demandPreview.querySelector(
    `[data-demand-value="${name}"]`,
  ).textContent = value;
}

async function updateDemandPreview() {
  demandPreviewStatus.textContent = "Updating estimate…";
  demandPreviewRequest?.abort();
  demandPreviewRequest = new AbortController();
  try {
    const response = await fetch("/event-inputs/demand-preview", {
      method: "POST",
      body: new FormData(eventInputsForm),
      signal: demandPreviewRequest.signal,
    });
    const preview = await response.json();
    if (!preview.ready) {
      demandPreviewValues.hidden = true;
      demandPreviewSummary.hidden = true;
      demandPreviewBreakEven.hidden = true;
      demandPreviewStatus.textContent =
        "Complete the demand and weather fields to see an even-split estimate.";
      return;
    }
    setDemandValue(
      "weather-adjusted-attendance",
      preview.weather_adjusted_attendance,
    );
    setDemandValue(
      "total-expected-food-buyers",
      preview.total_expected_food_buyers,
    );
    setDemandValue("total-food-vendors", preview.total_food_vendors);
    setDemandValue(
      "estimated-business-buyers",
      preview.estimated_business_buyers,
    );
    demandPreviewValues.hidden = false;
    demandPreviewSummary.textContent =
      `At an even split, this event provides about `
      + `${preview.estimated_business_buyers} expected buyers per vendor.`;
    demandPreviewSummary.hidden = false;
    demandPreviewBreakEven.textContent =
      preview.break_even_message ?? "";
    demandPreviewBreakEven.hidden = !preview.break_even_message;
    demandPreviewStatus.textContent = "Demand estimate updated.";
  } catch (error) {
    if (error.name !== "AbortError") {
      demandPreviewStatus.textContent =
        "The demand estimate is temporarily unavailable.";
    }
  }
}

function scheduleDemandPreview() {
  clearTimeout(demandPreviewTimer);
  demandPreviewTimer = setTimeout(updateDemandPreview, 250);
}

[
  "#estimated_attendance",
  "#expected_food_buyer_percentage",
  "#other_competing_food_vendors",
  "#weather_outlook",
  "#custom_weather_reduction",
].forEach((selector) => {
  document.querySelector(selector).addEventListener(
    "input",
    scheduleDemandPreview,
  );
});
protectionChoices.forEach((choice) => {
  choice.addEventListener("change", scheduleDemandPreview);
});
scheduleDemandPreview();

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
  scheduleWorkspaceCalculation();
});

useCalculatedSales.addEventListener("click", () => {
  revenueMethod.value = "attendance";
  updateSalesControls();
  scheduleWorkspaceCalculation();
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
  scheduleWorkspaceCalculation();
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
    scheduleWorkspaceCalculation();
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
  scheduleWorkspaceCalculation();
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
    scheduleWorkspaceCalculation();
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
  scheduleWorkspaceCalculation();
});

const workspaceForm = document.querySelector("[data-workspace='true']");
const workspaceStatus = document.querySelector("#analysis-update-status");
const workspaceBaseline = workspaceForm
  ? new FormData(workspaceForm)
  : null;
let workspaceTimer;
let workspaceRequest;
let workspaceRequestNumber = 0;

function clearWorkspaceErrors() {
  workspaceForm.querySelectorAll(".live-field-error").forEach(
    (error) => error.remove(),
  );
  workspaceForm.querySelectorAll('[aria-invalid="true"]').forEach(
    (input) => input.removeAttribute("aria-invalid"),
  );
}

function showWorkspaceError(input, message) {
  if (!input) {
    return;
  }
  input.setAttribute("aria-invalid", "true");
  const error = document.createElement("p");
  error.className = "live-field-error";
  error.textContent = message;
  const container = input.closest(".form-field")
    ?? input.closest("fieldset")
    ?? input.parentElement;
  container.append(error);
}

function showWorkspaceErrors(errors) {
  clearWorkspaceErrors();
  Object.entries(errors).forEach(([name, message]) => {
    if (name === "employee_labor") {
      employeeLaborEntries.querySelectorAll(".labor-entry").forEach(
        (entry, index) => {
          Object.entries(message[index] ?? {}).forEach(
            ([field, rowMessage]) => {
              const inputName = field === "hourly_rate"
                ? "employee_labor_rate"
                : "employee_labor_hours";
              showWorkspaceError(
                entry.querySelector(`[name="${inputName}"]`),
                rowMessage,
              );
            },
          );
        },
      );
      return;
    }
    if (name === "additional_costs") {
      additionalCostEntries
        .querySelectorAll(".additional-cost-entry")
        .forEach((entry, index) => {
          Object.entries(message[index] ?? {}).forEach(
            ([field, rowMessage]) => {
              const inputName = field === "name"
                ? "additional_cost_name"
                : "additional_cost_amount";
              showWorkspaceError(
                entry.querySelector(`[name="${inputName}"]`),
                rowMessage,
              );
            },
          );
        });
      return;
    }
    showWorkspaceError(
      workspaceForm.querySelector(`[name="${name}"]`),
      message,
    );
  });
}

function displayResultValue(element, value) {
  if (value === null || value === undefined) {
    element.textContent = "Not calculable";
  } else if (element.dataset.format === "money") {
    element.textContent = `$${value}`;
  } else if (element.dataset.format === "percent") {
    element.textContent = `${value}%`;
  } else {
    element.textContent = value;
  }
}

function updateWorkspaceResults(result) {
  document.querySelectorAll("[data-result-field]").forEach((element) => {
    displayResultValue(element, result[element.dataset.resultField]);
  });
  const targetResult = document.querySelector("#profit-target-result");
  if (result.profit_target?.is_met === null) {
    targetResult.textContent = "Profit-target evaluation is not available.";
  } else if (result.profit_target?.is_met) {
    targetResult.textContent = "The selected profit target is met.";
  } else {
    targetResult.textContent = "The selected profit target is not met.";
  }
  const warningList = document.querySelector("#analysis-warnings");
  warningList.replaceChildren();
  const warnings = result.warnings.length
    ? result.warnings
    : [{
      code: "none",
      severity: "info",
      message: "No factual notices for the current assumptions.",
    }];
  warnings.forEach((warning) => {
    const item = document.createElement("li");
    item.dataset.warningCode = warning.code;
    item.dataset.severity = warning.severity;
    item.textContent = warning.message;
    warningList.append(item);
  });
}

async function recalculateWorkspace() {
  const requestNumber = ++workspaceRequestNumber;
  workspaceRequest?.abort();
  workspaceRequest = new AbortController();
  workspaceStatus.dataset.state = "updating";
  workspaceStatus.textContent = "Updating analysis…";
  try {
    const response = await fetch(workspaceForm.dataset.calculationUrl, {
      method: "POST",
      body: new FormData(workspaceForm),
      signal: workspaceRequest.signal,
    });
    const payload = await response.json();
    if (requestNumber !== workspaceRequestNumber) {
      return;
    }
    if (!payload.valid) {
      showWorkspaceErrors(payload.errors);
      workspaceStatus.dataset.state = "invalid";
      workspaceStatus.textContent = payload.status;
      return;
    }
    clearWorkspaceErrors();
    updateWorkspaceResults(payload.result);
    workspaceStatus.dataset.state = "valid";
    workspaceStatus.textContent = payload.status;
  } catch (error) {
    if (error.name !== "AbortError") {
      workspaceStatus.dataset.state = "invalid";
      workspaceStatus.textContent =
        "Analysis could not update. Your entries have been preserved.";
    }
  }
}

function scheduleWorkspaceCalculation() {
  if (!workspaceForm) {
    return;
  }
  clearTimeout(workspaceTimer);
  workspaceTimer = setTimeout(recalculateWorkspace, 300);
}

function restoreWorkspaceBaseline() {
  const repeatableNames = new Set([
    "employee_labor_rate",
    "employee_labor_hours",
    "baseline_employee_labor_rate",
    "baseline_employee_labor_hours",
    "additional_cost_name",
    "additional_cost_amount",
  ]);
  workspaceForm.querySelectorAll("[name]").forEach((input) => {
    if (repeatableNames.has(input.name)) {
      return;
    }
    const values = workspaceBaseline.getAll(input.name);
    if (input.type === "radio" || input.type === "checkbox") {
      input.checked = values.includes(input.value);
    } else {
      input.value = values[0] ?? "";
    }
  });

  employeeLaborEntries.replaceChildren();
  const rates = workspaceBaseline.getAll("employee_labor_rate");
  const hours = workspaceBaseline.getAll("employee_labor_hours");
  rates.forEach((rate, index) => {
    const fragment = employeeLaborTemplate.content.cloneNode(true);
    const entry = fragment.querySelector(".labor-entry");
    entry.querySelector('[name="employee_labor_rate"]').value = rate;
    entry.querySelector('[name="employee_labor_hours"]').value =
      hours[index] ?? "";
    connectEventLaborRemove(entry.querySelector(".remove-event-labor"));
    connectLaborIndicator(entry);
    employeeLaborEntries.append(fragment);
  });

  additionalCostEntries.replaceChildren();
  const names = workspaceBaseline.getAll("additional_cost_name");
  const amounts = workspaceBaseline.getAll("additional_cost_amount");
  names.forEach((name, index) => {
    const fragment = additionalCostTemplate.content.cloneNode(true);
    const entry = fragment.querySelector(".additional-cost-entry");
    entry.querySelector('[name="additional_cost_name"]').value = name;
    entry.querySelector('[name="additional_cost_amount"]').value =
      amounts[index] ?? "";
    connectAdditionalCostRemove(
      entry.querySelector(".remove-additional-cost"),
    );
    additionalCostEntries.append(fragment);
  });

  updateWeatherControls();
  updateSalesControls();
  showConfirmedEventFoodMethod();
  updateEventProfitTarget();
  clearWorkspaceErrors();
  scheduleWorkspaceCalculation();
}

if (workspaceForm) {
  workspaceForm.addEventListener("submit", (event) => {
    event.preventDefault();
  });
  workspaceForm.addEventListener("input", scheduleWorkspaceCalculation);
  workspaceForm.addEventListener("change", scheduleWorkspaceCalculation);
  document.querySelector("#reset-analysis").addEventListener(
    "click",
    restoreWorkspaceBaseline,
  );
}
