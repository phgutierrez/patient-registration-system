import { apiClient } from './client';
import type { Patient } from '../types/patient';

export const listPatients = async (): Promise<Patient[]> => {
  const { data } = await apiClient.get<Patient[]>('/patients');
  return data;
};

export const createPatient = async (payload: Omit<Patient, 'id'>): Promise<Patient> => {
  const { data } = await apiClient.post<Patient>('/patients', payload);
  return data;
};
