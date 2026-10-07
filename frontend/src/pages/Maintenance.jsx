import { useState } from 'react';
import { api, when } from '../api.js';
import { useAction, useResources } from '../hooks.js';
import { Card, Empty, ErrorBox, Field, Flash, Loading, PageHeader, Pill } from '../components/ui.jsx';

const CATEGORIES = ['ELECTRICAL', 'PLUMBING', 'FURNITURE', 'CLEANING', 'INTERNET', 'GENERAL'];
const STATUSES = ['OPEN', 'IN_PROGRESS', 'RESOLVED'];
const BLANK = { room_id: '', title: '', category: 'GENERAL', priority: 'MEDIUM', description: '' };

export default function Maintenance() {
  const [filter, setFilter] = useState('');
  const { data, loading, error, reload } = useResources({
    requests: filter ? `/maintenance?status=${filter}` : '/maintenance',
    rooms: '/rooms',
  });
  const { busy, flash, setFlash, run } = useAction(reload);
  const [form, setForm] = useState(BLANK);
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  const submit = async (e) => {
    e.preventDefault();
    const body = { ...form, room_id: Number(form.room_id), description: form.description || null };
    if (await run(() => api.post('/maintenance', body), 'Request logged')) setForm(BLANK);
  };

  const changeStatus = (req, status) =>
    run(() => api.patch(`/maintenance/${req.id}/status`, { status }), `#${req.id} marked ${status.replace('_', ' ').toLowerCase()}`);
  const remove = (req) =>
    window.confirm(`Delete request #${req.id}?`) && run(() => api.del(`/maintenance/${req.id}`), `#${req.id} deleted`);

  return (
    <>
      <PageHeader title="Maintenance" subtitle="Repairs reported per room, tracked until resolved.">
        <div className="segmented">
          {['', ...STATUSES].map((s) => (
            <button key={s || 'all'} className={filter === s ? 'on' : ''} onClick={() => setFilter(s)}>
              {s ? s.replace('_', ' ').toLowerCase() : 'all'}
            </button>
          ))}
        </div>
      </PageHeader>
      <Flash flash={flash} onClose={() => setFlash(null)} />

      <Card title="Report an issue">
        <form className="form-grid" onSubmit={submit}>
          <Field label="Room">
            <select value={form.room_id} onChange={set('room_id')} required>
              <option value="">Select room</option>
              {(data?.rooms || []).map((r) => (
                <option key={r.id} value={r.id}>
                  {r.number} (Block {r.block})
                </option>
              ))}
            </select>
          </Field>
          <Field label="Issue">
            <input value={form.title} onChange={set('title')} placeholder="Tube light flickering" required />
          </Field>
          <Field label="Category">
            <select value={form.category} onChange={set('category')}>
              {CATEGORIES.map((c) => (
                <option key={c}>{c}</option>
              ))}
            </select>
          </Field>
          <Field label="Priority">
            <select value={form.priority} onChange={set('priority')}>
              {['LOW', 'MEDIUM', 'HIGH'].map((p) => (
                <option key={p}>{p}</option>
              ))}
            </select>
          </Field>
          <Field label="Details" wide>
            <textarea rows="2" value={form.description} onChange={set('description')} />
          </Field>
          <div className="form-actions">
            <button className="btn btn-primary" disabled={busy}>
              Log request
            </button>
          </div>
        </form>
      </Card>

      <Card title="Requests">
        {loading && !data ? (
          <Loading />
        ) : error ? (
          <ErrorBox message={error} onRetry={reload} />
        ) : data.requests.length === 0 ? (
          <Empty>No requests in this view.</Empty>
        ) : (
          <ul className="tickets">
            {data.requests.map((r) => (
              <li key={r.id} className={`ticket status-${r.status.toLowerCase()}`}>
                <div className="ticket-main">
                  <div className="ticket-title">
                    <span className="mono muted">#{r.id}</span> <strong>{r.title}</strong>
                  </div>
                  <small className="muted">
                    Room {r.room_number} · {r.category.toLowerCase()} · reported {when(r.reported_at)}
                  </small>
                  {r.description && <p>{r.description}</p>}
                </div>
                <div className="ticket-side">
                  <Pill value={r.priority} />
                  <select value={r.status} onChange={(e) => changeStatus(r, e.target.value)} disabled={busy}>
                    {STATUSES.map((s) => (
                      <option key={s} value={s}>
                        {s.replace('_', ' ')}
                      </option>
                    ))}
                  </select>
                  <button className="link danger" onClick={() => remove(r)} disabled={busy}>
                    delete
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </Card>
    </>
  );
}
