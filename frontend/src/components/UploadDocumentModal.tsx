import { useRef, useState, type ChangeEvent, type DragEvent, type SubmitEvent } from "react";

import { createIdempotencyKey, uploadDocument } from "../api/documents";
import {
  ALLOWED_UPLOAD_EXTENSIONS,
  ALLOWED_UPLOAD_MIME_TYPES,
  MAX_UPLOAD_BYTES,
} from "../config";
import { useToast } from "../context/ToastContext";
import { formatBytes } from "../utils/format";
import { Alert } from "./StatusMessage";
import { Button } from "./ui/Button";
import { Field } from "./ui/Field";
import { UploadIcon } from "./ui/Icons";
import { Modal } from "./ui/Modal";

interface UploadDocumentModalProps {
  open: boolean;
  onClose: () => void;
  onUploaded: () => void;
}

function isAllowedFile(file: File): boolean {
  const name = file.name.toLowerCase();
  return (
    ALLOWED_UPLOAD_EXTENSIONS.some((extension) => name.endsWith(extension)) ||
    (ALLOWED_UPLOAD_MIME_TYPES as readonly string[]).includes(file.type)
  );
}

export function UploadDocumentModal({
  open,
  onClose,
  onUploaded,
}: UploadDocumentModalProps) {
  const toast = useToast();
  const inputRef = useRef<HTMLInputElement>(null);

  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState("");
  const [idempotencyKey, setIdempotencyKey] = useState(() => createIdempotencyKey());
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  function reset() {
    setFile(null);
    setTitle("");
    setDragging(false);
    setError(null);
    setSubmitting(false);
    setIdempotencyKey(createIdempotencyKey());
    if (inputRef.current) inputRef.current.value = "";
  }

  function selectFile(selected: File | null) {
    setError(null);
    if (!selected) return;

    if (!isAllowedFile(selected)) {
      setError(
        `Unsupported file type. Allowed: ${ALLOWED_UPLOAD_EXTENSIONS.join(", ")}`,
      );
      return;
    }
    if (selected.size > MAX_UPLOAD_BYTES) {
      setError(`File is too large. Maximum size is ${formatBytes(MAX_UPLOAD_BYTES)}.`);
      return;
    }

    setFile(selected);
    if (!title) setTitle(selected.name.replace(/\.[^.]+$/, ""));
  }

  function handleInputChange(event: ChangeEvent<HTMLInputElement>) {
    selectFile(event.target.files?.[0] ?? null);
  }

  function handleDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    setDragging(false);
    selectFile(event.dataTransfer.files?.[0] ?? null);
  }

  async function handleSubmit(event: SubmitEvent) {
    event.preventDefault();
    setError(null);

    if (!file) {
      setError("Choose a file to upload");
      return;
    }

    setSubmitting(true);
    try {
      const job = await uploadDocument({
        file,
        title: title.trim() || undefined,
        idempotencyKey,
      });

      if (job.status === "failed") {
        setError(job.error_message || "The document could not be ingested.");
        return;
      }

      toast.success("Document uploaded and indexed.");
      onUploaded();
      reset();
      onClose();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Upload failed");
    } finally {
      setSubmitting(false);
    }
  }

  function handleClose() {
    if (submitting) return;
    reset();
    onClose();
  }

  return (
    <Modal
      open={open}
      title="Upload a document"
      description="Plain text, CSV and Markdown files up to 50 MB."
      onClose={handleClose}
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        {error && <Alert type="error" message={error} />}

        <div
          onDragOver={(event) => {
            event.preventDefault();
            setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={handleDrop}
          onClick={() => inputRef.current?.click()}
          className={`flex cursor-pointer flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed px-6 py-10 text-center transition ${
            dragging
              ? "border-emerald-400 bg-emerald-50"
              : "border-slate-300 bg-slate-50 hover:border-emerald-400 hover:bg-emerald-50/50"
          }`}
        >
          <UploadIcon className="h-8 w-8 text-emerald-600" />
          {file ? (
            <>
              <p className="text-sm font-medium text-slate-800">{file.name}</p>
              <p className="text-xs text-slate-500">{formatBytes(file.size)}</p>
            </>
          ) : (
            <>
              <p className="text-sm font-medium text-slate-700">
                Drop a file here or click to browse
              </p>
              <p className="text-xs text-slate-500">
                {ALLOWED_UPLOAD_EXTENSIONS.join(", ")}
              </p>
            </>
          )}
          <input
            ref={inputRef}
            type="file"
            accept={`${ALLOWED_UPLOAD_EXTENSIONS.join(",")},${ALLOWED_UPLOAD_MIME_TYPES.join(",")}`}
            className="hidden"
            onChange={handleInputChange}
          />
        </div>

        <Field
          label="Title (optional)"
          name="title"
          placeholder="Defaults to the file name"
          value={title}
          onChange={(event) => setTitle(event.target.value)}
        />

        <div className="flex justify-end gap-3 pt-1">
          <Button type="button" variant="secondary" onClick={handleClose} disabled={submitting}>
            Cancel
          </Button>
          <Button type="submit" loading={submitting} disabled={!file}>
            {submitting ? "Uploading…" : "Upload"}
          </Button>
        </div>
      </form>
    </Modal>
  );
}
