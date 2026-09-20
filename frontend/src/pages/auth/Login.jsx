import { useState } from "react";
import { login } from "../../services/authService";

function Login({ onLogin }) {
const [email, setEmail] = useState("");
const [password, setPassword] = useState("");
const [role, setRole] = useState("admin");
const [showPassword, setShowPassword] = useState(false);
const [error, setError] = useState("");
const [loading, setLoading] = useState(false);

const handleSubmit = async (event) => {
  event.preventDefault();

  setError("");

  if (!email.trim()) {
    setError("Please enter your email.");
    return;
  }

  if (!password.trim()) {
    setError("Please enter your password.");
    return;
  }

  setLoading(true);

  try {
    const result = await login(
      email.trim(),
      password,
      role
    );

    localStorage.setItem(
      "examnexus_token",
      result.access_token
    );

    localStorage.setItem(
      "examnexus_user",
      JSON.stringify(result.user)
    );

    onLogin(result.user);

  } catch (error) {

    setError(
      error.message ||
      "Unable to sign in."
    );

  } finally {

    setLoading(false);

  }
};

return (
<div className="min-h-screen bg-background">
<div className="grid min-h-screen lg:grid-cols-2">

    {/* ================================================= */}
    {/* LEFT SIDE */}
    {/* ================================================= */}

    <div className="relative hidden overflow-hidden bg-sidebar lg:flex">
      {/* Decorative circles */}
      <div className="absolute -left-24 -top-24 h-72 w-72 rounded-full bg-primary opacity-30" />

      <div className="absolute -bottom-32 -right-20 h-96 w-96 rounded-full bg-accent opacity-20" />

      <div className="relative z-10 flex flex-1 flex-col justify-between p-16">

        {/* Logo */}
        <div>
          <div className="flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-background">
              <span className="text-xl font-black text-sidebar">
                EN
              </span>
            </div>

            <span className="text-2xl font-bold tracking-wide text-white">
              ExamNexus
            </span>
          </div>
        </div>

        {/* Main Text */}
        <div className="max-w-lg">
          <p className="mb-5 text-sm font-semibold uppercase tracking-[0.25em] text-accent">
            Examination Management System
          </p>

          <h1 className="text-5xl font-bold leading-tight text-white">
            Manage examinations

            <span className="block text-accent">
              smarter.
            </span>
          </h1>

          <p className="mt-6 max-w-md text-lg leading-8 text-accent-light">
            A centralized platform for managing
            students, courses, examinations,
            halls, staff and examination
            allocations.
          </p>
        </div>

        {/* Footer */}
        <div className="text-sm text-accent-light">
          © 2026 ExamNexus
        </div>
      </div>
    </div>

    {/* ================================================= */}
    {/* RIGHT SIDE */}
    {/* ================================================= */}

    <div className="flex items-center justify-center px-6 py-12 sm:px-10">
      <div className="w-full max-w-md">

        {/* Mobile Logo */}
        <div className="mb-10 flex items-center gap-3 lg:hidden">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-sidebar">
            <span className="font-black text-white">
              EN
            </span>
          </div>

          <span className="text-xl font-bold text-sidebar">
            ExamNexus
          </span>
        </div>

        {/* Heading */}
        <div className="mb-8">
          <p className="mb-2 text-sm font-semibold uppercase tracking-wider text-primary">
            Secure Login
          </p>

          <h2 className="text-3xl font-bold text-text">
            Welcome back
          </h2>

          <p className="mt-2 text-text-muted">
            Sign in to continue to ExamNexus.
          </p>
        </div>

        {/* Error */}
        {error && (
          <div className="mb-5 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {error}
          </div>
        )}

        {/* Form */}
        <form
          onSubmit={handleSubmit}
          className="space-y-5"
        >
          {/* Email */}
          <div>
            <label className="mb-2 block text-sm font-semibold text-sidebar">
              Email address
            </label>

            <input
              type="email"
              value={email}
              onChange={(event) =>
                setEmail(event.target.value)
              }
              placeholder="admin@examnexus.edu"
              autoComplete="email"
              className="w-full rounded-xl border border-border bg-surface px-4 py-3.5 text-text outline-none transition placeholder:text-text-light focus:border-primary focus:ring-4 focus:ring-primary/10"
            />
          </div>

          {/* Password */}
          <div>
            <label className="mb-2 block text-sm font-semibold text-sidebar">
              Password
            </label>

            <div className="relative">
              <input
                type={
                  showPassword
                    ? "text"
                    : "password"
                }
                value={password}
                onChange={(event) =>
                  setPassword(event.target.value)
                }
                placeholder="Enter your password"
                autoComplete="current-password"
                className="w-full rounded-xl border border-border bg-surface px-4 py-3.5 pr-20 text-text outline-none transition placeholder:text-text-light focus:border-primary focus:ring-4 focus:ring-primary/10"
              />

              <button
                type="button"
                onClick={() =>
                  setShowPassword((previous) => !previous)
                }
                className="absolute right-3 top-1/2 -translate-y-1/2 px-2 text-sm font-semibold text-primary hover:text-sidebar"
              >
                {showPassword ? "Hide" : "Show"}
              </button>
            </div>
          </div>

          {/* Role */}
          <div>
            <label className="mb-2 block text-sm font-semibold text-sidebar">
              Login as
            </label>

            <select
              value={role}
              onChange={(event) =>
                setRole(event.target.value)
              }
              className="w-full appearance-none rounded-xl border border-border bg-surface px-4 py-3.5 text-text outline-none transition focus:border-primary focus:ring-4 focus:ring-primary/10"
            >
              <option value="admin">
                Administrator
              </option>

              <option value="staff">
                Staff
              </option>

              <option value="student">
                Student
              </option>
            </select>
          </div>

          {/* Remember */}
          <div className="flex items-center justify-between">
            <label className="flex cursor-pointer items-center gap-2 text-sm text-text-muted">
              <input
                type="checkbox"
                className="h-4 w-4 rounded border-gray-300 accent-sidebar"
              />

              Remember me
            </label>

            <button
              type="button"
              className="text-sm font-semibold text-primary hover:text-sidebar"
            >
              Forgot password?
            </button>
          </div>

          {/* Login */}
          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-xl bg-sidebar px-4 py-3.5 font-semibold text-white shadow-lg shadow-sidebar/20 transition hover:bg-primary disabled:cursor-not-allowed disabled:opacity-60"
          >
            {loading
              ? "Signing in..."
              : "Sign in"}
          </button>
        </form>

        {/* Security Notice */}
        <p className="mt-8 text-center text-xs text-text-light">
          Authorized users only. Your access
          is protected by ExamNexus security.
        </p>
      </div>
    </div>
  </div>
</div>


);
}

export default Login;