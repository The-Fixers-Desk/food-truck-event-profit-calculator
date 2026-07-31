function setBusy(button, label) {
  button.disabled = true;
  button.classList.add("is-loading");
  button.setAttribute("aria-busy", "true");
  button.textContent = label;
}

function clearBusy(button, label) {
  button.disabled = false;
  button.classList.remove("is-loading");
  button.removeAttribute("aria-busy");
  button.textContent = label;
}

const downloadForm = document.querySelector("#download-backup-form");
if (downloadForm) {
  const downloadButton = document.querySelector("#download-backup");
  downloadForm.addEventListener("submit", () => {
    setBusy(downloadButton, "Preparing backup…");
    window.setTimeout(() => clearBusy(
      downloadButton, "Download backup",
    ), 1500);
  });
}

const restoreForm = document.querySelector("#restore-backup-form");
if (restoreForm) {
  const restoreButton = document.querySelector("#restore-backup");
  restoreForm.addEventListener("submit", () => {
    setBusy(restoreButton, "Restoring…");
  });
}
