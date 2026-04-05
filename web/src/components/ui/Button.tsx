import type { ButtonHTMLAttributes, FC } from 'react';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'ghost';
}

export const Button: FC<ButtonProps> = ({ variant = 'primary', className = '', ...props }) => {
  const variantClass =
    variant === 'primary'
      ? 'bg-brand-500 text-white hover:bg-brand-700'
      : 'bg-white text-brand-700 border border-brand-500 hover:bg-brand-50';

  return <button className={`rounded-md px-4 py-2 text-sm font-semibold transition ${variantClass} ${className}`} {...props} />;
};
