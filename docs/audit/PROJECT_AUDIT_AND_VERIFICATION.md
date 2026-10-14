# ExamNexus — Project Audit and Verification

**Review date:** 2026-10-14  
**Repository:** `D:\GitHub\ExamNexus`  
**Branch / HEAD:** `main` / `6205bcc` (`chore: checkpoint project improvements and integration updates`)  
**Scope:** Project source and documentation review, automated tests, production build, lint, and safe runtime/database checks. Existing working-tree changes were preserved. The continuation included source and test changes documented below. No production migration, deployment, or production database write was performed.

## Status legend

- 🟢 Verified working — directly exercised successfully in this review.
- 🟡 Partially verified or verification pending — source/tests indicate implementation, but end-to-end runtime proof is incomplete.
- 🔴 Confirmed defect — reproducible failure or direct source evidence of a broken behavior.
- ⚪ Not implemented or not tested — absent by inspection, or not safely verifiable here.

## Executive Assessment

The latest recorded verification on 14 October 2026 reports **455 backend tests collected, 449 passed, 6 skipped, and 0 failed**. The frontend suite reports **83 passed tests across 15 test files**, with 0 failures. The frontend production build passed with a large-chunk advisory, and lint exited with code 0 with warnings remaining.

Read-only inspection of the local `examnexus_test` database confirmed Alembic revision `2e11c30af147`, the presence of `hall_incidents` and `hall_tickets.version`, and no new operations from Flask-Migrate's schema check.

**Full submission and production readiness are not established.** Browser-based workflows, responsive behavior, accessibility, and deployed production database state remain unverified. The frontend suite uses mocked API responses, so it does not prove complete integration with a live Flask API. Six skipped backend tests remain unverified for their intended scenarios.

## 1. Repository state and protection

Starting state from `git status --short --branch`: `main...origin/main`, with modified tracked files:

- `backend/app/auth/decorators.py`
- `backend/app/models/student.py`
- `backend/app/routes/dashboard.py`
- `backend/app/routes/examinations.py`
- `frontend/src/pages/admin/examinations/Examinations.jsx`
- `frontend/src/pages/staff/StaffDashboard.jsx`
- `frontend/src/services/allocationService.js`

Untracked at start: `backend/app/static/` (profile-image files), `backend/tests/test_new_coverage.py`, and the existing `docs/audit/` directory. All were preserved. Recent commits: `6205bcc`, `3b68116`, `17674fd`, `7526ef7`, `cc23b48`. The root has no `README.md`; setup guidance is in `docs/development-setup.md` and `frontend/README.md`. The earlier audit reports' clean-tree assertion describes a different starting state and is stale for this review.

## 2. Architecture and inventory

The system is a React 19 / Vite SPA, using hash-based admin navigation and role dispatch in `frontend/src/App.jsx`, calling a Flask API. The backend uses Flask, SQLAlchemy, Flask-Migrate/Alembic, JWT, and PostgreSQL drivers. Domain logic is separated into route blueprints, services, and SQLAlchemy models. The backend app factory registers 17 route modules; Flask's URL map contains 101 rules. The project docs describe a deterministic constraint-based allocation engine with administrator-controlled lifecycle transitions.

The source contains 17 route modules; services include allocation, seating, invigilator assignment, validation, requirements parsing, natural-language queries, explainability, reallocation, incidents, eligibility, CSV, reporting, tickets/PDF/QR, and profile-image handling. Frontend source contains role portals, admin pages for master data, exams, timetables, registrations, allocation, tickets and reports, a public QR verification page, and corresponding API service modules.

### Feature inventory (source/API/UI/test/runtime distinction)

Most backend business workflows are exposed by protected Flask routes and connected to frontend service/page code. Backend tests pass in the latest recorded full-suite run, but database-backed browser workflows and live frontend/API integration remain unverified. Test references are present in the named suites; six backend tests skip because the current fixtures cannot represent their target scenarios.

