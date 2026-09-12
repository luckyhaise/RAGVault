import { ApiError, request } from "./client";
import type {
  DocumentListResponse,
  DocumentSummary,
  DocumentTextResponse,
  IngestionJob,
  RetrieveDocumentCommand,
  UploadDocumentCommand,
} from "../types/document_types";

export function fetchDocuments(
  page: number,
  limit: number,
): Promise<DocumentListResponse> {
  return request({
    path: "/document/get-all-documents",
    body: { page, limit },
  });
}

export function fetchDocumentText(
  command: RetrieveDocumentCommand,
  signal?: AbortSignal,
): Promise<DocumentTextResponse> {
  return request({ path: "/document/get-document", body: command, signal });
}

export function deleteDocument(documentId: string): Promise<{ detail: string }> {
  return request({
    path: "/document/delete",
    query: { document_id: documentId },
  });
}

export function uploadDocument({
  file,
  title,
  idempotencyKey,
}: UploadDocumentCommand): Promise<IngestionJob> {
  const formData = new FormData();
  formData.append("text_file", file);
  formData.append("idempotency_key", idempotencyKey);

  return request({
    path: "/document/upload",
    formData,
    // `file_name` is a query param on the backend and overrides the stored title.
    query: title ? { file_name: title } : undefined,
  });
}

/**
 * The list endpoint's serialization is inconsistent (it can return bare id
 * strings), so coerce every item into a usable summary.
 */
export function normalizeDocument(item: DocumentSummary | string): DocumentSummary {
  if (typeof item === "string") return { id: item };
  return item;
}

export function createIdempotencyKey(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  // Fallback for non-secure contexts where randomUUID is unavailable.
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (char) => {
    const random = (Math.random() * 16) | 0;
    const value = char === "x" ? random : (random & 0x3) | 0x8;
    return value.toString(16);
  });
}

export function isApiError(error: unknown): error is ApiError {
  return error instanceof ApiError;
}
