# ExamNexus — System Architecture

## 1. Architecture Overview

ExamNexus is a web-based examination resource orchestration platform built with a React frontend, Flask backend, SQLAlchemy data layer, and relational database.

The architecture separates presentation, API handling, domain services, validation, persistence, and controlled intelligent assistance.

```text
┌─────────────────────────────────────┐
│ Frontend — React + Vite             │
│ Dashboard • Exams • Halls • Reports │
└──────────────────┬──────────────────┘
                   │ HTTP / JSON
                   ▼
┌─────────────────────────────────────┐
│ Backend — Flask                     │
│ Auth • Routes • Request Validation   │
└──────────────────┬──────────────────┘
                   ▼
┌─────────────────────────────────────┐
│ Application Services                │
│ Eligibility • Allocation • Seating  │
│ Validation • Reallocation • Reports │
│ CSV • Queries • Explainability      │
└──────────────────┬──────────────────┘
                   ▼
┌─────────────────────────────────────┐
│ SQLAlchemy Models + Constraints     │
└──────────────────┬──────────────────┘
                   ▼
┌─────────────────────────────────────┐
│ Relational Database                 │
└─────────────────────────────────────┘
```

---

## 2. Frontend Layer

The frontend uses **React and Vite**.

Major interfaces include:

* Authentication
* Administrator dashboard
* Examination and timetable management
* Students, staff, courses, subjects, and halls
* Registration and allocation
* Hall tickets
* Reports
* Requirement-understanding interfaces

The backend location is configurable through:

```text
VITE_API_BASE_URL
```

The frontend communicates with the backend through HTTP API requests.

---

## 3. Backend and Route Layer

The backend uses **Flask** and is organized under:

```text
backend/app/
├── auth/
├── models/
├── routes/
└── services/
```

Routes provide the API boundary for operations such as:

* Authentication
* Master data
* Examinations
* Timetable
* Registrations
* Allocations
* Requirements
* Natural-language queries
* Reports
* Hall tickets
* CSV imports

Routes handle request-level concerns and delegate examination-domain decisions to services.

---

## 4. Authentication and Authorization

ExamNexus uses JWT-based authentication.

```text
Login
  ↓
Credential Validation
  ↓
JWT Access Token
  ↓
Bearer Authentication
  ↓
JWT Verification
  ↓
Role Check
  ↓
Protected Operation
```

Tokens contain the user identifier, role, issued-at timestamp, and expiration.

Authentication and role checks provide separate authorization boundaries:

```text
Authentication → Authorization → Business Operation
```

Unauthenticated requests and unauthorized role access are rejected before protected operations execute.

---

## 5. Application Service Layer

Core examination logic is implemented in services including:

```text
eligibility
allocation
seat_allocation
invigilator_allocation
timetable
validation
lifecycle
reallocation
requirement_parser
allocation_options
natural_language_query
explanation
csv_import_service
hall_ticket
reports
```

This keeps complex examination rules out of route handlers and allows related workflows to reuse the same domain logic.

---

## 6. Eligibility

The eligibility service determines which registered students can participate in an examination.

```text
Examination
    ↓
Registered Students
    ↓
Valid Student?
    ↓
Active Student?
    ↓
Duplicate Check
    ↓
Eligible Students
```

The allocation engine consumes this result rather than recreating eligibility rules independently.

---

## 7. Hall Allocation

Hall allocation is implemented as a deterministic planning process.

```text
Eligible Students
       ↓
Timetable
       ↓
Usable Halls
       ↓
Constraint Checks
       ↓
Accessibility Check
       ↓
Deterministic Planning
       ↓
Hall Allocations
       ↓
Seat Allocation
       ↓
Validation
       ↓
Commit
```

The planner first creates an allocation plan in memory. Persistence occurs only after the required checks and dependent allocation stages succeed.

---

## 8. Hall Constraints

A hall normally must satisfy the required operational conditions:

* Active
* Available
* Not under maintenance
* Positive examination capacity
* No timetable conflict
* Not temporarily excluded

Timetable overlap is evaluated using date/time interval checks:

```text
existing.start < requested.end
AND
existing.end > requested.start
```

Only halls satisfying the applicable constraints become allocation candidates.

---

## 9. Accessibility-Aware Allocation

Accessibility requirements are part of the allocation logic.

Students requiring accessibility support are considered against suitable halls. The planner checks accessible capacity before completing the allocation.

Suitable halls include the required accessibility characteristics and operational conditions, including the implemented ground-floor/accessibility rules.

```text
Accessibility Students
        ↓
Accessible Hall Capacity
        ↓
Capacity Sufficient?
        ↓
Accessibility-Aware Allocation
```

Allocation purpose can identify:

```text
NORMAL
ACCESSIBILITY
MIXED
```

If sufficient suitable capacity is unavailable, the allocation does not silently assign an unsuitable hall.

---

## 10. Deterministic Allocation

The allocator uses explicit capacity, availability, timetable, accessibility, and ordering rules.

Equivalent inputs produce repeatable planning decisions.

The allocation engine does **not** depend on an external machine-learning model for hall selection.

Supported allocation options are intentionally restricted to recognized keys such as:

```text
minimize_halls
accessibility_required
exclude_maintenance_halls
exclude_unavailable_halls
avoid_timetable_conflicts
```

Unknown options or invalid value types are rejected.

---

## 11. Seat and Invigilator Allocation

Hall allocation connects downstream resource allocation.

```text
Hall Allocation
      ├── Seat Allocation
      └── Invigilator Allocation
```

