import type { Goal, IsoDate, IsoDateTime } from "@/lib/api/types"

// Formatters are built once per (options, zone) and reused: Intl constructors are slow.
const cache = new Map<string, Intl.DateTimeFormat>()
function fmt(timeZone: string, options: Intl.DateTimeFormatOptions) {
  const key = timeZone + JSON.stringify(options)
  let f = cache.get(key)
  if (!f) {
    f = new Intl.DateTimeFormat("en-US", { ...options, timeZone })
    cache.set(key, f)
  }
  return f
}

/** Calendar dates (week starts, due dates) carry no zone: format them as-is. */
function dateOnly(d: IsoDate) {
  return new Date(`${d}T12:00:00Z`)
}

/** "Nov 2" */
export function formatDay(d: IsoDate) {
  return fmt("UTC", { month: "short", day: "numeric" }).format(dateOnly(d))
}

/** "Mon, Nov 2" */
export function formatDayLong(d: IsoDate) {
  return fmt("UTC", {
    weekday: "short",
    month: "short",
    day: "numeric",
  }).format(dateOnly(d))
}

/** Week label for a Monday: "Nov 2" (the week is named by its Monday). */
export const formatWeek = formatDay

/** Instants in the company's zone: "Nov 4, 10:12 AM". */
export function formatInstant(t: IsoDateTime, timeZone: string) {
  return fmt(timeZone, {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(new Date(t))
}

export function formatTime(t: IsoDateTime, timeZone: string) {
  return fmt(timeZone, { hour: "numeric", minute: "2-digit" }).format(
    new Date(t)
  )
}

const numberFmt = new Intl.NumberFormat("en-US", { maximumFractionDigits: 2 })

export function formatNumber(v: number | null | undefined) {
  return v === null || v === undefined ? "" : numberFmt.format(v)
}

/** Units are "count", "%", "hours" or money like "$k": money prefixes "$" and keeps the scale. */
function unitParts(unit: string): { prefix: string; suffix: string } {
  if (unit === "count" || unit === "") return { prefix: "", suffix: "" }
  if (unit === "%") return { prefix: "", suffix: "%" }
  if (unit.startsWith("$")) return { prefix: "$", suffix: unit.slice(1) }
  return { prefix: "", suffix: ` ${unit}` }
}

export function formatValue(v: number | null, unit: string) {
  if (v === null) return "—"
  const { prefix, suffix } = unitParts(unit)
  return `${prefix}${numberFmt.format(v)}${suffix}`
}

/** "≥ 10", "≤ 3%", "2–4 hours", "= 1", "≥ $500k" */
export function formatGoal(goal: Goal, unit: string) {
  const { prefix, suffix } = unitParts(unit)
  const n = (x: number | null) => `${prefix}${formatNumber(x)}`
  switch (goal.type) {
    case "at_least":
      return `≥ ${n(goal.value)}${suffix}`
    case "at_most":
      return `≤ ${n(goal.value)}${suffix}`
    case "exactly":
      return `= ${n(goal.value)}${suffix}`
    case "between":
      return `${n(goal.min)}–${n(goal.max)}${suffix}`
  }
}

export function goalDescription(goal: Goal, unit: string) {
  const v = (x: number | null) => formatValue(x, unit)
  switch (goal.type) {
    case "at_least":
      return `Goal: at least ${v(goal.value)}`
    case "at_most":
      return `Goal: at most ${v(goal.value)}`
    case "exactly":
      return `Goal: exactly ${v(goal.value)}`
    case "between":
      return `Goal: between ${v(goal.min)} and ${v(goal.max)}`
  }
}

/** mm:ss for the meeting clock; hours fold into minutes (IDS is 60:00). */
export function formatClock(totalSeconds: number) {
  const s = Math.max(0, Math.floor(totalSeconds))
  const m = Math.floor(s / 60)
  return `${String(m).padStart(2, "0")}:${String(s % 60).padStart(2, "0")}`
}

export function initials(name: string) {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((p) => p[0]!.toUpperCase())
    .join("")
}

export const ROLE_LABEL = {
  admin: "Admin",
  team_member: "Team Member",
  observer: "Observer",
} as const

export const SECTION_LABEL = {
  scorecard: "Scorecard",
  ids: "IDS",
  conclude: "Conclude",
} as const
