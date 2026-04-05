import type { FC, PropsWithChildren } from 'react';

interface CardProps extends PropsWithChildren {
  title?: string;
}

export const Card: FC<CardProps> = ({ title, children }) => (
  <section className="rounded-xl bg-white/90 p-4 shadow-sm ring-1 ring-slate-200">
    {title ? <h2 className="mb-3 text-lg font-bold text-slate-800">{title}</h2> : null}
    {children}
  </section>
);
