import { useMutation, useQueryClient } from '@tanstack/react-query';

import { confirmSurgerySchedule, getSurgeryHemocomponentePdfUrl, getSurgeryPdfUrl, getSurgerySchedulePreview } from '../../api/surgery';
import { useSurgery } from '../../hooks/useSurgery';
import { useUiStore } from '../../store/uiStore';
import type { SurgeryRequest, SurgerySchedulePreview } from '../../types/surgery';
import { Button } from '../../components/ui/Button';
import { Card } from '../../components/ui/Card';
import { Modal } from '../../components/ui/Modal';
import { useState } from 'react';

const SurgeryPage = () => {
  const queryClient = useQueryClient();
  const { setToastMessage } = useUiStore();
  const query = useSurgery();
  const [selected, setSelected] = useState<SurgeryRequest | null>(null);
  const [preview, setPreview] = useState<SurgerySchedulePreview | null>(null);
  const [previewOpen, setPreviewOpen] = useState(false);

  const previewMutation = useMutation({
    mutationFn: async (surgeryId: number) => getSurgerySchedulePreview(surgeryId),
    onSuccess: (data) => {
      setPreview(data.preview);
      setPreviewOpen(true);
    },
    onError: () => {
      setToastMessage('Falha ao carregar preview de agendamento.');
    },
  });

  const confirmMutation = useMutation({
    mutationFn: async (surgeryId: number) => confirmSurgerySchedule(surgeryId),
    onSuccess: async () => {
      setToastMessage('Agendamento confirmado no Google Forms.');
      setPreviewOpen(false);
      await queryClient.invalidateQueries({ queryKey: ['surgery'] });
    },
    onError: () => {
      setToastMessage('Falha ao confirmar agendamento.');
    },
  });

  const openPreview = (item: SurgeryRequest) => {
    setSelected(item);
    previewMutation.mutate(item.id);
  };

  return (
    <>
      <Card title="Workflow de solicitações cirúrgicas">
        <p className="mb-3 text-sm text-slate-600">Fluxo completo: preview e confirmação de agendamento no Forms, além de downloads dos PDFs.</p>
        <ul className="space-y-3">
          {(query.data ?? []).map((item) => (
            <li className="rounded border border-slate-200 p-3" key={item.id}>
              <p className="font-semibold">{item.procedimento_solicitado}</p>
              <p className="text-sm text-slate-600">Data: {item.data_cirurgia} | Status: {item.status} | Agenda: {item.calendar_status ?? 'pendente'}</p>
              <div className="mt-3 flex flex-wrap gap-2">
                <Button type="button" onClick={() => openPreview(item)}>
                  Preview Agendamento
                </Button>
                <Button type="button" variant="ghost" onClick={() => window.open(getSurgeryPdfUrl(item.id), '_blank')}>
                  Baixar PDF Internação
                </Button>
                <Button
                  type="button"
                  variant="ghost"
                  disabled={!item.pdf_hemocomponente}
                  onClick={() => window.open(getSurgeryHemocomponentePdfUrl(item.id), '_blank')}
                >
                  Baixar PDF Hemocomponente
                </Button>
              </div>
            </li>
          ))}
        </ul>
      </Card>

      <Modal open={previewOpen} title="Preview de Agendamento" onClose={() => setPreviewOpen(false)}>
        {preview ? (
          <div className="space-y-2 text-sm text-slate-700">
            <p><strong>Título:</strong> {preview.title}</p>
            <p><strong>Data:</strong> {preview.date_display}</p>
            <p><strong>Ortopedista:</strong> {preview.orthopedist}</p>
            <p><strong>UTI:</strong> {preview.needs_icu_display}</p>
            <p><strong>OPME:</strong> {preview.opme_display}</p>
            <p><strong>Descrição:</strong></p>
            <pre className="max-h-48 overflow-auto rounded bg-slate-50 p-2 whitespace-pre-wrap">{preview.description}</pre>
            <div className="pt-2">
              <Button
                type="button"
                disabled={!selected || confirmMutation.isPending}
                onClick={() => selected && confirmMutation.mutate(selected.id)}
              >
                {confirmMutation.isPending ? 'Confirmando...' : 'Confirmar Agendamento'}
              </Button>
            </div>
          </div>
        ) : (
          <p>Carregando preview...</p>
        )}
      </Modal>
    </>
  );
};

export default SurgeryPage;
