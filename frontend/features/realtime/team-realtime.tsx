"use client"

import { createContext, use, useEffect, useState } from "react"
import { useQueryClient, type QueryClient } from "@tanstack/react-query"

import type { MeetingState, SocketMessage } from "@/lib/api/types"
import { qk } from "@/lib/query-keys"
import { syncServerClock } from "@/lib/server-clock"

export type SocketStatus = "connecting" | "live" | "reconnecting"

const SocketStatusContext = createContext<SocketStatus>("connecting")
export const useSocketStatus = () => use(SocketStatusContext)

const PING_MS = 15_000
const MAX_BACKOFF_MS = 10_000

function socketUrl(teamId: string) {
  const base =
    process.env.NEXT_PUBLIC_WS_URL ??
    `${window.location.protocol === "https:" ? "wss" : "ws"}://${window.location.host}`
  return `${base}/api/ws/teams/${encodeURIComponent(teamId)}`
}

/**
 * Applies a meeting snapshot to the cache. Snapshots carry `state_version`; an older
 * snapshot for the same meeting (reordered delivery) never overwrites a newer one.
 */
export function applyMeetingState(
  client: QueryClient,
  teamId: string,
  state: MeetingState
) {
  syncServerClock(state.server_now)
  const m = state.meeting
  if (!m) {
    client.setQueryData<MeetingState>(qk.activeMeeting(teamId), state)
    return
  }
  const key = qk.meeting(teamId, m.id)
  const current = client.getQueryData<MeetingState>(key)
  if (current?.meeting && current.meeting.state_version > m.state_version)
    return
  client.setQueryData<MeetingState>(key, state)
  client.setQueryData<MeetingState>(
    qk.activeMeeting(teamId),
    m.ended_at ? { meeting: null, server_now: state.server_now } : state
  )
  if (m.ended_at)
    void client.invalidateQueries({ queryKey: qk.summary(teamId, m.id) })
}

/**
 * One socket per team page. The server pushes; commands go over REST.
 * - `meeting.state`: full snapshot (also sent on every (re)connect, so refreshes,
 *   late joins and reconnects recover without extra calls).
 * - `data.changed`: mark those resources stale; TanStack Query refetches what's on screen.
 */
export function TeamRealtime({
  teamId,
  children,
}: {
  teamId: string
  children: React.ReactNode
}) {
  const client = useQueryClient()
  const [status, setStatus] = useState<SocketStatus>("connecting")

  useEffect(() => {
    let socket: WebSocket | null = null
    let ping: ReturnType<typeof setInterval> | undefined
    let retry: ReturnType<typeof setTimeout> | undefined
    let attempt = 0
    let disposed = false

    const connect = () => {
      socket = new WebSocket(socketUrl(teamId))

      socket.onopen = () => {
        attempt = 0
        setStatus("live")
        ping = setInterval(
          () => socket?.readyState === WebSocket.OPEN && socket.send("ping"),
          PING_MS
        )
        // Anything could have changed while we were away.
        void client.invalidateQueries({
          queryKey: qk.team(teamId),
          refetchType: "active",
        })
      }

      socket.onmessage = (event) => {
        let msg: SocketMessage
        try {
          msg = JSON.parse(event.data as string) as SocketMessage
        } catch {
          return
        }
        if (msg.type === "meeting.state")
          applyMeetingState(client, teamId, msg.data)
        else if (msg.type === "pong") syncServerClock(msg.server_now)
        else if (msg.type === "data.changed") {
          for (const r of msg.resources) {
            const key =
              r === "scorecard"
                ? qk.scorecard(teamId)
                : r === "issues"
                  ? qk.issues(teamId)
                  : qk.todos(teamId)
            void client.invalidateQueries({ queryKey: key })
          }
        }
      }

      socket.onclose = () => {
        clearInterval(ping)
        if (disposed) return
        setStatus("reconnecting")
        const delay =
          Math.min(MAX_BACKOFF_MS, 500 * 2 ** attempt++) + Math.random() * 250
        retry = setTimeout(connect, delay)
      }
    }

    connect()
    return () => {
      disposed = true
      clearInterval(ping)
      clearTimeout(retry)
      socket?.close()
    }
  }, [client, teamId])

  return <SocketStatusContext value={status}>{children}</SocketStatusContext>
}
