"use client"

import { useEffect, useRef } from "react"
import { BarChart3Icon } from "lucide-react"

import {
  Empty,
  EmptyDescription,
  EmptyHeader,
  EmptyMedia,
  EmptyTitle,
} from "@/components/ui/empty"
import { StatusMark } from "@/components/status-mark"
import type { Scorecard } from "@/lib/api/types"
import { formatGoal, formatWeek } from "@/lib/format"
import { cn } from "@/lib/utils"
import { useScorecard } from "@/features/team/queries"
import { useTeam } from "@/features/team/team-context"
import { ScoreCell } from "./score-cell"

/**
 * 13 weeks × Measurables. The newest week sits on the right (the way the numbers
 * are read: trend into now). On narrow screens the grid scrolls and opens at "now".
 * `focusWeek` frames one column — in the meeting, the last closed week under review.
 */
export function ScorecardBoard({
  initialData,
  focusWeek,
}: {
  initialData?: Scorecard
  focusWeek?: string
}) {
  const { teamId, calendar } = useTeam()
  const { data } = useScorecard(teamId, initialData)
  const scroller = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const el = scroller.current
    if (el) el.scrollLeft = el.scrollWidth
  }, [])

  if (!data || data.rows.length === 0) {
    return (
      <Empty className="border py-10">
        <EmptyHeader>
          <EmptyMedia variant="icon">
            <BarChart3Icon />
          </EmptyMedia>
          <EmptyTitle>No Measurables yet</EmptyTitle>
          <EmptyDescription>
            This team&apos;s Measurables come from the seed data. Once they
            exist, weekly scores show here.
          </EmptyDescription>
        </EmptyHeader>
      </Empty>
    )
  }

  const lastClosed = calendar.last_closed_week

  return (
    <div className="flex flex-col gap-3">
      <div
        ref={scroller}
        className="relative -mx-4 overflow-x-auto overscroll-x-contain sm:mx-0"
        role="region"
        aria-label="Scorecard, scrolls sideways"
        tabIndex={0}
      >
        <table className="w-full min-w-max border-separate border-spacing-0 text-sm">
          <caption className="sr-only">
            Weekly scores for each Measurable, oldest week first. The current
            week is {formatWeek(data.current_week)}.
          </caption>
          <thead>
            <tr>
              <th
                scope="col"
                className="sticky left-0 z-20 min-w-44 bg-background py-2 pr-3 pl-4 text-left align-bottom font-semibold text-muted-foreground sm:min-w-60 sm:pl-0"
              >
                Measurable
              </th>
              <th
                scope="col"
                className="hidden px-3 py-2 text-left align-bottom font-semibold text-muted-foreground md:table-cell"
              >
                Goal
              </th>
              {data.weeks.map((w) => {
                const isNow = w === data.current_week
                const isFocus = w === focusWeek
                return (
                  <th
                    key={w}
                    scope="col"
                    className={cn(
                      "w-16 px-0.5 py-2 text-center align-bottom font-normal whitespace-nowrap",
                      isNow && "text-now-ink",
                      isFocus && "text-foreground"
                    )}
                  >
                    <span className="flex flex-col items-center leading-tight">
                      <span
                        className={cn(
                          "text-xs text-muted-foreground",
                          (isNow || isFocus || w === lastClosed) &&
                            "font-semibold text-foreground"
                        )}
                      >
                        {isNow
                          ? "This week"
                          : w === lastClosed
                            ? "Last week"
                            : "\u00a0"}
                      </span>
                      <span
                        className={cn(
                          "type-numeric",
                          (isNow || isFocus) && "font-bold"
                        )}
                      >
                        {formatWeek(w)}
                      </span>
                    </span>
                  </th>
                )
              })}
            </tr>
          </thead>
          <tbody>
            {data.rows.map((row) => (
              <tr key={row.id} className="group/row">
                <th
                  scope="row"
                  className="sticky left-0 z-10 border-t bg-background py-2 pr-3 pl-4 text-left align-middle font-normal sm:pl-0"
                >
                  <span className="flex flex-col">
                    <span className="font-semibold text-foreground">
                      {row.name}
                    </span>
                    <span className="text-xs text-muted-foreground">
                      {row.owner.name}
                      <span className="md:hidden">
                        , goal {formatGoal(row.goal, row.unit)}
                      </span>
                    </span>
                  </span>
                </th>
                <td className="type-numeric hidden border-t px-3 py-2 align-middle whitespace-nowrap text-muted-foreground md:table-cell">
                  {formatGoal(row.goal, row.unit)}
                </td>
                {row.cells.map((cell) => (
                  <td
                    key={cell.week_start}
                    className={cn(
                      "border-t p-0.5 align-middle",
                      cell.week_start === data.current_week && "bg-now/35",
                      cell.week_start === focusWeek && "bg-now/60"
                    )}
                  >
                    <ScoreCell
                      row={row}
                      cell={cell}
                      isCurrentWeek={cell.week_start === data.current_week}
                    />
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <Legend />
    </div>
  )
}

function Legend() {
  return (
    <ul
      className="flex flex-wrap gap-x-5 gap-y-1 text-xs text-muted-foreground"
      aria-label="Legend"
    >
      <li className="flex items-center gap-1.5">
        <StatusMark status="on_track" />
        On track: meets the goal, edges included
      </li>
      <li className="flex items-center gap-1.5">
        <StatusMark status="off_track" />
        Off track, or a closed week with no score
      </li>
      <li className="flex items-center gap-1.5">
        <StatusMark status="pending" />
        Pending: this week, no score yet
      </li>
    </ul>
  )
}
