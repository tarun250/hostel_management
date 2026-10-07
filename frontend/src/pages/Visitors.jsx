import { useState } from 'react';
import { api, when } from '../api.js';
import { useAction, useResources } from '../hooks.js';
import { Card, Empty, ErrorBox, Field, Flash, Loading, PageHeader, Pill, StudentSelect } from '../components/ui.jsx';

const BLANK = { student_id: '', visitor_name: '', relation: '', phone: '', purpose: '' };

export default function Visitors() {
  const [insideOnly, setInsideOnly] = useState(false);
  const { data, loading, error, reload } = useResources({
    visitors: insideOnly ? '/visitors?inside=true' : '/visitors',
    students: '/students',
  });
  const { busy, flash, setFlash, run } = useAction(reload);
  const [form, setForm] = useState(BLANK);
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  const submit = async (e) => {
    e.preventDefault();
    const body = { ...form, student_id: Number(form.student_id), phone: form.phone || null, purpose: form.purpose || null };
    if (await run(() => api.post('/visitors', body), `${form.visitor_name} checked in`)) setForm(BLANK);
  };

  const checkout = (v) => run(() => api.post(`/visitors/${v.id}/checkout`), `${v.visitor_name} checked out`);

  return (
    <>
      <PageHeader title="Visitor log" subtitle="Gate register for guests meeting residents.">
        <label className="toggle">
          <input type="checkbox" checked={insideOnly} onChange={(e) => setInsideOnly(e.target.checked)} />
          Only visitors still inside
        </label>
      </PageHeader>
      <Flash flash={flash} onClose={() => setFlash(null)} />

      <Card title="Check in a visitor">
        <form className="form-grid" onSubmit={submit}>
          <Field label="Visiting student">
            <StudentSelect students={data?.students || []} value={form.student_id} onChange={(v) => setForm({ ...form, student_id: v })} />
          </Field>
          <Field label="Visitor name">
            <input value={form.visitor_name} onChange={set('visitor_name')} required />
          </Field>
          <Field label="Relation">
            <input value={form.relation} onChange={set('relation')} placeholder="Mother, friend..." required />
          </Field>
          <Field label="Phone">
            <input value={form.phone} onChange={set('phone')} />
          </Field>
          <Field label="Purpose">
            <input value={form.purpose} onChange={set('purpose')} />
          </Field>
          <div className="form-actions">
            <button className="btn btn-primary" disabled={busy}>
              Check in
            </button>
          </div>
        </form>
      </Card>

      <Card title="Register">
        {loading && !data ? (
          <Loading />
        ) : error ? (
          <ErrorBox message={error} onRetry={reload} />
        ) : data.visitors.length === 0 ? (
          <Empty>{insideOnly ? 'Nobody inside right now.' : 'No visitor entries yet.'}</Empty>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Visitor</th>
                  <th>Meeting</th>
                  <th>Purpose</th>
                  <th>In</th>
                  <th>Out</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {data.visitors.map((v) => (
                  <tr key={v.id}>
                    <td>
                      <div>{v.visitor_name}</div>
                      <small className="muted">
                        {v.relation}
                        {v.phone ? ` · ${v.phone}` : ''}
                      </small>
                    </td>
                    <td>{v.student_name}</td>
                    <td>{v.purpose || <span className="muted">-</span>}</td>
                    <td>{when(v.check_in)}</td>
                    <td>{v.check_out ? when(v.check_out) : <Pill value="INSIDE" label="inside" />}</td>
                    <td className="row-actions">
                      {!v.check_out && (
                        <button className="btn btn-ghost btn-sm" onClick={() => checkout(v)} disabled={busy}>
                          Check out
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </>
  );
}
