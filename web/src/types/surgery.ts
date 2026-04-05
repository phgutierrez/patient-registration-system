export interface SurgeryRequest {
  id: number;
  patient_id: number;
  procedimento_solicitado: string;
  data_cirurgia: string;
  status: string;
  pdf_filename?: string | null;
  pdf_hemocomponente?: string | null;
  calendar_status?: string | null;
  scheduled_at?: string | null;
  scheduled_event_link?: string | null;
}

export interface SurgerySchedulePreview {
  title: string;
  date_display: string;
  orthopedist: string;
  needs_icu_display: string;
  opme_display: string;
  description: string;
  all_day: boolean;
}
