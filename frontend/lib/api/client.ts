import { toApiError } from "./errors"

/**
 * Browser-side fetcher. Requests go to `/api/*` on this origin; Next rewrites them
 * to FastAPI, so the HttpOnly session cookie travels without CORS.
 */
export async function api<T>(
  path: string,
  init?: RequestInit & { json?: unknown }
): Promise<T> {
  const { json, headers, ...rest } = init ?? {}
  const res = await fetch(`/api${path}`, {
    credentials: "same-origin",
    ...rest,
    headers: {
      Accept: "application/json",
      ...(json !== undefined ? { "Content-Type": "application/json" } : {}),
      ...headers,
    },
    body: json !== undefined ? JSON.stringify(json) : rest.body,
  })
  if (!res.ok) throw await toApiError(res)
  if (res.status === 204) return undefined as T
  return (await res.json()) as T
}

/** Same as `api`, plus the status code, for endpoints where 200 vs 201 means something. */
export async function apiWithStatus<T>(
  path: string,
  init?: RequestInit
): Promise<{ data: T; status: number }> {
  const res = await fetch(`/api${path}`, {
    credentials: "same-origin",
    headers: { Accept: "application/json" },
    ...init,
  })
  if (!res.ok) throw await toApiError(res)
  return { data: (await res.json()) as T, status: res.status }
}
