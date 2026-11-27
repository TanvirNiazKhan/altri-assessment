import type { Metadata } from "next"

import { MeetingRoom } from "@/features/meeting/meeting-room"
import {
  getMeeting,
  getMeetingSummary,
  getOpenIssues,
  getScorecard,
  getTodos,
} from "@/lib/api/server"

export const metadata: Metadata = { title: "Level 10 Meeting" }

export default async function MeetingPage({
  params,
}: PageProps<"/teams/[teamId]/meetings/[meetingId]">) {
  const { teamId, meetingId } = await params
  const state = await getMeeting(teamId, meetingId)

  // Ended: only the frozen summary is needed. Running: everything the sections show,
  // fetched in parallel so switching sections never waits.
  if (state.meeting?.ended_at) {
    const summary = await getMeetingSummary(teamId, meetingId)
    return (
      <MeetingRoom
        meetingId={meetingId}
        initialState={state}
        initialSummary={summary}
      />
    )
  }
  const [scorecard, openIssues, todos] = await Promise.all([
    getScorecard(teamId),
    getOpenIssues(teamId),
    getTodos(teamId),
  ])
  return (
    <MeetingRoom
      meetingId={meetingId}
      initialState={state}
      scorecard={scorecard}
      openIssues={openIssues}
      todos={todos}
    />
  )
}
