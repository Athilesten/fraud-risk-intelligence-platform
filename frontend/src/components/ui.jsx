export function Navbar() {
  const links = [
    ["Overview", "#overview"],
    ["Predict", "#predict"],
    ["Batch", "#batch"],
    ["Logs", "#logs"],
    ["Monitoring", "#monitoring"],
    ["Big Data", "#big-data"],
    ["Architecture", "#architecture"],
  ];

  return (
    <header className="navbar">
      <a className="brand" href="#overview" aria-label="Fraud Risk Intelligence home">
        <span className="brand-mark">FR</span>
        <span>
          <strong>Fraud Risk Intelligence</strong>
          <small>Risk decisioning platform</small>
        </span>
      </a>

      <nav className="nav-links" aria-label="Primary navigation">
        {links.map(([label, href]) => (
          <a href={href} key={href}>
            {label}
          </a>
        ))}
      </nav>
    </header>
  );
}

export function SectionHeader({ eyebrow, title, description }) {
  return (
    <div className="section-header">
      {eyebrow && <p className="eyebrow">{eyebrow}</p>}
      <h2>{title}</h2>
      {description && <p>{description}</p>}
    </div>
  );
}

export function StatusCard({ health, onRefresh }) {
  const isHealthy = health === "healthy";

  return (
    <aside className="status-card">
      <div>
        <span className="status-label">System Status</span>
        <strong className={isHealthy ? "status-healthy" : "status-down"}>
          {health === "checking" ? "Checking API" : isHealthy ? "Operational" : "Backend unavailable"}
        </strong>
      </div>

      <div className="status-list">
        <span>FastAPI scoring service</span>
        <span>PostgreSQL audit logging</span>
        <span>Prometheus metrics endpoint</span>
      </div>

      <button className="button secondary small" onClick={onRefresh}>
        Refresh
      </button>
    </aside>
  );
}

export function MetricCard({ label, value, tone = "default" }) {
  return (
    <div className={`metric-card tone-${tone}`}>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

export function ErrorBanner({ message }) {
  if (!message) return null;

  return <div className="error-banner">{message}</div>;
}

export function LoadingState({ label = "Loading" }) {
  return <div className="loading-state">{label}...</div>;
}

export function DataTable({ columns, rows, emptyMessage = "No records available." }) {
  if (!rows?.length) {
    return <p className="empty-state">{emptyMessage}</p>;
  }

  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            {columns.map((column) => (
              <th key={column.key}>{column.label}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, rowIndex) => (
            <tr key={row.id || rowIndex}>
              {columns.map((column) => (
                <td key={column.key}>{column.render ? column.render(row) : row[column.key]}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
