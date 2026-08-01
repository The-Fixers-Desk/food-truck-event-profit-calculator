const copySupportButton = document.querySelector("#copy-support-information");
const copySupportStatus = document.querySelector("#support-copy-status");

function supportText(metadata) {
  return [
    `${metadata.app_name} support information`,
    `App version: ${metadata.app_version}`,
    `Operating system: ${metadata.operating_system}`,
    `Data storage: ${metadata.data_storage}`,
    `Database schema version: ${metadata.database_schema_version}`,
    `Last successful export: ${metadata.last_successful_export}`,
    `Connection: ${navigator.onLine ? "Online" : "Offline"}`,
    `Current screen: ${window.location.pathname}`,
  ].join("\n");
}

copySupportButton?.addEventListener("click", async () => {
  copySupportStatus.hidden = false;
  try {
    const response = await fetch(copySupportButton.dataset.diagnosticsUrl, {
      headers: { "Accept": "application/json" },
    });
    if (!response.ok) throw new Error("Diagnostics unavailable");
    await navigator.clipboard.writeText(supportText(await response.json()));
    copySupportStatus.textContent = "Support information copied. You can paste it into your email.";
  } catch (_error) {
    copySupportStatus.textContent = "Support information could not be copied. Please try again.";
  }
  copySupportButton.focus();
});

document.querySelectorAll(".help-section-nav a").forEach((link) => {
  link.addEventListener("click", () => {
    const section = document.querySelector(link.hash);
    window.setTimeout(() => section?.focus(), 0);
  });
});
