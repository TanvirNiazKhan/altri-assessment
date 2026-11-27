import type { MeasurableStatus, RockStatus } from "@/lib/api/types"

/** Signal colors mean one thing each. Every status also has words, never color alone. */
export const MEASURABLE_STATUS: Record<
  MeasurableStatus,
  { label: string; cell: string; dot: string }
> = {
  on_track: {
    label: "On track",
    cell: "bg-on-track-soft text-on-track-ink",
    dot: "bg-on-track",
  },
  off_track: {
    label: "Off track",
    cell: "bg-off-track-soft text-off-track-ink font-bold",
    dot: "bg-off-track",
  },
  pending: {
    label: "Pending",
    cell: "hatch-pending bg-pending-soft text-muted-foreground",
    dot: "bg-pending",
  },
}

export const ROCK_STATUS: Record<
  RockStatus,
  { label: string; text: string; bar: string; dot: string }
> = {
  on_track: {
    label: "On track",
    text: "text-on-track-ink",
    bar: "bg-on-track",
    dot: "bg-on-track",
  },
  off_track: {
    label: "Off track",
    text: "text-off-track-ink",
    bar: "bg-off-track",
    dot: "bg-off-track",
  },
  complete: {
    label: "Complete",
    text: "text-primary",
    bar: "bg-primary",
    dot: "bg-primary",
  },
}
