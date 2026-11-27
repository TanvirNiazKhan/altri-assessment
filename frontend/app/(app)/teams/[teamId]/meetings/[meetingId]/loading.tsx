import { Skeleton } from "@/components/ui/skeleton"

export default function Loading() {
  return (
    <main
      className="mx-auto flex w-full max-w-[1400px] flex-col gap-6 px-4 pt-8 sm:px-6"
      aria-busy
      aria-label="Loading the meeting"
    >
      <Skeleton className="h-12 w-72" />
      <Skeleton className="h-3 w-full" />
      <Skeleton className="h-28 w-64" />
      <Skeleton className="h-64 w-full" />
    </main>
  )
}
