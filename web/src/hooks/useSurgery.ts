import { useQuery } from '@tanstack/react-query';

import { listSurgeries } from '../api/surgery';

export const useSurgery = () =>
  useQuery({
    queryKey: ['surgery'],
    queryFn: listSurgeries,
  });
