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

/* Event Inputs intentionally shows warnings, not a miniature result preview. */
/*
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
*/

const revenueMethod = document.querySelector("#revenue_method");
const useCustomSales = document.querySelector("#use-custom-sales");
const customSalesField = document.querySelector("#custom-sales-field");
const expectedSalesAmount = document.querySelector("#expected_sales_amount");

function updateSalesControls() {
  const customIsActive = revenueMethod.value === "manual_sales";
  if (!useCustomSales || !customSalesField || !expectedSalesAmount) return;
  useCustomSales.checked = customIsActive;
  customSalesField.hidden = !customIsActive;
  expectedSalesAmount.required = customIsActive;
  if (!customIsActive) {
    expectedSalesAmount.value = "";
  }
}

if (useCustomSales) {
  useCustomSales.addEventListener("change", () => {
    revenueMethod.value = useCustomSales.checked
      ? "manual_sales" : "attendance";
    updateSalesControls();
    scheduleWorkspaceCalculation();
  });
}

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
const repeatableStatus = document.createElement("p");
repeatableStatus.className = "visually-hidden";
repeatableStatus.setAttribute("role", "status");
employeeLaborEntries.before(repeatableStatus);

function updateEventLaborNames() {
  employeeLaborEntries.querySelectorAll(".labor-entry").forEach(
    (entry, index) => {
      entry.setAttribute("role", "group");
      entry.setAttribute("aria-label", `Employee labor entry ${index + 1}`);
      entry.querySelector(".remove-event-labor").setAttribute(
        "aria-label", `Remove employee labor entry ${index + 1}`,
      );
    },
  );
}

