// Request/response contracts for the /api/v1/document/* routes.

export type JobStatus = "pending" | "processing" | "completed" | "failed";

export interface IngestionJob {
  id: string;
  user_id: string;
  document_id: string | null;
  status: JobStatus;
  error_message?: string | null;
  idempotency_key: string;
  completed_at?: string | null;
  updated_at: string;
  created_at: string;
}

export interface DocumentPagination {
  total_items: number;
  total_pages: number;
  has_next: boolean;
  has_previous: boolean;
}

export interface DocumentSummary {
  id: string;
  title?: string;
  user_id?: string;
  original_text?: string;
  created_at?: string;
  updated_at?: string;
}

export interface DocumentListResponse {
  // The backend currently serializes rows in an inconsistent shape, so we keep
  // this permissive and normalize on the client.
  items: Array<DocumentSummary | string>;
  pagination: DocumentPagination;
}

export interface DocumentTextPagination {
  text_length: number;
  next_start: number;
  has_next: boolean;
  has_prev: boolean;
}

export interface DocumentTextResponse {
  items: string;
  pagination: DocumentTextPagination;
}

export interface RetrieveDocumentCommand {
  id: string;
  start: number;
  limit: number;
  prev: boolean;
}

export interface UploadDocumentCommand {
  file: File;
  title?: string;
  idempotencyKey: string;
}
