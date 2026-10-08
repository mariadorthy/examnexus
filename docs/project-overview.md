# ExamNexus — Project Overview

## 1. Introduction

**ExamNexus** is a dynamic examination resource orchestration platform for coordinating the operational complexity of university examinations.

It connects examination data, registration, eligibility, timetables, halls, seats, invigilators, validation, approval, hall tickets, reporting, and adaptive reallocation into one workflow.

The goal is to help administrators generate, validate, explain, approve, and adapt examination resource arrangements while maintaining control over critical decisions.

---

## 2. Problem Statement

University examinations involve interdependent resources and constraints:

* Students and eligibility
* Courses and subjects
* Examination dates and sessions
* Hall capacity and availability
* Accessibility requirements
* Seat assignments
* Invigilator assignments
* Examination lifecycle
* Hall tickets and reporting

A change to one resource can affect other arrangements. For example, an unavailable hall may require students to be reassigned while preserving capacity, accessibility, timetable, and allocation constraints.

ExamNexus addresses this through centralized resource orchestration, independent validation, explainability, and controlled reallocation.

---

## 3. Core Workflow

```text id="9t5z8q"
Login / RBAC
      ↓
Master Data
      ↓
Examination + Timetable
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

When conditions change:

```text id="xjgj4x"
Existing Allocation
      ↓
Resource / Constraint Change
      ↓
What-If Reallocation
      ↓
Validation
      ↓
Administrator Approval
      ↓
Apply Changes
```

---

## 4. Main Capabilities

### Examination Management

* Departments, courses, subjects, students, staff, and halls
* Examination and timetable management
* Student registration and eligibility
* Controlled examination lifecycle

### Resource Orchestration

* Deterministic hall allocation
* Capacity and timetable conflict checks
* Accessibility-aware allocation
* Student seat allocation
* Invigilator allocation
* Allocation regeneration

### Validation and Control

* Independent allocation validation
* Duplicate and capacity checks
* Accessibility validation
* Seat integrity
* Timetable consistency
* Lifecycle and approval control

### Adaptive Operations

* Temporary resource exclusions
* What-if reallocation
* Alternative allocation proposals
* Re-validation before application
* Administrator-controlled changes

### Intelligent Assistance

* Requirement understanding
* Controlled natural-language read-only queries
* Explainable allocation decisions
* Structured CSV validation

The intelligent capabilities assist the workflow but do not replace deterministic critical-decision logic.

---

## 5. Core Domain Model

```text id="5n3f7f"
Department
    ↓
Course
    ↓
Subject
    ↓
Examination
    ├── Timetable
    ├── Registration → Eligibility
    ├── Hall Allocation → Seats
    ├── Invigilator Allocation
    └── Hall Tickets
```

Halls provide resource properties such as capacity, examination capacity, accessibility, availability, and maintenance status.

Students provide eligibility and accessibility information used during resource planning.

---

## 6. Accessibility and Constraint Awareness

Accessibility is represented directly in the student and hall models.

The allocation engine considers accessibility together with:

* Capacity
* Hall availability
* Maintenance
* Timetable conflicts
* Eligible student count
* Temporary exclusions

Accessibility requirements are treated as explicit constraints. If suitable capacity is unavailable, the system reports the allocation failure rather than silently assigning an unsuitable hall.

---

## 7. Validation and Lifecycle Control

ExamNexus separates generation from validation:

```text id="o2n0id"
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

The verified examination lifecycle includes:

```text id="t9cmzz"
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

Invalid lifecycle transitions and invalid allocation conditions are rejected.

---

## 8. Intelligent Orchestration

ExamNexus follows a human-in-the-loop model:

```text id="q66o7g"
Administrator
      ↓
Intelligent Assistance
      ↓
Structured Constraints / Queries / Proposals
      ↓
Deterministic Services
      ↓
Validation
      ↓
Administrator Approval
      ↓
Execution
```

The system supports requirement interpretation, read-only natural-language queries, explainable allocation, and dynamic what-if planning.

> **AI assists understanding, querying, explanation, and adaptation; deterministic constraints, validation, optimization, and administrator approval govern critical examination decisions.**

The supplied implementation does **not** establish an ML model, LLM inference pipeline, vector database, or autonomous AI agent.

---

## 9. CSV Validation

Supported master-data imports use a validation-first workflow:

```text id="82p9fz"
CSV
 ↓
Normalize
 ↓
Validate Fields / References
 ↓
Detect Duplicates
 ↓
Business Validation
 ↓
Structured Report
 ↓
Import Valid Data
```

Validation prevents invalid or conflicting data from being silently inserted.

---

## 10. Security

The backend uses JWT authentication and role-based authorization.

```text id="5u6m4u"
Request
   ↓
Authentication
   ↓
Role Authorization
   ↓
Protected Operation
```

Administrative operations such as allocation changes, requirement application, and reallocation are protected by authorization controls.

---

## 11. Technology Stack

| Layer      | Technologies                                                      |
| ---------- | ----------------------------------------------------------------- |
| Frontend   | React, Vite, Tailwind CSS, Lucide React                           |
| Backend    | Python, Flask, Flask-SQLAlchemy, Flask-CORS, Flask-Migrate, PyJWT |
| Database   | Relational database through SQLAlchemy                            |
| Testing    | pytest                                                            |
| Supporting | QRCode, Pillow                                                    |

---

## 12. Verification Evidence

The automated backend verification reported:

* **290 tests collected**
* **288 passed**
* **2 skipped**
* **0 failed**
* **0 errors**

The focused intelligent-feature suite reported:

* **116 tests collected**
* **116 passed**

Testing covers core examination workflows, allocation, validation, intelligent assistance, reallocation, and related regression behavior.

---

## 13. Design Principles

* **Constraint-aware:** resource decisions use explicit examination rules.
* **Deterministic:** critical allocation and validation behavior is repeatable.
* **Validation-first:** generated arrangements are checked before approval.
* **Explainable:** decisions can be represented through structured evidence.
* **Adaptive:** resource changes can trigger controlled replanning.
* **Human-in-the-loop:** administrators retain authority over critical operations.
* **Safe intelligence:** natural-language capabilities operate within supported operations rather than unrestricted database access.
* **No silent guessing:** unsupported requirements and invalid data are explicitly reported.

---

## 14. Project Outcome

ExamNexus provides a connected examination resource-management workflow from master data and registration through allocation, validation, approval, hall tickets, reporting, and controlled reallocation.

Its central capability is not simply scheduling examinations or assigning halls, but **coordinating interdependent resources, validating the resulting arrangements, explaining decisions, and adapting them when constraints change**.

This positions ExamNexus as a **dynamic examination resource orchestration platform** combining conventional examination management with deterministic intelligent assistance and controlled what-if planning.
