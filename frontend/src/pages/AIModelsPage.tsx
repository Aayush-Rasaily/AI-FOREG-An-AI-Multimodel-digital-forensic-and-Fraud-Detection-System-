import { BrainCircuit, Cpu, RefreshCw } from "lucide-react";

import { useAIModelsQuery, useInferenceJobsQuery, useReloadModelMutation } from "../hooks/useAI";
import { ApiClientError } from "../services/api/client";
import type { AIModel, InferenceJob } from "../types/ai";import { PageHeader } from "../components/layout/PageHeader";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/Card";
import { EmptyState } from "../components/ui/EmptyState";
import { ErrorState } from "../components/ui/ErrorState";
import { LoadingState } from "../components/ui/LoadingState";

const statusTone: Record<string, "neutral" | "cyan" | "green" | "amber" | "red"> = {
  REGISTERED: "neutral",
  LOADED: "green",
  UNLOADED: "amber",
  FAILED: "red",
};

export function AIModelsPage() {
  const modelsQuery = useAIModelsQuery();
  const jobsQuery = useInferenceJobsQuery();
  const reloadMutation = useReloadModelMutation();
  const models = modelsQuery.data?.data.items ?? [];
  const cacheStats = modelsQuery.data?.data.cache_statistics;
  const devices = modelsQuery.data?.data.devices ?? [];

  return (
    <div>
      <PageHeader
        description="Registered inference models, device availability, cache state, and job history. No forensic predictions are shown."
        eyebrow="AI infrastructure"
        title="AI Models"
      />

      {modelsQuery.isPending && <LoadingState label="Loading AI models" />}
      {modelsQuery.isError && (
        <ErrorState
          description={
            modelsQuery.error instanceof ApiClientError
              ? modelsQuery.error.message
              : "AI models could not be loaded."
          }
          onRetry={() => void modelsQuery.refetch()}
        />
      )}

      {modelsQuery.isSuccess && (
        <div className="grid gap-4 xl:grid-cols-[1.4fr_1fr]">
          <Card>
            <CardHeader>
              <CardTitle>Registered models</CardTitle>
              <BrainCircuit aria-hidden="true" className="text-slate-600" size={17} />
            </CardHeader>
            <CardContent>
              {models.length === 0 ? (
                <EmptyState
                  description="No models are registered in the AI registry."
                  title="No models"
                />
              ) : (
                <div className="space-y-3">
                  {models.map((model: AIModel) => (
                    <div
                      className="rounded-lg border border-slate-800 bg-slate-950/50 p-3"
                      key={model.id}
                    >
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <div>
                          <p className="text-sm font-medium text-slate-200">{model.name}</p>
                          <p className="text-[11px] text-slate-500">
                            v{model.version} · {model.framework}
                          </p>
                        </div>
                        <div className="flex flex-wrap items-center gap-2">
                          <Badge tone={statusTone[model.status] ?? "neutral"}>
                            {model.status}
                          </Badge>
                          <Button
                            disabled={reloadMutation.isPending}
                            onClick={() => reloadMutation.mutate(model.name)}
                            size="sm"
                            variant="secondary"
                          >
                            <RefreshCw aria-hidden="true" size={14} />
                            Reload
                          </Button>
                        </div>
                      </div>
                      <dl className="mt-3 grid gap-2 text-[11px] sm:grid-cols-2">
                        <div>
                          <dt className="text-slate-600">Device</dt>
                          <dd className="text-slate-300">
                            {model.current_device ?? model.required_device}
                          </dd>
                        </div>
                        <div>
                          <dt className="text-slate-600">Last latency</dt>
                          <dd className="text-slate-300">
                            {model.last_latency_ms != null
                              ? `${model.last_latency_ms.toFixed(2)} ms`
                              : "—"}
                          </dd>
                        </div>
                        <div>
                          <dt className="text-slate-600">Cache</dt>
                          <dd className="text-slate-300">
                            {model.cache_state?.loaded ? "loaded" : "not cached"}
                          </dd>
                        </div>
                        <div>
                          <dt className="text-slate-600">Hash</dt>
                          <dd className="truncate font-mono text-slate-400">
                            {model.model_hash.slice(0, 16)}…
                          </dd>
                        </div>
                      </dl>
                    </div>
                  ))}
                </div>
              )}
              {reloadMutation.isError && (
                <p className="mt-3 text-[11px] text-red-300">
                  {reloadMutation.error instanceof ApiClientError
                    ? reloadMutation.error.message
                    : "Model reload failed."}
                </p>
              )}
            </CardContent>
          </Card>

          <div className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Devices & cache</CardTitle>
                <Cpu aria-hidden="true" className="text-slate-600" size={17} />
              </CardHeader>
              <CardContent className="space-y-3">
                {devices.map((device: Record<string, unknown>) => (
                  <div
                    className="flex items-center justify-between rounded border border-slate-800 px-3 py-2 text-xs"
                    key={String(device.device_type)}
                  >
                    <span className="text-slate-400">{String(device.name)}</span>
                    <Badge tone={device.available ? "green" : "neutral"}>
                      {device.available ? "available" : "unavailable"}
                    </Badge>
                  </div>
                ))}
                {cacheStats && (
                  <div className="rounded border border-slate-800 px-3 py-2 text-[11px] text-slate-400">
                    Cache hits {cacheStats.hits} · misses {cacheStats.misses} · evictions{" "}
                    {cacheStats.evictions}
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Recent inference jobs</CardTitle>
              </CardHeader>
              <CardContent>
                {jobsQuery.isPending && <LoadingState label="Loading inference jobs" />}
                {jobsQuery.isSuccess && jobsQuery.data.data.items.length === 0 && (
                  <EmptyState
                    description="Inference jobs appear after model reload or warmup."
                    title="No jobs"
                  />
                )}
                {jobsQuery.isSuccess && jobsQuery.data.data.items.length > 0 && (
                  <div className="space-y-2">
                    {jobsQuery.data.data.items.slice(0, 6).map((job: InferenceJob) => (
                      <div
                        className="rounded border border-slate-800 px-2.5 py-2 text-xs text-slate-400"
                        key={job.id}
                      >
                        <div className="flex flex-wrap items-center gap-2">
                          <Badge tone={job.status === "SUCCEEDED" ? "green" : "neutral"}>
                            {job.status}
                          </Badge>
                          <span>{job.model_name}</span>
                          {job.latency_ms != null && (
                            <span className="text-[10px] text-slate-600">
                              {job.latency_ms.toFixed(2)} ms
                            </span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
}
