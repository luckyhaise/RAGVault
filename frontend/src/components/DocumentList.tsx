import { useCallback, useEffect, useState } from "react";

import { deleteDocument, fetchDocuments, normalizeDocument } from "../api/documents";
import { DEFAULT_PAGE_SIZE } from "../config";
import { useToast } from "../context/ToastContext";
import type { DocumentPagination, DocumentSummary } from "../types/document_types";
import { formatDateTime, truncate } from "../utils/format";
import { Alert } from "./StatusMessage";
import { Button } from "./ui/Button";
import {
  ChevronLeftIcon,
  ChevronRightIcon,
  DocumentIcon,
  RefreshIcon,
  TrashIcon,
  UploadIcon,
} from "./ui/Icons";
import { Modal } from "./ui/Modal";

interface DocumentListProps {
  page: number;
  reloadToken: number;
  onPageChange: (page: number) => void;
  onOpenDocument: (document: DocumentSummary) => void;
  onDocumentsChanged: () => void;
  onUploadClick: () => void;
}

const EMPTY_PAGINATION: DocumentPagination = {
  total_items: 0,
  total_pages: 1,
  has_next: false,
  has_previous: false,
};

export function DocumentList({
  page,
  reloadToken,
  onPageChange,
  onOpenDocument,
  onDocumentsChanged,
  onUploadClick,
}: DocumentListProps) {
  const toast = useToast();

  const [documents, setDocuments] = useState<DocumentSummary[]>([]);
  const [pagination, setPagination] = useState<DocumentPagination>(EMPTY_PAGINATION);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [pendingDelete, setPendingDelete] = useState<DocumentSummary | null>(null);
  const [deleting, setDeleting] = useState(false);

  const runFetch = useCallback(async () => {
    try {
      const result = await fetchDocuments(page, DEFAULT_PAGE_SIZE);
      const items = Array.isArray(result.items) ? result.items : [];
      setDocuments(items.map(normalizeDocument));
      setPagination(result.pagination ?? EMPTY_PAGINATION);
      setError(null);
    } catch (caught) {
      setError(
        caught instanceof Error ? caught.message : "Unable to load documents",
      );
      setDocuments([]);
      setPagination(EMPTY_PAGINATION);
    } finally {
      setLoading(false);
    }
  }, [page]);

  useEffect(() => {
    // `runFetch` only updates state after the request resolves, so this does not
    // cause the synchronous cascading render the rule guards against.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void runFetch();
  }, [runFetch, reloadToken]);

  function goToPage(nextPage: number) {
    setLoading(true);
    onPageChange(nextPage);
  }

  async function handleDelete() {
    if (!pendingDelete) return;
    setDeleting(true);
    try {
      await deleteDocument(pendingDelete.id);
      toast.success("Document deleted.");
      setPendingDelete(null);
      onDocumentsChanged();
    } catch (caught) {
      toast.error(caught instanceof Error ? caught.message : "Delete failed");
    } finally {
      setDeleting(false);
    }
  }

  const canGoPrevious = page > 1;
  const canGoNext = page < pagination.total_pages;

  return (
    <section className="rounded-2xl border border-slate-200 bg-white shadow-sm">
      <header className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 px-6 py-4">
        <div>
          <h2 className="text-base font-semibold text-slate-900">Your documents</h2>
          <p className="text-xs text-slate-500">
            {pagination.total_items} document
            {pagination.total_items === 1 ? "" : "s"} in your vault
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => {
              setLoading(true);
              void runFetch();
            }}
            disabled={loading}
          >
            <RefreshIcon />
            Refresh
          </Button>
          <Button size="sm" onClick={onUploadClick}>
            <UploadIcon className="h-4 w-4" />
            Upload
          </Button>
        </div>
      </header>

      <div className="px-6 py-4">
        {error && (
          <div className="mb-4">
            <Alert type="error" message={error} />
          </div>
        )}

        {loading ? (
          <ul className="space-y-2">
            {Array.from({ length: 3 }).map((_, index) => (
              <li
                key={index}
                className="h-16 animate-pulse rounded-xl border border-slate-100 bg-slate-50"
              />
            ))}
          </ul>
        ) : documents.length === 0 ? (
          <div className="flex flex-col items-center justify-center gap-3 py-14 text-center">
            <span className="flex h-12 w-12 items-center justify-center rounded-full bg-emerald-50 text-emerald-600">
              <DocumentIcon className="h-6 w-6" />
            </span>
            <div>
              <p className="text-sm font-medium text-slate-800">No documents yet</p>
              <p className="text-xs text-slate-500">
                Upload a .txt, .csv or .md file to get started.
              </p>
            </div>
            <Button size="sm" onClick={onUploadClick}>
              <UploadIcon className="h-4 w-4" />
              Upload your first document
            </Button>
          </div>
        ) : (
          <ul className="divide-y divide-slate-100">
            {documents.map((document) => {
              const displayTitle = document.title?.trim() || "Untitled document";
              const subtitle = document.original_text
                ? truncate(document.original_text.replace(/\s+/g, " "), 90)
                : document.created_at
                  ? `Added ${formatDateTime(document.created_at)}`
                  : undefined;
              return (
                <li
                  key={document.id}
                  className="flex items-center gap-4 py-3 transition hover:bg-slate-50/70"
                >
                  <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-emerald-50 text-emerald-600">
                    <DocumentIcon />
                  </span>

                  <button
                    type="button"
                    onClick={() => onOpenDocument(document)}
                    className="min-w-0 flex-1 text-left"
                  >
                    <p className="truncate text-sm font-medium text-slate-800">
                      {displayTitle}
                    </p>
                    {subtitle && (
                      <p className="truncate text-xs text-slate-500">{subtitle}</p>
                    )}
                  </button>

                  {document.updated_at && (
                    <div className="hidden shrink-0 text-right text-xs text-slate-400 sm:block">
                      <p>Updated {formatDateTime(document.updated_at)}</p>
                    </div>
                  )}

                  <div className="flex shrink-0 items-center gap-1">
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => onOpenDocument(document)}
                    >
                      Open
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      aria-label="Delete document"
                      onClick={() => setPendingDelete(document)}
                      className="text-rose-600 hover:bg-rose-50"
                    >
                      <TrashIcon />
                    </Button>
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </div>

      {pagination.total_pages > 1 && (
        <footer className="flex items-center justify-between border-t border-slate-100 px-6 py-3">
          <span className="text-xs text-slate-500">
            Page {page} of {pagination.total_pages}
          </span>
          <div className="flex gap-2">
            <Button
              variant="secondary"
              size="sm"
              disabled={!canGoPrevious || loading}
              onClick={() => goToPage(page - 1)}
            >
              <ChevronLeftIcon />
              Previous
            </Button>
            <Button
              variant="secondary"
              size="sm"
              disabled={!canGoNext || loading}
              onClick={() => goToPage(page + 1)}
            >
              Next
              <ChevronRightIcon />
            </Button>
          </div>
        </footer>
      )}

      <Modal
        open={pendingDelete !== null}
        size="sm"
        title="Delete document"
        onClose={() => (deleting ? undefined : setPendingDelete(null))}
        footer={
          <>
            <Button
              variant="secondary"
              onClick={() => setPendingDelete(null)}
              disabled={deleting}
            >
              Cancel
            </Button>
            <Button variant="danger" loading={deleting} onClick={() => void handleDelete()}>
              Delete
            </Button>
          </>
        }
      >
        <p className="text-sm text-slate-600">
          Are you sure you want to delete{" "}
          <span className="font-medium text-slate-900">
            {pendingDelete?.title?.trim() || "this document"}
          </span>
          ? This permanently removes the document and its chunks.
        </p>
      </Modal>
    </section>
  );
}
