function StatCard({
  title,
  value,
  description,
  icon: Icon,
  loading = false,
}) {

  return (
    <div
      className="
        rounded-2xl
        border border-border
        bg-surface
        p-5
        shadow-sm
        transition
        hover:-translate-y-0.5
        hover:shadow-md
      "
    >

      <div className="flex items-start justify-between">

        {/* ================================================= */}
        {/* VALUE */}
        {/* ================================================= */}

        <div>

          <p className="text-sm font-medium text-text-muted">
            {title}
          </p>

          <p className="mt-2 text-3xl font-bold text-text">
            {loading ? "..." : value}
          </p>

        </div>


        {/* ================================================= */}
        {/* ICON */}
        {/* ================================================= */}

        <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-accent-light text-primary">
          {Icon && <Icon size={21} />}
        </div>

      </div>


      {/* ================================================= */}
      {/* DESCRIPTION */}
      {/* ================================================= */}

      <p className="mt-4 text-xs text-text-muted">
        {description}
      </p>

    </div>
  );
}


export default StatCard;
