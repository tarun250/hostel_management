import { useState } from 'react';
import { api } from '../api.js';
import { useAction, useResources } from '../hooks.js';
import { Card, Empty, ErrorBox, Field, Flash, Loading, PageHeader } from '../components/ui.jsx';

const BLANK = { roll_no: '', full_name: '', email: '', phone: '', course: '', year: 1, guardian_phone: '' };

export default function Students() {
  const [search, setSearch] = useState('');
  const query = search ? `/students?search=${encodeURIComponent(search)}` : '/students';
  const { data, loading, error, reload } = useResources({ students: query });
  const { busy, flash, setFlash, run } = useAction(reload);
  const [form, setForm] = useState(BLANK);

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  const submit = async (e) => {
    e.preventDefault();
    const body = { ...form, year: Number(form.year), phone: form.phone || null, guardian_phone: form.guardian_phone || null };
    if (await run(() => api.post('/students', body), `Registered ${form.full_name}`)) setForm(BLANK);
  };

  const remove = (s) => {
    if (!window.confirm(`Remove ${s.full_name} (${s.roll_no})? Their fees, complaints and visitor log go too.`)) return;
    run(() => api.del(`/students/${s.id}`), `Removed ${s.full_name}`);
  };

  return (
    <>
      <PageHeader title="Students" subtitle="Register residents and see where they stay." />
      <Flash flash={flash} onClose={() => setFlash(null)} />

      <Card title="Register a student">
        <form className="form-grid" onSubmit={submit}>
          <Field label="Roll number">
            <input value={form.roll_no} onChange={set('roll_no')} placeholder="24BCS10133" required />
          </Field>
          <Field label="Full name">
            <input value={form.full_name} onChange={set('full_name')} required />
          </Field>
          <Field label="Email">
            <input type="email" value={form.email} onChange={set('email')} required />
          </Field>
          <Field label="Phone">
            <input value={form.phone} onChange={set('phone')} />
          </Field>
          <Field label="Course">
            <input value={form.course} onChange={set('course')} placeholder="B.Tech CSE" required />
          </Field>
          <Field label="Year">
            <select value={form.year} onChange={set('year')}>
              {[1, 2, 3, 4, 5].map((y) => (
                <option key={y}>{y}</option>
              ))}
            </select>
          </Field>
          <Field label="Guardian phone">
            <input value={form.guardian_phone} onChange={set('guardian_phone')} />
          </Field>
          <div className="form-actions">
            <button className="btn btn-primary" disabled={busy}>
              {busy ? 'Saving...' : 'Register'}
            </button>
          </div>
        </form>
      </Card>

      <Card
        title="Residents"
        aside={
          <input
            className="search"
            placeholder="Search name or roll no"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        }
      >
        {loading && !data ? (
          <Loading />
        ) : error ? (
          <ErrorBox message={error} onRetry={reload} />
        ) : data.students.length === 0 ? (
          <Empty>{search ? 'No match for that search.' : 'No students registered yet.'}</Empty>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Roll no</th>
                  <th>Name</th>
                  <th>Course</th>
                  <th>Year</th>
                  <th>Contact</th>
                  <th>Room</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {data.students.map((s) => (
                  <tr key={s.id}>
                    <td className="mono">{s.roll_no}</td>
                    <td>{s.full_name}</td>
                    <td>{s.course}</td>
                    <td>{s.year}</td>
                    <td>
                      <div>{s.email}</div>
                      <small className="muted">{s.phone || ''}</small>
                    </td>
                    <td>{s.room_number ? <span className="room-tag">{s.room_number}</span> : <span className="muted">Not allotted</span>}</td>
                    <td className="row-actions">
                      <button className="btn btn-danger-ghost" onClick={() => remove(s)} disabled={busy}>
                        Remove
                      </button>
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
