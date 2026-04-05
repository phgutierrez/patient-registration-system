import { useQuery } from '@tanstack/react-query';

import { listPatients } from '../api/patients';

export const usePatients = () =>
  useQuery({
    queryKey: ['patients'],
    queryFn: listPatients,
  });
