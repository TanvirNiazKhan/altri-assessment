"use client"

import { useId, useState } from "react"
import { ChevronDownIcon, ListChecksIcon } from "lucide-react"
import { toast } from "sonner"

import { Checkbox } from "@/components/ui/checkbox"
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible"
import {
  Empty,
  EmptyDescription,
  EmptyHeader,
  EmptyMedia,
  EmptyTitle,
} from "@/components/ui/empty"
import { Button } from "@/components/ui/button"
import { ListSkeleton, LoadError } from "@/components/list-states"
import { SectionHeading } from "@/components/section-heading"
import { errorMessage } from "@/lib/api/errors"
import type { Todo, TodoList } from "@/lib/api/types"
import { formatDay, formatInstant, formatWeek } from "@/lib/format"
import { cn } from "@/lib/utils"
import { useTodos, useToggleTodo } from "@/features/team/queries"
import { useTeam } from "@/features/team/team-context"

export function TodosPanel({
  initialData,
  filter,
  title = "To-Dos",
  emptyText,
  showCompletion = true,
  headingLevel = "h2",
}: {
  initialData?: TodoList
  /** Narrow the list, e.g. to the To-Dos created in a meeting. */
  filter?: (t: Todo) => boolean
  title?: string
  emptyText?: string
  showCompletion?: boolean
  headingLevel?: "h2" | "h3"
}) {
  const { teamId } = useTeam()
  const query = useTodos(teamId, initialData)
  const items = query.data
    ? filter
      ? query.data.items.filter(filter)
      : query.data.items
    : []

  // Open first by due date (overdue rise to the top), done after, newest first.
  const open = items
    .filter((t) => !t.done_at)
    .toSorted((a, b) => a.due_date.localeCompare(b.due_date))
  const done = items
    .filter((t) => t.done_at)
    .toSorted((a, b) => (b.done_at ?? "").localeCompare(a.done_at ?? ""))

  return (
    <section aria-labelledby={`${title}-title`} className="flex flex-col gap-4">
      <SectionHeading
        id={`${title}-title`}
        as={headingLevel}
        title={title}
        count={query.data ? open.length : undefined}
      />
      {showCompletion && query.data ? (
        <CompletionMeter data={query.data.last_closed_week} />
      ) : null}
      {query.isError ? (
        <LoadError error={query.error} onRetry={() => query.refetch()} />
      ) : !query.data ? (
        <ListSkeleton rows={3} />
      ) : items.length === 0 ? (
        <Empty className="flex-none border border-dashed py-8">
          <EmptyHeader>
            <EmptyMedia variant="icon">
              <ListChecksIcon />
            </EmptyMedia>
            <EmptyTitle>No To-Dos</EmptyTitle>
            <EmptyDescription>
              {emptyText ??
                "Add To-Dos from an Issue. They're due 7 days later."}
            </EmptyDescription>
          </EmptyHeader>
        </Empty>
      ) : (
        <>
          {open.length > 0 ? (
            <ul className="flex flex-col">
              {open.map((t) => (
                <TodoRow key={t.id} todo={t} />
              ))}
            </ul>
          ) : (
            <p className="text-sm text-muted-foreground">All done.</p>
          )}
          {done.length > 0 ? <DoneList todos={done} /> : null}
        </>
      )}
    </section>
  )
}

function DoneList({ todos }: { todos: Todo[] }) {
  const [open, setOpen] = useState(false)
  return (
    <Collapsible open={open} onOpenChange={setOpen}>
      <CollapsibleTrigger asChild>
        <Button
          variant="ghost"
          size="sm"
          className="-ml-2 text-muted-foreground"
        >
          <ChevronDownIcon
            data-icon="inline-start"
            className={cn("transition-transform", open && "rotate-180")}
          />
          {open ? "Hide done" : `Show done (${todos.length})`}
        </Button>
      </CollapsibleTrigger>
      <CollapsibleContent>
        <ul className="flex flex-col">
          {todos.map((t) => (
            <TodoRow key={t.id} todo={t} />
          ))}
        </ul>
      </CollapsibleContent>
    </Collapsible>
  )
}

