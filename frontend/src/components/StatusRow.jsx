function StatusRow({
  label,
  status,
}) {

  const normalizedStatus =
    String(status || "").toLowerCase();


  const getStatusStyles = () => {

    switch (normalizedStatus) {

      case "ready":
      case "active":
      case "completed":
        return {
          dot: "bg-success",
          badge: "bg-accent-light text-success",
        };


      case "pending":
      case "scheduled":
        return {
          dot: "bg-warning",
          badge: "bg-warning/10 text-warning",
        };


      case "inactive":
      case "disabled":
      case "not ready":
      case "failed":
        return {
          dot: "bg-danger",
          badge: "bg-danger/10 text-danger",
        };


      default:
        return {
          dot: "bg-accent",
          badge: "bg-accent-light text-primary",
        };
    }
  };


  const styles = getStatusStyles();


  return (
    <div className="flex items-center justify-between gap-4">

      {/* ================================================= */}
      {/* LABEL */}
      {/* ================================================= */}

      <div className="flex min-w-0 items-center gap-3">

        <div
          className={`
            h-2.5 w-2.5
            shrink-0
            rounded-full
            ${styles.dot}
          `}
        />

        <span className="truncate text-sm font-medium text-sidebar">
          {label}
        </span>

      </div>


      {/* ================================================= */}
      {/* STATUS */}
      {/* ================================================= */}

      <span
        className={`
          shrink-0
          rounded-full
          px-3
          py-1
          text-xs
          font-semibold
          ${styles.badge}
        `}
      >
        {status}

      </span>

    </div>
  );
}


export default StatusRow;
