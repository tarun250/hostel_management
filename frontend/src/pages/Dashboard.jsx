import { money, when } from '../api.js';
import { useResources } from '../hooks.js';
import { Card, Empty, ErrorBox, Loading, PageHeader, Pill } from '../components/ui.jsx';

function Kpi({ label, value, hint, tone = 'navy', href }) {
  const body = (
    <>
      <span className="kpi-label">{label}</span>
      <span className="kpi-value">{value}</span>
      {hint && <span className="kpi-hint">{hint}</span>}
    </>
  );
  return href ? (
    <a className={`kpi kpi-${tone}`} href={href}>
      {body}
    </a>
  ) : (
    <div className={`kpi kpi-${tone}`}>{body}</div>
  );
}

export default function Dashboard() {
  const { data, loading, error, reload } = useResources({
    summary: '/stats/summary',
    rooms: '/rooms',
    maintenance: '/maintenance?status=OPEN',
    complaints: '/complaints?status=OPEN',
  });

  if (loading && !data) return <Loading label="Loading overview" />;
  if (error) return <ErrorBox message={error} onRetry={reload} />;

  const { summary: s, rooms, maintenance, complaints } = data;
  const blocks = rooms.reduce((acc, r) => {
    acc[r.block] = acc[r.block] || { beds: 0, used: 0 };
    acc[r.block].beds += r.capacity;
    acc[r.block].used += r.occupied;
    return acc;
  }, {});

  return (
    <>
      <PageHeader title="Hostel dashboard" subtitle="Live snapshot of occupancy, dues and open issues.">
        <button className="btn btn-ghost" onClick={reload} disabled={loading}>
          {loading ? 'Refreshing...' : 'Refresh'}
        </button>
      </PageHeader>

      <div className="occupancy-hero card">
        <div>
          <span className="kpi-label">Bed occupancy</span>
          <div className="hero-figure">{s.occupancy_pct}%</div>
          <span className="muted">
            {s.occupied_beds} of {s.total_beds} beds filled across {s.rooms} rooms
          </span>
        </div>
        <div className="meter" aria-label={`${s.occupancy_pct}% occupied`}>
          <div className="meter-fill" style={{ width: `${Math.min(s.occupancy_pct, 100)}%` }} />
        </div>
      </div>

      <div className="kpi-grid">
        <Kpi label="Students registered" value={s.students} hint={`${s.unallocated_students} without a room`} href="#/students" />
        <Kpi label="Rooms with vacancy" value={s.available_rooms} hint={`${s.total_beds - s.occupied_beds} free beds`} tone="teal" href="#/rooms" />
        <Kpi label="Pending fees" value={money(s.pending_fees_amount)} hint={`${s.pending_fees_count} invoices, ${s.overdue_fees_count} overdue`} tone="amber" href="#/fees" />
        <Kpi label="Open complaints" value={s.open_complaints} tone="rose" href="#/complaints" />
        <Kpi label="Open maintenance" value={s.open_maintenance} tone="rose" href="#/maintenance" />
        <Kpi label="Visitors inside" value={s.visitors_inside} tone="teal" href="#/visitors" />
      </div>

      <div className="two-col">
        <Card title="Occupancy by block">
          {Object.keys(blocks).length === 0 ? (
            <Empty>No rooms yet. Add rooms from the Rooms page.</Empty>
          ) : (
            <ul className="block-list">
              {Object.entries(blocks).map(([block, b]) => {
                const pct = b.beds ? Math.round((b.used * 100) / b.beds) : 0;
                return (
                  <li key={block}>
                    <span className="block-name">Block {block}</span>
                    <div className="meter meter-sm">
                      <div className="meter-fill" style={{ width: `${pct}%` }} />
                    </div>
                    <span className="block-num">
                      {b.used}/{b.beds}
                    </span>
                  </li>
                );
              })}
            </ul>
          )}
        </Card>

        <Card title="Needs attention">
          {maintenance.length + complaints.length === 0 ? (
            <Empty>Nothing open. All quiet in the hostel.</Empty>
          ) : (
            <ul className="feed">
              {maintenance.slice(0, 4).map((m) => (
                <li key={`m${m.id}`}>
                  <Pill value={m.priority} />
                  <div>
                    <strong>{m.title}</strong>
                    <small className="muted">
                      Room {m.room_number} · {when(m.reported_at)}
                    </small>
                  </div>
                </li>
              ))}
              {complaints.slice(0, 4).map((c) => (
                <li key={`c${c.id}`}>
                  <Pill value="OPEN" label={c.category} />
                  <div>
                    <strong>{c.subject}</strong>
                    <small className="muted">
                      {c.student_name} · {when(c.filed_at)}
                    </small>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </Card>
      </div>
    </>
  );
}
