# ExamNexus — Testing and Verification

ExamNexus uses automated testing and targeted verification to validate examination planning, resource allocation, intelligent assistance, and administrative workflows.

The testing strategy focuses on:

1. **Determinism** — equivalent inputs produce consistent results.
2. **Constraint safety** — critical examination decisions satisfy explicit rules.
3. **Non-regression** — intelligent features do not break existing workflows.

---

## 1. Testing Scope

The backend test suite covers:

* Authentication and authorization
* Master-data management
* CSV import and validation
* Examination and timetable management
* Student eligibility and registration
* Hall, accessibility, seat, and invigilator allocation
* Examination lifecycle
* Reports and hall tickets
* Requirement understanding
* Natural-language queries
* Dynamic reallocation and what-if planning
* Explainable allocation
* Requirements-to-allocation integration
* End-to-end regression

Tests cover both successful workflows and deliberately invalid states.

---

## 2. Automated Testing

Backend tests use **pytest** and run against an isolated test environment.

Major verification areas include:

| Area           | Verification                                           |
| -------------- | ------------------------------------------------------ |
| Authentication | Login, protected routes, role checks                   |
| Master Data    | Departments, courses, subjects, students, staff, halls |
| Allocation     | Capacity, availability, conflicts, accessibility       |
| Seating        | Seat uniqueness and student assignment                 |
| Requirements   | Supported/unsupported requirement handling             |
| Queries        | Read-only queries and unsafe-input rejection           |
| Reallocation   | What-if planning and controlled application            |
| Explainability | Deterministic allocation reasons                       |
| CSV            | Parsing, validation, duplicates, references            |
| Lifecycle      | Valid and invalid state transitions                    |
| Regression     | Complete examination workflow                          |

---

## 3. Allocation and Constraint Verification

Allocation tests verify that:

* eligible students can be allocated;
* hall capacity is respected;
* inactive, unavailable, or maintenance halls are excluded;
* timetable conflicts are prevented;
* duplicate hall assignments are rejected;
* accessibility requirements are respected;
* every eligible student receives a valid seat;
* seats cannot be assigned to multiple students.

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

* hall allocation;
* seat allocation;
* requirement parsing;
* natural-language query parsing;
* dynamic reallocation;
* explanations;
* requirement-to-allocation integration.

Repeated regeneration is also checked to ensure that duplicate hall allocations or seats are not accumulated.

When no allocation options are supplied, integration tests verify that existing allocation behavior remains unchanged.

---

## 5. Intelligent Requirement Understanding

Requirement parsing is tested for supported requirements such as:

* minimizing halls;
* accessibility requirements;
* excluding maintenance halls;
* excluding unavailable halls;
* avoiding timetable conflicts.

The tests also cover:

* multiple requirements;
* unsupported requirements;
* empty or whitespace input;
* invalid input types;
* invalid structured keys/types;
* case-insensitive input.

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

1. load an existing allocation;
2. identify affected resources;
3. temporarily exclude unavailable halls;
4. discover alternative capacity;
5. preserve allocation constraints;
6. produce a deterministic proposal;
7. validate the proposal;
8. keep what-if planning separate from persisted state.

Additional tests verify that rejected proposals do not mutate persisted data and that critical reallocation requires administrator authorization.

Successful reallocation also verifies dependent updates such as invigilator assignments and invalidation of affected issued hall tickets.

---

## 8. Explainable Allocation

The explanation service is tested against the actual allocation logic.

Tests verify that:

* reason codes belong to the supported vocabulary;
* selected and rejected halls receive appropriate reasons;
* explanations correspond to persisted allocation state;
* unsupported reasons are not invented;
* explanations are deterministic;
* explanation generation does not modify database state.

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

* valid files;
* missing fields or columns;
* duplicate identifiers;
* existing database duplicates;
* invalid emails, integers, booleans, and dates;
* foreign-key references;
* capacity boundaries;
* empty or malformed files;
* normalized headers and values;
* warnings for possible duplicate names.

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

The complete backend suite was executed with:

```powershell
pytest -q
```

Verified result:

| Result          | Count |
| --------------- | ----: |
| Tests collected |   290 |
| Passed          |   288 |
| Skipped         |     2 |
| Failed          |     0 |
| Errors          |     0 |

The two skipped tests are conditional scenarios unavailable in the current test configuration.

A focused intelligent-feature suite was also executed:

```text
116 collected
116 passed
0 failed
```

This suite covers:

* Requirement understanding
* Natural-language queries
* Dynamic reallocation
* Explainable allocation
* Requirements-to-allocation integration

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

* supported-operation boundaries;
* unsafe-request rejection;
* deterministic behavior;
* constraint preservation;
* explainability;
* administrator control;
* non-mutation of read-only operations;
* regression safety.

---

## 14. Verification Status

The current verified backend result is:

**290 tests collected → 288 passed → 2 skipped → 0 failed → 0 errors.**

The testing evidence demonstrates that ExamNexus's deterministic examination workflows and intelligent-assistance features operate within defined constraints while preserving validation, safety, and administrator control.
