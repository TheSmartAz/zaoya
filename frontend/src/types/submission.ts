// Submission types
export interface FormSubmission {
  id: string;
  project_id: string;
  public_id: string;
  form_id: string;
  data: Record<string, unknown>;
  metadata: {
    ip?: string;
    user_agent?: string;
    referer?: string;
    submitted_at: string;
    created_at?: string;
  };
  notification_sent: boolean;
}

export interface SubmissionsListResponse {
  submissions: FormSubmission[];
  pagination: {
    page: number;
    per_page: number;
    total: number;
    pages: number;
  };
}

export interface SubmissionSummary {
  total_submissions: number;
  recent_submissions: number;
  last_submission: string | null;
}
