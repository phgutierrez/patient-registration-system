import type { FC, PropsWithChildren } from 'react';
import { Link } from 'react-router-dom';

const links = [
  { to: '/', label: 'Dashboard' },
  { to: '/patients', label: 'Pacientes' },
  { to: '/surgery', label: 'Cirurgias' },
  { to: '/calendar', label: 'Calendário' },
];

export const MainLayout: FC<PropsWithChildren> = ({ children }) => (
  <div className="mx-auto max-w-6xl p-4 md:p-6">
    <header className="mb-6 rounded-xl bg-white/90 p-4 shadow-sm ring-1 ring-slate-200">
      <h1 className="text-xl font-bold text-brand-700">Patient Registration System</h1>
      <nav className="mt-2 flex flex-wrap gap-2">
        {links.map((item) => (
          <Link className="rounded bg-brand-50 px-3 py-1 text-sm font-medium text-brand-700" key={item.to} to={item.to}>
            {item.label}
          </Link>
        ))}
      </nav>
    </header>
    <main className="space-y-4">{children}</main>
  </div>
);