| Feature/workflow | Code / API / UI evidence | Tests present | Current verification |
|---|---|---|---|
| Authentication, login/logout, JWT and roles | `auth.py`, decorators/security; Login, App and auth service | phase 1, new coverage | 🟡 Backend tests pass; browser session flow is unverified. |
| Admin/staff/student restrictions and dashboards | Protected dashboard routes and role-specific UI | phase 1, regression, new coverage | 🟡 Backend tests pass; UI uses mocked API tests. |
| Departments, courses, subjects, students, staff, halls CRUD | GET/POST/PUT/PATCH routes; no DELETE route found for six entities | phase 2 and CSV tests | 🟡 Tested read/create/update/status operations pass; delete API unsupported. No visible delete controls found, though unused delete service helpers exist. |
| CSV validation/import | Import routes, CSV component/services, row/reference checks | phase 3, phase 13 | 🟡 Backend tests pass; browser upload flow unverified. |
| Examination management and DRAFT deletion | GET/POST/PUT/bulk and guarded DELETE; admin page | phase 4, new coverage | 🟡 Backend create/update/lifecycle/delete and rollback tests pass; browser flow unverified. |
| Timetables and conflict checks | Timetable routes/service/UI | phase 5, phase 13 | 🟡 Backend tests pass; live browser/API integration unverified. |
| Registration and eligibility | Registration routes/services/UI, eligibility service | phase 6 and post-phase-7 | 🟡 Backend tests pass; browser integration unverified. |
| Readiness/availability | readiness endpoint, hall availability/incidents services | new coverage, incident/allocation tests | 🟡 Backend tests pass; cross-page UI flow unverified. |
| Hall allocation and accessibility | allocation routes/services, options, accessible handling; allocation UI | phase 7, integration tests | 🟡 Backend tests pass; one mixed-course tamper scenario skips due fixture data. |
| Seat allocation and uniqueness | seat service/model/routes/UI | allocation tests | 🟡 Backend tests pass; UI-to-API flow unverified. |
| Invigilator assignment/workload/conflict validation | service/routes/models/UI | post-phase-7 invigilator tests | 🟡 Backend tests pass; cross-examination overlap case skips due seed shape. |
| Independent allocation validation | validation service, route, panel | allocation/lifecycle tests | 🟡 Backend tests pass; browser flow unverified. |
| Review, approve, reject, modify, publish lifecycle | lifecycle service/routes and ApprovalPanel | lifecycle tests | 🟡 Backend state-transition tests pass; browser flow unverified. |
| Ticket generation/versioning/PDF/QR verification | ticket service/routes, PDF service, public page, QR service | ticket/PDF/version tests | 🟡 Backend tests pass, including owner and cross-student PDF authorization; one QR scoping case is unobservable with fixture data. |
| Reports and operational dashboards | report/dashboard routes/services and pages | reports and new coverage | 🟡 Backend tests pass; live displayed values/filtering unverified. |
| Feature 17: allocation optimization | allocation options/selection service and deterministic planner | allocation tests | 🟡 Determinism and constraints tested; no comparative optimization benchmark defined. |
| Feature 18: natural-language requirements | requirement parser/routes/service/component | phase 8 and integration tests | 🟡 Parser/apply tests pass; browser interaction unverified. |
| Feature 19: natural-language DB questions | parser and restricted query service/route/component | phase 9 | 🟡 Read-only query tests pass; full cross-role UI behavior unverified. |
| Feature 20: explainable allocation | explanation service/routes/UI | phase 11 | 🟡 Explanation tests pass; one candidate-dependent negative case skips. |
| Feature 21: what-if/dynamic reallocation | simulation/apply routes, service and UI | phase 10 | 🟡 Backend tests pass; three emergency replans skip because no feasible seed-data plan exists. |
| CSV intelligent validation | validation service/route and UI | phase 13 | 🟡 Backend tests pass; browser file-picker flow unverified. |
| Emergency incident/reallocation | incident/emergency routes/service/UI; ticket invalidation | post-phase-7 tests | 🟡 Core tests pass; three feasible replan cases skip; no deployed workflow tested. |
| Profile-image persistence | upload service and local static files | profile-image tests | 🟡 Upload validation passes; durable deployment storage unverified. |
| Two-factor setting | `Student.two_factor_enabled`; default currently false | No end-to-end 2FA tests | ⚪ No complete second-factor challenge/verification flow found. |

