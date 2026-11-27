import type { MeasurableStatus, RockStatus } from "@/lib/api/types"
import { cn } from "@/lib/utils"

/**
 * Shape + color, so status survives color blindness and grayscale printing:
 * on track = filled circle, off track = triangle, pending = open ring, complete = check disc.
 */
export function StatusMark({
  status,
  className,
}: {
  status: MeasurableStatus | RockStatus
  className?: string
}) {
  const base = cn("inline-block size-2.5 shrink-0", className)
  switch (status) {
    case "on_track":
      return (
        <svg
          aria-hidden
          viewBox="0 0 10 10"
          className={cn(base, "fill-on-track")}
        >
          <circle cx="5" cy="5" r="5" />
        </svg>
      )
    case "off_track":
      return (
        <svg
          aria-hidden
          viewBox="0 0 10 10"
          className={cn(base, "fill-off-track")}
        >
          <path d="M5 0.5 10 9.5H0z" />
        </svg>
      )
    case "pending":
      return (
        <svg
          aria-hidden
          viewBox="0 0 10 10"
          className={cn(base, "fill-none stroke-pending")}
        >
          <circle cx="5" cy="5" r="4" strokeWidth="2" />
        </svg>
      )
    case "complete":
      return (
        <svg
          aria-hidden
          viewBox="0 0 10 10"
          className={cn(base, "fill-primary")}
        >
          <circle cx="5" cy="5" r="5" />
          <path
            d="M2.6 5.2 4.3 6.8 7.4 3.6"
            className="fill-none stroke-primary-foreground"
            strokeWidth="1.4"
          />
        </svg>
      )
  }
}
