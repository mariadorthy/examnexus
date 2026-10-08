# ExamNexus — AI and Intelligent Orchestration

## 1. Purpose

ExamNexus uses **AI-assisted and intelligent orchestration** to help administrators understand requirements, query examination data, adapt allocations, and explain decisions.

> **AI assists understanding, querying, explanation, and adaptation; deterministic constraints, validation, optimization, and administrator approval govern critical examination decisions.**

The supplied implementation does **not** establish an ML model, LLM inference pipeline, vector database, or autonomous AI agent. Intelligent behavior is implemented through controlled parsers, rule-based logic, deterministic allocation, adaptive planning, and explainable decision logic.

---

## 2. Intelligent Orchestration Model

```text
Understand
    ↓
Constrain
    ↓
Optimize
    ↓
Validate
    ↓
Explain
    ↓
Approve
    ↓
Execute
    ↓
Adapt
```

| Stage      | Responsibility                                                  |
| ---------- | --------------------------------------------------------------- |
| Understand | Interpret supported requirements and natural-language questions |
| Constrain  | Convert supported requirements into structured constraints      |
| Optimize   | Generate deterministic resource allocations                     |
| Validate   | Check capacity, conflicts, availability, and other rules        |
| Explain    | Provide evidence-based reasons for decisions                    |
| Approve    | Keep critical changes under administrator control               |
| Execute    | Persist validated changes                                       |
| Adapt      | Re-plan when resources or constraints change                    |

---

## 3. Intelligent Components

The main intelligent-assistance capabilities are:

* Requirement understanding
* Natural-language read-only querying
* Allocation options
* Deterministic optimization
* Dynamic reallocation and what-if planning
* Explainable allocation
* Structured CSV/data-quality validation

These capabilities operate through existing examination services rather than an independent autonomous AI subsystem.

```text
Intelligent Assistance
        │
        ├── Requirement Understanding
        ├── Natural-Language Queries
        └── Explainability
                ↓
      Deterministic Services
        ├── Allocation
        ├── Validation
        └── Reallocation
                ↓
             Database
```

---

## 4. Requirement Understanding

Supported requirement concepts include:

```text
minimize_halls
accessibility_required
exclude_maintenance_halls
exclude_unavailable_halls
avoid_timetable_conflicts
```

Requirements are converted only into constraints supported by the allocation engine.

```text
Requirement
    ↓
Interpretation
    ↓
Supported?
 ┌──┴──┐
Yes   No
 ↓     ↓
Option  Explicit
       Unsupported Result
```

Allocation options use a **closed schema**. Unknown options or incorrectly typed values are rejected rather than silently interpreted.

---

## 5. Natural-Language Querying

ExamNexus provides controlled, read-only natural-language access to examination information.

Supported intents include:

* Examination listing and status
* Timetable information
* Hall capacity and status
* Eligible/registered student counts
* Students assigned to halls
* Hall allocation summaries
* Unallocated student counts

The service can identify supported entities such as examination names, halls, courses, and examination IDs.

```text
Natural-Language Input
        ↓
Intent Detection
        ↓
Entity Extraction
        ↓
Supported Read-Only Intent?
   ├── No → Reject
   └── Yes
          ↓
   Structured Query
          ↓
      Read Result
```

Mutation operations such as `DELETE`, `UPDATE`, `INSERT`, `DROP`, `APPROVE`, and `PUBLISH` are rejected. The query layer does not expose arbitrary SQL execution.

---

## 6. Deterministic Allocation Engine

The actual examination resource decision remains deterministic.

The allocator considers:

* Hall availability and activity
* Maintenance status
* Examination capacity
* Timetable conflicts
* Accessibility requirements
* Eligible student count
* Temporary exclusions

Accessibility students are handled first, followed by normal students using deterministic capacity-based selection.

```text
Structured Requirements
        ↓
Deterministic Allocator
        ↓
Hall Selection
        ↓
Validation
```

Therefore, ExamNexus demonstrates **intelligent orchestration and deterministic optimization**, not ML-based prediction.

---

## 7. Dynamic Reallocation and What-If Planning

