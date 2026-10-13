import { useEffect, useState } from "react";
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
import HallTicketVerification
  from "./pages/public/HallTicketVerification";
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

  // --------------------------------------------------
  // URL HASH ROUTER (DEF-01)
  // Lets F5 / Back / Forward / deep links work without
  // pulling in react-router. Public verify route is
  // already handled separately above.
  // --------------------------------------------------

  useEffect(() => {
    const readHash = () => {
      const raw = window.location.hash.replace(/^#\/?/, "");
      if (!raw) return "Dashboard";
      // Match against known admin pages (case-insensitive,
      // dashes -> nothing). Unknown values fall back.
      const known = [
        "Dashboard", "Departments", "Courses", "Subjects",
        "Students", "Staff", "Examinations", "Timetable",
        "Registrations", "Halls", "Allocations",
        "HallTickets", "Reports",
      ];
      const match = known.find(
        (k) => k.toLowerCase() === raw.toLowerCase()
      );
      return match || "Dashboard";
    };

        const onHashChange = () => {
      setAdminPage(readHash());
    };

    // Apply the current hash only if it disagrees with the
    // current state. Avoids a redundant render on mount.
    const initial = readHash();
    setAdminPage((current) =>
      current === initial ? current : initial
    );

    window.addEventListener("hashchange", onHashChange);
    return () =>
      window.removeEventListener("hashchange", onHashChange);
  }, []);

  const navigateTo = (page) => {
    setAdminPage(page);
    const slug =
      page === "Hall Tickets" ? "HallTickets" : page;
    window.location.hash = `#/${slug}`;
  };  

  useEffect(() => {
    const onUnauthorized = () => {
      setUser(null);
      setAdminPage("Dashboard");
      window.location.hash = "";
    };

    window.addEventListener(
      "examnexus:unauthorized",
      onUnauthorized
    );

    return () => {
      window.removeEventListener(
        "examnexus:unauthorized",
        onUnauthorized
      );
    };
  }, []);

  // --------------------------------------------------
  // PUBLIC HALL-TICKET QR VERIFICATION
  // Must run BEFORE authentication checks.
  // QR scanners must not be redirected to Login.
  // --------------------------------------------------
  if (
    window.location.pathname.startsWith(
      "/verify-hall-ticket/"
    )
  ) {
    return <HallTicketVerification />;
  }

    const handleLogin = (userData) => {

    setUser(userData);

    setAdminPage("Dashboard");

    window.location.hash = "#/Dashboard";

  };
  const handleLogout = () => {

    logout();

    setUser(null);

    setAdminPage("Dashboard");

    window.location.hash = "";

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
          onNavigate={navigateTo}
        />
      );

    }


    if (adminPage === "Courses") {
      return (
        <Courses
          user={user}
          onLogout={handleLogout}
          onNavigate={navigateTo}
        />
      );
    }

    if (adminPage === "Subjects") {
      return (
        <Subjects
          user={user}
          onLogout={handleLogout}
          onNavigate={navigateTo}
        />
      );
    }

    if (adminPage === "Students") {
      return (
        <Students
          user={user}
          onLogout={handleLogout}
         onNavigate={navigateTo}
        />
      );
    }

    if (adminPage === "Staff") {
      return (
        <Staff
          user={user}
          onLogout={handleLogout}
          onNavigate={navigateTo}
        />
      );
    }

    if (adminPage === "Examinations") {
      return (
        <Examinations
          user={user}
          onLogout={handleLogout}
          onNavigate={navigateTo}
        />
      );
    }

    if (adminPage === "Timetable") {
      return (
        <Timetables
          user={user}
          onLogout={handleLogout}
         onNavigate={navigateTo}
        />
      );
    }

    if (adminPage === "Registrations") {
      return (
        <ExamRegistrations
          user={user}
          onLogout={handleLogout}
          onNavigate={navigateTo}
        />
      );
    }

    if (adminPage === "Halls") {
      return (
        <Halls
          user={user}
          onLogout={handleLogout}
         onNavigate={navigateTo}
        />
      );
    }

    if (adminPage === "Allocations") {
      return (
        <Allocations
          user={user}
          onLogout={handleLogout}
      onNavigate={navigateTo}
        />
      );
    }

    if (adminPage === "HallTickets") {
      return (
        <HallTickets
          user={user}
          onLogout={handleLogout}
         onNavigate={navigateTo}
        />
      );
    }

    if (adminPage === "Reports") {
      return (
        <Reports
          user={user}
          onLogout={handleLogout}
         onNavigate={navigateTo}
        />
      );
    }
    return (
      <AdminDashboard
        user={user}
        onLogout={handleLogout}
       onNavigate={navigateTo}
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

  // Unknown role: send the user back to Login without
  // mutating state during render (DEF-02).
  logout();
  return <Login onLogin={handleLogin} />;
}


export default App;
