"use client"

import { useState } from "react"
import { CircleCheckBigIcon, InboxIcon, TriangleAlertIcon } from "lucide-react"
import { toast } from "sonner"

import {
  Empty,
  EmptyDescription,
  EmptyHeader,
  EmptyMedia,
  EmptyTitle,
} from "@/components/ui/empty"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { ListSkeleton, LoadError } from "@/components/list-states"
import { SectionHeading } from "@/components/section-heading"
import { errorMessage } from "@/lib/api/errors"
import type { Issue } from "@/lib/api/types"
import { formatInstant, formatWeek } from "@/lib/format"
import { cn } from "@/lib/utils"
import { useIssues, useSetPriority } from "@/features/team/queries"
import { useTeam } from "@/features/team/team-context"
import { AddTodoDialog } from "./add-todo-dialog"
import { CreateIssueForm } from "./create-issue-form"
import { PrioritySelect, priorityLabel } from "./priority-select"
import { SolveDialog } from "./solve-dialog"

/**
 * The Issues list, used on the Team page and in IDS. Open Issues are numbered because
 * order is the point: priority 5 first, oldest first within a priority, unprioritized last.
 */
export function IssuesPanel({
  initialOpen,
  headingLevel = "h2",
}: {
  initialOpen?: Issue[]
  headingLevel?: "h2" | "h3"
}) {
  const { teamId, canWrite } = useTeam()
  const [tab, setTab] = useState<"open" | "solved">("open")
  const open = useIssues(teamId, "open", initialOpen)

  return (
    <section aria-labelledby="issues-title" className="flex flex-col gap-4">
      <SectionHeading
        id="issues-title"
        as={headingLevel}
        title="Issues"
        count={open.data?.length}
      />
      {canWrite ? <CreateIssueForm /> : null}
      <Tabs
        value={tab}
        onValueChange={(v) => setTab(v as "open" | "solved")}
        className="gap-3"
      >
        <TabsList>
          <TabsTrigger value="open">In Issue order</TabsTrigger>
          <TabsTrigger value="solved">Solved</TabsTrigger>
        </TabsList>
        <TabsContent value="open">
          {open.isError ? (
            <LoadError onRetry={() => open.refetch()} error={open.error} />
          ) : !open.data ? (
            <ListSkeleton />
          ) : open.data.length === 0 ? (
            <Empty className="flex-none border border-dashed py-10">
              <EmptyHeader>
                <EmptyMedia variant="icon">
                  <CircleCheckBigIcon />
                </EmptyMedia>
                <EmptyTitle>Nothing in the way</EmptyTitle>
                <EmptyDescription>
                  {canWrite
                    ? "No open Issues. Add one above, or raise one from an off-track score."
                    : "No open Issues right now."}
                </EmptyDescription>
              </EmptyHeader>
            </Empty>
          ) : (
            <ol className="flex flex-col">
              {open.data.map((issue, i) => (
                <OpenIssueRow key={issue.id} issue={issue} rank={i + 1} />
              ))}
            </ol>
          )}
        </TabsContent>
        <TabsContent value="solved">
          {tab === "solved" ? <SolvedList /> : null}
        </TabsContent>
      </Tabs>
    </section>
  )
}

function OpenIssueRow({ issue, rank }: { issue: Issue; rank: number }) {
  const { teamId, canWrite, calendar } = useTeam()
  const setPriority = useSetPriority(teamId)

  return (
    <li
      id={`issue-${issue.id}`}
      className="grid scroll-mt-20 grid-cols-[2.25rem_1fr] gap-x-3 border-b py-3 last:border-b-0 sm:grid-cols-[2.5rem_1fr_auto]"
    >
      <span
        aria-hidden
        className="type-display type-numeric pt-0.5 text-right text-3xl text-muted-foreground"
      >
        {rank}
      </span>
      <div className="flex min-w-0 flex-col gap-1">
        <p className="font-semibold text-pretty">
          <span className="sr-only">{rank}. </span>
          {issue.title}
        </p>
        <p className="flex flex-wrap gap-x-3 gap-y-0.5 text-sm text-muted-foreground">
          <span>{issue.owner.name}</span>
          <span>
            Raised {formatInstant(issue.created_at, calendar.timezone)}
          </span>
          {issue.source?.type === "measurable" && issue.source.week_start ? (
            <span className="inline-flex items-center gap-1 text-off-track-ink">
              <TriangleAlertIcon aria-hidden className="size-3.5" />
              {issue.source.measurable_name}, week of{" "}
              {formatWeek(issue.source.week_start)}
            </span>
          ) : null}
        </p>
      </div>
      <div className="col-start-2 mt-2 flex flex-wrap items-center gap-1.5 sm:col-start-3 sm:row-start-1 sm:mt-0 sm:justify-end">
        {canWrite ? (
          <>
            <PrioritySelect
              compact
              value={issue.priority}
              disabled={setPriority.isPending}
              aria-label={`Priority for ${issue.title}`}
              className={cn(
                issue.priority === 5 && "border-foreground font-bold"
              )}
              onChange={(p) =>
                setPriority.mutate(
                  { issueId: issue.id, priority: p },
                  { onError: (e) => toast.error(errorMessage(e)) }
                )
              }
            />
            <AddTodoDialog issue={issue} />
            <SolveDialog issue={issue} />
          </>
        ) : (
          <span className="text-sm text-muted-foreground">
            {priorityLabel(issue.priority)}
          </span>
        )}
      </div>
    </li>
  )
}

function SolvedList() {
  const { teamId, calendar } = useTeam()
  const solved = useIssues(teamId, "solved")

  if (solved.isError)
    return <LoadError onRetry={() => solved.refetch()} error={solved.error} />
  if (!solved.data) return <ListSkeleton />
  if (solved.data.length === 0) {
    return (
      <Empty className="flex-none border border-dashed py-10">
        <EmptyHeader>
          <EmptyMedia variant="icon">
            <InboxIcon />
          </EmptyMedia>
          <EmptyTitle>No solved Issues yet</EmptyTitle>
          <EmptyDescription>
            Solved Issues and their resolutions collect here.
          </EmptyDescription>
        </EmptyHeader>
      </Empty>
    )
  }
  return (
    <ul className="flex flex-col">
      {solved.data.map((issue) => (
        <li
          key={issue.id}
          className="flex flex-col gap-1 border-b py-3 last:border-b-0"
        >
          <p className="font-semibold text-pretty">{issue.title}</p>
          {issue.resolution_note ? (
            <p className="border-l-2 border-on-track pl-3 text-sm text-pretty">
              {issue.resolution_note}
            </p>
          ) : null}
          <p className="text-sm text-muted-foreground">
            Solved{" "}
            {issue.solved_at
              ? formatInstant(issue.solved_at, calendar.timezone)
              : ""}
            , raised by {issue.owner.name}
          </p>
        </li>
      ))}
    </ul>
  )
}