The earlier split inventory and UI notes were consolidated from `FEATURE_AUDIT_MATRIX.md`, `PROJECT_INVENTORY.md`, and `FRONTEND_UI_AUDIT.md`; see Section 13 for the consolidation record. Their historical runtime figures are not adopted as current results.

## 3. Backend APIs, services, models, migrations

The API is organized by domain blueprint: auth, dashboards, six master-data entities, examinations, registrations, timetables, readiness, CSV import, allocations, requirements, natural-language queries, tickets, and reports. Master-data update methods include PUT/PATCH; the six master-data domains do not expose DELETE. The current examinations route has a `DELETE /api/examinations/<id>` admin handler that rejects missing IDs and non-DRAFT status, refuses when allocations or tickets exist, removes timetable/registration rows, and commits transactionally. Tests for this path, including rollback and error redaction, passed in the latest recorded verification.

Models cover users and academic data plus allocations, timetable, registrations, tickets, incidents, activities, and dependent assignments. Nine migration files form one source-level Alembic chain with a single head `2e11c30af147`. The `hall_incidents` revision creates the incident table and indexes; the ticket-version revision adds non-null `version` with server default 1, replaces uniqueness on (student, examination) with (student, examination, version), and downgrade removes that column/uniqueness. Existing-row behavior is therefore defined by the server default at upgrade.

Read-only inspection of the local `examnexus_test` database confirmed the current Alembic revision `2e11c30af147` and the presence of `hall_incidents` and `hall_tickets.version`. Flask-Migrate's read-only schema check reported no new operations. This establishes the observed state of the inspected local test database only; it does not establish that the deployed Render production database has the same revision or schema. No migration command that changes schema was run.

The initial migration and later examination/timetable revisions were read at source level; no deployed schema equivalence is inferred. In particular, the historical claim that a database was already at head cannot be confirmed in this environment.

## 4. Frontend pages and integration

The SPA has admin pages for dashboards, six master-data entities, examinations, timetables, registrations, allocations (hall/seat/invigilator/validation/approval/what-if/requirements/explanation), hall tickets and reports; staff and student dashboards; login; and public hall-ticket verification. Services are organized per API domain. Frontend component tests use mocked fetch responses, so passing tests verify component behavior against those mocks rather than a live Flask server.

Current tree improvements: the examinations delete control sends DELETE; staff dashboard reads `department_name` with ID fallback; allocation service clears stored credentials and dispatches `examnexus:unauthorized` on HTTP 401. Oxlint currently warns about an unused `post` import in `Examinations.jsx` and several hook/dependency, immutability, and unused-symbol issues.

Source-level UI risks from the prior report remain pending browser confirmation: table overflow at narrow widths, 10-column mobile QR verification layout, allocation tab overflow, icon-only action labels, loading announcements, tab semantics, modal focus management, and contrast. No browser, device emulation, accessibility scanner, or screen-reader session was run. Thus these are risks, not claimed observed browser failures. Loading/empty/error states are exercised by frontend mock tests, but actual API error mapping and cross-layer data consistency are pending.

## 5. Commands and results from this review

Commands were run from the indicated project directory. Historical runs are retained as records of earlier checkpoints; the latest full-suite results are recorded in Section 11.

| Command/check | Result |
|---|---|
| `git status --short --branch`, `git branch --show-current`, `git log -5 --oneline`, `git diff --stat`, `git diff` | Captured starting state and existing modifications; preserved all. |
| Earlier backend run: `backend\venv\Scripts\python.exe -m pytest -q -rs` | Historical checkpoint: 454 collected, 448 passed, 6 skipped, exit 0 (18.04 s); this was before the final delete rollback test was added. Superseded by the latest full-suite result in Section 11. |
| `backend\venv\Scripts\python.exe -m pytest tests\test_new_coverage.py::TestExaminationDelete -q` | 7 passed, exit 0, including transaction rollback and error redaction. |
| `backend\venv\Scripts\python.exe -m pytest tests\test_post_phase7_hall_ticket_pdf.py -q` | 12 passed, 1 skipped, exit 0; includes student-own PDF and cross-student 403 tests. |
| Earlier frontend test runs: `frontend\npm run test -- --reporter=dot` | Historical baseline: 81 passed. After adding 2 API tests, an intervening full run had 1 failed, 82 passed (double PATCH on fast repeat submit). Guard was added; focused rerun passed 7/7. The latest full run is recorded in Section 11. |
| Earlier `frontend\npm run build` | Passed before the latest status/mobile layout edits; 1,909 modules, JS chunk ~691 kB advisory. The latest build passed; see Section 11. |
| Earlier `frontend\npm run lint` | Exit 0 before latest edits, with numerous Oxlint warnings. The latest lint result is recorded in Section 11. |
| Read-only query using `TEST_DATABASE_URL` | Target `examnexus_test`, revision `2e11c30af147`; `hall_incidents=True`; `hall_tickets.version=True`. |
| Flask-Migrate read-only `db check` | No new upgrade operations detected, exit 0, against `examnexus_test`. |
| Python Flask smoke: import `run.app`, GET `/`, count URL rules | GET `/` returned 200; 101 URL rules registered. |

