import { useRef, useState, type DragEvent, type FormEvent } from "react";
import { CheckCircle2, FileUp } from "lucide-react";

import { useUploadEvidenceMutation } from "../../hooks/useEvidence";
import { ApiClientError } from "../../services/api/client";
import { cn } from "../../lib/utils";
import { Button } from "../ui/Button";
import { Panel } from "../ui/Panel";

interface EvidenceUploadFormProps {
  caseId: string;
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function EvidenceUploadForm({ caseId }: EvidenceUploadFormProps) {
  const [file, setFile] = useState<File | null>(null);
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const upload = useUploadEvidenceMutation(caseId);

  const assignFile = (next: File | null | undefined) => {
    if (next) {
      setFile(next);
    }
  };

  const onDrop = (event: DragEvent<HTMLLabelElement>) => {
    event.preventDefault();
    setDragging(false);
    assignFile(event.dataTransfer.files?.[0]);
  };

  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!file) return;
    upload.mutate(file, {
      onSuccess: () => {
        setFile(null);
        if (inputRef.current) inputRef.current.value = "";
      },
    });
  };

  return (
    <Panel collapsible title="Register evidence">
      <form className="space-y-4 p-4 sm:p-5" onSubmit={submit}>
        <label
          className={cn(
            "flex min-h-36 cursor-pointer flex-col items-center justify-center rounded-lg border border-dashed bg-background/50 p-5 text-center sm:min-h-44 sm:p-8",
            "duration-fast transition-colors",
            "focus-within:border-primary focus-within:ring-2 focus-within:ring-ring",
            dragging
              ? "border-primary bg-primary-soft/40"
              : "border-border-strong hover:border-primary/60",
          )}
          onDragEnter={(event) => {
            event.preventDefault();
            setDragging(true);
          }}
          onDragLeave={(event) => {
            event.preventDefault();
            setDragging(false);
          }}
          onDragOver={(event) => event.preventDefault()}
          onDrop={onDrop}
        >
          <FileUp aria-hidden="true" className="text-primary" size={28} />
          <span className="mt-3 block text-body font-medium text-foreground">
            Select an original evidence file
          </span>
          <span className="mt-1 max-w-md block text-caption text-muted">
            Drop a file here or tap to browse. Images, documents, video, and
            audio are accepted by the backend policy.
          </span>
          <input
            accept=".jpg,.jpeg,.png,.webp,.tif,.tiff,.pdf,.docx,.mp4,.mov,.avi,.mkv,.webm,.wav,.mp3,.m4a,.aac,.flac"
            className="sr-only"
            onChange={(event) => assignFile(event.target.files?.[0])}
            ref={inputRef}
            type="file"
          />
        </label>
        {file && (
          <div className="rounded-lg border border-border bg-background p-3 text-caption sm:text-body">
            <p className="truncate font-medium text-foreground">{file.name}</p>
            <p className="mt-1 text-muted">
              {file.type || "Unknown MIME"} · {formatBytes(file.size)}
            </p>
          </div>
        )}
        {upload.isError && (
          <p className="text-caption text-danger" role="alert">
            {upload.error instanceof ApiClientError
              ? upload.error.message
              : "Evidence could not be registered."}
          </p>
        )}
        {upload.isSuccess && (
          <p className="flex items-center gap-2 text-caption text-success">
            <CheckCircle2 aria-hidden="true" size={15} />
            {upload.data.data.evidence_number} registered. Original bytes
            preserved; analysis has not started.
          </p>
        )}
        <Button
          className="min-h-11 w-full sm:w-auto"
          disabled={!file || upload.isPending}
          type="submit"
          variant="primary"
        >
          {upload.isPending ? "Registering..." : "Register evidence"}
        </Button>
      </form>
    </Panel>
  );
}
