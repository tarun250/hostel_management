import { useEffect, useState } from 'react';
import Dashboard from './pages/Dashboard.jsx';
import Students from './pages/Students.jsx';
import Rooms from './pages/Rooms.jsx';
import Maintenance from './pages/Maintenance.jsx';
import Complaints from './pages/Complaints.jsx';
import Visitors from './pages/Visitors.jsx';
import Fees from './pages/Fees.jsx';

const SECTIONS = [
  { id: 'dashboard', label: 'Overview', icon: '◧', Page: Dashboard },
  { id: 'students', label: 'Students', icon: '☺', Page: Students },
  { id: 'rooms', label: 'Rooms', icon: '▦', Page: Rooms },
  { id: 'maintenance', label: 'Maintenance', icon: '⚒', Page: Maintenance },
  { id: 'complaints', label: 'Complaints', icon: '✎', Page: Complaints },
  { id: 'visitors', label: 'Visitor Log', icon: '⇄', Page: Visitors },
  { id: 'fees', label: 'Fees', icon: '₹', Page: Fees },
];

function currentSection() {
  const id = window.location.hash.replace('#/', '');
  return SECTIONS.find((s) => s.id === id) || SECTIONS[0];
}

export default function App() {
  const [section, setSection] = useState(currentSection);
  const [apiUp, setApiUp] = useState(null);

  useEffect(() => {
    const onHash = () => setSection(currentSection());
    window.addEventListener('hashchange', onHash);
    return () => window.removeEventListener('hashchange', onHash);
  }, []);

  useEffect(() => {
    const check = () =>
      fetch('/api/stats/summary')
        .then((r) => setApiUp(r.ok))
        .catch(() => setApiUp(false));
    check();
    const t = setInterval(check, 30000);
    return () => clearInterval(t);
  }, []);

  const { Page } = section;

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-mark">H</span>
          <div>
            <strong>HostelHub</strong>
            <small>Warden console</small>
          </div>
        </div>
        <nav>
          {SECTIONS.map((s) => (
            <a key={s.id} href={`#/${s.id}`} className={s.id === section.id ? 'active' : ''}>
              <span className="nav-icon" aria-hidden="true">
                {s.icon}
              </span>
              {s.label}
            </a>
          ))}
        </nav>
        <div className={`api-status ${apiUp ? 'up' : apiUp === false ? 'down' : ''}`}>
          <span className="dot" /> API {apiUp === null ? 'checking' : apiUp ? 'online' : 'offline'}
        </div>
      </aside>
      <main className="content">
        <Page key={section.id} />
      </main>
    </div>
  );
}
