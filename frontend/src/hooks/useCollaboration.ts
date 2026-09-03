import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { collaborationApi } from "../services/api/collaboration";

export function useCaseMembersQuery(caseId: string) {
  return useQuery({
    queryKey: ["case", caseId, "members"],
    queryFn: () => collaborationApi.listMembers(caseId),
    enabled: Boolean(caseId),
  });
}

export function useCaseTasksQuery(caseId: string) {
  return useQuery({
    queryKey: ["case", caseId, "tasks"],
    queryFn: () => collaborationApi.listTasks(caseId),
    enabled: Boolean(caseId),
  });
}

export function useCaseActivityQuery(caseId: string) {
  return useQuery({
    queryKey: ["case", caseId, "activity"],
    queryFn: () => collaborationApi.listActivity(caseId),
    enabled: Boolean(caseId),
  });
}

export function useCaseWorkflowQuery(caseId: string) {
  return useQuery({
    queryKey: ["case", caseId, "workflow"],
    queryFn: () => collaborationApi.getWorkflow(caseId),
    enabled: Boolean(caseId),
  });
}

export function useCaseCommentsQuery(caseId: string) {
  return useQuery({
    queryKey: ["case", caseId, "comments"],
    queryFn: () => collaborationApi.listComments("case", caseId),
    enabled: Boolean(caseId),
  });
}

export function useNotificationsQuery(enabled = true) {
  return useQuery({
    queryKey: ["notifications"],
    queryFn: () => collaborationApi.listNotifications(),
    enabled,
  });
}

export function useCreateTaskMutation(caseId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: { title: string; priority?: string }) =>
      collaborationApi.createTask(caseId, payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: ["case", caseId, "tasks"],
      });
      await queryClient.invalidateQueries({
        queryKey: ["case", caseId, "activity"],
      });
    },
  });
}

export function useCreateCommentMutation(caseId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: string) =>
      collaborationApi.createComment({
        case_id: caseId,
        resource_type: "case",
        resource_id: caseId,
        body,
      }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: ["case", caseId, "comments"],
      });
      await queryClient.invalidateQueries({
        queryKey: ["case", caseId, "activity"],
      });
    },
  });
}

export function useWorkflowTransitionMutation(caseId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (stage: string) =>
      collaborationApi.updateWorkflow(caseId, stage),
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: ["case", caseId, "workflow"],
      });
      await queryClient.invalidateQueries({
        queryKey: ["case", caseId, "activity"],
      });
    },
  });
}

export function useUpdateNotificationMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) =>
      collaborationApi.updateNotification(id, status),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["notifications"] });
    },
  });
}

export function useUpdateTaskMutation(caseId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      taskId,
      payload,
    }: {
      taskId: string;
      payload: Record<string, unknown>;
    }) => collaborationApi.updateTask(taskId, payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: ["case", caseId, "tasks"],
      });
    },
  });
}
