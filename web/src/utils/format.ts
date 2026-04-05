export const formatDate = (value: string): string => {
  if (!value) return '-';
  return new Date(value).toLocaleDateString('pt-BR');
};
