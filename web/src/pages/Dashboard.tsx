import { DashboardStats } from '../components/features/DashboardStats';
import { Card } from '../components/ui/Card';
import { usePatients } from '../hooks/usePatients';
import { useSurgery } from '../hooks/useSurgery';

const Dashboard = () => {
  const patients = usePatients();
  const surgeries = useSurgery();

  return (
    <>
      <DashboardStats />
      <div className="grid gap-4 md:grid-cols-2">
        <Card title="Pacientes">
          <p className="text-3xl font-bold text-brand-700">{patients.data?.length ?? 0}</p>
          <p className="text-xs text-slate-500">cadastros ativos</p>
        </Card>
        <Card title="Solicitações cirúrgicas">
          <p className="text-3xl font-bold text-brand-700">{surgeries.data?.length ?? 0}</p>
          <p className="text-xs text-slate-500">itens registrados</p>
        </Card>
      </div>
    </>
  );
};

export default Dashboard;
