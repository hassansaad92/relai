import { NavLink } from 'react-router-dom';

const links = [
  { to: '/', label: 'Overview' },
  { to: '/mechanics', label: 'Mechanics' },
  { to: '/projects', label: 'Projects' },
  { to: '/skills', label: 'Skills' },
  { to: '/gantt', label: 'Gantt' },
];

export default function Sidebar() {
  return (
    <div className="sidebar">
      <div className="sidebar-title">Scheduling</div>
      {links.map(({ to, label }) => (
        <NavLink
          key={to}
          to={to}
          end={to === '/'}
          className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}
        >
          {label}
        </NavLink>
      ))}
    </div>
  );
}
