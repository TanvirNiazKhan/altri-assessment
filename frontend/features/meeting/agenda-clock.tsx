"use client"

import type { Meeting, MeetingSection } from "@/lib/api/types"
import { SECTION_LABEL, formatClock } from "@/lib/format"
import { useServerNow } from "@/lib/server-clock"
import { cn } from "@/lib/utils"

function useElapsed(meeting: Meeting) {
  const now = useServerNow()
  if (now === null) return null
  return Math.max(0, (now - Date.parse(meeting.section_started_at)) / 1000)
}

/**
 * The agenda as a track: each section's width is its share of the 75 minutes
 * (5 / 60 / 10), so the shape of the meeting is visible at a glance. The current
 * section fills as time passes; past sections are solid; overtime shows red.
 */
export function AgendaTrack({ meeting }: { meeting: Meeting }) {
  const elapsed = useElapsed(meeting)
  const currentIndex = meeting.agenda.findIndex(
    (a) => a.section === meeting.current_section
  )

  return (
    <ol className="flex w-full gap-1" aria-label="Agenda">
      {meeting.agenda.map((item, i) => {
        const state =
          i < currentIndex ? "done" : i === currentIndex ? "current" : "next"
        const fill =
          state === "done"
            ? 1
            : state === "current" && elapsed !== null
              ? Math.min(1, elapsed / item.duration_s)
              : 0
        const over =
          state === "current" && elapsed !== null && elapsed > item.duration_s
        return (
          <li
            key={item.section}
            aria-current={state === "current" ? "step" : undefined}
            className="flex min-w-[5.5rem] flex-col gap-1.5"
            style={{ flex: `${item.duration_s} 1 0` }}
          >
            <span
              className={cn(
                "relative block h-3 overflow-hidden rounded-sm",
                state === "current" ? "bg-primary/15" : "bg-muted"
              )}
            >
              <span
                className={cn(
                  "absolute inset-y-0 left-0 block transition-[width] duration-1000 ease-linear motion-reduce:transition-none",
                  state === "done"
                    ? "bg-foreground/60"
                    : over
                      ? "bg-off-track"
                      : "bg-primary"
                )}
                style={{ width: `${fill * 100}%` }}
              />
            </span>
            <span className="flex flex-col leading-tight">
              <span
                className={cn(
                  "text-sm font-semibold",
                  state === "current" && "text-primary",
                  state === "next" && "text-muted-foreground",
                  state === "done" &&
                    "text-muted-foreground line-through decoration-1"
                )}
              >
                {SECTION_LABEL[item.section]}
                {state === "current" ? (
                  <span className="sr-only"> (now)</span>
                ) : null}
              </span>
              <span className="type-numeric text-xs text-muted-foreground">
                {item.duration_s / 60} min
              </span>
            </span>
          </li>
        )
      })}
    </ol>
  )
}

/** The server owns the timer: remaining = duration − (server now − section start). Never auto-advances. */
export function SectionClock({ meeting }: { meeting: Meeting }) {
  const elapsed = useElapsed(meeting)
  const duration = meeting.section_duration_s
  const over = elapsed !== null && elapsed > duration
  const remaining =
    elapsed === null ? duration : over ? elapsed - duration : duration - elapsed
  const label = SECTION_LABEL[meeting.current_section as MeetingSection]

  return (
    <div className="flex flex-col items-start">
      <p
        className={cn(
          "text-sm font-semibold",
          over ? "text-off-track-ink" : "text-muted-foreground"
        )}
      >
        {over ? `${label} is over time` : `Left in ${label}`}
      </p>
      <p
        className={cn(
          "type-display type-numeric text-[clamp(4.5rem,16vw,8.5rem)] leading-[0.85]",
          over && "text-off-track",
          elapsed === null && "opacity-40"
        )}
        // Announce section changes, not every second.
        aria-hidden
      >
        {over ? "+" : ""}
        {formatClock(remaining)}
      </p>
      <span className="sr-only">
        {label}, {Math.round(duration / 60)} minutes planned.
      </span>
    </div>
  )
}
