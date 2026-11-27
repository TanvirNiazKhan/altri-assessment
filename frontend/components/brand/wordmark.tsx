import Link from "next/link"

import { cn } from "@/lib/utils"

/** A signage plate: "10" on lake blue, then the product name. */
export function Wordmark({
  className,
  href = "/",
}: {
  className?: string
  href?: string
}) {
  return (
    <Link
      href={href}
      className={cn(
        "inline-flex items-center gap-2 rounded-md outline-none focus-visible:ring-3 focus-visible:ring-ring/50",
        className
      )}
      aria-label="Level 10, home"
    >
      <span
        aria-hidden
        className="type-display grid h-8 min-w-8 place-items-center rounded-sm bg-primary px-1 text-xl text-primary-foreground"
      >
        10
      </span>
      <span className="type-display hidden text-xl sm:inline">Level 10</span>
    </Link>
  )
}
