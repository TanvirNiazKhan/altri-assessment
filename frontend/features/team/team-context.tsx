"use client"

import { createContext, use } from "react"

import type { Calendar, User } from "@/lib/api/types"

export interface TeamContextValue {
  teamId: string
  teamName: string
  /** From the server's access check. Buttons hide for Observers; the API still enforces it. */
  canWrite: boolean
  user: User
  calendar: Calendar
  /** Admins and Team Members of this team: the owner picker for To-Dos. */
  owners: { id: string; name: string }[]
}

const TeamContext = createContext<TeamContextValue | null>(null)

export function TeamProvider({
  value,
  children,
}: {
  value: TeamContextValue
  children: React.ReactNode
}) {
  return <TeamContext value={value}>{children}</TeamContext>
}

export function useTeam(): TeamContextValue {
  const ctx = use(TeamContext)
  if (!ctx) throw new Error("useTeam must be used inside <TeamProvider>")
  return ctx
}
