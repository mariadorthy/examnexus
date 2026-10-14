# ExamNexus — Testing and Verification

ExamNexus uses automated testing and targeted verification to validate examination planning, resource allocation, intelligent assistance, and administrative workflows.

The testing strategy focuses on:

1. **Determinism** — equivalent inputs produce consistent results.
2. **Constraint safety** — critical examination decisions satisfy explicit rules.
3. **Non-regression** — intelligent features do not break existing workflows.

---

## 1. Testing Scope

The backend test suite covers:

- Authentication and authorization
- Master-data management
- CSV import and validation
- Examination and timetable management
- Student eligibility and registration
- Hall, accessibility, seat, and invigilator allocation
- Examination lifecycle
- Reports and hall tickets
- Requirement understanding
- Natural-language queries
- Dynamic reallocation and what-if planning
- Explainable allocation
- Requirements-to-allocation integration
- End-to-end regression

Tests cover both successful workflows and deliberately invalid states.

---

## 2. Automated Testing

Backend tests use **pytest** and run against an isolated test environment.

Major verification areas include:

| Area | Verification |
|---|---|
| Authentication | Login, protected routes, role checks |
| Master Data | Departments, courses, subjects, students, staff, halls |
| Allocation | Capacity, availability, conflicts, accessibility |
| Seating | Seat uniqueness and student assignment |
| Requirements | Supported/unsupported requirement handling |
| Queries | Read-only queries and unsafe-input rejection |
| Reallocation | What-if planning and controlled application |
| Explainability | Deterministic allocation reasons |
| CSV | Parsing, validation, duplicates, references |
| Lifecycle | Valid and invalid state transitions |
| Regression | Complete examination workflow |

---

## 3. Allocation and Constraint Verification

Allocation tests verify that:

- Eligible students can be allocated.
- Hall capacity is respected.
- Inactive, unavailable, or maintenance halls are excluded.
- Timetable conflicts are prevented.
- Duplicate hall assignments are rejected.
- Accessibility requirements are respected.
- Every eligible student receives a valid seat.
- Seats cannot be assigned to multiple students.

The validation layer is also tested independently by deliberately creating invalid states such as capacity overruns and accessibility violations.

```text
Generate Allocation
       ↓
Persisted State
       ↓
Independent Validation
       ↓
VALID / INVALID
```

This confirms that validation does not simply trust the allocation generator.

---

## 4. Determinism and Regeneration

Tests verify repeatability for:

- Hall allocation
- Seat allocation
- Requirement parsing
- Natural-language query parsing
- Dynamic reallocation
- Explanations
- Requirement-to-allocation integration

Repeated regeneration is also checked to ensure that duplicate hall allocations or seats are not accumulated.

When no allocation options are supplied, integration tests verify that existing allocation behavior remains unchanged.

---

## 5. Intelligent Requirement Understanding

Requirement parsing is tested for supported requirements such as:

- Minimizing halls
- Accessibility requirements
- Excluding maintenance halls
- Excluding unavailable halls
- Avoiding timetable conflicts

The tests also cover:

- Multiple requirements
- Unsupported requirements
- Empty or whitespace input
- Invalid input types
- Invalid structured keys/types
- Case-insensitive input

Unsupported requirements are reported rather than guessed.

The parser produces structured requirements and cannot directly execute allocation or approval actions.

---

## 6. Natural-Language Query Safety

Natural-language querying is restricted to supported read-only operations, including examination, timetable, hall, student, and allocation queries.

The test suite verifies rejection of unsafe or mutation-oriented input such as:

```text
INSERT
UPDATE
DELETE
DROP
APPROVE
PUBLISH
UNION SELECT
SQL-injection-like patterns
```

Tests also verify that read-only queries do not mutate examination, student, hall, allocation, or seat data.

---

## 7. Dynamic Reallocation

Dynamic reallocation tests verify that the system can:

1. Load an existing allocation.
2. Identify affected resources.
3. Temporarily exclude unavailable halls.
4. Discover alternative capacity.
5. Preserve allocation constraints.
6. Produce a deterministic proposal.
7. Validate the proposal.
8. Keep what-if planning separate from persisted state.

Additional tests verify that rejected proposals do not mutate persisted data and that critical reallocation requires administrator authorization.

Successful reallocation also verifies dependent updates such as invigilator assignments and invalidation of affected issued hall tickets.

---

## 8. Explainable Allocation

The explanation service is tested against the actual allocation logic.

Tests verify that:

