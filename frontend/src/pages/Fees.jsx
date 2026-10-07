import { useState } from 'react';
import { api, day, money } from '../api.js';
import { useAction, useResources } from '../hooks.js';
import { Card, Empty, ErrorBox, Field, Flash, Loading, PageHeader, Pill, StudentSelect } from '../components/ui.jsx';

const BLANK = { student_id: '', term: '2026-SEM2', amount: 27000, due_date: '' };

export default function Fees() {
  const [filter, setFilter] = useState('PENDING');
  const { data, loading, error, reload } = useResources({
    fees: filter ? `/fees?status=${filter}` : '/fees',
    students: '/students',
  });
  const { busy, flash, setFlash, run } = useAction(reload);
  const [form, setForm] = useState(BLANK);
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  const submit = async (e) => {
    e.preventDefault();
    const body = { ...form, student_id: Number(form.student_id), amount: Number(form.amount) };
    if (await run(() => api.post('/fees', body), 'Fee raised')) setForm({ ...BLANK, term: form.term });
  };

  const markPaid = (f) => {
    const ref = window.prompt(`Payment reference for ${f.student_name} (${money(f.amount)})`, '');
    if (ref === null) return;
    run(() => api.put(`/fees/${f.id}/pay`, { payment_ref: ref || null }), `${f.student_name}: ${f.term} marked paid`);
  };

  const total = (data?.fees || []).reduce((sum, f) => sum + Number(f.amount), 0);

  return (
    <>
      <PageHeader title="Fees" subtitle="Hostel fee status per student and term.">
        <div className="segmented">
          {[
            ['PENDING', 'pending'],
            ['PAID', 'paid'],
            ['', 'all'],
          ].map(([v, label]) => (
            <button key={label} className={filter === v ? 'on' : ''} onClick={() => setFilter(v)}>
              {label}
            </button>
          ))}
        </div>
      </PageHeader>
      <Flash flash={flash} onClose={() => setFlash(null)} />

      <Card title="Raise a fee">
        <form className="form-grid" onSubmit={submit}>
          <Field label="Student">
            <StudentSelect students={data?.students || []} value={form.student_id} onChange={(v) => setForm({ ...form, student_id: v })} />
          </Field>
          <Field label="Term">
            <input value={form.term} onChange={set('term')} required />
          </Field>
          <Field label="Amount (INR)">
            <input type="number" min="1" value={form.amount} onChange={set('amount')} required />
          </Field>
          <Field label="Due date">
            <input type="date" value={form.due_date} onChange={set('due_date')} required />
          </Field>
          <div className="form-actions">
            <button className="btn btn-primary" disabled={busy}>
              Raise fee
            </button>
          </div>
        </form>
      </Card>

      <Card title="Ledger" aside={data && <span className="ledger-total">{money(total)}</span>}>
        {loading && !data ? (
          <Loading />
        ) : error ? (
          <ErrorBox message={error} onRetry={reload} />
        ) : data.fees.length === 0 ? (
          <Empty>No fees in this view.</Empty>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Student</th>
                  <th>Term</th>
                  <th className="num">Amount</th>
                  <th>Due</th>
                  <th>Status</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {data.fees.map((f) => (
                  <tr key={f.id} className={f.overdue ? 'row-alert' : ''}>
                    <td>{f.student_name}</td>
                    <td className="mono">{f.term}</td>
                    <td className="num">{money(f.amount)}</td>
                    <td>{day(f.due_date)}</td>
                    <td>
                      {f.overdue ? <Pill value="OVERDUE" /> : <Pill value={f.status} />}
                      {f.status === 'PAID' && (
                        <small className="muted block">
                          {day(f.paid_on)}
                          {f.payment_ref ? ` · ${f.payment_ref}` : ''}
                        </small>
                      )}
                    </td>
                    <td className="row-actions">
                      {f.status === 'PENDING' && (
                        <button className="btn btn-primary btn-sm" onClick={() => markPaid(f)} disabled={busy}>
                          Mark paid
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
