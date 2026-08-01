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
  });
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
