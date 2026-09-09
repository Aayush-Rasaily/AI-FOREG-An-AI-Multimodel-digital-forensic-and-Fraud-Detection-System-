import { useEffect, useRef, useState, type ReactNode } from "react";
import {
  Copy,
  Download,
  Maximize2,
  Minimize2,
  Pin,
  PinOff,
} from "lucide-react";

import { useProductivity } from "../../context/ProductivityContext";
import { cn } from "../../lib/utils";
import { Button } from "../ui/Button";
import { Panel } from "../ui/Panel";

interface WorkspacePanelChromeProps {
  panelId: string;
  title: string;
  description?: string;
  children: ReactNode;
  exportText?: string;
  className?: string;
  collapsible?: boolean;
}

export function WorkspacePanelChrome({
  panelId,
  title,
  description,
  children,
  exportText,
  className,
  collapsible = true,
}: WorkspacePanelChromeProps) {
  const { pinnedPanels, togglePinnedPanel, notify } = useProductivity();
  const bodyRef = useRef<HTMLDivElement>(null);
  const [fullscreen, setFullscreen] = useState(false);
  const pinned = pinnedPanels.includes(panelId);

  useEffect(() => {
    const onChange = () => {
      setFullscreen(Boolean(document.fullscreenElement));
    };
    document.addEventListener("fullscreenchange", onChange);
    return () => document.removeEventListener("fullscreenchange", onChange);
  }, []);

  const copyResults = async () => {
    const text =
      exportText ||
      bodyRef.current?.innerText ||
      `${title} — no textual results`;
    try {
      await navigator.clipboard.writeText(text);
      notify({
        title: "Copied to clipboard",
        description: title,
        tone: "success",
        category: "general",
      });
    } catch {
      notify({
        title: "Copy failed",
        description: "Clipboard permission denied.",
        tone: "warning",
        category: "system",
      });
    }
  };

  const exportResults = () => {
    const text =
      exportText ||
      bodyRef.current?.innerText ||
      `${title}\nExported from AI_Forge`;
    const blob = new Blob([text], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `${panelId.replaceAll(":", "-")}.txt`;
    anchor.click();
    URL.revokeObjectURL(url);
    notify({
      title: "Export started",
      description: `${title} saved as text.`,
      tone: "info",
      category: "general",
    });
  };

  const toggleFullscreen = (node: HTMLElement | null) => {
    if (!node) {
      return;
    }
    if (document.fullscreenElement) {
      void document.exitFullscreen();
      return;
    }
    void node.requestFullscreen();
  };

  return (
    <div
      className={cn("min-w-0", className)}
      data-panel-id={panelId}
      ref={(node) => {
        if (node) {
          (node as HTMLElement & { __fs?: HTMLElement }).__fs = node;
        }
      }}
    >
      <Panel
        collapsible={collapsible}
        description={description}
        headerActions={
          <div className="flex items-center gap-0.5">
            <Button
              aria-label={pinned ? "Unpin panel" : "Pin panel"}
              onClick={() => togglePinnedPanel(panelId)}
              size="sm"
              variant="ghost"
            >
              {pinned ? <PinOff size={14} /> : <Pin size={14} />}
            </Button>
            <Button
              aria-label="Copy results"
              onClick={() => void copyResults()}
              size="sm"
              variant="ghost"
            >
              <Copy size={14} />
            </Button>
            <Button
              aria-label="Export results"
              onClick={exportResults}
              size="sm"
              variant="ghost"
            >
              <Download size={14} />
            </Button>
            <Button
              aria-label="Toggle fullscreen"
              onClick={(event) => {
                const root = (event.currentTarget as HTMLElement).closest(
                  "[data-panel-id]",
                ) as HTMLElement | null;
                toggleFullscreen(root);
              }}
              size="sm"
              variant="ghost"
            >
              {fullscreen ? <Minimize2 size={14} /> : <Maximize2 size={14} />}
            </Button>
          </div>
        }
        title={title}
      >
        <div className="max-h-[40rem] overflow-auto" ref={bodyRef}>
          {children}
        </div>
      </Panel>
    </div>
  );
}