The previous audit's figures (409 collected, 190 failures/144 passes/7 skips/140 errors; frontend tests blocked) are historical and stale. A later sandboxed connection returned 10013, but read-only inspection and pytest runs against `examnexus_test` succeeded. The root cause of the earlier connection denial is not asserted.

### Six skips in the latest 455-test backend run

All six were conditional on the current fixture data:

1. `test_phase7_allocation.py:832` — no mixed-course hall available for the tamper scenario.
2–4. `test_post_phase7_emergency_reallocation.py:194` — no single-hall exclusion yields a feasible emergency replan with current accessibility capacity (three scenarios).
5. `test_post_phase7_hall_ticket_pdf.py:490` — every seeded student has every subject, so the timetable-scope leak is unobservable in this dataset.
6. `test_post_phase7_invigilator.py:359` — no overlapping timetable exists in another examination.

These are data-variation gaps, not infrastructure skips. Rework fixture diversity if those negative cases are required for acceptance.

## 6. End-to-end workflow verification

| Workflow | Result |
|---|---|
| Backend startup / health | 🟢 Flask imports, registers routes, and `/` responds 200. |
| Login/logout, missing/invalid/expired tokens, role matrix | 🟢 Backend auth/RBAC suite passes; live browser session behavior unverified. |
| Master-data CRUD, CSV, examination/timetable/eligibility | 🟢 Backend tests pass; frontend uses mocked API tests. |
| Allocation, capacity/accessibility, seat/invigilator validation | 🟡 Backend tests pass; conditional fixture gaps remain. |
| Review/approve/reject/publish | 🟢 Backend lifecycle tests pass. |
| Requirement understanding and read-only natural-language query | 🟢 Parser and DB-backed restricted-query tests pass. |
| Explainability compared with actual allocations | 🟡 Tests pass, but candidate-dependent case skips. |
| What-if simulation and apply/confirmation | 🟡 Core tests pass; three emergency replans skip for lack of feasible seed-data cases. |
| Ticket/PDF generation and QR verification | 🟡 Backend tests pass, including ownership; one QR scoping leak case is unobservable with shared-subject test data. |
| Emergency report → simulate → apply → ticket version changes | 🟡 Core tests pass; feasible variants skip on current seed data; deployed flow not tested. |
| Frontend behavior | 🟡 All 83 mock-based tests pass across 15 test files; live browser integration remains unverified. |

The frontend dev server was started for browser inspection, but browser navigation to local Vite timed out (`ERR_CONNECTION_TIMED_OUT`); the server was stopped. No live network requests, browser console, or responsive layout was observed.

## 7. Database and migration safety

The test fixture selects `TEST_DATABASE_URL` from `.env.test` (value omitted); the parsed target is `examnexus_test` on localhost:5432. Read-only inspection confirmed database identity, Alembic revision `2e11c30af147`, and both `hall_incidents` and `hall_tickets.version`. Flask-Migrate `db check` reports no new operations. The backend suite passed against the inspected test database. A sandboxed connection attempt returned 10013; the historical cause remains undetermined.

No production endpoint/data was contacted, and no upgrade/create-all/stamp/reset/destructive SQL ran. **The local test database verification does not establish the state of the deployed Render database.** Any production migration issue must be diagnosed separately against the actual deployed database before choosing a corrective action.

