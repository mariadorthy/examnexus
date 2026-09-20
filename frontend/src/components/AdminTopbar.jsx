import { Menu } from "lucide-react";


function AdminTopbar({
  user,
  title,
  section = "Administration",
  onOpenSidebar,
}) {

  const userName =
    user?.name || "Administrator";


  const firstLetter =
    userName.charAt(0).toUpperCase();


  return (
    <header
      className="
        sticky
        top-0
        z-20
        flex
        h-20
        items-center
        justify-between
        border-b
        border-border
        bg-background/95
        px-5
        backdrop-blur
        md:px-8
      "
    >

      {/* ================================================= */}
      {/* LEFT */}
      {/* ================================================= */}

      <div className="flex items-center gap-4">

        {/* Mobile menu */}

        <button
          type="button"
          onClick={onOpenSidebar}
          className="
            rounded-lg
            p-2
            text-sidebar
            transition
            hover:bg-white
            lg:hidden
          "
          aria-label="Open sidebar"
        >
          <Menu size={23} />
        </button>


        {/* Page title */}

        <div>

          <p
            className="
              text-xs
              font-semibold
              uppercase
              tracking-widest
              text-accent
            "
          >
            {section}
          </p>

          <h1
            className="
              text-xl
              font-bold
              text-text
              md:text-2xl
            "
          >
            {title}
          </h1>

        </div>

      </div>


      {/* ================================================= */}
      {/* RIGHT - USER */}
      {/* ================================================= */}

      <div className="flex items-center gap-3">

        {/* User details */}

        <div className="hidden text-right sm:block">

          <p className="text-sm font-semibold text-text">
            {userName}
          </p>

          <p className="text-xs text-text-muted">
            Administrator
          </p>

        </div>


        {/* Avatar */}

        <div
          className="
            flex
            h-10
            w-10
            items-center
            justify-center
            rounded-full
            bg-primary
            font-bold
            text-white
          "
        >
          {firstLetter}
        </div>

      </div>

    </header>
  );
}


export default AdminTopbar;