function TodoRow({ todo }: { todo: Todo }) {
  const { teamId, canWrite, calendar } = useTeam()
  const toggle = useToggleTodo(teamId)
  const id = useId()
  const done = Boolean(todo.done_at)
  const doneAt =
    todo.done_at && !Number.isNaN(Date.parse(todo.done_at))
      ? todo.done_at
      : null

  return (
    <li className="flex items-start gap-3 border-b py-2.5 last:border-b-0">
      <Checkbox
        id={id}
        checked={done}
        disabled={!canWrite}
        className="mt-0.5 size-5"
        aria-describedby={`${id}-meta`}
        onCheckedChange={(c) =>
          toggle.mutate(
            { todoId: todo.id, done: c === true },
            {
              onSuccess: () =>
                toast.success(c === true ? "Marked done" : "Marked not done", {
                  description: todo.title,
                }),
              onError: (e) => toast.error(errorMessage(e)),
            }
          )
        }
      />
      <div className="flex min-w-0 flex-1 flex-col gap-0.5">
        <label
          htmlFor={id}
          className={cn(
            "font-medium text-pretty",
            done && "text-muted-foreground line-through decoration-1"
          )}
        >
          {todo.title}
        </label>
        <p
          id={`${id}-meta`}
          className="flex flex-wrap gap-x-3 text-sm text-muted-foreground"
        >
          <span>{todo.owner.name}</span>
          {done ? (
            <span>
              Done{" "}
              {doneAt ? formatInstant(doneAt, calendar.timezone) : "just now"}
            </span>
          ) : todo.overdue ? (
            <span className="font-semibold text-off-track-ink">
              Overdue, was due {formatDay(todo.due_date)}
            </span>
          ) : (
            <span>Due {formatDay(todo.due_date)}</span>
          )}
          {todo.source_issue ? (
            <span className="truncate">
              From Issue: {todo.source_issue.title}
            </span>
          ) : null}
        </p>
      </div>
    </li>
  )
}

/** Last closed week's completion against the 90% target, as a bar with the target marked. */
function CompletionMeter({ data }: { data: TodoList["last_closed_week"] }) {
  const c = data.completion
  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-baseline justify-between gap-3">
        <p className="text-sm">
          <span className="font-semibold">Last week</span>{" "}
          <span className="text-muted-foreground">
            (week of {formatWeek(data.week_start)}):{" "}
            {c ? `${c.done} of ${c.due} done on time` : "nothing was due"}
          </span>
        </p>
        <p
          className={cn(
            "type-display type-numeric text-3xl",
            c
              ? c.meets_target
                ? "text-on-track-ink"
                : "text-off-track-ink"
              : "text-muted-foreground"
          )}
        >
          {c ? `${c.rate_percent}%` : "—"}
        </p>
      </div>
      <div
        role="meter"
        aria-label="Last week's To-Do completion"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={c?.rate_percent ?? 0}
        aria-valuetext={
          c
            ? `${c.rate_percent}%, ${c.meets_target ? "meets" : "below"} the ${data.target_percent}% target`
            : "No To-Dos were due"
        }
        className="relative h-2 rounded-full bg-muted"
      >
        {c ? (
          <div
            className={cn(
              "h-full rounded-full",
              c.meets_target ? "bg-on-track" : "bg-off-track"
            )}
            style={{ width: `${Math.min(100, c.rate_percent)}%` }}
          />
        ) : null}
        <span
          aria-hidden
          className="absolute -top-1 h-4 w-0.5 bg-foreground"
          style={{ left: `${data.target_percent}%` }}
          title={`Target ${data.target_percent}%`}
        />
      </div>
      <p className="text-xs text-muted-foreground">
        Target {data.target_percent}%. The tick marks it.
      </p>
    </div>
  )
}
