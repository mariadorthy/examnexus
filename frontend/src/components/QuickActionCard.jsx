function QuickActionCard({
  title,
  description,
  icon: Icon,
  onClick,
  variant = "light",
}) {

  const isDark = variant === "dark";

  return (
    <button
      type="button"
      onClick={onClick}
      className={`
        group
        w-full
        rounded-2xl
        p-6
        text-left
        transition
        ${
          isDark
            ? "bg-sidebar text-white shadow-lg shadow-sidebar/10 hover:bg-primary"
            : "border border-border bg-surface text-text shadow-sm hover:border-accent hover:shadow-md"
        }
      `}
    >

      {/* ================================================= */}
      {/* TOP */}
      {/* ================================================= */}

      <div className="mb-5 flex items-center justify-between">

        {/* Icon */}

        <div
          className={`
            flex h-11 w-11 items-center justify-center rounded-xl
            ${
              isDark
                ? "bg-white/10 text-white"
                : "bg-accent-light text-primary"
            }
          `}
        >
          {Icon && <Icon size={22} />}
        </div>


        {/* Arrow */}

        <svg
          width="20"
          height="20"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          className={`
            transition
            group-hover:translate-x-1
            ${
              isDark
                ? "text-white"
                : "text-accent"
            }
          `}
        >
          <path d="M5 12h14" />
          <path d="m12 5 7 7-7 7" />
        </svg>

      </div>


      {/* ================================================= */}
      {/* CONTENT */}
      {/* ================================================= */}

      <h4
        className={`
          font-semibold
          ${
            isDark
              ? "text-white"
              : "text-text"
          }
        `}
      >
        {title}
      </h4>


      <p
        className={`
          mt-1 text-sm leading-6
          ${
            isDark
              ? "text-accent-light"
              : "text-text-muted"
          }
        `}
      >
        {description}
      </p>

    </button>
  );
}


export default QuickActionCard;
