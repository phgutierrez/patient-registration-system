export interface Patient {
  id: number;
  nome: string;
  prontuario: string;
  data_nascimento: string;
  sexo: string;
  nome_mae: string;
  cns: string;
  cidade: string;
  endereco?: string | null;
  estado?: string | null;
  contato: string;
  diagnostico: string;
  cid: string;
}
