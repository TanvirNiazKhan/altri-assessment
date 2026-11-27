import { CheckIcon, ChevronDownIcon, MountainIcon } from "lucide-react"

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
import { SectionHeading } from "@/components/section-heading"
import { StatusMark } from "@/components/status-mark"
import type { Rock } from "@/lib/api/types"
import { formatDay } from "@/lib/format"
import { ROCK_STATUS } from "@/lib/status"
import { cn } from "@/lib/utils"

/** Read-only and never changed by anyone in the app, so this stays a Server Component. */
export function RocksPanel({
  rocks,
  quarter,
  today,
}: {
  rocks: Rock[]
  quarter: string
  today: string
}) {
  const [year, q] = quarter.split("-")
  return (
    <section aria-labelledby="rocks-title" className="flex flex-col gap-4">
      <SectionHeading
        id="rocks-title"
        title="Rocks"
        count={rocks.length}
        description={`${q} ${year} priorities`}
      />
      {rocks.length === 0 ? (
        <Empty className="border border-dashed py-8">
          <EmptyHeader>
            <EmptyMedia variant="icon">
              <MountainIcon />
            </EmptyMedia>
            <EmptyTitle>No Rocks this quarter</EmptyTitle>
            <EmptyDescription>
              Rocks come from the seed data for the current quarter.
            </EmptyDescription>
          </EmptyHeader>
        </Empty>
      ) : (
        <ul className="flex flex-col">
          {rocks.map((rock) => (
            <RockRow key={rock.id} rock={rock} today={today} />
          ))}
        </ul>
      )}
    </section>
  )
}

function RockRow({ rock, today }: { rock: Rock; today: string }) {
  const s = ROCK_STATUS[rock.status]
  const done = rock.milestones.filter((m) => m.done).length
  return (
    <li className="border-b last:border-b-0">
      <Collapsible>
        <CollapsibleTrigger className="group flex w-full flex-col gap-2 rounded-sm py-3 text-left outline-none focus-visible:ring-3 focus-visible:ring-ring/50">
          <span className="flex w-full items-start gap-3">
            <span className="flex min-w-0 flex-1 flex-col gap-0.5">
              <span className="font-semibold text-pretty">{rock.title}</span>
              <span className="flex flex-wrap gap-x-3 text-sm text-muted-foreground">
                <span>{rock.owner.name}</span>
                <span
                  className={cn(
                    "inline-flex items-center gap-1.5 font-semibold",
                    s.text
                  )}
                >
                  <StatusMark status={rock.status} />
                  {s.label}
                </span>
              </span>
            </span>
            <span className="type-display type-numeric text-2xl">
              {rock.progress_percent}%
            </span>
            <ChevronDownIcon
              aria-hidden
              className="mt-1.5 size-4 shrink-0 text-muted-foreground transition-transform group-data-[state=open]:rotate-180"
            />
          </span>
          <span
            role="progressbar"
            aria-label={`${rock.title} progress`}
            aria-valuemin={0}
            aria-valuemax={100}
            aria-valuenow={rock.progress_percent}
            className="block h-1.5 w-full rounded-full bg-muted"
          >
            <span
              className={cn("block h-full rounded-full", s.bar)}
              style={{ width: `${rock.progress_percent}%` }}
            />
          </span>
          <span className="text-xs text-muted-foreground">
            {rock.milestones.length === 0
              ? "No Milestones"
              : `${done} of ${rock.milestones.length} Milestones done`}
          </span>
        </CollapsibleTrigger>
        <CollapsibleContent>
          {rock.milestones.length > 0 ? (
            <ol className="mb-3 flex flex-col gap-1.5 border-l-2 pl-4">
              {rock.milestones.map((m) => {
                const pastDue = !m.done && m.due_date < today
                return (
                  <li key={m.id} className="flex items-start gap-2 text-sm">
                    <span
                      aria-hidden
                      className={cn(
                        "mt-0.5 grid size-4 shrink-0 place-items-center rounded-sm border",
                        m.done &&
                          "border-primary bg-primary text-primary-foreground"
                      )}
                    >
                      {m.done ? <CheckIcon className="size-3" /> : null}
                    </span>
                    <span
                      className={cn(
                        "flex-1",
                        m.done && "text-muted-foreground"
                      )}
                    >
                      {m.title}
                      <span className="sr-only">
                        {m.done ? ", done" : ", not done"}
                      </span>
                    </span>
                    <span
                      className={cn(
                        "type-numeric shrink-0",
                        pastDue
                          ? "font-semibold text-off-track-ink"
                          : "text-muted-foreground"
                      )}
                    >
                      {pastDue
                        ? `Past due ${formatDay(m.due_date)}`
                        : formatDay(m.due_date)}
                    </span>
                  </li>
                )
              })}
            </ol>
          ) : null}
        </CollapsibleContent>
      </Collapsible>
    </li>
  )
}
