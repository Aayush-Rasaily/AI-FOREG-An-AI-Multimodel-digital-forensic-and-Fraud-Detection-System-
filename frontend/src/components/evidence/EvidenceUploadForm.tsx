import { useRef, useState, type FormEvent } from "react";
import { CheckCircle2, FileUp } from "lucide-react";

import { useUploadEvidenceMutation } from "../../hooks/useEvidence";
import { ApiClientError } from "../../services/api/client";
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
  const inputRef = useRef<HTMLInputElement>(null);
  const upload = useUploadEvidenceMutation(caseId);

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
    <Panel title="Register evidence">
      <form className="space-y-4" onSubmit={submit}>
        <label className="block cursor-pointer rounded-lg border border-dashed border-slate-700 bg-slate-950/50 p-5 text-center hover:border-cyan-400/60">
          <FileUp aria-hidden="true" className="mx-auto text-cyan-300" size={22} />
          <span className="mt-2 block text-xs font-medium text-slate-200">
            Select an original evidence file
          </span>
          <span className="mt-1 block text-[11px] text-slate-500">
            Images, documents, video, and audio are accepted by the backend policy.
          </span>
          <input
            accept=".jpg,.jpeg,.png,.webp,.tif,.tiff,.pdf,.docx,.mp4,.mov,.avi,.mkv,.webm,.wav,.mp3,.m4a,.aac,.flac"
            className="sr-only"
            onChange={(event) => setFile(event.target.files?.[0] ?? null)}
            ref={inputRef}
            type="file"
          />
        </label>
        {file && (
          <div className="rounded-lg border border-slate-800 bg-slate-950 p-3 text-xs">
            <p className="truncate font-medium text-slate-200">{file.name}</p>
            <p className="mt-1 text-slate-500">
              {file.type || "Unknown MIME"} · {formatBytes(file.size)}
            </p>
          </div>
        )}
        {upload.isError && (
          <p className="text-xs text-red-300">
            {upload.error instanceof ApiClientError
              ? upload.error.message
              : "Evidence could not be registered."}
          </p>
        )}
        {upload.isSuccess && (
          <p className="flex items-center gap-2 text-xs text-emerald-300">
            <CheckCircle2 aria-hidden="true" size={15} />
            {upload.data.data.evidence_number} registered. Original bytes preserved; analysis has not started.
          </p>
        )}
        <Button disabled={!file || upload.isPending} type="submit" variant="primary">
          {upload.isPending ? "Registering..." : "Register evidence"}
        </Button>
      </form>
    </Panel>
  );
}
