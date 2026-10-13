// =========================================================
// Shared API response fixtures.
// Keep these aligned with what the backend actually returns.
// =========================================================

import { jsonResponse } from "../helpers";

// ---------------------------------------------------------
// Dashboard payload — matches AdminDashboard.jsx expectations.
// ---------------------------------------------------------

export const EMPTY_DASHBOARD = {
  success: true,
  statistics: {
    students: 0,
    staff: 0,
    courses: 0,
    departments: 0,
    subjects: 0,
    halls: 0,
  },
  upcoming_examinations: [],
  recent_activity: [],
  allocation: {
    total_examinations: 0,
    examinations_with_allocations: 0,
    total_allocations: 0,
    status: "NOT_STARTED",
  },
  system_status: {
    departments: false,
    courses: false,
    subjects: false,
    students: false,
    staff: false,
    halls: false,
  },
};

export const POPULATED_DASHBOARD = {
  ...EMPTY_DASHBOARD,
  statistics: {
    students: 120,
    staff: 15,
    courses: 8,
    departments: 4,
    subjects: 42,
    halls: 6,
  },
  allocation: {
    total_examinations: 3,
    examinations_with_allocations: 1,
    total_allocations: 4,
    status: "PARTIAL",
  },
  system_status: {
    departments: true,
    courses: true,
    subjects: true,
    students: true,
    staff: true,
    halls: true,
  },
};

// ---------------------------------------------------------
// List endpoints — return [] by default; individual tests
// can return richer arrays when they need to.
// ---------------------------------------------------------

export const EMPTY_LIST = [];

// ---------------------------------------------------------
// Fetch rule factory — the minimum stubs a navigation test
// needs. Handles every read the app does after login.
//
//   buildAdminRoutesStubs({
//     dashboard: POPULATED_DASHBOARD,
//     departments: [{ id: 1, ... }],
//   })
// ---------------------------------------------------------

export function buildAdminRoutesStubs(overrides = {}) {
  const dashboard = overrides.dashboard ?? EMPTY_DASHBOARD;

  const listRoutes = {
    "/api/departments":         overrides.departments  ?? EMPTY_LIST,
    "/api/courses":             overrides.courses      ?? EMPTY_LIST,
    "/api/subjects":            overrides.subjects     ?? EMPTY_LIST,
    "/api/students":            overrides.students     ?? EMPTY_LIST,
    "/api/staff":               overrides.staff        ?? EMPTY_LIST,
    "/api/halls":               overrides.halls        ?? EMPTY_LIST,
    "/api/examinations":        overrides.examinations ?? EMPTY_LIST,
    "/api/exam-registrations":  overrides.registrations ?? EMPTY_LIST,
    "/api/timetable":           overrides.timetable    ?? EMPTY_LIST,
    "/api/hall-tickets":        overrides.hallTickets  ?? EMPTY_LIST,
    "/api/reports":             overrides.reports      ?? EMPTY_LIST,
  };

  const rules = [
    ["GET /api/dashboard/", () => jsonResponse(dashboard)],
  ];

  for (const [fragment, payload] of Object.entries(listRoutes)) {
    rules.push([
      `GET ${fragment}`,
      () => jsonResponse(payload),
    ]);
  }

  // Anything we didn't anticipate: 404 with a JSON body so
  // an unexpected call surfaces as a readable failure
  // instead of an "undefined" chain.
  rules.push([
    "*",
    () => jsonResponse({ message: "Unstubbed route" }, { status: 404 }),
  ]);

  return rules;
}