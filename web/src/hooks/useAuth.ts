import { useQuery } from '@tanstack/react-query';

import { me } from '../api/auth';

export const useAuth = () =>
  useQuery({
    queryKey: ['auth', 'me'],
    queryFn: me,
    retry: false,
  });
