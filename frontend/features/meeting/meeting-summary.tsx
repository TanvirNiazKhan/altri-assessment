"use client"

import Link from "next/link"
import { ArrowLeftIcon } from "lucide-react"

import { Button } from "@/components/ui/button"
import { ListSkeleton, LoadError } from "@/components/list-states"
import { SectionHeading } from "@/components/section-heading"
import { StatusMark } from "@/components/status-mark"
import type { MeetingSummary } from "@/lib/api/types"
import {
  formatDay,
  formatDayLong,
  formatInstant,
  formatTime,
  formatValue,
  formatWeek,
} from "@/lib/format"
import { MEASURABLE_STATUS } from "@/lib/status"
import { useTeam } from "@/features/team/team-context"
import { useMeetingSummary } from "./queries"

/** The frozen record of an ended meeting. Later edits never change it. */
export function MeetingSummaryView({
  meetingId,
  initialData,
}: {
  meetingId: string
  initialData?: MeetingSummary
}) {
  const { teamId, teamName, calendar } = useTeam()
  const { data, isError, error, refetch } = useMeetingSummary(
    teamId,
    meetingId,
    true,
    initialData
  )
  const tz = calendar.timezone

  if (isError) return <LoadError error={error} onRetry={() => refetch()} />
  if (!data) return <ListSkeleton rows={6} />

  const startDate = new Date(data.started_at).toLocaleDateString("en-CA", {
    timeZone: tz,
  })

  return (
    <article className="flex flex-col gap-12">
      <header className="flex flex-col gap-6 md:flex-row md:items-end md:justify-between">
        <div className="flex flex-col gap-2">
          <p className="text-muted-foreground">
            {teamName} Level 10 Meeting, ended
          </p>
          <h1 className="type-display text-5xl sm:text-6xl">
            {formatDayLong(startDate)}
          </h1>
          <p className="text-muted-foreground">
            {formatTime(data.started_at, tz)} to {formatTime(data.ended_at, tz)}
            , run by {data.facilitator.name}
          </p>
        </div>
        <div className="flex items-end gap-6">
          <p className="flex flex-col">
            <span className="type-display type-numeric text-7xl leading-none">
              {data.average_rating === null
                ? "–"
                : data.average_rating.toFixed(1)}
            </span>
            <span className="text-sm text-muted-foreground">
              {data.average_rating === null
                ? "No one rated"
                : `Rating from ${data.ratings.length} ${data.ratings.length === 1 ? "person" : "people"}`}
            </span>
          </p>
        </div>
      </header>

      <div className="grid gap-12 lg:grid-cols-2 lg:gap-10">
        <section
          aria-labelledby="sum-scorecard"
          className="flex flex-col gap-3"
        >
          <SectionHeading
            id="sum-scorecard"
            title="Scorecard"
            description={`Week of ${formatWeek(data.scorecard_week)}, as reviewed`}
          />
          <ul className="flex flex-col">
            {data.measurables.map((m) => (
              <li
                key={m.id}
                className="flex items-center gap-3 border-b py-2.5 last:border-b-0"
              >
                <StatusMark status={m.status} />
                <span className="flex-1 font-medium">{m.name}</span>
                <span className="type-numeric font-semibold">
                  {formatValue(m.value, m.unit)}
                </span>
                <span className="w-20 text-right text-sm text-muted-foreground">
                  {MEASURABLE_STATUS[m.status].label}
                </span>
              </li>
            ))}
          </ul>
        </section>

        <section aria-labelledby="sum-issues" className="flex flex-col gap-3">
          <SectionHeading
            id="sum-issues"
            title="Issues solved"
            count={data.issues_solved.length}
          />
          {data.issues_solved.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No Issues were solved in this meeting.
            </p>
          ) : (
            <ul className="flex flex-col">
              {data.issues_solved.map((i) => (
                <li
                  key={i.id}
                  className="flex flex-col gap-1 border-b py-2.5 last:border-b-0"
                >
                  <span className="font-semibold">{i.title}</span>
                  {i.resolution_note ? (
                    <span className="border-l-2 border-on-track pl-3 text-sm">
                      {i.resolution_note}
                    </span>
                  ) : null}
                </li>
              ))}
            </ul>
          )}
        </section>

        <section aria-labelledby="sum-todos" className="flex flex-col gap-3">
          <SectionHeading
            id="sum-todos"
            title="New To-Dos"
            count={data.todos_created.length}
          />
          {data.todos_created.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No To-Dos were created in this meeting.
            </p>
          ) : (
            <ul className="flex flex-col">
              {data.todos_created.map((t) => (
                <li
                  key={t.id}
                  className="flex items-baseline gap-3 border-b py-2.5 last:border-b-0"
                >
                  <span className="flex-1 font-medium">{t.title}</span>
                  <span className="text-sm text-muted-foreground">
                    {t.owner.name}
                  </span>
                  <span className="type-numeric text-sm">
                    Due {formatDay(t.due_date)}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section aria-labelledby="sum-people" className="flex flex-col gap-3">
          <SectionHeading
            id="sum-people"
            title="Attendees"
            count={data.attendees.length}
          />
          <ul className="flex flex-col">
            {data.attendees.map((a) => {
              const r = data.ratings.find((x) => x.user.id === a.id)
              return (
                <li
                  key={a.id}
                  className="flex items-baseline justify-between gap-3 border-b py-2.5 last:border-b-0"
                >
                  <span className="font-medium">{a.name}</span>
                  <span className="type-numeric text-sm text-muted-foreground">
                    {r ? (
                      <span className="font-semibold text-foreground">
                        Rated {r.rating}
                      </span>
                    ) : (
                      "No rating"
                    )}
                  </span>
                </li>
              )
            })}
          </ul>
        </section>
      </div>

      <footer className="flex flex-wrap items-center gap-3 border-t pt-6">
        <Button asChild variant="outline" size="lg">
          <Link href={`/teams/${teamId}`}>
            <ArrowLeftIcon data-icon="inline-start" />
            Back to {teamName}
          </Link>
        </Button>
        <p className="text-sm text-muted-foreground">
          Saved {formatInstant(data.ended_at, tz)}. Later edits don&apos;t
          change this summary.
        </p>
      </footer>
    </article>
  )
}
