import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import type { Meeting } from "@/lib/api/types"
import { ROLE_LABEL, initials } from "@/lib/format"

export function AttendeesList({
  meeting,
  currentUserId,
}: {
  meeting: Meeting
  currentUserId: string
}) {
  const ratingBy = new Map(meeting.ratings.map((r) => [r.user_id, r.rating]))
  const showRatings = meeting.current_section === "conclude"
  return (
    <section aria-labelledby="attendees-title" className="flex flex-col gap-3">
      <h2
        id="attendees-title"
        className="type-display flex items-baseline gap-2 text-2xl"
      >
        In the room
        <span className="type-numeric font-sans text-sm font-semibold text-muted-foreground">
          {meeting.attendees.length}
        </span>
      </h2>
      <ul className="flex flex-col gap-2">
        {meeting.attendees.map((a) => (
          <li key={a.id} className="flex items-center gap-2.5">
            <Avatar className="size-8">
              <AvatarFallback className="bg-secondary text-xs font-semibold text-secondary-foreground">
                {initials(a.name)}
              </AvatarFallback>
            </Avatar>
            <span className="flex min-w-0 flex-1 flex-col leading-tight">
              <span className="truncate text-sm font-semibold">
                {a.name}
                {a.id === currentUserId ? (
                  <span className="font-normal text-muted-foreground">
                    {" "}
                    (you)
                  </span>
                ) : null}
              </span>
              <span className="text-xs text-muted-foreground">
                {a.id === meeting.facilitator.id
                  ? "Facilitator"
                  : ROLE_LABEL[a.role]}
              </span>
            </span>
            {showRatings && a.can_rate ? (
              <span
                className="type-numeric text-sm font-semibold"
                aria-label={
                  ratingBy.has(a.id)
                    ? `Rated ${ratingBy.get(a.id)}`
                    : "Not rated yet"
                }
              >
                {ratingBy.get(a.id) ?? (
                  <span className="font-normal text-muted-foreground">–</span>
                )}
              </span>
            ) : null}
          </li>
        ))}
      </ul>
    </section>
  )
}
