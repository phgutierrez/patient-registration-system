import { z } from 'zod';

export const patientSchema = z.object({
  nome: z.string().min(1),
  prontuario: z.string().min(1),
  data_nascimento: z.string().min(1),
  sexo: z.enum(['M', 'F']),
  nome_mae: z.string().min(1),
  cns: z.string().min(1),
  cidade: z.string().min(1),
  contato: z.string().min(1),
  diagnostico: z.string().min(1),
  cid: z.string().min(1),
  endereco: z.string().optional(),
  estado: z.string().optional(),
});

export type PatientFormInput = z.infer<typeof patientSchema>;
