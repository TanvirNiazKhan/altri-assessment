"use client"

import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { cn } from "@/lib/utils"

const NONE = "none"
export const PRIORITIES = [5, 4, 3, 2, 1] as const

export function priorityLabel(p: number | null) {
  return p === null ? "No priority" : `Priority ${p}`
}

/** Priority 5 is most urgent (sorts first). Null sorts last. */
export function PrioritySelect({
  value,
  onChange,
  disabled,
  id,
  className,
  compact,
  "aria-label": ariaLabel,
}: {
  value: number | null
  onChange: (p: number | null) => void
  disabled?: boolean
  id?: string
  className?: string
  compact?: boolean
  "aria-label"?: string
}) {
  return (
    <Select
      value={value === null ? NONE : String(value)}
      onValueChange={(v) => onChange(v === NONE ? null : Number(v))}
      disabled={disabled}
    >
      <SelectTrigger
        id={id}
        aria-label={ariaLabel}
        className={cn(compact ? "w-[4.5rem]" : "w-36", className)}
      >
        <SelectValue>
          {compact
            ? value === null
              ? "P–"
              : `P${value}`
            : priorityLabel(value)}
        </SelectValue>
      </SelectTrigger>
      <SelectContent>
        <SelectGroup>
          {PRIORITIES.map((p) => (
            <SelectItem key={p} value={String(p)}>
              {priorityLabel(p)}
              {p === 5 ? (
                <span className="text-muted-foreground">, most urgent</span>
              ) : null}
            </SelectItem>
          ))}
          <SelectItem value={NONE}>No priority</SelectItem>
        </SelectGroup>
      </SelectContent>
    </Select>
  )
}
