import { useState } from "react";

import Login from "./pages/auth/Login";
import AdminDashboard from "./pages/admin/AdminDashboard";
import Departments from "./pages/admin/departments/Departments";

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
      <div>
        Staff dashboard
      </div>
    );

  }


  if (user.role === "student") {

    return (
      <div>
        Student dashboard
      </div>
    );

  }


  handleLogout();

  return null;
}


export default App;
