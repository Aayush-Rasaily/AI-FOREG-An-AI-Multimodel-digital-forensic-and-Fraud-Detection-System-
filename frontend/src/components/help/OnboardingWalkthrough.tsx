import { useEffect, useState } from "react";
import { Sparkles } from "lucide-react";

import { useWorkspacePreferences } from "../../hooks/useWorkspacePreferences";
import { Button } from "../ui/Button";
import { Dialog } from "../ui/Dialog";

const STEPS = [
  {
    title: "Investigation workspace",
    body: "Open a case to analyze evidence, run AI modalities, and reconstruct timelines without altering originals.",
  },
  {
    title: "Command palette",
    body: "Press Ctrl+K (⌘K) anytime to jump to cases, dashboards, or help without leaving the keyboard.",
  },
  {
    title: "Analytics & dashboards",
    body: "Executive and interactive analytics surfaces use persisted platform metrics — never fabricated forecasts.",
  },
];

interface OnboardingWalkthroughProps {
  /** Force open (e.g. from Settings). */
  forceOpen?: boolean;
  onCloseForced?: () => void;
}

export function OnboardingWalkthrough({
  forceOpen = false,
  onCloseForced,
}: OnboardingWalkthroughProps) {
  const { onboardingDismissed, setOnboardingDismissed } =
    useWorkspacePreferences();
  const [step, setStep] = useState(0);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (forceOpen) {
      setStep(0);
      setOpen(true);
      return;
    }
    if (!onboardingDismissed) {
      setOpen(true);
    }
  }, [forceOpen, onboardingDismissed]);

  if (!open) {
    return null;
  }

  const current = STEPS[step] ?? STEPS[0];
  const isLast = step >= STEPS.length - 1;

  const dismiss = () => {
    setOnboardingDismissed(true);
    setOpen(false);
    onCloseForced?.();
  };

  return (
    <Dialog
      description="A short orientation for investigators. Dismiss anytime — replay from Settings."
      onClose={dismiss}
      open={open}
      title="Welcome to AI_Forge"
    >
      <div className="space-y-4">
        <div className="flex items-start gap-3 rounded-lg border border-border bg-background/50 p-3">
          <Sparkles aria-hidden="true" className="mt-0.5 text-primary" size={18} />
          <div>
            <p className="text-caption font-medium text-foreground">
              {current.title}
            </p>
            <p className="mt-1 text-caption leading-relaxed text-muted">
              {current.body}
            </p>
          </div>
        </div>
        <p className="text-micro text-subtle">
          Step {step + 1} of {STEPS.length}
        </p>
        <div className="flex flex-wrap justify-end gap-2">
          <Button onClick={dismiss} size="sm" type="button" variant="ghost">
            Skip
          </Button>
          {!isLast ? (
            <Button
              onClick={() => setStep((currentStep) => currentStep + 1)}
              size="sm"
              type="button"
            >
              Next
            </Button>
          ) : (
            <Button onClick={dismiss} size="sm" type="button">
              Get started
            </Button>
          )}
        </div>
      </div>
    </Dialog>
  );
}
