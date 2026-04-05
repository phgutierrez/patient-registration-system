import { apiClient } from './client';

export interface CalendarEvent {
  uid: string;
  title: string;
  date: string;
}

export const listCalendarEvents = async (): Promise<CalendarEvent[]> => {
  const { data } = await apiClient.get<CalendarEvent[]>('/calendar/events');
  return data;
};
