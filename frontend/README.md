# ExamNexus — Dynamic Examination Resource Orchestration Platform

ExamNexus is a web application that helps universities manage examination data, timetables, eligibility, halls, student seating, invigilators, validation, hall tickets, and AI-assisted planning (later).  
The MVP focuses on a **deterministic, reliable examination workflow** before adding AI or advanced features.

---

## 🎯 Project Vision
Workflow: **Login → Role-based dashboard → Master data → Examination creation → Timetable → Registration → Eligibility → Hall allocation → Seat allocation → Invigilator allocation → Validation → Admin approval → Hall ticket generation → Reports/Dashboard**

---

## 👥 User Roles
- **Admin**: Full exam management (departments, courses, subjects, students, staff, halls, exams, timetables, allocations, validation, approval, hall tickets, reports).  
- **Staff/Invigilator**: Login, view assigned exams/halls/duties, access permitted reports.  
- **Student**: Login, view profile, exam schedule, eligibility, hall/seat allocation, hall ticket with QR verification.

---

## 🔐 Authentication
- Email/ID + password login  
- Password hashing (never plaintext)  
- Role-based access control (Admin, Staff, Student)  
- Protected routes + logout  
- No 2FA for MVP (Admin 2FA deferred)  

---

## 🚀 MVP Features (P0)
Mandatory for MVP:
1. Authentication & RBAC  
2. Department/Course/Subject/Student/Staff/Hall CRUD  
3. Manual entry + CSV upload  
4. Examination creation + timetable validation  
5. Student registration + eligibility checking  
6. Hall availability + hall allocation (capacity, accessibility-first)  
7. Seat allocation (valid numbering, no duplicates)  
8. Invigilator allocation (availability, no overlaps)  
9. Independent validation service  
10. Admin review & approval  
11. Hall ticket generation + QR verification  
12. Dashboard & basic reports  

---

## ⛔ Exclusions (MVP)
Do not introduce unless justified later:
- FastAPI, Next.js, Redux  
- MongoDB, Redis  
- Docker/Kubernetes, microservices  
- LangChain/LangGraph, ML, vector DBs  
- WebSockets, OR-Tools, complex distributed architecture  

---

## 📊 Demo Story
1. Admin logs in.  
2. Creates master data (departments, courses, subjects, students, staff, halls).  
3. Creates an examination and timetable.  
4. Registers students and checks eligibility.  
5. Allocates halls and seats.  
6. Assigns invigilators.  
7. Runs validation service.  
8. Reviews and approves plan.  
9. Generates hall tickets with QR codes.  
10. Views dashboard and reports.  

---

## ✅ MVP Stop Condition
Phase 0 is complete when the **basic examination workflow works reliably end-to-end** with authentication, CRUD, timetable, eligibility, allocation, validation, approval, hall tickets, and dashboard.

---

## 🛠 Tech Stack
- **Frontend**: React, Vite, Tailwind CSS  
- **Backend**: Flask, Flask-SQLAlchemy, SQLAlchemy, Flask-Login, Werkzeug hashing  
- **Database**: PostgreSQL (normalized schema)  
- **Tools**: Git/GitHub, Postman/Thunder Client, pytest, qrcode, ReportLab, dotenv, Flask-CORS
