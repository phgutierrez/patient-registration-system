import { zodResolver } from '@hookform/resolvers/zod';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';

import { createPatient } from '../../api/patients';
import { useUiStore } from '../../store/uiStore';
import { patientSchema, type PatientFormInput } from '../../utils/validation';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';

export const PatientForm = () => {
  const queryClient = useQueryClient();
  const { setToastMessage } = useUiStore();
  const form = useForm<PatientFormInput>({ resolver: zodResolver(patientSchema) });

  const mutation = useMutation({
    mutationFn: async (data: PatientFormInput) =>
      createPatient({
        ...data,
        endereco: data.endereco ?? null,
        estado: data.estado ?? null,
      }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['patients'] });
      setToastMessage('Paciente salvo com sucesso.');
      form.reset();
    },
  });

  return (
    <form className="grid gap-3 md:grid-cols-2" onSubmit={form.handleSubmit((values) => mutation.mutate(values))}>
      <Input label="Nome" {...form.register('nome')} />
      <Input label="Prontuário" {...form.register('prontuario')} />
      <Input label="Data de Nascimento" type="date" {...form.register('data_nascimento')} />
      <Input label="Sexo (M/F)" {...form.register('sexo')} />
      <Input label="Nome da Mãe" {...form.register('nome_mae')} />
      <Input label="CNS" {...form.register('cns')} />
      <Input label="Cidade" {...form.register('cidade')} />
      <Input label="Contato" {...form.register('contato')} />
      <Input label="CID" {...form.register('cid')} />
      <Input label="Estado" {...form.register('estado')} />
      <Input label="Diagnóstico" className="md:col-span-2" {...form.register('diagnostico')} />
      <Input label="Endereço" className="md:col-span-2" {...form.register('endereco')} />
      <div className="md:col-span-2">
        <Button type="submit" disabled={mutation.isPending}>{mutation.isPending ? 'Salvando...' : 'Salvar paciente'}</Button>
      </div>
    </form>
  );
};
