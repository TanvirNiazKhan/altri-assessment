import { cn } from "@/lib/utils"

/**
 * Sections sit directly on the page (no card chrome): a heavy signage title over a
 * rule, an optional count, and actions on the right.
 */
export function SectionHeading({
  id,
  title,
  count,
  description,
  actions,
  className,
  as: Tag = "h2",
}: {
  id?: string
  title: string
  count?: number
  description?: React.ReactNode
  actions?: React.ReactNode
  className?: string
  as?: "h2" | "h3"
}) {
  return (
    <div
      className={cn(
        "flex flex-wrap items-end gap-x-4 gap-y-2 border-b-2 border-foreground pb-2",
        className
      )}
    >
      <div className="flex min-w-0 flex-1 flex-col gap-1">
        <Tag
          id={id}
          className="type-display flex items-baseline gap-2 text-3xl sm:text-4xl"
        >
          {title}
          {count !== undefined ? (
            <span className="type-numeric font-sans text-base font-semibold text-muted-foreground">
              {count}
              <span className="sr-only"> items</span>
            </span>
          ) : null}
        </Tag>
        {description ? (
          <p className="text-sm text-muted-foreground">{description}</p>
        ) : null}
      </div>
      {actions ? (
        <div className="flex shrink-0 items-center gap-2">{actions}</div>
      ) : null}
    </div>
  )
}