Seat allocation connects students to halls and seats while maintaining uniqueness constraints.

Invigilator allocation connects staff to examination/timetable resources and halls.

These stages operate after the required hall allocation information is available.

---

## 12. Validation and Lifecycle

Validation checks examination resource consistency, including:

* Hall capacity
* Hall availability and maintenance
* Student allocation completeness
* Accessibility requirements
* Duplicate assignments
* Seat uniqueness
* Timetable consistency
* Invigilator consistency

The examination lifecycle is controlled through verified states:

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

Invalid or unsupported transitions are rejected.

---

## 13. Transactional Regeneration

When an allocation is regenerated, dependent records are cleared and recreated in a controlled sequence.

```text
Seat Allocations
      ↓
Invigilator Allocations
      ↓
Hall Allocations
      ↓
New Hall Plan
      ↓
New Seats
      ↓
Validation
      ↓
Commit
```

Database flush and rollback behavior prevents a failed regeneration from leaving partially updated allocation state.

---

## 14. Dynamic Reallocation

Dynamic reallocation reuses the same deterministic planner.

A hall can be temporarily excluded through:

```text
excluded_hall_ids
```

The system can therefore evaluate:

```text
Existing Allocation
       ↓
Temporary Resource Change
       ↓
What-If Replanning
       ↓
Validation
       ↓
Administrator Approval
       ↓
Apply Changes
```

Planning does not permanently modify the affected hall simply because a what-if scenario is evaluated.

---

## 15. Requirement Understanding and Intelligent Assistance

ExamNexus includes controlled intelligent-assistance services for interpreting supported requirements, natural-language queries, and allocation explanations.

Supported requirement options are converted into validated allocation options rather than directly controlling database state.

Natural-language querying is read-only and supports defined examination, timetable, hall, student, and allocation queries.

Mutation-oriented commands such as update, delete, insert, approve, or publish are rejected by the query layer.

The system therefore follows:

```text
Intelligent Assistance
        ↓
Structured Interpretation
        ↓
Deterministic Services
        ↓
Validation
        ↓
Administrator Control
```

---

## 16. Explainability

Allocation explanation is implemented as a read-only service.

It evaluates existing allocation information and allocation predicates to produce structured reasons for selected or rejected halls.

Examples include:

```text
HALL_ACTIVE
HALL_AVAILABLE
HAS_EXAM_CAPACITY
NO_TIMETABLE_CONFLICT
ACCESSIBILITY_SUITABLE
REJECTED_MAINTENANCE
REJECTED_NO_EXAM_CAPACITY
REJECTED_TIMETABLE_CONFLICT
```

The reason vocabulary is controlled rather than generated as arbitrary decision categories.

---

## 17. CSV Import

CSV processing follows a validation-first pipeline:

```text
Upload
  ↓
File/Header Validation
  ↓
Parsing + Normalization
  ↓
Field Validation
  ↓
Reference Validation
  ↓
Business Rules
  ↓
Duplicate Detection
  ↓
Validation Report
  ↓
Import Valid Rows
```

Validation issues contain structured fields such as:

```text
code
field
message
severity
```

Invalid rows are not imported through the valid-row path.

---

## 18. Database Model and Integrity

SQLAlchemy models represent the examination domain, including:

```text
Department
Course
Subject
Student
Staff
Hall
Examination
Timetable
ExamRegistration
HallAllocation
SeatAllocation
InvigilatorAllocation
HallTicket
```

The main relationships connect:

```text
Department → Course → Subject

Examination → Timetable

Examination → Registration → Student

Examination → Timetable → HallAllocation
                              ├── Hall
                              └── SeatAllocation
```

Database constraints complement service-level validation by preventing duplicate identifiers and allocation conflicts.

Examples include uniqueness for student, staff, course, department, and subject identifiers, plus allocation-level uniqueness for timetable/hall/student/seat combinations.

---

## 19. Overall Request Flow

```text
Frontend
   ↓
Flask Route
   ↓
Authentication / Authorization
   ↓
Request Validation
   ↓
Application Service
   ├── Eligibility
   ├── Constraint Checks
   ├── Planning
   ├── Validation
   └── Persistence
   ↓
SQLAlchemy
   ↓
Database
   ↓
Structured Result
   ↓
Frontend
```

---

## 20. Architectural Principles

ExamNexus follows these principles:

* **Separation of concerns:** routes provide the API boundary; services contain domain logic.
* **Deterministic critical decisions:** allocation and validation use explicit rules.
* **Reusable planning:** the same planner supports normal and adaptive allocation.
* **Validation before persistence:** inputs and proposed changes are checked before commit.
* **Transactional changes:** regeneration protects against incomplete database state.
* **Controlled intelligence:** intelligent assistance is bounded by supported operations and validation.
* **Read-only intelligence where appropriate:** querying and explanation do not provide unrestricted database mutation.
* **Explainability:** allocation outcomes can be represented through structured reasons.
* **Administrator control:** critical examination decisions remain subject to validation and approval.

---

## 21. Architecture Summary

ExamNexus connects user-facing examination workflows with a structured domain-service pipeline:

```text
React + Vite
     ↓
Flask API
     ↓
Authentication / Routes
     ↓
Domain Services
     ├── Eligibility
     ├── Allocation
     ├── Seating
     ├── Validation
     ├── Reallocation
     ├── Intelligent Assistance
     └── Reporting
     ↓
SQLAlchemy Models
     ↓
Relational Database
```

The architecture supports dynamic examination planning while keeping critical resource allocation, validation, and persistence governed by explicit rules and administrator-controlled workflows.
