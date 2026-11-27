import { PanelSkeleton, ScorecardSkeleton } from "./skeletons"
import { Skeleton } from "@/components/ui/skeleton"

export default function Loading() {
  return (
    <main
      className="mx-auto flex w-full max-w-[1400px] flex-col gap-12 px-4 pt-8 pb-24 sm:px-6 sm:pt-10"
      aria-busy
      aria-label="Loading the team"
    >
      <div className="flex flex-col gap-3">
        <Skeleton className="h-16 w-64" />
        <Skeleton className="h-4 w-48" />
      </div>
      <ScorecardSkeleton />
      <div className="grid gap-12 lg:grid-cols-12 lg:gap-10">
        <div className="lg:col-span-7">
          <PanelSkeleton title="Issues" />
        </div>
        <div className="lg:col-span-5">
          <PanelSkeleton title="To-Dos" />
        </div>
      </div>
    </main>
  )
}