When a resource becomes unavailable, ExamNexus can generate an alternative allocation using the same planning engine.

```text
Current Allocation
        ↓
Temporary Hall Exclusion
        ↓
Re-run Planner
        ↓
Alternative Allocation
        ↓
Validate
        ↓
Administrator Review
```

The temporary exclusion supports what-if evaluation without requiring the hall's persistent availability state to be changed during planning.

Reallocation continues to respect:

```text
Capacity
Accessibility
Availability
Maintenance
Timetable Conflicts
Duplicate Prevention
```

---

## 8. Explainable Allocation

The explanation service examines actual allocations using the same decision predicates used by the allocator.

Possible selection reasons include:

```text
HALL_ACTIVE
HALL_AVAILABLE
NOT_UNDER_MAINTENANCE
HAS_EXAM_CAPACITY
NO_TIMETABLE_CONFLICT
ACCESSIBILITY_SUITABLE
SELECTED_BY_ALLOCATOR_STRATEGY
```

Rejected-hall reasons include conditions such as:

```text
REJECTED_INACTIVE
REJECTED_UNAVAILABLE
REJECTED_MAINTENANCE
REJECTED_NO_EXAM_CAPACITY
REJECTED_TIMETABLE_CONFLICT
REJECTED_TRANSIENTLY_EXCLUDED
REJECTED_NO_REMAINING_CAPACITY
```

The reason vocabulary is closed and evidence-based.

```text
Actual Allocation
       ↓
Allocation Predicates
       ↓
Known Reason Codes
       ↓
Human-Readable Explanation
```

This avoids generating explanations that are unrelated to the actual allocation logic.

---

## 9. Intelligent CSV Validation

CSV import follows a structured data-quality workflow rather than LLM-based data repair.

```text
CSV
 ↓
Normalize
 ↓
Validate
 ↓
Detect Errors / Duplicates / Warnings
 ↓
Structured Validation Report
```

Issues contain:

```text
code
field
message
severity
```

The final import remains deterministic and validation-driven.

---

## 10. Human-in-the-Loop and Safety

ExamNexus separates intelligent assistance from operational authority.

### Intelligent assistance

* Understand
* Query
* Suggest
* Simulate
* Explain
* Adapt

### Deterministic operational control

* Validate
* Enforce constraints
* Persist
* Approve
* Publish

The intelligent layer cannot bypass capacity or accessibility constraints, execute arbitrary database mutations, or silently invent unsupported requirements.

```text
Administrator
     ↓
Intelligent Assistance
     ↓
Deterministic Services
     ↓
Validation
     ↓
Administrator Approval
     ↓
Execution
```

---

## 11. Implementation Boundary

### Implemented

* Requirement interpretation
* Structured allocation options
* Natural-language read-only queries
* Deterministic resource allocation/optimization
* Accessibility-aware allocation
* Dynamic reallocation
* What-if planning
* Explainable allocation
* Structured CSV validation

### Not established by the supplied implementation

* Machine-learning prediction
* Generative LLM inference
* Autonomous AI agents
* Vector-database retrieval
* Model fine-tuning
* Unrestricted AI database access

The accurate characterization is:

> **ExamNexus is an AI-assisted examination resource orchestration platform where intelligent interfaces and adaptive planning work together with deterministic constraints, validation, explainability, and administrator approval.**

---

## 12. End-to-End Workflow

```text
Administrator Requirement
          ↓
Requirement Understanding
          ↓
Structured Constraints
          ↓
Deterministic Allocation
          ↓
Validation
          ↓
Explanation
          ↓
Administrator Review
          ↓
Approval
          ↓
Execution
          ↓
Resource / Constraint Change
          ↓
Reallocation
          ↓
Re-validation
```

### Design principles

1. **Assistance over autonomy** — administrators retain operational authority.
2. **Constraints over guesses** — critical decisions use explicit rules.
3. **Evidence over free-form explanations** — explanations reflect actual system state.
4. **Adaptation over static scheduling** — resource changes can trigger controlled replanning.
5. **Validation over blind execution** — proposed decisions are checked before becoming operational state.
