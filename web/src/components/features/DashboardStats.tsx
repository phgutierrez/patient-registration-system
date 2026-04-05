import { useQuery } from '@tanstack/react-query';

import { listCalendarEvents } from '../../api/calendar';
import { Card } from '../ui/Card';

export const DashboardStats = () => {
  const events = useQuery({ queryKey: ['calendar-events'], queryFn: listCalendarEvents });

  return (
    <Card title="Agenda em tempo real">
      <p className="text-sm text-slate-600">Eventos no calendário: {events.data?.length ?? 0}</p>
      {events.isFetching ? <p className="text-xs text-slate-500">Atualizando...</p> : null}
    </Card>
  );
};
