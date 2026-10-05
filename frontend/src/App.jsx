import { useState } from "react";

import Login from "./pages/auth/Login";
import AdminDashboard from "./pages/admin/AdminDashboard";
import Departments from "./pages/admin/departments/Departments";
import Courses from "./pages/admin/courses/Courses";
import Subjects from "./pages/admin/subjects/Subjects";
import Students from "./pages/admin/students/Students";
import Staff from "./pages/admin/staff/Staff";
import Examinations from "./pages/admin/examinations/Examinations";
import Timetables from "./pages/admin/timetable/Timetables";
import ExamRegistrations from "./pages/admin/registrations/ExamRegistrations";
import Halls from "./pages/admin/halls/Halls";
import Allocations from "./pages/admin/allocations/Allocations";
import HallTickets from "./pages/admin/hall-tickets/HallTickets";
import Reports from "./pages/admin/reports/Reports";
import StaffDashboard from "./pages/staff/StaffDashboard";
import StudentDashboard from "./pages/student/StudentDashboard";
import {
  getStoredUser,
  logout,
} from "./services/authService";


function App() {

  const [user, setUser] = useState(
    getStoredUser()
  );

  const [adminPage, setAdminPage] =
    useState("Dashboard");

  const handleLogin = (userData) => {

    setUser(userData);

    setAdminPage("Dashboard");

  };

  const handleLogout = () => {

    logout();

    setUser(null);

    setAdminPage("Dashboard");

  };

  if (!user) {

    return (
      <Login
        onLogin={handleLogin}
      />
    );

  }


  if (user.role === "admin") {

    if (adminPage === "Departments") {

      return (
        <Departments
          user={user}
          onLogout={handleLogout}
          onNavigate={setAdminPage}
        />
      );

    }


if (adminPage === "Courses") {
  return (
    <Courses
      user={user}
      onLogout={handleLogout}
      onNavigate={setAdminPage}
    />
  );
}

if (adminPage === "Subjects") {
  return (
    <Subjects
      user={user}
      onLogout={handleLogout}
      onNavigate={setAdminPage}
    />
  );
}

if (adminPage === "Students") {
  return (
    <Students
      user={user}
      onLogout={handleLogout}
      onNavigate={setAdminPage}
    />
  );
}

if (adminPage === "Staff") {
  return (
    <Staff
      user={user}
      onLogout={handleLogout}
      onNavigate={setAdminPage}
    />
  );
}

if (adminPage === "Examinations") {
  return (
    <Examinations
  user={user}
  onLogout={handleLogout}
  onNavigate={setAdminPage}
/>
  );
}

if (adminPage === "Timetable") {
  return (
    <Timetables
      user={user}
      onLogout={handleLogout}
      onNavigate={setAdminPage}
    />
  );
}

if (adminPage === "Registrations") {
  return (
    <ExamRegistrations
      user={user}
      onLogout={handleLogout}
      onNavigate={setAdminPage}
    />
  );
}

if (adminPage === "Halls") {
  return (
    <Halls
      user={user}
      onLogout={handleLogout}
      onNavigate={setAdminPage}
    />
  );
}

if (adminPage === "Allocations") {
  return (
    <Allocations
      user={user}
      onLogout={handleLogout}
      onNavigate={setAdminPage}
    />
  );
}

if (adminPage === "HallTickets") {
  return (
    <HallTickets
      user={user}
      onLogout={handleLogout}
      onNavigate={setAdminPage}
    />
  );
}

if (adminPage === "Reports") {
  return (
    <Reports
      user={user}
      onLogout={handleLogout}
      onNavigate={setAdminPage}
    />
  );
}
    return (
      <AdminDashboard
        user={user}
        onLogout={handleLogout}
        onNavigate={setAdminPage}
      />
    );

  }


  if (user.role === "staff") {

    return (
      <StaffDashboard
      user={user}
      onLogout={handleLogout}
    />
    );

  }


  if (user.role === "student") {

    return (
       <StudentDashboard
      user={user}
      onLogout={handleLogout}
    />
    );

  }


  handleLogout();

  return null;
}


export default App;
