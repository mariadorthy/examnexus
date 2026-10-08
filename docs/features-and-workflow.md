# ExamNexus — Features and Workflows

## 1. Overview

ExamNexus provides an end-to-end workflow for managing university examinations and coordinating students, halls, seats, staff, validation, and publication.

```text
Login
  ↓
Master Data
  ↓
Examination
  ↓
Timetable
  ↓
Registration
  ↓
Eligibility
  ↓
Hall Allocation
  ↓
Seat Allocation
  ↓
Invigilator Allocation
  ↓
Validation
  ↓
Approval / Publishing
  ↓
Hall Tickets + Reports
```

Intelligent capabilities support requirement understanding, natural-language querying, explainability, CSV validation, and adaptive reallocation.

---

## 2. Authentication and RBAC

ExamNexus uses JWT-based authentication with role-protected operations.

```text
Login
  ↓
JWT Token
  ↓
Authenticated Request
  ↓
Authentication Check
  ↓
Role Check
  ↓
Operation
```

### Roles

* **Administrator** — manages examinations, resources, allocation, validation, approval, and operations.
* **Staff / Invigilator** — accesses assigned examination and invigilation responsibilities.
* **Student** — accesses examination, eligibility, allocation, and hall-ticket information.

---

## 3. Master Data and CSV Import

The platform manages the foundational entities required for examination operations:

```text
Departments
Courses
Subjects
Students
Staff
Halls
```

Hall records include operational properties such as capacity, examination capacity, accessibility, availability, and maintenance status.

Administrators can import supported master data through CSV.

```text
CSV Upload
   ↓
File / Header Validation
   ↓
Parsing + Normalization
   ↓
Field / Reference Validation
   ↓
Business Rules + Duplicate Detection
   ↓
Validation Report
   ↓
Import Valid Rows
```

Validation detects missing fields, invalid types/dates/emails, invalid references, duplicates, and invalid relationships. The system does not silently repair or guess conflicting data.

---

## 4. Examination and Timetable Management

An examination contains information such as:

* Name and type
* Course and semester
* Dates and duration
* Session configuration
* Excluded dates
* Lifecycle status

Timetable entries connect examinations and subjects to examination dates and sessions.

Timetable information is also used during resource allocation to prevent overlapping hall assignments.

---

## 5. Registration and Eligibility

Students are associated with examinations through registrations.

```text
Student ↔ Examination
        ↓
Eligibility
        ↓
Resource Planning
```

The eligibility service builds the allocation population from registered students while filtering unsuitable records such as inactive students and duplicate references.

Eligible students become inputs to hall allocation, seat allocation, validation, and reporting.

---

## 6. Deterministic Hall Allocation

Hall allocation assigns available examination resources while enforcing explicit constraints.

The allocator considers:

* Hall activity and availability
* Maintenance status
* Examination capacity
* Timetable conflicts
* Accessibility requirements
* Eligible student count
* Temporary exclusions

```text
Eligible Students
       ↓
Candidate Halls
       ↓
Capacity + Accessibility
+ Availability + Maintenance
+ Timetable Conflicts
       ↓
Deterministic Allocation
       ↓
Hall Allocations
```

The allocation checks sufficient capacity before creating assignments.

### Accessibility-aware allocation

Students requiring accessibility support are considered first. Suitable halls must satisfy the required accessibility and operational conditions.

If sufficient accessible capacity is unavailable, allocation fails rather than silently assigning an unsuitable resource.

Persisted allocation purposes can identify:

```text
NORMAL
ACCESSIBILITY
MIXED
```

---

## 7. Seat Allocation

Seat allocation follows hall allocation and creates student-level assignments containing:

* Examination
* Timetable
* Hall
* Hall allocation
* Student
* Seat number / position

Integrity constraints prevent duplicate student assignments and duplicate use of the same seat for a timetable.

```text
Hall Allocation
      ↓
Student Assignment
      ↓
Seat Allocation
```

---

## 8. Invigilator Allocation

Invigilators are assigned in relation to examination timetable and hall assignments.

```text
Examination
    ↓
Timetable
    ↓
Hall
    ↓
Invigilator
```

Controlled regeneration and adaptive allocation workflows can regenerate dependent assignments when required.

---

## 9. Validation and Examination Lifecycle

Allocation generation is separated from independent validation.

