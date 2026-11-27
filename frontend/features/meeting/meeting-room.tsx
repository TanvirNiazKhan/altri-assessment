"use client"

import { useEffect, useRef } from "react"
import { toast } from "sonner"

import type {
  Issue,
  MeetingState,
  MeetingSummary,
  Scorecard,
  TodoList,
} from "@/lib/api/types"
import { errorMessage } from "@/lib/api/errors"
import { SECTION_LABEL, formatTime } from "@/lib/format"
import { syncServerClock } from "@/lib/server-clock"
import { IssuesPanel } from "@/features/issues/issues-panel"
import { ScorecardBoard } from "@/features/scorecard/scorecard-board"
import { TodosPanel } from "@/features/todos/todos-panel"
import { useTeam } from "@/features/team/team-context"
import { AgendaTrack, SectionClock } from "./agenda-clock"
import { AttendeesList } from "./attendees-list"
import { MeetingControls } from "./meeting-controls"
import { MeetingSummaryView } from "./meeting-summary"
import { OffTrackReview } from "./off-track-review"
import { useJoinMeeting, useMeeting } from "./queries"
import { RatingPanel } from "./rating-panel"

export function MeetingRoom({
  meetingId,
  initialState,
  initialSummary,
  scorecard,
  openIssues,
  todos,
}: {
  meetingId: string
  initialState: MeetingState
  initialSummary?: MeetingSummary
  scorecard?: Scorecard
  openIssues?: Issue[]
  todos?: TodoList
}) {
  const { teamId, user, calendar } = useTeam()
  const { data } = useMeeting(teamId, meetingId, initialState)
  const join = useJoinMeeting(teamId)
  const meeting = data?.meeting
  const active = meeting && !meeting.ended_at

  // Server time first, so the clock is right on the first tick.
  useEffect(
    () => syncServerClock(initialState.server_now),
    [initialState.server_now]
  )

  // Opening the page while the meeting runs is attendance (Observers too). Idempotent.
  const joined = useRef(false)
  useEffect(() => {
    if (!active || joined.current) return
    joined.current = true
    join.mutate(meetingId, { onError: (e) => toast.error(errorMessage(e)) })
  }, [active, join, meetingId])

  // Announce section changes to screen readers, not every tick of the clock.
  const section = meeting?.current_section

  if (!meeting) return null
  if (meeting.ended_at) {
    return (
      <main className="mx-auto w-full max-w-[1400px] px-4 pt-8 pb-24 sm:px-6 sm:pt-10">
        <MeetingSummaryView
          meetingId={meeting.id}
          initialData={initialSummary}
        />
      </main>
    )
  }

  return (
    <main className="mx-auto flex w-full max-w-[1400px] flex-col gap-8 px-4 pt-6 pb-24 sm:px-6 sm:pt-8">
      <p className="sr-only" aria-live="polite">
        Now in {section ? SECTION_LABEL[section] : ""}.
      </p>

      <header className="flex flex-col gap-6">
        <div className="flex flex-wrap items-baseline justify-between gap-x-6 gap-y-1">
          <h1 className="type-display text-4xl sm:text-5xl">
            Level 10 Meeting
          </h1>
          <p className="text-sm text-muted-foreground">
            Started {formatTime(meeting.started_at, calendar.timezone)} by{" "}
            {meeting.facilitator.name}
          </p>
        </div>
        <AgendaTrack meeting={meeting} />
        <div className="flex flex-col gap-6 md:flex-row md:items-end md:justify-between">
          <SectionClock meeting={meeting} />
          <MeetingControls meeting={meeting} />
        </div>
      </header>

      <div className="grid gap-10 lg:grid-cols-[1fr_16rem] lg:gap-12">
        <div
          className="flex min-w-0 flex-col gap-8"
          key={meeting.current_section}
        >
          {meeting.current_section === "scorecard" ? (
            <>
              <section
                aria-labelledby="m-scorecard"
                className="flex flex-col gap-4"
              >
                <h2 id="m-scorecard" className="sr-only">
                  Scorecard
                </h2>
                <OffTrackReview week={calendar.last_closed_week} />
                <ScorecardBoard
                  initialData={scorecard}
                  focusWeek={calendar.last_closed_week}
                />
              </section>
            </>
          ) : meeting.current_section === "ids" ? (
            <div className="grid gap-10 xl:grid-cols-[1fr_22rem]">
              <IssuesPanel initialOpen={openIssues} />
              <TodosPanel
                initialData={todos}
                title="New To-Dos"
                showCompletion={false}
                filter={(t) => t.created_in_meeting_id === meeting.id}
                emptyText="To-Dos added from Issues during this meeting show here."
              />
            </div>
          ) : (
            <div className="grid gap-10 xl:grid-cols-2">
              <TodosPanel
                initialData={todos}
                title="New To-Dos"
                showCompletion={false}
                filter={(t) => t.created_in_meeting_id === meeting.id}
                emptyText="No To-Dos were added in this meeting."
              />
              <RatingPanel meeting={meeting} />
            </div>
          )}
        </div>
        <aside className="lg:border-l lg:pl-8">
          <AttendeesList meeting={meeting} currentUserId={user.id} />
        </aside>
      </div>
    </main>
  )
}