- Reason codes belong to the supported vocabulary.
- Selected and rejected halls receive appropriate reasons.
- Explanations correspond to persisted allocation state.
- Unsupported reasons are not invented.
- Explanations are deterministic.
- Explanation generation does not modify database state.

Example reasons include:

```text
HALL_ACTIVE
HALL_AVAILABLE
HAS_EXAM_CAPACITY
NO_TIMETABLE_CONFLICT
ACCESSIBILITY_SUITABLE
REJECTED_MAINTENANCE
REJECTED_TIMETABLE_CONFLICT
```

---

## 9. CSV and Data Validation

CSV tests cover:

- Valid files
- Missing fields or columns
- Duplicate identifiers
- Existing database duplicates
- Invalid emails, integers, booleans, and dates
- Foreign-key references
- Capacity boundaries
- Empty or malformed files
- Normalized headers and values
- Warnings for possible duplicate names

The import workflow is validation-first:

```text
CSV
 ↓
Parse + Normalize
 ↓
Validate
 ↓
Report Issues
 ↓
Import Valid Rows
```

Invalid data is reported rather than silently corrected.

---

## 10. Lifecycle and Administrative Controls

The examination lifecycle is tested through:

```text
DRAFT
  ↓
GENERATED
  ↓
VALIDATED
  ↓
REVIEW
  ↓
APPROVED
  ↓
PUBLISHED
```

Tests verify that invalid, skipped, or backward transitions are rejected.

Allocation modifications after protected lifecycle states are also rejected, preserving administrator control over critical examination decisions.

---

## 11. End-to-End Regression

The regression workflow verifies the complete examination process:

```text
Examination
    ↓
Allocation
    ↓
Invigilators
    ↓
Validation
    ↓
Approval / Lifecycle
    ↓
Publication
    ↓
Hall Tickets
```

This regression coverage ensures that requirement understanding, natural-language queries, explainability, and dynamic reallocation do not break the existing examination workflow.

---

## 12. Test Evidence

### Latest backend verification

Command:

```powershell
python -m pytest -q
```

| Result | Count |
|---|---:|
| Tests collected | 455 |
| Passed | 449 |
| Skipped | 6 |
| Failed | 0 |
| Duration | 94.53 seconds |

### Latest frontend verification

Command:

```powershell
npm test
```

| Result | Count |
|---|---:|
| Test files passed | 15 |
| Tests passed | 83 |
| Failed | 0 |
| Duration | 111.83 seconds |

### Additional verification

- Frontend production build completed successfully, with a large-chunk advisory.
- Lint exited with code 0; warnings remain.
- The read-only schema check of the local `examnexus_test` database reported no new migration operations.
- The inspected local test database was at Alembic revision `2e11c30af147`; `hall_incidents` and `hall_tickets.version` were present.
- Browser-based visual, responsive, accessibility, and complete live frontend/API verification remain pending.

The earlier 290-test result and focused 116-test result are historical results, not the latest verification baseline. The six skipped backend tests are not counted as passed. They depend on fixture data that does not currently represent the required scenarios. Their specific reasons and the remaining audit findings are documented in `audit/PROJECT_AUDIT_AND_VERIFICATION.md`.

The local database verification does not establish that the deployed Render production database has the same schema or migration revision.

---

## 13. Verification Philosophy

ExamNexus follows an **AI-assisted, not AI-controlled** verification model.

```text
User Requirement
      ↓
Structured Interpretation
      ↓
Deterministic Constraints
      ↓
Allocation / Validation
      ↓
Explanation
      ↓
Administrator Review
      ↓
Approved Action
```

Intelligent capabilities are therefore verified not only for correct output, but also for:

- Supported-operation boundaries
- Unsafe-request rejection
- Deterministic behavior
- Constraint preservation
- Explainability
- Administrator control
- Non-mutation of read-only operations
- Regression safety

---

## 14. Verification Status

The latest recorded backend and frontend automated test suites passed with no failures. The production build completed successfully, with a large-chunk advisory. Lint exited with code 0, with warnings remaining.

The backend suite includes six skipped, fixture-dependent scenarios. The frontend suite uses mocked API responses. Local database schema verification does not establish the state of the deployed production database.

Browser rendering, responsive behavior, accessibility, and complete live browser-to-API workflows remain unverified. Passing automated tests alone does not establish full submission or production readiness.

See `audit/PROJECT_AUDIT_AND_VERIFICATION.md` for detailed results, skip reasons, findings, and remaining verification gaps.