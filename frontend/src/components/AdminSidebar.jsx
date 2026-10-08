import {
  LayoutDashboard,
  Building2,
  BookOpen,
  GraduationCap,
  Users,
  ClipboardList,
  CalendarDays,
  MapPinned,
  BarChart3,
  LogOut,
  X,
} from "lucide-react";


function AdminSidebar({
  user,
  onLogout,
  sidebarOpen,
  setSidebarOpen,
  activePage = "Dashboard",
  onNavigate,
}) {

  const navigation = [
    {
      label: "Dashboard",
      icon: LayoutDashboard,
    },
    {
      label: "Departments",
      icon: Building2,
    },
    {
      label: "Courses",
      icon: BookOpen,
    },
    {
      label: "Subjects",
      icon: GraduationCap,
    },
    {
      label: "Students",
      icon: Users,
    },
    {
      label: "Staff",
      icon: Users,
    },
    {
      label: "Examinations",
      icon: CalendarDays,
    },
    {
      label: "Timetable",
      icon: CalendarDays,
    },
    {
      label: "Registrations",
      icon: ClipboardList,
    },
    {
      label: "Halls",
      icon: MapPinned,
    },
    {
      label: "Allocations",
      icon: ClipboardList,
    },
{
  label: "Hall Tickets",
  icon: ClipboardList,
  route: "HallTickets",
},
{
  label: "Reports",
  icon: BarChart3,
  route: "Reports",
},
  ];

const handleNavigation = (item) => {

  if (onNavigate) {
    onNavigate(item.route || item.label);
  }

  if (setSidebarOpen) {
    setSidebarOpen(false);
  }
};

  return (
    <>
      {/* ================================================= */}
      {/* MOBILE OVERLAY */}
      {/* ================================================= */}

      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/30 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}


      {/* ================================================= */}
      {/* SIDEBAR */}
      {/* ================================================= */}

      <aside
        className={`
          fixed inset-y-0 left-0 z-50
          flex w-72 flex-col
          bg-sidebar
          text-white
          shadow-xl
          transition-transform duration-300
          lg:translate-x-0
          ${sidebarOpen
            ? "translate-x-0"
            : "-translate-x-full"
          }
        `}
      >

        {/* ================================================= */}
        {/* LOGO */}
        {/* ================================================= */}

        <div className="flex h-20 items-center justify-between border-b border-white/10 px-6">

          <div className="flex items-center gap-3">

            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-white">
              <span className="text-lg font-black text-sidebar">
                EN
              </span>
            </div>

            <div>
              <p className="text-lg font-bold tracking-wide">
                ExamNexus
              </p>

              <p className="text-xs text-accent-light">
                Administration
              </p>
            </div>

          </div>


          {/* Mobile close */}

          <button
            type="button"
            onClick={() => setSidebarOpen(false)}
            className="rounded-lg p-2 text-accent-light transition hover:bg-white/10 hover:text-white lg:hidden"
            aria-label="Close sidebar"
          >
            <X size={21} />
          </button>

        </div>


        {/* ================================================= */}
        {/* NAVIGATION */}
        {/* ================================================= */}

        <nav className="flex-1 overflow-y-auto px-4 py-6">

          <p className="mb-3 px-3 text-[11px] font-semibold uppercase tracking-[0.18em] text-accent-light">
            Main Menu
          </p>


          <div className="space-y-1">

            {navigation.map((item) => {

              const Icon = item.icon;

              const isActive =
                activePage === item.label;


              return (
                <button
                  key={item.label}
                  type="button"
                  onClick={() =>
  handleNavigation(item)
}
                  className={`
                    group flex w-full items-center gap-3
                    rounded-xl px-3 py-3
                    text-left text-sm font-medium
                    transition
                    ${isActive
                      ? "bg-white text-sidebar shadow-sm"
                      : "text-accent-light hover:bg-white/10 hover:text-white"
                    }
                  `}
                >

                  <Icon
                    size={19}
                    className={`
                      shrink-0
                      ${isActive
                        ? "text-primary"
                        : "text-accent-light group-hover:text-white"
                      }
                    `}
                  />

                  <span>
                    {item.label}
                  </span>

                </button>
              );

            })}

          </div>

        </nav>


        {/* ================================================= */}
        {/* USER / LOGOUT */}
        {/* ================================================= */}

        <div className="border-t border-white/10 p-4">

          <div className="mb-3 flex items-center gap-3 rounded-xl bg-white/5 p-3">

            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-accent font-bold text-white">
              {(user?.name || "A")
                .charAt(0)
                .toUpperCase()}
            </div>


            <div className="min-w-0">

              <p className="truncate text-sm font-semibold text-white">
                {user?.name || "Administrator"}
              </p>

              <p className="truncate text-xs text-accent-light">
                {user?.email || "Administrator"}
              </p>

            </div>

          </div>


          <button
            type="button"
            onClick={onLogout}
            className="flex w-full items-center gap-3 rounded-xl px-3 py-3 text-sm font-medium text-accent-light transition hover:bg-white/10 hover:text-white"
          >

            <LogOut size={19} />

            <span>
              Logout
            </span>

          </button>

        </div>

      </aside>
    </>
  );
}


export default AdminSidebar;
