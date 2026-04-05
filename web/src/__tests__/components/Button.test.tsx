import { render, screen } from '@testing-library/react';

import { Button } from '../../components/ui/Button';

describe('Button', () => {
  it('renders label', () => {
    render(<Button>Salvar</Button>);
    expect(screen.getByRole('button', { name: 'Salvar' })).toBeInTheDocument();
  });
});
