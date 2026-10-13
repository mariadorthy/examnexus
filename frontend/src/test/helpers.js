import { vi } from "vitest";
import { render, fireEvent } from "@testing-library/react";
// ---------------------------------------------------------
// Response builders — shape matches the backend exactly.
// ---------------------------------------------------------

export function jsonResponse(body, { status = 200 } = {}) {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
    // Some services read .text() (authService after FIX-B, etc.)
    text: async () => JSON.stringify(body),
  };
}

export function htmlResponse(html, { status = 500 } = {}) {
  return {
    ok: false,
    status,
    json: async () => { throw new SyntaxError("Unexpected token <"); },
    text: async () => html,
  };
}

export function networkError(message = "Failed to fetch") {
  return Promise.reject(new TypeError(message));
}

// ---------------------------------------------------------
// fetch mocking by URL predicate.
//
// Usage:
//   stubFetch([
//     ["POST /api/auth/login",         () => jsonResponse({ access_token: "t", user: {...} })],
//     ["GET  /api/dashboard/",          () => jsonResponse({ success: true, statistics: {...} })],
//     ["*",                             () => jsonResponse({ message: "Not stubbed" }, { status: 500 })],
//   ]);
//
// Order matters: first matching rule wins.
// The rule string is `<METHOD> <substring>` or `*`.
// ---------------------------------------------------------

export function stubFetch(rules) {
  const matcher = (method, url) => {
    for (const [pattern, handler] of rules) {
      if (pattern === "*") return handler;
      const [m, frag] = pattern.split(" ", 2);
      if (m !== method) continue;
      if (url.includes(frag)) return handler;
    }
    throw new Error(`No fetch stub matched ${method} ${url}`);
  };

  const mock = vi.fn(async (input, init = {}) => {
    const url = typeof input === "string" ? input : input.url;
    const method = (init.method || "GET").toUpperCase();
    const handler = matcher(method, url);
    const result = handler({ url, method, init });
    return await result;
  });

  vi.stubGlobal("fetch", mock);
  return mock;
}

// ---------------------------------------------------------
// Convenience: render with sensible defaults.
// ---------------------------------------------------------

export function renderApp(ui) {
  return render(ui);
}

// ---------------------------------------------------------
// Seed localStorage with a logged-in user (for route tests).
// ---------------------------------------------------------

export function seedUser(user) {
  localStorage.setItem("examnexus_token", "test-token");
  localStorage.setItem("examnexus_user", JSON.stringify(user));

  // Fresh hash so a leaked page from a prior test cannot
  // hijack the initial render (DEF-01 hash router).
  if (window.location.hash) {
    window.history.replaceState(
      null,
      "",
      window.location.pathname +
        window.location.search
    );
  }
}

export const ADMIN_USER = {
  id: 1,
  name: "Test Admin",
  email: "admin@example.com",
  role: "admin",
};

export const STUDENT_USER = {
  id: 2,
  name: "Test Student",
  email: "student@example.com",
  role: "student",
};

// ---------------------------------------------------------
// Bypass user-event's `accept=` filter for tests that
// specifically exercise non-CSV rejection.
// ---------------------------------------------------------

export function forceFileChange(input, file) {
  fireEvent.change(input, { target: { files: [file] } });
}