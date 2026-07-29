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
