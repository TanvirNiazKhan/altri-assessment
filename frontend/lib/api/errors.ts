import type { Problem } from "./types"

export class ApiError extends Error {
  readonly status: number
  readonly code: string
  readonly problem: Problem | null

  constructor(status: number, problem: Problem | null) {
    super(problem?.detail || problem?.title || `Request failed (${status})`)
    this.name = "ApiError"
    this.status = status
    this.code = problem?.code ?? "unknown"
    this.problem = problem
  }
}

export async function toApiError(res: Response): Promise<ApiError> {
  let problem: Problem | null = null
  try {
    problem = (await res.json()) as Problem
  } catch {
    // Non-JSON error body (proxy error page, etc.)
  }
  return new ApiError(res.status, problem)
}

/** Message shown to people. Server details are written for users already; fall back by status. */
export function errorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.status === 422) {
      const first = error.problem?.errors?.[0]?.msg
      return first
        ? `Check the form: ${first.replace(/^Value error, /, "")}`
        : "Check the form and try again."
    }
    if (error.status === 403)
      return "Your role can view this team but not change it."
    if (error.status === 401) return "Your session ended. Sign in again."
    if (error.status >= 500)
      return "The server couldn't finish that. Try again in a moment."
    return error.message
  }
  if (error instanceof TypeError)
    return "Can't reach the server. Check your connection and try again."
  return "Something went wrong. Try again."
}
