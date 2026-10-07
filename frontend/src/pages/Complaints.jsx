import { useState } from 'react';
import { api, when } from '../api.js';
import { useAction, useResources } from '../hooks.js';
import { Card, Empty, ErrorBox, Field, Flash, Loading, PageHeader, Pill, StudentSelect } from '../components/ui.jsx';

const CATEGORIES = ['MESS', 'NOISE', 'CLEANLINESS', 'SECURITY', 'ROOMMATE', 'OTHER'];
const STATUSES = ['OPEN', 'IN_REVIEW', 'CLOSED'];
const BLANK = { student_id: '', subject: '', category: 'OTHER', details: '' };

export default function Complaints() {
  const { data, loading, error, reload } = useResources({ complaints: '/complaints', students: '/students' });
  const { busy, flash, setFlash, run } = useAction(reload);
  const [form, setForm] = useState(BLANK);
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  const submit = async (e) => {
    e.preventDefault();
    const body = { ...form, student_id: Number(form.student_id), details: form.details || null };
    if (await run(() => api.post('/complaints', body), 'Complaint filed')) setForm(BLANK);
  };

  const setStatus = (c, status) => run(() => api.put(`/complaints/${c.id}`, { status }), `Complaint #${c.id} updated`);
  const remove = (c) =>
    window.confirm(`Delete complaint #${c.id}?`) && run(() => api.del(`/complaints/${c.id}`), `Complaint #${c.id} deleted`);

  const columns = STATUSES.map((s) => ({ status: s, items: (data?.complaints || []).filter((c) => c.status === s) }));

  return (
    <>
      <PageHeader title="Complaints" subtitle="Student grievances, from filing to closure." />
      <Flash flash={flash} onClose={() => setFlash(null)} />

      <Card title="File a complaint">
        <form className="form-grid" onSubmit={submit}>
          <Field label="Student">
            <StudentSelect students={data?.students || []} value={form.student_id} onChange={(v) => setForm({ ...form, student_id: v })} />
          </Field>
          <Field label="Subject">
            <input value={form.subject} onChange={set('subject')} placeholder="Water cooler on 2nd floor broken" required />
          </Field>
          <Field label="Category">
            <select value={form.category} onChange={set('category')}>
              {CATEGORIES.map((c) => (
                <option key={c}>{c}</option>
              ))}
            </select>
          </Field>
          <Field label="Details" wide>
            <textarea rows="2" value={form.details} onChange={set('details')} />
          </Field>
          <div className="form-actions">
            <button className="btn btn-primary" disabled={busy}>
              File complaint
            </button>
          </div>
        </form>
      </Card>

      {loading && !data ? (
        <Loading />
      ) : error ? (
        <ErrorBox message={error} onRetry={reload} />
      ) : data.complaints.length === 0 ? (
        <Empty>No complaints filed. Good sign.</Empty>
      ) : (
        <div className="lanes">
          {columns.map((col) => (
            <section key={col.status} className="lane">
              <h2>
                <Pill value={col.status} /> <span className="muted">{col.items.length}</span>
              </h2>
              {col.items.map((c) => (
                <article key={c.id} className="note">
                  <span className="note-cat">{c.category}</span>
                  <strong>{c.subject}</strong>
                  {c.details && <p>{c.details}</p>}
                  <small className="muted">
                    {c.student_name} · {when(c.filed_at)}
                  </small>
                  <div className="note-actions">
                    {STATUSES.filter((s) => s !== c.status).map((s) => (
                      <button key={s} className="btn btn-ghost btn-sm" disabled={busy} onClick={() => setStatus(c, s)}>
                        {s === 'CLOSED' ? 'Close' : s === 'OPEN' ? 'Reopen' : 'Review'}
                      </button>
                    ))}
                    <button className="link danger" disabled={busy} onClick={() => remove(c)}>
                      delete
                    </button>
                  </div>
                </article>
              ))}
            </section>
          ))}
        </div>
      )}
    </>
  );
}
