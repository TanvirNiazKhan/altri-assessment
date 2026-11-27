"use client"

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import { api } from "@/lib/api/client"
import type {
  MeetingSection,
  MeetingState,
  MeetingSummary,
} from "@/lib/api/types"
import { qk } from "@/lib/query-keys"
import { applyMeetingState } from "@/features/realtime/team-realtime"

const base = (teamId: string) => `/teams/${encodeURIComponent(teamId)}/meetings`

export function useActiveMeeting(teamId: string, initialData?: MeetingState) {
  return useQuery({
    queryKey: qk.activeMeeting(teamId),
    queryFn: () => api<MeetingState>(`${base(teamId)}/active`),
    initialData,
  })
}

export function useMeeting(
  teamId: string,
  meetingId: string,
  initialData?: MeetingState
) {
  const client = useQueryClient()
  return useQuery({
    queryKey: qk.meeting(teamId, meetingId),
    queryFn: async () => {
      const state = await api<MeetingState>(`${base(teamId)}/${meetingId}`)
      applyMeetingState(client, teamId, state)
      return state
    },
    initialData,
  })
}

export function useMeetingSummary(
  teamId: string,
  meetingId: string,
  enabled: boolean,
  initialData?: MeetingSummary
) {
  return useQuery({
    queryKey: qk.summary(teamId, meetingId),
    queryFn: () => api<MeetingSummary>(`${base(teamId)}/${meetingId}/summary`),
    enabled,
    initialData,
    staleTime: Infinity, // frozen at the end of the meeting
  })
}

/** Every meeting command returns the new snapshot; apply it before the socket echo arrives. */
function useMeetingCommand<V>(
  teamId: string,
  fn: (v: V) => Promise<MeetingState>
) {
  const client = useQueryClient()
  return useMutation({
    mutationFn: fn,
    onSuccess: (state) => applyMeetingState(client, teamId, state),
    // A 409 (stale section, already ended…) means our copy is old: pull the truth.
    onError: () =>
      client.invalidateQueries({ queryKey: ["team", teamId, "meeting"] }),
  })
}

export const useStartMeeting = (teamId: string) =>
  useMeetingCommand(teamId, () =>
    api<MeetingState>(base(teamId), { method: "POST" })
  )

export const useJoinMeeting = (teamId: string) =>
  useMeetingCommand(teamId, (meetingId: string) =>
    api<MeetingState>(`${base(teamId)}/${meetingId}/join`, { method: "POST" })
  )

export const useAdvanceMeeting = (teamId: string) =>
  useMeetingCommand(
    teamId,
    (v: { meetingId: string; expected: MeetingSection }) =>
      api<MeetingState>(`${base(teamId)}/${v.meetingId}/advance`, {
        method: "POST",
        json: { expected_section: v.expected },
      })
  )

export const useEndMeeting = (teamId: string) =>
  useMeetingCommand(teamId, (meetingId: string) =>
    api<MeetingState>(`${base(teamId)}/${meetingId}/end`, { method: "POST" })
  )

export const useRateMeeting = (teamId: string) =>
  useMeetingCommand(teamId, (v: { meetingId: string; rating: number }) =>
    api<MeetingState>(`${base(teamId)}/${v.meetingId}/rating`, {
      method: "PUT",
      json: { rating: v.rating },
    })
  )
