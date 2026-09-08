import { Dialog } from "./Dialog";
import { Button } from "./Button";

interface ConfirmationDialogProps {
  open: boolean;
  title: string;
  description: string;
  confirmLabel?: string;
  cancelLabel?: string;
  onConfirm: () => void;
  onClose: () => void;
  loading?: boolean;
}

export function ConfirmationDialog({
  open,
  title,
  description,
  confirmLabel = "Confirm",
  cancelLabel = "Cancel",
  onConfirm,
  onClose,
  loading = false,
}: ConfirmationDialogProps) {
  return (
    <Dialog description={description} onClose={onClose} open={open} title={title}>
      <div className="flex justify-end gap-2">
        <Button onClick={onClose} type="button" variant="secondary">
          {cancelLabel}
        </Button>
        <Button loading={loading} onClick={onConfirm} type="button" variant="danger">
          {confirmLabel}
        </Button>
      </div>
    </Dialog>
  );
}