## 8. Security and authorization

- Protected routes use `roles_required`; unauthenticated and wrong-role behavior has tests that passed in the latest backend suite.
- Current uncommitted decorators populate `flask.g.current_user` from JWT claims before invoking protected views. Current PDF route relies on this identity and passes the caller role/student ID to the service. This addresses the earlier source-level identity gap, and owner download and cross-student denial tests pass.
- Public QR verification intentionally allows anonymous read of safe ticket data; PDF access is role-protected. Token invalidation and superseded responses are represented in services/tests, not exercised in a deployed environment.
- Natural-language query source uses a restricted intent model rather than arbitrary SQL; mutation rejection tests exist and pass in the recorded backend suite.
- No token-refresh endpoint was found; JWT expiry is configured, so session renewal appears to require re-login. Whether a refresh flow is a product requirement is unspecified.
- `two_factor_enabled` is a student model flag only in inspected auth paths; no complete second-factor challenge/verification flow was found. Current modified model default is `False`.
- Profile images are written under the app's local `static/profile_images` directory. This is directly confirmed by source and creates deployment persistence risk on ephemeral filesystems; deployed storage behavior was not tested.
- Backend dependency requirements are mostly unpinned package names, which weakens reproducibility.

## 9. Earlier audit finding reconciliation

| Earlier claim | Current classification | Evidence in current tree |
|---|---|---|
| Test DB lacks `hall_incidents` and `hall_tickets.version` | Not reproduced; confirmed present in the inspected local test database | Read-only query against `examnexus_test` confirmed both; database revision is at head. Production state remains unverified. |
| Frontend test dependencies/scripts missing | Already fixed / stale | Vitest is present; frontend suite runs. |
| Examination DELETE is a stub | Already fixed in current tree | Guarded route/UI exist; backend tests pass including rollback/error redaction. |
| Staff dashboard shows only `department_id` | Already fixed in current tree | Backend emits `department_name`; UI renders name with ID fallback. |
| PDF identity gate lacks `flask.g.current_user` | Decorator fixed; subject-claim issue also fixed | Token account ID is `sub`, not a `student_id` claim; route maps `sub` to Student ID. Owner download and cross-student denial tests pass. |
| Master entity delete routes absent | Confirmed source limitation | No DELETE route found for departments, courses, subjects, students, staff, or halls; status PATCH is supported. |
| `allocationService` lacks 401 handling | Already fixed in current tree | `handle401IfNeeded` clears credentials and dispatches event on non-OK 401 responses. |
| Dependency versions not reproducible | Confirmed | `backend/requirements.txt` contains unpinned requirements. Frontend uses semver ranges and lockfile is present. |
| Missing refresh behavior | Partially confirmed | No refresh endpoint was found in auth routes/services; requirement status unknown. |
| Profile images may be lost on redeploy | Partially confirmed risk | Local static-directory writes confirmed; platform's actual filesystem persistence not tested. |
| Responsive overflow/accessibility issues | Partially confirmed source risks | Historical static inspection indicates likely issues; no current browser/device/accessibility execution. |
| Misleading/incomplete two-factor setting | Partially confirmed, likely defect | Boolean field exists; complete 2FA flow not found in inspected auth routes. |
| Stale test counts/status labels in docs | Partially reconciled | Project overview and testing guide now show the current 455/449/6 backend result. Older audit notes retain explicitly historical counts. Examination summary counts PUBLISHED. |
| New examination DELETE and `test_new_coverage.py` | Present and database-tested | Delete tests pass, including rollback/error redaction. |
| Allocation edit double submission | Confirmed defect, fixed | FRM-04 previously sent 2 PATCH requests; a synchronous ref guard now passes focused regression. |
| Admin hall-ticket tables mobile overflow | Confirmed source gap, fixed in source | Tables now have horizontal scrolling/minimum widths; browser viewport validation is still unverified. |

## 10. Confirmed defects and material risks

### Confirmed

