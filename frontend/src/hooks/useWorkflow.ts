import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { workflowApi } from "../services/api/workflow";

export function useInvestigationWorkflowQuery(caseId: string) {
  return useQuery({
    queryKey: ["case", caseId, "investigation-workflow"],
    queryFn: () => workflowApi.getWorkflow(caseId),
    enabled: Boolean(caseId),
  });
}

export function useWorkflowTasksQuery(caseId: string) {
  return useQuery({
    queryKey: ["case", caseId, "workflow-tasks"],
    queryFn: () => workflowApi.listTasks(caseId),
    enabled: Boolean(caseId),
  });
}

export function useWorkflowNotesQuery(caseId: string) {
  return useQuery({
    queryKey: ["case", caseId, "workflow-notes"],
    queryFn: () => workflowApi.listNotes(caseId),
    enabled: Boolean(caseId),
  });
}

export function useWorkflowReviewsQuery(caseId: string) {
  return useQuery({
    queryKey: ["case", caseId, "workflow-reviews"],
    queryFn: () => workflowApi.listReviews(caseId),
    enabled: Boolean(caseId),
  });
}

export function useWorkflowMilestonesQuery(caseId: string) {
  return useQuery({
    queryKey: ["case", caseId, "workflow-milestones"],
    queryFn: () => workflowApi.listMilestones(caseId),
    enabled: Boolean(caseId),
  });
}

export function useWorkflowNotificationsQuery(caseId: string) {
  return useQuery({
    queryKey: ["case", caseId, "workflow-notifications"],
    queryFn: () => workflowApi.listNotifications(caseId),
    enabled: Boolean(caseId),
  });
}

export function useWorkflowStatusMutation(caseId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (status: string) =>
      workflowApi.updateStatus(caseId, { status }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: ["case", caseId, "investigation-workflow"],
      });
      await queryClient.invalidateQueries({
        queryKey: ["case", caseId, "workflow-milestones"],
      });
      await queryClient.invalidateQueries({
        queryKey: ["case", caseId, "workflow-notifications"],
      });
    },
  });
}

export function useCreateWorkflowTaskMutation(caseId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: { title: string; task_type?: string }) =>
      workflowApi.createTask(caseId, payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: ["case", caseId, "workflow-tasks"],
      });
      await queryClient.invalidateQueries({
        queryKey: ["case", caseId, "investigation-workflow"],
      });
      await queryClient.invalidateQueries({
        queryKey: ["case", caseId, "workflow-notifications"],
      });
    },
  });
}

export function useUpdateWorkflowTaskMutation(caseId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      taskId,
      action,
    }: {
      taskId: string;
      action: string;
    }) => workflowApi.updateTask(taskId, { action }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: ["case", caseId, "workflow-tasks"],
      });
      await queryClient.invalidateQueries({
        queryKey: ["case", caseId, "investigation-workflow"],
      });
    },
  });
}

export function useCreateWorkflowNoteMutation(caseId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (content_markdown: string) =>
      workflowApi.createNote(caseId, { content_markdown }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: ["case", caseId, "workflow-notes"],
      });
      await queryClient.invalidateQueries({
        queryKey: ["case", caseId, "investigation-workflow"],
      });
    },
  });
}