Validation checks conditions including:

* Capacity
* Hall validity
* Student seating
* Accessibility compatibility
* Duplicate prevention
* Timetable consistency
* Invigilator consistency

```text
Generate
   ↓
Validate
   ↓
Review
   ↓
Approve
   ↓
Publish
```

Examinations move through controlled lifecycle states such as:

```text
DRAFT → GENERATED → VALIDATED → REVIEW → APPROVED → PUBLISHED
```

Invalid lifecycle transitions are rejected.

---

## 10. Allocation Regeneration

Existing allocations can be regenerated through a controlled operation.

Dependent records are cleared in the required order before a new allocation is generated.

```text
Existing Allocation
       ↓
Clear Dependent Seats
       ↓
Clear Invigilators
       ↓
Clear Hall Allocations
       ↓
Plan New Allocation
       ↓
Generate Seats
       ↓
Commit
```

Transactional behavior allows the operation to roll back when a later stage fails.

---

## 11. Dynamic Reallocation

ExamNexus supports controlled reallocation when a resource becomes unavailable.

```text
Existing Allocation
       ↓
Resource Change
       ↓
Temporary Exclusion
       ↓
Re-run Allocation Planner
       ↓
Validate Proposal
       ↓
Administrator Approval
       ↓
Apply Changes
```

The same deterministic allocation logic is reused rather than introducing a separate reallocation algorithm.

Temporary exclusions allow what-if planning without immediately changing persistent hall availability.

---

## 12. Intelligent Assistance

ExamNexus provides controlled intelligent capabilities around the deterministic examination engine.

### Requirement understanding

Supported requirements include:

```text
Minimum number of halls
Accessibility required
Exclude maintenance halls
Exclude unavailable halls
Avoid timetable conflicts
```

Unsupported requirements are explicitly rejected rather than guessed.

### Natural-language querying

Supported read-only queries include examination status, timetable information, hall capacity/status, student counts, hall assignments, and allocation summaries.

```text
Natural Language
      ↓
Intent + Entity Extraction
      ↓
Supported Read Operation
      ↓
Structured Result
```

Mutation requests and arbitrary database operations are rejected.

### Allocation explainability

The system can explain hall selection or rejection using structured reason codes based on actual allocation predicates, including capacity, availability, maintenance, timetable conflicts, and accessibility.

Detailed intelligent-orchestration behavior is documented in `04_AI_AND_INTELLIGENT_ORCHESTRATION.md`.

---

## 13. Hall Tickets and Reporting

Hall-ticket functionality connects students with their examination information, including examination, student, verification token, issue timestamp, and status.

Reporting functionality covers operational views such as:

* Allocation reports
* Student allocation
* Hall utilization
* Invigilator workload

These outputs provide visibility into the results of examination resource orchestration.

---

## 14. End-to-End Workflow

```text
Master Data
    ↓
Examination
    ↓
Timetable
    ↓
Registration
    ↓
Eligibility
    ↓
Hall Allocation
    ↓
Seat Allocation
    ↓
Invigilator Allocation
    ↓
Validation
    ↓
Review / Approval
    ↓
Publishing
    ↓
Hall Tickets + Reports
```

### Adaptive path

```text
Resource Change
    ↓
Affected Allocation
    ↓
Temporary Exclusion
    ↓
Deterministic Reallocation
    ↓
Validation
    ↓
Administrator Approval
    ↓
Regenerate Dependent Resources
```

---

## 15. Feature Design Principles

* **Constraint-first:** critical decisions use explicit examination rules.
* **Deterministic:** allocation uses repeatable logic rather than prediction.
* **Validation before commitment:** generated results are checked before operational use.
* **Controlled intelligence:** natural-language capabilities operate within supported schemas and operations.
* **Accessibility-aware:** accessibility requirements are included in resource planning.
* **Human-in-the-loop:** administrators retain approval authority for critical changes.
* **Explainable:** allocation decisions can be represented through structured evidence.
* **No silent guessing:** unsupported requirements and invalid input are reported explicitly.

### Feature Summary

```text
Master Data
    +
Examination & Timetable
    +
Eligibility
    +
Resource Allocation
    +
Accessibility
    +
Validation & Lifecycle
    +
Adaptive Reallocation
    +
Intelligent Assistance
    +
Hall Tickets & Reporting
```
