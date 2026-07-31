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
