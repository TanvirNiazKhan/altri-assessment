import "server-only"

import { cache } from "react"
import { cookies } from "next/headers"
import { notFound, redirect } from "next/navigation"

import { toApiError } from "./errors"
import type {
  Me,
  MeetingState,
  MeetingSummary,
  Rock,
  Scorecard,
  Issue,
  TeamDetail,
  TodoList,
  User,
} from "./types"

export const SESSION_COOKIE = "l10_session"
const API_URL = process.env.API_INTERNAL_URL ?? "http://localhost:8000"

/**
 * Server-side fetcher for Server Components. Forwards the session cookie to FastAPI.
 * 401 sends the person to sign in; 404 (missing or inaccessible team, same answer
 * on purpose) renders the not-found page.
 */
async function serverApi<T>(path: string): Promise<T> {
  const session = (await cookies()).get(SESSION_COOKIE)?.value
  if (!session) redirect("/sign-in")

  const res = await fetch(`${API_URL}/api${path}`, {
    headers: {
      Accept: "application/json",
      Cookie: `${SESSION_COOKIE}=${session}`,
    },
    cache: "no-store",
  })
  if (res.status === 401) redirect("/sign-in")
  if (res.status === 404) notFound()
  if (!res.ok) throw await toApiError(res)
  return (await res.json()) as T
}

// React.cache dedupes per request: the layout and page both ask for `me` and the team.
export const getMe = cache(() => serverApi<Me>("/me"))
export const getTeam = cache((teamId: string) =>
  serverApi<TeamDetail>(`/teams/${enc(teamId)}`)
)

export const getScorecard = (teamId: string) =>
  serverApi<Scorecard>(`/teams/${enc(teamId)}/scorecard`)
export const getOpenIssues = (teamId: string) =>
  serverApi<Issue[]>(`/teams/${enc(teamId)}/issues?status=open`)
export const getTodos = (teamId: string) =>
  serverApi<TodoList>(`/teams/${enc(teamId)}/todos`)
export const getRocks = (teamId: string) =>
  serverApi<Rock[]>(`/teams/${enc(teamId)}/rocks`)
export const getOwners = cache((teamId: string) =>
  serverApi<User[]>(`/teams/${enc(teamId)}/members?can_own=true`)
)
export const getActiveMeeting = (teamId: string) =>
  serverApi<MeetingState>(`/teams/${enc(teamId)}/meetings/active`)
export const getMeeting = (teamId: string, meetingId: string) =>
  serverApi<MeetingState>(`/teams/${enc(teamId)}/meetings/${enc(meetingId)}`)
export const getMeetingSummary = (teamId: string, meetingId: string) =>
  serverApi<MeetingSummary>(
    `/teams/${enc(teamId)}/meetings/${enc(meetingId)}/summary`
  )

/** Public: the sign-in picker. Does not need a session. */
export async function getSignInUsers(): Promise<User[]> {
  const res = await fetch(`${API_URL}/api/auth/users`, { cache: "no-store" })
  if (!res.ok) throw await toApiError(res)
  return (await res.json()) as User[]
}

function enc(s: string) {
  return encodeURIComponent(s)
}