1. **P1 — Student hall-ticket PDF ownership bug (fixed).** JWT `sub` identifies the student, but the PDF endpoint previously read a missing `student_id` claim. The route now maps `sub` to student PK; owner access and cross-student 403 tests pass.
2. **P2 — Examination DELETE error disclosure (fixed).** The route no longer returns raw database exception text; a forced commit failure test verifies rollback and response redaction.
3. **P2 — Six master-data domains have no DELETE endpoint.** No delete routes found for departments, courses, subjects, students, staff, or halls; no visible delete buttons found, though unused service helpers exist. Product behavior (deactivate vs delete) remains a decision.
4. **P2 — Profile-image persistence depends on local disk.** Durable deployment storage is not established.
5. **P2 — Backend dependency versions are unpinned.** Reproducible installs are not assured.
6. **P2 — No token refresh route was found.** Expired sessions appear to require reauthentication; product requirement remains undecided.
7. **P2 — No complete two-factor flow was found.** The student boolean field is not an authentication factor.
8. **P3 — Historical test totals remain in older audit records.** Current project overview and testing guide have been updated to the latest recorded baseline; older figures are retained as historical evidence.
9. **P2 — Allocation form double-submit race (fixed).** A fast repeat click previously sent duplicate PATCH calls; `useRef` guard and regression now pass.
10. **P2 — Admin hall-ticket tables lacked horizontal scrolling (fixed in source).** Actual viewport behavior remains unverified.
11. **P3 — Lint warnings and bundle-size advisory remain.**

### Not confirmed as current defects

The earlier migration absence is not reproduced: the inspected local test database has the relevant objects and is at head. This does not prove that Render production has the same schema. Examination DELETE, staff department display, PDF identity and ownership, allocation 401 handling, and double-submit behavior now have source/runtime evidence. Existing user changes were preserved.

## 11. Coverage gaps and blockers

- Backend full suite: `python -m pytest -q` — **455 collected, 449 passed, 6 skipped, 0 failed**; exit code 0; 94.53 seconds.
- Frontend full suite: `npm test` — **15 test files passed, 83 tests passed, 0 failed**; 111.83 seconds.
- Frontend production build passed with a large-chunk advisory. Lint exited with code 0 with warnings remaining. The local database schema check reported no new migration operations; production database state remains unverified.
- Browser navigation to local Vite timed out. No viewport emulation, console/network, Lighthouse/axe, screen-reader, or keyboard-only browser check occurred.
- Backend tests exercise ticket/PDF generation, QR responses, reallocation and rollback; no browser scan or deployed operation occurred.
- No production credentials or secrets are included in this report. Environment variable names are `DATABASE_URL`, `TEST_DATABASE_URL`, `JWT_SECRET_KEY`, `JWT_ACCESS_TOKEN_EXPIRES_MINUTES`, and `VITE_API_BASE_URL` (plus test config); values were not recorded.
- Sandboxed localhost access returned 10013, while approved read-only inspection and test runs against the verified test DB succeeded. No dependencies were installed during the recorded final verification.

## 12. Readiness and prioritized next session

**Assessment: backend tests, frontend tests/build, and local schema checks pass, but submission readiness is not established.** Browser and deployment verification are unavailable. Product decisions remain for master-data removal, durable profile storage, token renewal, and 2FA.

Recommended order for a separately authorized fix-and-improvement session:

1. Verify browser workflows and viewports 320–430, 768–1024, and ≥1280 px on an environment the browser can reach.
2. Add varied disposable fixtures for the six conditional skips, especially emergency replanning and distinct timetable scopes.
3. Decide master-data removal policy, profile-image object storage, session renewal, and 2FA scope.
4. Pin backend runtime dependencies; review remaining documentation for stale claims.

## 13. Historical audit references

The earlier split audit documents (`AUDIT_SUMMARY.md`, `DEFECTS_AND_RISKS.md`, `FEATURE_AUDIT_MATRIX.md`, `FRONTEND_UI_AUDIT.md`, `PROJECT_INVENTORY.md`, `RESPONSIVE_AND_ACCESSIBILITY_AUDIT.md`, and `TEST_COVERAGE_GAPS.md`) were reviewed and their relevant evidence consolidated here. They were generated during the prior audit and removed after consolidation. The resumable [IMPLEMENTATION_AND_VERIFICATION_LOG.md](IMPLEMENTATION_AND_VERIFICATION_LOG.md) retains the historical execution record; this report distinguishes those earlier claims from the current checks above.