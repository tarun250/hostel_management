export function PageHeader({ title, subtitle, children }) {
  return (
    <header className="page-head">
      <div>
        <h1>{title}</h1>
        {subtitle && <p className="muted">{subtitle}</p>}
      </div>
      {children && <div className="page-actions">{children}</div>}
    </header>
  );
}

export function Card({ title, children, className = '', aside }) {
  return (
    <section className={`card ${className}`}>
      {(title || aside) && (
        <div className="card-head">
          {title && <h2>{title}</h2>}
          {aside}
        </div>
      )}
      {children}
    </section>
  );
}

export function Loading({ label = 'Loading' }) {
  return (
    <div className="state state-loading" role="status">
      <span className="spinner" aria-hidden="true" /> {label}...
    </div>
  );
}

export function ErrorBox({ message, onRetry }) {
  return (
    <div className="state state-error" role="alert">
      <strong>Could not load data.</strong> {message}
      {onRetry && (
        <button className="btn btn-ghost" onClick={onRetry}>
          Retry
        </button>
      )}
    </div>
  );
}

export function Empty({ children }) {
  return <div className="state state-empty">{children}</div>;
}

export function Flash({ flash, onClose }) {
  if (!flash) return null;
  return (
    <div className={`flash flash-${flash.kind}`} role="status">
      <span>{flash.text}</span>
      <button className="flash-x" onClick={onClose} aria-label="Dismiss">
        x
      </button>
    </div>
  );
}

const TONES = {
  OPEN: 'amber',
  IN_PROGRESS: 'blue',
  IN_REVIEW: 'blue',
  RESOLVED: 'green',
  CLOSED: 'green',
  PAID: 'green',
  PENDING: 'amber',
  OVERDUE: 'red',
  HIGH: 'red',
  MEDIUM: 'amber',
  LOW: 'grey',
  INSIDE: 'blue',
  LEFT: 'grey',
};

export function Pill({ value, label }) {
  return <span className={`pill pill-${TONES[value] || 'grey'}`}>{label || value.replace('_', ' ')}</span>;
}

export function Field({ label, children, wide }) {
  return (
    <label className={`field ${wide ? 'field-wide' : ''}`}>
      <span>{label}</span>
      {children}
    </label>
  );
}

export function StudentSelect({ students, value, onChange, required = true, placeholder = 'Select student' }) {
  return (
    <select value={value} onChange={(e) => onChange(e.target.value)} required={required}>
      <option value="">{placeholder}</option>
      {students.map((s) => (
        <option key={s.id} value={s.id}>
          {s.roll_no} - {s.full_name}
        </option>
      ))}
    </select>
  );
}
