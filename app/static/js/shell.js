const sidebar = document.querySelector("#app-sidebar");
const menuTrigger = document.querySelector("#mobile-menu-trigger");
const drawerBackdrop = document.querySelector("#drawer-backdrop");
const compactShell = window.matchMedia("(max-width: 1023px)");

function setDrawer(open, restoreFocus = false) {
  if (!sidebar || !menuTrigger || !drawerBackdrop) return;
  const shouldOpen = compactShell.matches && open;
  sidebar.classList.toggle("is-open", shouldOpen);
  sidebar.setAttribute("aria-hidden", String(compactShell.matches && !shouldOpen));
  menuTrigger.setAttribute("aria-expanded", String(shouldOpen));
  menuTrigger.setAttribute("aria-label", shouldOpen ? "Close navigation" : "Open navigation");
  drawerBackdrop.hidden = !shouldOpen;
  document.body.classList.toggle("has-open-drawer", shouldOpen);
  if (restoreFocus) menuTrigger.focus();
}

if (sidebar && menuTrigger && drawerBackdrop) {
  menuTrigger.addEventListener("click", () => {
    setDrawer(!sidebar.classList.contains("is-open"));
    if (sidebar.classList.contains("is-open")) {
      sidebar.querySelector("a, button")?.focus();
    }
  });
  drawerBackdrop.addEventListener("click", () => setDrawer(false, true));
  sidebar.querySelectorAll("a").forEach((link) => {
    link.addEventListener("click", () => setDrawer(false));
  });
  compactShell.addEventListener("change", () => setDrawer(false));
  setDrawer(false);
}

const utilityTriggers = Array.from(document.querySelectorAll(
  "[data-utility-trigger]",
));

function closeUtilityPanels(except = null) {
  utilityTriggers.forEach((trigger) => {
    const panel = document.querySelector(`#${trigger.dataset.utilityTrigger}`);
    if (panel !== except) {
      panel.hidden = true;
      trigger.setAttribute("aria-expanded", "false");
    }
  });
}

utilityTriggers.forEach((trigger) => {
  const panel = document.querySelector(`#${trigger.dataset.utilityTrigger}`);
  trigger.addEventListener("click", () => {
    const opening = panel.hidden;
    closeUtilityPanels(panel);
    panel.hidden = !opening;
    trigger.setAttribute("aria-expanded", String(opening));
    if (opening) panel.querySelector("button, a")?.focus();
  });
});

document.addEventListener("click", (event) => {
  if (!event.target.closest(".topbar-utilities")) closeUtilityPanels();
  if (workspacePanel && !workspacePanel.hidden && !event.target.closest(".workspace-menu")) {
    workspacePanel.hidden = true;
    workspaceTrigger.setAttribute("aria-expanded", "false");
  }
});

async function updateNotification(path, statusText) {
  const response = await fetch(path, { method: "POST", headers: { "X-Requested-With": "fetch" } });
  if (!response.ok) throw new Error("Notification update failed");
  const status = document.querySelector("#notification-status");
  if (status) status.textContent = statusText;
}

document.querySelectorAll("[data-notification-read]").forEach((button) => {
  button.addEventListener("click", async () => {
    const item = button.closest("[data-notification-id]");
    await updateNotification(`/notifications/${item.dataset.notificationId}/read`, "Notification marked as read.");
    item.classList.remove("notification-item--unread");
    button.remove();
  });
});
document.querySelector("[data-notifications-read-all]")?.addEventListener("click", async (event) => {
  await updateNotification("/notifications/read-all", "All notifications marked as read.");
  document.querySelectorAll(".notification-item--unread").forEach((item) => item.classList.remove("notification-item--unread"));
  document.querySelectorAll("[data-notification-read]").forEach((button) => button.remove());
  event.currentTarget.remove();
});
document.querySelectorAll("[data-notification-dismiss]").forEach((button) => {
  button.addEventListener("click", async () => {
    const item = button.closest("[data-notification-id]");
    await updateNotification(`/notifications/${item.dataset.notificationId}/dismiss`, "Notification dismissed.");
    item.remove();
    if (!document.querySelector(".notification-item")) window.location.reload();
  });
});
document.querySelectorAll("[data-notification-action]").forEach((link) => {
  link.addEventListener("click", () => {
    const item = link.closest("[data-notification-id]");
    navigator.sendBeacon?.(`/notifications/${item.dataset.notificationId}/read`, new Blob());
  });
});

const profileDialog = document.querySelector("#local-profile-dialog");
document.querySelectorAll("[data-profile-open]").forEach((button) => {
  button.addEventListener("click", () => {
    workspacePanel.hidden = true;
    workspaceTrigger.setAttribute("aria-expanded", "false");
    profileDialog.showModal();
    profileDialog.querySelector("input")?.focus();
  });
});
document.querySelector("#local-profile-form")?.addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  form.querySelectorAll(".field-error").forEach((node) => { node.textContent = ""; });
  const response = await fetch(form.action, { method: "POST", body: new FormData(form) });
  const payload = await response.json();
  if (!payload.saved) {
    Object.entries(payload.errors || {}).forEach(([field, message]) => {
      const error = document.querySelector(`#profile-${field.replaceAll("_", "-")}-error`);
      if (error) error.textContent = message;
    });
    document.querySelector("#local-profile-status").textContent = "Correct the highlighted profile fields.";
    form.querySelector(".field-error:not(:empty)")?.previousElementSibling?.focus();
    return;
  }
  document.querySelector("#local-profile-status").textContent = "Local profile saved.";
  window.location.reload();
});

const workspaceTrigger = document.querySelector("#workspace-menu-trigger");
const workspacePanel = document.querySelector("#workspace-menu-panel");
if (workspaceTrigger && workspacePanel) {
  workspaceTrigger.addEventListener("click", () => {
    const opening = workspacePanel.hidden;
    workspacePanel.hidden = !opening;
    workspaceTrigger.setAttribute("aria-expanded", String(opening));
  });
}

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    if (sidebar?.classList.contains("is-open")) setDrawer(false, true);
    closeUtilityPanels();
    if (workspacePanel && !workspacePanel.hidden) {
      workspacePanel.hidden = true;
      workspaceTrigger.setAttribute("aria-expanded", "false");
      workspaceTrigger.focus();
    }
  }
  if (event.key === "Tab" && sidebar?.classList.contains("is-open")) {
    const focusable = Array.from(sidebar.querySelectorAll("a, button:not([disabled])"));
    if (!focusable.length) return;
    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  }
});

const offlineState = document.querySelector("#offline-system-state");
function updateConnectionState() {
  if (offlineState) offlineState.hidden = navigator.onLine;
}
window.addEventListener("online", updateConnectionState);
window.addEventListener("offline", updateConnectionState);
document.querySelector("#retry-connection")?.addEventListener(
  "click", updateConnectionState,
);
updateConnectionState();

document.querySelectorAll("[data-retry-page]").forEach((button) => {
  button.addEventListener("click", () => window.location.reload());
});
