const onboardingPage = document.querySelector("[data-onboarding-page]");

if (onboardingPage && window.localStorage.getItem("business-defaults-draft")) {
  const setup = onboardingPage.querySelector('[data-onboarding-progress="setup"]');
  const defaults = onboardingPage.querySelector('[data-onboarding-progress="defaults"]');
  setup?.classList.remove("is-active");
  setup?.classList.add("is-complete");
  if (setup) setup.querySelector(".journey-progress__marker").textContent = "✓";
  defaults?.classList.add("is-active");
}
