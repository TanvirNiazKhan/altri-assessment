import { Skeleton } from "@/components/ui/skeleton"
import { ListSkeleton } from "@/components/list-states"
import { SectionHeading } from "@/components/section-heading"

export function ScorecardSkeleton() {
  return (
    <div
      className="flex flex-col gap-1.5"
      aria-busy
      aria-label="Loading the Scorecard"
    >
      {Array.from({ length: 4 }, (_, r) => (
        <div key={r} className="flex gap-1">
          <Skeleton className="h-10 w-44 shrink-0 sm:w-60" />
          <div className="flex flex-1 gap-1 overflow-hidden">
            {Array.from({ length: 13 }, (_, c) => (
              <Skeleton key={c} className="h-10 min-w-14 flex-1" />
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}

export function PanelSkeleton({ title }: { title: string }) {
  return (
    <div className="flex flex-col gap-4">
      <SectionHeading title={title} />
      <ListSkeleton />
    </div>
  )
}
