import { apiClient } from './client';
import type { SurgeryRequest, SurgerySchedulePreview } from '../types/surgery';

export const listSurgeries = async (): Promise<SurgeryRequest[]> => {
  const { data } = await apiClient.get<SurgeryRequest[]>('/surgery');
  return data;
};

export const createSurgery = async (payload: Record<string, unknown>): Promise<SurgeryRequest> => {
  const { data } = await apiClient.post<SurgeryRequest>('/surgery', payload);
  return data;
};

export const getSurgerySchedulePreview = async (
  surgeryId: number,
): Promise<{ ok: boolean; preview: SurgerySchedulePreview; already_scheduled: boolean }> => {
  const { data } = await apiClient.get<{ ok: boolean; preview: SurgerySchedulePreview; already_scheduled: boolean }>(
    `/surgery/${surgeryId}/schedule/preview`,
  );
  return data;
};

export const confirmSurgerySchedule = async (
  surgeryId: number,
): Promise<{ ok: boolean; message: string; scheduled_at: string }> => {
  const { data } = await apiClient.post<{ ok: boolean; message: string; scheduled_at: string }>(
    `/surgery/${surgeryId}/schedule/confirm`,
  );
  return data;
};

export const getSurgeryPdfUrl = (surgeryId: number): string => `/api/surgery/${surgeryId}/pdf`;

export const getSurgeryHemocomponentePdfUrl = (surgeryId: number): string =>
  `/api/surgery/${surgeryId}/pdf-hemocomponente`;
