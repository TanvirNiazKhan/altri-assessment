import { Suspense } from "react"
import type { Metadata } from "next"
import { EyeIcon } from "lucide-react"

import { SectionHeading } from "@/components/section-heading"
import { IssuesPanel } from "@/features/issues/issues-panel"
import { MeetingCallout } from "@/features/meeting/meeting-callout"
import { RocksPanel } from "@/features/rocks/rocks-panel"
import { ScorecardBoard } from "@/features/scorecard/scorecard-board"
import { TodosPanel } from "@/features/todos/todos-panel"
import {
  getMe,
  getOpenIssues,
  getRocks,
  getScorecard,
  getTeam,
  getTodos,
} from "@/lib/api/server"
import { formatWeek } from "@/lib/format"
import { PanelSkeleton, ScorecardSkeleton } from "./skeletons"

export async function generateMetadata({
  params,
}: PageProps<"/teams/[teamId]">): Promise<Metadata> {
  const { teamId } = await params
  const team = await getTeam(teamId)
  return { title: team.name }
}

export default async function TeamPage({
  params,
}: PageProps<"/teams/[teamId]">) {
  const { teamId } = await params
  // Both are cached for this request (the layout already asked).
  const [me, team] = await Promise.all([getMe(), getTeam(teamId)])
  const { calendar } = me
  const [year, q] = calendar.quarter.split("-")

  return (
    <main className="mx-auto flex w-full max-w-[1400px] flex-col gap-12 px-4 pt-8 pb-24 sm:px-6 sm:pt-10">
      <header className="flex flex-col gap-5 md:flex-row md:items-end md:justify-between">
        <div className="flex flex-col gap-2">
          <h1 className="type-display text-6xl sm:text-7xl">{team.name}</h1>
          <p className="text-muted-foreground">
            Week of {formatWeek(calendar.current_week)}, {q} {year}. Times in
            Chicago.
          </p>
        </div>
        <MeetingCallout />
      </header>

      {!team.can_write ? (
        <p className="-mt-6 flex items-center gap-2 rounded-md bg-secondary px-3 py-2 text-sm text-secondary-foreground">
          <EyeIcon aria-hidden className="size-4 shrink-0" />
          You&apos;re an Observer here: you can read everything and join
          meetings, but not change data.
        </p>
      ) : null}

      <section
        aria-labelledby="scorecard-title"
        className="flex flex-col gap-4"
      >
        <SectionHeading
          id="scorecard-title"
          title="Scorecard"
          description={
            team.can_write
              ? "13 weeks, newest on the right. Select a cell to enter a score or raise an Issue."
              : "13 weeks, newest on the right. Select a cell for its goal and status."
          }
        />
        <Suspense fallback={<ScorecardSkeleton />}>
          <ScorecardSection teamId={teamId} />
        </Suspense>
      </section>

      <div className="grid gap-12 lg:grid-cols-12 lg:gap-10">
        <div className="lg:col-span-7">
          <Suspense fallback={<PanelSkeleton title="Issues" />}>
            <IssuesSection teamId={teamId} />
          </Suspense>
        </div>
        <div className="flex flex-col gap-12 lg:col-span-5">
          <Suspense fallback={<PanelSkeleton title="To-Dos" />}>
            <TodosSection teamId={teamId} />
          </Suspense>
          <Suspense fallback={<PanelSkeleton title="Rocks" />}>
            <RocksSection
              teamId={teamId}
              quarter={calendar.quarter}
              today={calendar.today}
            />
          </Suspense>
        </div>
      </div>
    </main>
  )
}

// Each section fetches its own data, so they stream in parallel and one slow list
// doesn't hold up the rest.
async function ScorecardSection({ teamId }: { teamId: string }) {
  return <ScorecardBoard initialData={await getScorecard(teamId)} />
}

async function IssuesSection({ teamId }: { teamId: string }) {
  return <IssuesPanel initialOpen={await getOpenIssues(teamId)} />
}

async function TodosSection({ teamId }: { teamId: string }) {
  return <TodosPanel initialData={await getTodos(teamId)} />
}

async function RocksSection({
  teamId,
  quarter,
  today,
}: {
  teamId: string
  quarter: string
  today: string
}) {
  return (
    <RocksPanel
      rocks={await getRocks(teamId)}
      quarter={quarter}
      today={today}
    />
  )
}
