"use client"

import { CircleAlertIcon, FlagIcon } from "lucide-react"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import { Spinner } from "@/components/ui/spinner"
import { StatusMark } from "@/components/status-mark"
import { errorMessage } from "@/lib/api/errors"
import { formatValue, formatWeek, goalDescription } from "@/lib/format"
import { useMakeIssue, useScorecard } from "@/features/team/queries"
import { useTeam } from "@/features/team/team-context"

/**
 * The Scorecard section's job in one list: what was off track last week, with
 * Make it an Issue one tap away. Reads the same cache as the grid above it.
 */
export function OffTrackReview({ week }: { week: string }) {
  const { teamId, canWrite } = useTeam()
  const { data } = useScorecard(teamId)
  const makeIssue = useMakeIssue(teamId)

  const off = (data?.rows ?? []).flatMap((row) => {
    const cell = row.cells.find((c) => c.week_start === week)
    return cell && cell.status === "off_track" ? [{ row, cell }] : []
  })

  return (
    <section
      aria-labelledby="off-track-title"
      className="flex flex-col gap-3 rounded-md bg-off-track-soft/60 p-4"
    >
      <h3 id="off-track-title" className="type-display text-2xl">
        Off track in the week of {formatWeek(week)}
      </h3>
      {off.length === 0 ? (
        <p className="flex items-center gap-2 text-sm">
          <StatusMark status="on_track" />
          Everything hit its goal. Move on to IDS.
        </p>
      ) : (
        <ul className="flex flex-col">
          {off.map(({ row, cell }) => {
            const pending =
              makeIssue.isPending &&
              makeIssue.variables?.measurableId === row.id
            return (
              <li
                key={row.id}
                className="flex flex-wrap items-center gap-x-3 gap-y-2 border-b border-off-track/20 py-2 last:border-b-0"
              >
                <StatusMark status="off_track" />
                <span className="flex min-w-0 flex-1 flex-col">
                  <span className="font-semibold">{row.name}</span>
                  <span className="text-sm text-muted-foreground">
                    {cell.value === null
                      ? "No score"
                      : formatValue(cell.value, row.unit)}{" "}
                    against a goal of{" "}
                    {goalDescription(row.goal, row.unit).replace("Goal: ", "")},{" "}
                    {row.owner.name}
                  </span>
                </span>
                {cell.open_issue_id ? (
                  <span className="inline-flex items-center gap-1.5 text-sm font-semibold text-off-track-ink">
                    <FlagIcon aria-hidden className="size-3.5 fill-current" />
                    On the Issues list
                  </span>
                ) : canWrite ? (
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={pending}
                    onClick={() =>
                      makeIssue.mutate(
                        { measurableId: row.id, week },
                        {
                          onSuccess: ({ created }) =>
                            toast.success(
                              created
                                ? "Issue added to the list"
                                : "This already has an open Issue"
                            ),
                          onError: (e) => toast.error(errorMessage(e)),
                        }
                      )
                    }
                  >
                    {pending ? (
                      <Spinner data-icon="inline-start" />
                    ) : (
                      <CircleAlertIcon data-icon="inline-start" />
                    )}
                    Make it an Issue
                  </Button>
                ) : null}
              </li>
            )
          })}
        </ul>
      )}
    </section>
  )
}
