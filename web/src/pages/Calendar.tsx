import { useQuery } from '@tanstack/react-query';

import { listCalendarEvents } from '../api/calendar';
import { Card } from '../components/ui/Card';

const CalendarPage = () => {
  const query = useQuery({ queryKey: ['calendar-events'], queryFn: listCalendarEvents });

  return (
    <Card title="Calendário">
      {query.isLoading ? <p>Carregando...</p> : null}
      <ul className="space-y-2">
        {(query.data ?? []).map((event) => (
          <li className="rounded border border-slate-200 p-2" key={event.uid}>
            <p className="font-semibold">{event.title}</p>
            <p className="text-sm text-slate-600">{event.date}</p>
          </li>
        ))}
      </ul>
    </Card>
  );
};

export default CalendarPage;
