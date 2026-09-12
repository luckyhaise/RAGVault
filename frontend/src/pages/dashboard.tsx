import { useState } from "react";

import ChangePasswordForm from "../components/ChangePasswordForm";
import { DocumentList } from "../components/DocumentList";
import { UploadDocumentModal } from "../components/UploadDocumentModal";
import { Button } from "../components/ui/Button";
import { KeyIcon, LogoutIcon, VaultIcon } from "../components/ui/Icons";
import { Modal } from "../components/ui/Modal";
import { useAuth } from "../context/AuthContext";
import { useToast } from "../context/ToastContext";
import type { DocumentSummary } from "../types/document_types";
import { DocumentReader } from "./DocumentReader";

export function Dashboard() {
  const { user, signOut } = useAuth();
  const toast = useToast();

  const [page, setPage] = useState(1);
  const [reloadToken, setReloadToken] = useState(0);
  const [uploadOpen, setUploadOpen] = useState(false);
  const [changePasswordOpen, setChangePasswordOpen] = useState(false);
  const [activeDocument, setActiveDocument] = useState<DocumentSummary | null>(null);
  const [signingOut, setSigningOut] = useState(false);

  const displayName = user?.name || user?.user_name || user?.email || "signed in";

  function handleDocumentsChanged() {
    setReloadToken((current) => current + 1);
  }

  function handleUploaded() {
    setPage(1);
    setReloadToken((current) => current + 1);
  }

  async function handleSignOut() {
    setSigningOut(true);
    try {
      await signOut();
    } catch (caught) {
      toast.error(caught instanceof Error ? caught.message : "Sign out failed");
      setSigningOut(false);
    }
  }

  // The reader is a full page rather than a dialog.
  if (activeDocument) {
    return (
      <DocumentReader
        document={activeDocument}
        onBack={() => setActiveDocument(null)}
      />
    );
  }

  return (
    <div className="min-h-screen bg-slate-100">
      <header className="sticky top-0 z-30 border-b border-slate-200 bg-white/90 backdrop-blur">
        <div className="mx-auto flex max-w-5xl items-center justify-between gap-4 px-4 py-3 sm:px-6">
          <div className="flex items-center gap-3">
            <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-600 text-white">
              <VaultIcon className="h-5 w-5" />
            </span>
            <div>
              <p className="text-sm font-semibold leading-tight text-slate-900">Ragvault</p>
              <p className="text-xs leading-tight text-slate-500">
                Signed in as {displayName}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setChangePasswordOpen(true)}
            >
              <KeyIcon />
              <span className="hidden sm:inline">Password</span>
            </Button>
            <Button
              variant="secondary"
              size="sm"
              loading={signingOut}
              onClick={() => void handleSignOut()}
            >
              <LogoutIcon />
              <span className="hidden sm:inline">Sign out</span>
            </Button>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-5xl px-4 py-8 sm:px-6">
        <DocumentList
          page={page}
          reloadToken={reloadToken}
          onPageChange={setPage}
          onOpenDocument={setActiveDocument}
          onDocumentsChanged={handleDocumentsChanged}
          onUploadClick={() => setUploadOpen(true)}
        />
      </main>

      <UploadDocumentModal
        open={uploadOpen}
        onClose={() => setUploadOpen(false)}
        onUploaded={handleUploaded}
      />

      <Modal
        open={changePasswordOpen}
        size="sm"
        title="Change password"
        description="You'll stay signed in after updating."
        onClose={() => setChangePasswordOpen(false)}
      >
        <ChangePasswordForm onSuccess={() => setChangePasswordOpen(false)} />
      </Modal>
    </div>
  );
}
