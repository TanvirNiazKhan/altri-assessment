"use client"

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import { api, apiWithStatus } from "@/lib/api/client"
import type { Issue, Scorecard, Todo, TodoList } from "@/lib/api/types"
import { qk } from "@/lib/query-keys"

const t = (teamId: string) => `/teams/${encodeURIComponent(teamId)}`

// ---------- Scorecard ----------

export function useScorecard(teamId: string, initialData?: Scorecard) {
  return useQuery({
    queryKey: qk.scorecard(teamId),
    queryFn: () => api<Scorecard>(`${t(teamId)}/scorecard`),
    initialData,
  })
}

export function useSetScore(teamId: string) {
  const client = useQueryClient()
  return useMutation({
    mutationFn: (v: {
      measurableId: string
      week: string
      value: number | null
    }) =>
      api<unknown>(
        `${t(teamId)}/scorecard/measurables/${v.measurableId}/weeks/${v.week}`,
        {
          method: "PUT",
          json: { value: v.value },
        }
      ),
    // Show the typed number at once; status comes back from the server on refetch.
    onMutate: async (v) => {
      await client.cancelQueries({ queryKey: qk.scorecard(teamId) })
      const previous = client.getQueryData<Scorecard>(qk.scorecard(teamId))
      if (previous) {
        client.setQueryData<Scorecard>(qk.scorecard(teamId), {
          ...previous,
          rows: previous.rows.map((r) =>
            r.id !== v.measurableId
              ? r
              : {
                  ...r,
                  cells: r.cells.map((c) =>
                    c.week_start === v.week ? { ...c, value: v.value } : c
                  ),
                }
          ),
        })
      }
      return { previous }
    },
    onError: (_e, _v, ctx) =>
      ctx?.previous && client.setQueryData(qk.scorecard(teamId), ctx.previous),
    onSettled: () =>
      client.invalidateQueries({ queryKey: qk.scorecard(teamId) }),
  })
}

export function useMakeIssue(teamId: string) {
  const client = useQueryClient()
  return useMutation({
    mutationFn: (v: { measurableId: string; week: string }) =>
      apiWithStatus<Issue>(
        `${t(teamId)}/scorecard/measurables/${v.measurableId}/weeks/${v.week}/issue`,
        {
          method: "POST",
        }
      ).then(({ data, status }) => ({ issue: data, created: status === 201 })),
    onSuccess: () => {
      void client.invalidateQueries({ queryKey: qk.scorecard(teamId) })
      void client.invalidateQueries({ queryKey: qk.issues(teamId) })
    },
  })
}

// ---------- Issues ----------

export function useIssues(
  teamId: string,
  status: "open" | "solved",
  initialData?: Issue[]
) {
  return useQuery({
    queryKey: qk.issueList(teamId, status),
    queryFn: () => api<Issue[]>(`${t(teamId)}/issues?status=${status}`),
    initialData,
  })
}

function useIssueMutation<V, R>(
  teamId: string,
  fn: (v: V) => Promise<R>,
  alsoTodos = false
) {
  const client = useQueryClient()
  return useMutation({
    mutationFn: fn,
    onSuccess: () => {
      void client.invalidateQueries({ queryKey: qk.issues(teamId) })
      void client.invalidateQueries({ queryKey: qk.scorecard(teamId) })
      if (alsoTodos)
        void client.invalidateQueries({ queryKey: qk.todos(teamId) })
    },
  })
}

export const useCreateIssue = (teamId: string) =>
  useIssueMutation(teamId, (v: { title: string; priority: number | null }) =>
    api<Issue>(`${t(teamId)}/issues`, { method: "POST", json: v })
  )

export const useSetPriority = (teamId: string) =>
  useIssueMutation(teamId, (v: { issueId: string; priority: number | null }) =>
    api<Issue>(`${t(teamId)}/issues/${v.issueId}`, {
      method: "PATCH",
      json: { priority: v.priority },
    })
  )

export const useSolveIssue = (teamId: string) =>
  useIssueMutation(teamId, (v: { issueId: string; note: string }) =>
    api<Issue>(`${t(teamId)}/issues/${v.issueId}/solve`, {
      method: "POST",
      json: { note: v.note },
    })
  )

export const useAddTodo = (teamId: string) =>
  useIssueMutation(
    teamId,
    (v: { issueId: string; title: string; ownerId: string }) =>
      api<Todo>(`${t(teamId)}/issues/${v.issueId}/todos`, {
        method: "POST",
        json: { title: v.title, owner_id: v.ownerId },
      }),
    true
  )

// ---------- To-Dos ----------

export function useTodos(teamId: string, initialData?: TodoList) {
  return useQuery({
    queryKey: qk.todos(teamId),
    queryFn: () => api<TodoList>(`${t(teamId)}/todos`),
    initialData,
  })
}

export function useToggleTodo(teamId: string) {
  const client = useQueryClient()
  return useMutation({
    mutationFn: (v: { todoId: string; done: boolean }) =>
      api<Todo>(`${t(teamId)}/todos/${v.todoId}/done`, {
        method: v.done ? "PUT" : "DELETE",
      }),
    onMutate: async (v) => {
      await client.cancelQueries({ queryKey: qk.todos(teamId) })
      const previous = client.getQueryData<TodoList>(qk.todos(teamId))
      if (previous) {
        client.setQueryData<TodoList>(qk.todos(teamId), {
          ...previous,
          items: previous.items.map((i) =>
            i.id === v.todoId
              ? {
                  ...i,
                  done_at: v.done ? (i.done_at ?? "pending") : null,
                  overdue: false,
                }
              : i
          ),
        })
      }
      return { previous }
    },
    onError: (_e, _v, ctx) =>
      ctx?.previous && client.setQueryData(qk.todos(teamId), ctx.previous),
    onSettled: () => client.invalidateQueries({ queryKey: qk.todos(teamId) }),
  })
}