function connectEventLaborRemove(button) {
  button.addEventListener("click", () => {
    const entry = button.closest(".labor-entry");
    const nextFocus = entry.nextElementSibling?.querySelector("input")
      ?? entry.previousElementSibling?.querySelector("input")
      ?? addEmployeeLabor;
    entry.remove();
    updateEventLaborNames();
    repeatableStatus.textContent = "Employee labor entry removed.";
    nextFocus.focus();
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
updateEventLaborNames();

addEmployeeLabor.addEventListener("click", () => {
  const entry = employeeLaborTemplate.content.cloneNode(true);
  connectEventLaborRemove(entry.querySelector(".remove-event-labor"));
  employeeLaborEntries.append(entry);
  updateEventLaborNames();
  employeeLaborEntries.lastElementChild.querySelector("input").focus();
  repeatableStatus.textContent = "Employee labor entry added.";
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

function updateAdditionalCostNames() {
  additionalCostEntries.querySelectorAll(".additional-cost-entry").forEach(
    (entry, index) => {
      entry.setAttribute("role", "group");
      entry.setAttribute("aria-label", `Additional cost ${index + 1}`);
      const inputs = entry.querySelectorAll("input");
      inputs[0]?.setAttribute("aria-label", `Additional cost ${index + 1} name`);
      inputs[1]?.setAttribute("aria-label", `Additional cost ${index + 1} amount`);
      entry.querySelector(".remove-additional-cost").setAttribute(
        "aria-label", `Remove additional cost ${index + 1}`,
      );
    },
  );
}

function connectAdditionalCostRemove(button) {
  button.addEventListener("click", () => {
    const entry = button.closest(".additional-cost-entry");
    const nextFocus = entry.nextElementSibling?.querySelector("input")
      ?? entry.previousElementSibling?.querySelector("input")
      ?? addAdditionalCost;
    entry.remove();
    updateAdditionalCostNames();
    repeatableStatus.textContent = "Additional cost removed.";
    nextFocus.focus();
    scheduleWorkspaceCalculation();
  });
}

additionalCostEntries
  .querySelectorAll(".remove-additional-cost")
  .forEach(connectAdditionalCostRemove);
updateAdditionalCostNames();

addAdditionalCost.addEventListener("click", () => {
  const entry = additionalCostTemplate.content.cloneNode(true);
  connectAdditionalCostRemove(
    entry.querySelector(".remove-additional-cost"),
  );
  additionalCostEntries.append(entry);
  updateAdditionalCostNames();
  additionalCostEntries.lastElementChild.querySelector("input").focus();
  repeatableStatus.textContent = "Additional cost added.";
  scheduleWorkspaceCalculation();
});

const workspaceForm = document.querySelector("[data-workspace='true']");
const workspaceStatus = document.querySelector("#analysis-update-status");
const eventInputsWarningForm = document.querySelector(
  "form.form-panel:not([data-workspace='true'])",
);
let warningTimer;
let warningRequest;
let warningRequestNumber = 0;

const warningGroups = {
  even_split_buyers_below_break_even: "demand",
  break_even_exceeds_all_expected_food_demand: "demand",
  below_profit_target: "profit",
  estimated_loss: "profit",
  exactly_at_break_even: "profit",
};

function clearContextualWarnings() {
  document.querySelectorAll("[data-warning-group]").forEach((container) => {
    container.replaceChildren();
    container.hidden = true;
  });
}

function showContextualWarnings(warnings) {
  clearContextualWarnings();
  warnings.forEach((warning) => {
    const group = warningGroups[warning.code];
    const container = document.querySelector(
      `[data-warning-group="${group}"]`,
    );
    if (!container) return;
    const notice = document.createElement("p");
    notice.className = "contextual-warning";
    const headline = warning.code === "below_profit_target"
      ? "Current assumptions do not meet your minimum profit target."
      : warning.code.includes("break_even")
        ? "Demand may not cover current costs."
        : warning.code === "estimated_loss"
          ? "Current assumptions show an estimated loss."
          : "Current assumptions are exactly at break-even.";
    notice.textContent = `⚠ Warning: ${headline} Based on your current entries and `
      + `saved business defaults, ${warning.message}`;
    container.append(notice);
    container.hidden = false;
  });
}

async function updateContextualWarnings() {
  const requestNumber = ++warningRequestNumber;
  warningRequest?.abort();
  warningRequest = new AbortController();
  try {
    const response = await fetch("/event-inputs/warnings", {
      method: "POST",
      body: new FormData(eventInputsWarningForm),
      signal: warningRequest.signal,
    });
    const payload = await response.json();
    if (requestNumber !== warningRequestNumber) return;
    showContextualWarnings(payload.ready ? payload.warnings : []);
  } catch (error) {
    if (error.name !== "AbortError") clearContextualWarnings();
  }
}

function scheduleContextualWarnings() {
  clearTimeout(warningTimer);
  warningTimer = setTimeout(updateContextualWarnings, 300);
}

if (eventInputsWarningForm) {
  eventInputsWarningForm.addEventListener("input", scheduleContextualWarnings);
  eventInputsWarningForm.addEventListener("change", scheduleContextualWarnings);
  scheduleContextualWarnings();
}

let workspaceBaseline = workspaceForm
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
  const recommendation = document.querySelector("#decision-recommendation");
  if (result.profit_target?.is_met == null) {
    targetResult.textContent = "Unavailable";
    recommendation.textContent =
      "Your profit target cannot be evaluated with these assumptions.";
  } else if (result.profit_target?.is_met) {
    targetResult.textContent = "Target met";
    recommendation.textContent =
      "These assumptions meet your selected profit target.";
  } else {
    targetResult.textContent = "Target not met";
    recommendation.textContent =
      "These assumptions are below your selected profit target.";
  }
  recommendation.dataset.profitabilityStatus = result.profitability_status;
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
    item.textContent = `${warning.severity}: ${warning.message}`;
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
  if (eventInputsWarningForm) {
    scheduleContextualWarnings();
  }
  if (!workspaceForm) {
    return;
  }
  clearTimeout(workspaceTimer);
  workspaceTimer = setTimeout(recalculateWorkspace, 300);
  updateWorkspaceDirtyState();
}

function workspaceSignature(formData) {
  return JSON.stringify(
    Array.from(formData.entries()).filter(
      ([name]) => !["active_event_id", "active_scenario_id"].includes(name),
    ),
  );
}

function updateWorkspaceDirtyState() {
  if (!workspaceForm) {
    return;
  }
  const dirty = workspaceSignature(new FormData(workspaceForm))
    !== workspaceSignature(workspaceBaseline);
  workspaceForm.dataset.dirty = String(dirty);
  document.querySelector("#open-save-analysis").disabled = !dirty;
  document.querySelector("#open-save-as-new").disabled = !dirty;
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
  updateWorkspaceDirtyState();
}

if (workspaceForm) {
  let discardNavigationApproved = false;
  workspaceForm.addEventListener("submit", (event) => {
    event.preventDefault();
  });
  workspaceForm.addEventListener("input", scheduleWorkspaceCalculation);
  workspaceForm.addEventListener("change", scheduleWorkspaceCalculation);
  document.querySelector("#reset-analysis").addEventListener(
    "click",
    restoreWorkspaceBaseline,
  );
  document.querySelectorAll("a[href]").forEach((link) => {
    link.addEventListener("click", (event) => {
      if (workspaceForm.dataset.dirty === "true") {
        if (!window.confirm(
          "Discard unsaved changes and leave this analysis?",
        )) {
          event.preventDefault();
        } else {
          discardNavigationApproved = true;
        }
      }
    });
  });
  window.addEventListener("beforeunload", (event) => {
    if (
      workspaceForm.dataset.dirty === "true"
      && !discardNavigationApproved
    ) {
      event.preventDefault();
      event.returnValue = "";
    }
  });
  updateWorkspaceDirtyState();
}

const saveAnalysisDialog = document.querySelector("#save-analysis-dialog");

if (workspaceForm && saveAnalysisDialog) {
  const openSave = document.querySelector("#open-save-analysis");
  const openSaveAsNew = document.querySelector("#open-save-as-new");
  let saveDialogTrigger = openSave;
  const saveModes = saveAnalysisDialog.querySelectorAll(
    'input[name="save_mode"]',
  );
  const newNameField = document.querySelector("#new-scenario-name-field");
  const newNameInput = document.querySelector("#new_scenario_name");
  const overwriteField = document.querySelector(
    "#overwrite-confirmation-field",
  );
  const overwriteConfirmation = document.querySelector(
    "#overwrite_confirmed",
  );
  const scenarioNameError = document.querySelector("#scenario-name-error");
  const overwriteError = document.querySelector("#overwrite-error");
  const saveError = document.querySelector("#save-analysis-error");
  const confirmSave = document.querySelector("#confirm-save-analysis");
  saveAnalysisDialog.addEventListener("close", () => saveDialogTrigger.focus());

  function clearSaveErrors() {
    [scenarioNameError, overwriteError, saveError].forEach((error) => {
      error.hidden = true;
      error.textContent = "";
    });
  }

  function selectedSaveMode() {
    return saveAnalysisDialog.querySelector(
      'input[name="save_mode"]:checked',
    ).value;
  }

  function updateSaveMode() {
    const saveAsNew = selectedSaveMode() === "new";
    newNameField.hidden = !saveAsNew;
    overwriteField.hidden = saveAsNew;
    newNameInput.required = saveAsNew;
    if (saveAsNew) {
      overwriteConfirmation.checked = false;
    }
    confirmSave.textContent = saveAsNew
      ? "Save as new scenario" : "Overwrite current scenario";
    clearSaveErrors();
  }

  function openSaveDialog(mode, trigger) {
    saveDialogTrigger = trigger;
    saveAnalysisDialog.querySelector(
      `input[name="save_mode"][value="${mode}"]`,
    ).checked = true;
    newNameInput.value = "";
    overwriteConfirmation.checked = false;
    updateSaveMode();
    saveAnalysisDialog.showModal();
    if (mode === "new") newNameInput.focus();
    else overwriteConfirmation.focus();
  }

  openSave.addEventListener("click", () => {
    openSaveDialog("overwrite", openSave);
  });
  openSaveAsNew.addEventListener("click", () => {
    openSaveDialog("new", openSaveAsNew);
  });

  saveModes.forEach((mode) => {
    mode.addEventListener("change", updateSaveMode);
  });

  document.querySelector("#cancel-save-analysis").addEventListener(
    "click",
    () => saveAnalysisDialog.close(),
  );

  confirmSave.addEventListener(
    "click",
    async () => {
      clearSaveErrors();
      const formData = new FormData(workspaceForm);
      const mode = selectedSaveMode();
      confirmSave.disabled = true;
      confirmSave.classList.add("is-loading");
      confirmSave.setAttribute("aria-busy", "true");
      confirmSave.textContent = mode === "new" ? "Saving…" : "Overwriting…";
      formData.set("save_mode", mode);
      formData.set("scenario_name", newNameInput.value);
      formData.set(
        "overwrite_confirmed",
        String(overwriteConfirmation.checked),
      );
      try {
        const response = await fetch(workspaceForm.dataset.saveUrl, {
          method: "POST",
          body: formData,
        });
        const payload = await response.json();
        if (!payload.saved) {
          if (payload.errors) {
            showWorkspaceErrors(payload.errors);
          }
          if (payload.scenario_name_error) {
            scenarioNameError.textContent = payload.scenario_name_error;
            scenarioNameError.hidden = false;
          }
          if (payload.overwrite_error) {
            overwriteError.textContent = payload.overwrite_error;
            overwriteError.hidden = false;
          }
          if (payload.save_error || payload.message) {
            saveError.textContent = payload.save_error ?? payload.message;
            saveError.hidden = false;
          }
          return;
        }
        document.querySelector("#active_scenario_id").value =
          payload.active_scenario_id;
        document.querySelector("#active-scenario-name").textContent =
          payload.active_scenario_name;
        document.querySelector("[data-scenario-action-name]").textContent =
          payload.active_scenario_name;
        document.querySelector("#overwrite-scenario-name").textContent =
          payload.active_scenario_name;
        updateWorkspaceResults(payload.result);
        workspaceBaseline = new FormData(workspaceForm);
        updateWorkspaceDirtyState();
        workspaceStatus.dataset.state = "valid";
        workspaceStatus.textContent = payload.message;
        saveAnalysisDialog.close();
      } catch {
        saveError.textContent =
          "The scenario could not be saved. Your changes are preserved.";
        saveError.hidden = false;
      } finally {
        confirmSave.disabled = false;
        confirmSave.classList.remove("is-loading");
        confirmSave.removeAttribute("aria-busy");
        confirmSave.textContent = mode === "new"
          ? "Save as new scenario" : "Overwrite current scenario";
      }
    },
  );
}

const sectionNavigation = document.querySelector("[data-section-navigation]");
const formSections = Array.from(document.querySelectorAll("[data-form-section]"));

if (sectionNavigation && formSections.length) {
  const sectionButtons = Array.from(
    sectionNavigation.querySelectorAll("[data-section-target]"),
  );
  const isWorkspaceSections = Boolean(workspaceForm);
  const backButton = document.querySelector("#section-back");
  const continueButton = document.querySelector("#section-continue");
  const analyzeButton = document.querySelector("#analyze-event");
  const progress = document.querySelector("#section-progress");
  let completedThrough = 0;
  let activeSection = Number(
    formSections.find((section) => section.querySelector(
      '[aria-invalid="true"], .field-error',
    ))
      ?.dataset.formSection ?? (isWorkspaceSections ? 2 : 1),
  );
  if (!isWorkspaceSections && document.querySelector(
    '[aria-invalid="true"], .field-error',
  )) {
    completedThrough = Math.max(0, activeSection - 1);
  }
  const revenueSection = formSections.find(
    (section) => section.dataset.formSection === "3",
  );
  const averageOrderField = document.querySelector(
    "#average_order_sale_amount",
  )?.closest(".form-field");
  if (revenueSection && averageOrderField) revenueSection.prepend(averageOrderField);
  const customRevenueControl = document.querySelector(
    ".workspace-revenue-control",
  );
  if (revenueSection && customRevenueControl) {
    revenueSection.prepend(customRevenueControl);
  }

  function sectionFields(number) {
    return formSections
      .filter((section) => Number(section.dataset.formSection) === number)
      .flatMap((section) => Array.from(section.querySelectorAll(
        "input, select, textarea",
      )));
  }

  function updateReview() {
    const review = document.querySelector("#event-review-summary");
    if (!review) return;
    review.replaceChildren();
    for (let number = 1; number <= 5; number += 1) {
      const card = document.createElement("article");
      card.className = "review-section";
      const heading = document.createElement("h3");
      heading.textContent = sectionButtons[number - 1].textContent.trim();
      const values = sectionFields(number)
        .filter((field) => field.name && field.type !== "hidden" && field.value)
        .slice(0, 4)
        .map((field) => {
          const label = field.labels?.[0]?.textContent.trim();
          return label ? `${label}: ${field.value}` : field.value;
        });
      const summary = document.createElement("p");
      summary.textContent = values.length
        ? values.join(" · ") : "No values entered yet.";
      const edit = document.createElement("button");
      edit.type = "button";
      edit.className = "button-secondary";
      edit.textContent = "Edit";
      edit.addEventListener("click", () => showSection(number));
      card.append(heading, summary, edit);
      review.append(card);
    }
  }

  function showSection(number) {
    activeSection = number;
    formSections.forEach((section) => {
      section.hidden = Number(section.dataset.formSection) !== number;
    });
    sectionButtons.forEach((button) => {
      const target = Number(button.dataset.sectionTarget);
      const active = target === number;
      button.classList.toggle("is-active", active);
      button.classList.toggle("is-complete", target <= completedThrough);
      button.setAttribute("aria-current", active ? "step" : "false");
      if (!isWorkspaceSections) {
        button.disabled = target > completedThrough + 1 && !active;
      }
    });
    if (backButton) backButton.hidden = number === 1;
    if (continueButton) continueButton.hidden = number === 6;
    if (analyzeButton) analyzeButton.hidden = number !== 6;
    if (progress) progress.textContent = `Step ${number} of 6`;
    if (number === 6) updateReview();
  }

  function validateActiveSection() {
    const invalid = sectionFields(activeSection).find((field) => (
      !field.closest("[hidden]") && !field.checkValidity()
    ));
    if (!invalid) return true;
    invalid.reportValidity();
    invalid.focus();
    sectionButtons.find((button) => (
      Number(button.dataset.sectionTarget) === activeSection
    ))?.classList.add("has-error");
    return false;
  }

  sectionButtons.forEach((button) => {
    button.addEventListener("click", () => {
      const target = Number(button.dataset.sectionTarget);
      if (isWorkspaceSections || target <= completedThrough + 1) {
        showSection(target);
      }
    });
  });
  backButton?.addEventListener("click", () => showSection(activeSection - 1));
  continueButton?.addEventListener("click", () => {
    if (!validateActiveSection()) return;
    completedThrough = Math.max(completedThrough, activeSection);
    showSection(activeSection + 1);
  });

  formSections.forEach((section) => {
    if (section.querySelector('[aria-invalid="true"], .field-error')) {
      sectionButtons.find((button) => (
        button.dataset.sectionTarget === section.dataset.formSection
      ))?.classList.add("has-error");
    }
  });
  showSection(activeSection);
}

const firstEventError = document.querySelector('[aria-invalid="true"]')
  ?? document.querySelector("[data-form-section] .field-error")
    ?.closest("[data-form-section]")?.querySelector("input, select, textarea");
if (firstEventError) window.requestAnimationFrame(() => firstEventError.focus());
document.querySelectorAll('[aria-invalid="true"]').forEach((input, index) => {
  const error = input.closest(".form-field, fieldset")?.querySelector(".field-error");
  if (!error) return;
  error.id ||= `event-field-error-${index + 1}`;
  const describedBy = new Set((input.getAttribute("aria-describedby") ?? "").split(" ").filter(Boolean));
  describedBy.add(error.id);
  input.setAttribute("aria-describedby", Array.from(describedBy).join(" "));
});
