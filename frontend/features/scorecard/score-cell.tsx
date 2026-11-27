"use client"

import { useState } from "react"
import { CircleAlertIcon, FlagIcon } from "lucide-react"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import {
  Field,
  FieldDescription,
  FieldError,
  FieldLabel,
} from "@/components/ui/field"
import { Input } from "@/components/ui/input"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"
import { Separator } from "@/components/ui/separator"
import { Spinner } from "@/components/ui/spinner"
import { StatusMark } from "@/components/status-mark"
import { errorMessage } from "@/lib/api/errors"
import type { ScoreCell as Cell, ScorecardRow } from "@/lib/api/types"
import {
  formatNumber,
  formatValue,
  formatWeek,
  goalDescription,
} from "@/lib/format"
import { MEASURABLE_STATUS } from "@/lib/status"
import { cn } from "@/lib/utils"
import { useMakeIssue, useSetScore } from "@/features/team/queries"
import { useTeam } from "@/features/team/team-context"

const NUMBER = /^-?\d+(\.\d{1,4})?$/

export function ScoreCell({
  row,
  cell,
  isCurrentWeek,
}: {
  row: ScorecardRow
  cell: Cell
  isCurrentWeek: boolean
}) {
  const [open, setOpen] = useState(false)
  const status = MEASURABLE_STATUS[cell.status]
  const label = `${row.name}, week of ${formatWeek(cell.week_start)}: ${
    cell.value === null ? "no score" : formatValue(cell.value, row.unit)
  }, ${status.label.toLowerCase()}${cell.open_issue_id ? ", Issue open" : ""}`

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <button
          type="button"
          aria-label={label}
          data-status={cell.status}
          className={cn(
            "type-numeric relative flex h-10 w-full min-w-14 items-center justify-center rounded-sm text-sm outline-none",
            "transition-[box-shadow] hover:ring-2 hover:ring-foreground/25 focus-visible:ring-3 focus-visible:ring-ring",
            "data-[state=open]:ring-2 data-[state=open]:ring-foreground",
            status.cell
          )}
        >
          {cell.value === null ? (
            <span aria-hidden>{isCurrentWeek ? "" : "—"}</span>
          ) : (
            formatNumber(cell.value)
          )}
          {cell.status === "off_track" ? (
            // Corner notch: off-track reads at a glance even without color.
            <span
              aria-hidden
              className="absolute top-0 right-0 size-0 border-t-[9px] border-l-[9px] border-t-off-track border-l-transparent"
            />
          ) : null}
          {cell.open_issue_id ? (
            <FlagIcon
              aria-hidden
              className="absolute bottom-0.5 left-0.5 size-3 fill-current"
            />
          ) : null}
        </button>
      </PopoverTrigger>
      <PopoverContent className="w-72" align="center" collisionPadding={12}>
        <ScoreEditor row={row} cell={cell} onDone={() => setOpen(false)} />
      </PopoverContent>
    </Popover>
  )
}

function ScoreEditor({
  row,
  cell,
  onDone,
}: {
  row: ScorecardRow
  cell: Cell
  onDone: () => void
}) {
  const { teamId, canWrite } = useTeam()
  const setScore = useSetScore(teamId)
  const makeIssue = useMakeIssue(teamId)
  const [draft, setDraft] = useState(
    cell.value === null ? "" : String(cell.value)
  )
  const [touched, setTouched] = useState(false)
  const status = MEASURABLE_STATUS[cell.status]

  const trimmed = draft.trim().replace(/,/g, "")
  const invalid = trimmed !== "" && !NUMBER.test(trimmed)
  const inputId = `score-${row.id}-${cell.week_start}`

  function save(value: number | null) {
    setScore.mutate(
      { measurableId: row.id, week: cell.week_start, value },
      {
        onSuccess: () =>
          toast.success(value === null ? "Score cleared" : "Score saved"),
        onError: (e) => toast.error(errorMessage(e)),
      }
    )
    onDone()
  }

  function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    setTouched(true)
    if (invalid) return
    const value = trimmed === "" ? null : Number(trimmed)
    if (value === cell.value) return onDone()
    save(value)
  }

  function raise() {
    makeIssue.mutate(
      { measurableId: row.id, week: cell.week_start },
      {
        onSuccess: ({ issue, created }) => {
          toast.success(
            created
              ? "Issue added to the list"
              : "This already has an open Issue",
            {
              description: issue.title,
            }
          )
          onDone()
        },
        onError: (e) => toast.error(errorMessage(e)),
      }
    )
  }

  return (
    <div className="flex flex-col gap-3">
      <div className="flex flex-col gap-0.5">
        <p className="font-semibold">{row.name}</p>
        <p className="text-sm text-muted-foreground">
          Week of {formatWeek(cell.week_start)}.{" "}
          {goalDescription(row.goal, row.unit)}.
        </p>
        <p className="mt-1 flex items-center gap-1.5 text-sm font-semibold">
          <StatusMark status={cell.status} />
          {status.label}
        </p>
      </div>

      {canWrite ? (
        <form onSubmit={onSubmit} className="flex flex-col gap-3" noValidate>
          <Field data-invalid={touched && invalid ? true : undefined}>
            <FieldLabel htmlFor={inputId}>
              Score{row.unit && row.unit !== "count" ? ` (${row.unit})` : ""}
            </FieldLabel>
            <Input
              id={inputId}
              autoFocus
              inputMode="decimal"
              autoComplete="off"
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              aria-invalid={touched && invalid ? true : undefined}
              className="type-numeric text-base"
              placeholder="No score"
            />
            {touched && invalid ? (
              <FieldError>Enter a number, up to 4 decimal places.</FieldError>
            ) : (
              <FieldDescription>
                Leave empty to clear. Last save wins.
              </FieldDescription>
            )}
          </Field>
          <div className="flex gap-2">
            <Button type="submit" className="flex-1">
              Save score
            </Button>
            <Button type="button" variant="outline" onClick={onDone}>
              Cancel
            </Button>
          </div>
        </form>
      ) : (
        <p className="text-sm text-muted-foreground">
          Score:{" "}
          <span className="type-numeric font-semibold text-foreground">
            {formatValue(cell.value, row.unit)}
          </span>
        </p>
      )}

      {cell.status === "off_track" ? (
        <>
          <Separator />
          {cell.open_issue_id ? (
            <p className="flex items-start gap-2 text-sm">
              <FlagIcon
                aria-hidden
                className="mt-0.5 size-4 shrink-0 fill-current text-off-track"
              />
              An open Issue tracks this week. Solve it from the Issues list.
            </p>
          ) : canWrite ? (
            <Button
              variant="secondary"
              onClick={raise}
              disabled={makeIssue.isPending}
            >
              {makeIssue.isPending ? (
                <Spinner data-icon="inline-start" />
              ) : (
                <CircleAlertIcon data-icon="inline-start" />
              )}
              Make it an Issue
            </Button>
          ) : (
            <p className="text-sm text-muted-foreground">
              Off track with no Issue yet.
            </p>
          )}
        </>
      ) : null}
    </div>
  )
}
