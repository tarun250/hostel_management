import { useState } from 'react';
import { api, money } from '../api.js';
import { useAction, useResources } from '../hooks.js';
import { Card, Empty, ErrorBox, Field, Flash, Loading, PageHeader, StudentSelect } from '../components/ui.jsx';

const BLANK = { number: '', block: 'A', floor: 0, room_type: 'DOUBLE', capacity: 2, monthly_rent: 4500 };
const DEFAULT_CAPACITY = { SINGLE: 1, DOUBLE: 2, TRIPLE: 3, DORM: 6 };

function RoomCard({ room, occupants, unallocated, busy, onAllocate, onVacate, onDelete }) {
  const [pick, setPick] = useState('');
  const beds = Array.from({ length: room.capacity }, (_, i) => i < room.occupied);
  const full = room.vacancies === 0;

  return (
    <article className={`room ${full ? 'room-full' : ''}`}>
      <header>
        <div>
          <h3>{room.number}</h3>
          <small className="muted">
            Block {room.block} · Floor {room.floor} · {room.room_type.toLowerCase()}
          </small>
        </div>
        <span className={`vacancy ${full ? 'none' : ''}`}>{full ? 'Full' : `${room.vacancies} free`}</span>
      </header>
      <div className="beds" aria-label={`${room.occupied} of ${room.capacity} beds used`}>
        {beds.map((used, i) => (
          <span key={i} className={`bed ${used ? 'used' : ''}`} />
        ))}
      </div>
      <ul className="occupants">
        {occupants.map((s) => (
          <li key={s.id}>
            <span>{s.full_name}</span>
            <button className="link" disabled={busy} onClick={() => onVacate(room, s)}>
              vacate
            </button>
          </li>
        ))}
        {occupants.length === 0 && <li className="muted">Empty room</li>}
      </ul>
      {!full && (
        <div className="allocate">
          <StudentSelect students={unallocated} value={pick} onChange={setPick} placeholder="Allocate student..." />
          <button
            className="btn btn-primary btn-sm"
            disabled={!pick || busy}
            onClick={() => onAllocate(room, Number(pick)).then(() => setPick(''))}
          >
            Allocate
          </button>
        </div>
      )}
      <footer>
        <span>{money(room.monthly_rent)}/month</span>
        <button className="link danger" disabled={busy} onClick={() => onDelete(room)}>
          delete room
        </button>
      </footer>
    </article>
  );
}

export default function Rooms() {
  const [onlyAvailable, setOnlyAvailable] = useState(false);
  const { data, loading, error, reload } = useResources({
    rooms: onlyAvailable ? '/rooms/available' : '/rooms',
    students: '/students',
  });
  const { busy, flash, setFlash, run } = useAction(reload);
  const [form, setForm] = useState(BLANK);
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  const submit = async (e) => {
    e.preventDefault();
    const body = { ...form, floor: Number(form.floor), capacity: Number(form.capacity), monthly_rent: Number(form.monthly_rent) };
    if (await run(() => api.post('/rooms', body), `Room ${form.number} added`)) setForm({ ...BLANK, block: form.block });
  };

  const allocate = (room, studentId) =>
    run(() => api.post(`/rooms/${room.id}/allocate`, { student_id: studentId }), `Allocated to ${room.number}`);
  const vacate = (room, s) =>
    run(() => api.post(`/rooms/${room.id}/deallocate`, { student_id: s.id }), `${s.full_name} vacated ${room.number}`);
  const remove = (room) =>
    window.confirm(`Delete room ${room.number}?`) && run(() => api.del(`/rooms/${room.id}`), `Room ${room.number} deleted`);

  return (
    <>
      <PageHeader title="Rooms" subtitle="Availability, allocation and vacating.">
        <label className="toggle">
          <input type="checkbox" checked={onlyAvailable} onChange={(e) => setOnlyAvailable(e.target.checked)} />
          Only rooms with vacancy
        </label>
      </PageHeader>
      <Flash flash={flash} onClose={() => setFlash(null)} />

      <Card title="Add a room">
        <form className="form-grid" onSubmit={submit}>
          <Field label="Room number">
            <input value={form.number} onChange={set('number')} placeholder="A-101" required />
          </Field>
          <Field label="Block">
            <input value={form.block} onChange={set('block')} required />
          </Field>
          <Field label="Floor">
            <input type="number" min="0" value={form.floor} onChange={set('floor')} />
          </Field>
          <Field label="Type">
            <select
              value={form.room_type}
              onChange={(e) => setForm({ ...form, room_type: e.target.value, capacity: DEFAULT_CAPACITY[e.target.value] })}
            >
              {Object.keys(DEFAULT_CAPACITY).map((t) => (
                <option key={t}>{t}</option>
              ))}
            </select>
          </Field>
          <Field label="Beds">
            <input type="number" min="1" max="12" value={form.capacity} onChange={set('capacity')} />
          </Field>
          <Field label="Rent / month (INR)">
            <input type="number" min="0" value={form.monthly_rent} onChange={set('monthly_rent')} />
          </Field>
          <div className="form-actions">
            <button className="btn btn-primary" disabled={busy}>
              Add room
            </button>
          </div>
        </form>
      </Card>

      {loading && !data ? (
        <Loading label="Loading rooms" />
      ) : error ? (
        <ErrorBox message={error} onRetry={reload} />
      ) : data.rooms.length === 0 ? (
        <Empty>{onlyAvailable ? 'Every room is full.' : 'No rooms yet. Add the first one above.'}</Empty>
      ) : (
        <div className="room-grid">
          {data.rooms.map((room) => (
            <RoomCard
              key={room.id}
              room={room}
              occupants={data.students.filter((s) => s.room_id === room.id)}
              unallocated={data.students.filter((s) => s.room_id === null)}
              busy={busy}
              onAllocate={allocate}
              onVacate={vacate}
              onDelete={remove}
            />
          ))}
        </div>
      )}
    </>
  );
}
