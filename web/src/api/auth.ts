import { apiClient } from './client';

export interface LoginPayload {
  username: string;
  password: string;
}

export interface AuthMe {
  id: number;
  username: string;
  full_name: string;
  role: 'admin' | 'medico' | 'enfermeiro';
}

export const login = async (payload: LoginPayload): Promise<{ access_token: string; expires_in: number }> => {
  const { data } = await apiClient.post('/auth/login', payload);
  return data;
};

export const me = async (): Promise<AuthMe> => {
  const { data } = await apiClient.get<AuthMe>('/auth/me');
  return data;
};
