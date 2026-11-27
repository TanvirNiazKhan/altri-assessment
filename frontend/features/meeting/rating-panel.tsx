"use client"

import { toast } from "sonner"

import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group"
import { errorMessage } from "@/lib/api/errors"
import type { Meeting } from "@/lib/api/types"
import { useTeam } from "@/features/team/team-context"
import { useRateMeeting } from "./queries"

const SCALE = Array.from({ length: 10 }, (_, i) => i + 1)

export function RatingPanel({ meeting }: { meeting: Meeting }) {
  const { teamId, user } = useTeam()
  const rate = useRateMeeting(teamId)
  const me = meeting.attendees.find((a) => a.id === user.id)
  const mine = meeting.ratings.find((r) => r.user_id === user.id)?.rating
  const raters = meeting.attendees.filter((a) => a.can_rate)

  return (
    <section aria-labelledby="rating-title" className="flex flex-col gap-4">
      <div className="flex items-end justify-between gap-4 border-b-2 border-foreground pb-2">
        <h3 id="rating-title" className="type-display text-3xl">
          Rate this meeting
        </h3>
        <p className="text-right">
          <span className="type-display type-numeric block text-4xl">
            {meeting.average_rating === null
              ? "–"
              : meeting.average_rating.toFixed(1)}
          </span>
          <span className="text-xs text-muted-foreground">
            average of {meeting.ratings.length} of {raters.length}
          </span>
        </p>
      </div>
      {me?.can_rate ? (
        <div className="flex flex-col gap-2">
          <p id="rating-help" className="text-sm text-muted-foreground">
            1 is a waste of time, 10 is the best meeting we could have had.
            Change it any time until the meeting ends.
          </p>
          <ToggleGroup
            type="single"
            variant="outline"
            value={mine ? String(mine) : ""}
            onValueChange={(v) => {
              if (!v) return // keep the rating; there's no "unrate" in the API
              rate.mutate(
                { meetingId: meeting.id, rating: Number(v) },
                { onError: (e) => toast.error(errorMessage(e)) }
              )
            }}
            aria-describedby="rating-help"
            aria-label="Your rating, 1 to 10"
            className="grid w-full grid-cols-5 sm:grid-cols-10"
          >
            {SCALE.map((n) => (
              <ToggleGroupItem
                key={n}
                value={String(n)}
                aria-label={`Rate ${n}`}
                className="type-numeric h-12 text-lg font-bold data-[state=on]:bg-primary data-[state=on]:text-primary-foreground"
              >
                {n}
              </ToggleGroupItem>
            ))}
          </ToggleGroup>
        </div>
      ) : (
        <p className="text-sm text-muted-foreground">
          {me
            ? "Observers watch the meeting but don't rate it."
            : "Join the meeting to rate it."}
        </p>
      )}
    </section>
  )
}
