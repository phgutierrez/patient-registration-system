import type { FC, InputHTMLAttributes } from 'react';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
}

export const Input: FC<InputProps> = ({ label, className = '', ...props }) => (
  <label className="flex flex-col gap-1 text-sm font-medium text-slate-700">
    {label}
    <input className={`rounded-md border border-slate-300 px-3 py-2 focus:border-brand-500 focus:outline-none ${className}`} {...props} />
  </label>
);
