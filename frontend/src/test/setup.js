// =========================================================
// Global test setup — runs once per test file.
// =========================================================

// jest-dom matchers: toBeInTheDocument, toHaveValue, etc.
import "@testing-library/jest-dom/vitest";

import { afterEach, vi } from "vitest";
import { cleanup } from "@testing-library/react";

// ---------------------------------------------------------
// Cleanup between tests
// ---------------------------------------------------------

afterEach(() => {
  cleanup();                  // unmount React trees
  localStorage.clear();       // avoid token/user leakage
  sessionStorage.clear();

  // Reset the URL hash so the DEF-01 hash router does not
  // carry a page name from one test into the next.
  if (window.location.hash) {
    window.history.replaceState(
      null,
      "",
      window.location.pathname +
        window.location.search
    );
  }
});

// ---------------------------------------------------------
// Browser APIs jsdom does not fully implement
// ---------------------------------------------------------

// window.confirm — used in Allocations, WhatIfReallocation,
// ApprovalPanel, RequirementUnderstanding, Examinations,
// Departments, etc. Default to TRUE so tests can exercise
// the "user clicks OK" path. Individual tests override with
// vi.spyOn(window, "confirm").mockReturnValue(false) to
// exercise the cancel path.
if (!window.confirm.__isMocked) {
  window.confirm = vi.fn(() => true);
  window.confirm.__isMocked = true;
}

// window.alert — same idea, no-op by default.
if (!window.alert.__isMocked) {
  window.alert = vi.fn();
  window.alert.__isMocked = true;
}

// matchMedia — some Tailwind/lucide components probe it.
if (!window.matchMedia) {
  window.matchMedia = (query) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => false,
  });
}

// IntersectionObserver — some UI patterns require it.
if (!window.IntersectionObserver) {
  window.IntersectionObserver = class {
    observe() {}
    unobserve() {}
    disconnect() {}
  };
}

// ResizeObserver — same.
if (!window.ResizeObserver) {
  window.ResizeObserver = class {
    observe() {}
    unobserve() {}
    disconnect() {}
  };
}

// ---------------------------------------------------------
// Silence the noisy React 19 "not wrapped in act(...)"
// warnings that fire from async effects in tests we don't
// control. Real React errors and our own thrown errors
// still surface. Tighten later if you want strictness.
// ---------------------------------------------------------
const originalError = console.error;
console.error = (...args) => {
  const first = String(args[0] ?? "");
  if (first.includes("not wrapped in act")) return;
  originalError(...args);
};