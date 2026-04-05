import { PatientForm } from '../../components/forms/PatientForm';
import { Card } from '../../components/ui/Card';
import { usePatients } from '../../hooks/usePatients';

const PatientsPage = () => {
  const query = usePatients();

  return (
    <>
      <Card title="Novo paciente">
        <PatientForm />
      </Card>
      <Card title="Lista de pacientes">
        <ul className="space-y-2">
          {(query.data ?? []).map((patient) => (
            <li className="rounded border border-slate-200 p-2" key={patient.id}>
              <p className="font-semibold">{patient.nome}</p>
              <p className="text-sm text-slate-600">Prontuário: {patient.prontuario}</p>
            </li>
          ))}
        </ul>
      </Card>
    </>
  );
};

export default PatientsPage;
