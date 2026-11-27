"use client"

import { ArrowRightIcon, SquareIcon } from "lucide-react"
import { toast } from "sonner"

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog"
import { Button } from "@/components/ui/button"
import { Spinner } from "@/components/ui/spinner"
import { ApiError, errorMessage } from "@/lib/api/errors"
import type { Meeting } from "@/lib/api/types"
import { SECTION_LABEL } from "@/lib/format"
import { useTeam } from "@/features/team/team-context"
import { useAdvanceMeeting, useEndMeeting } from "./queries"

/** Only the facilitator drives. Everyone else follows automatically. */
export function MeetingControls({ meeting }: { meeting: Meeting }) {
  const { teamId, user } = useTeam()
  const advance = useAdvanceMeeting(teamId)
  const end = useEndMeeting(teamId)
  const isFacilitator = meeting.facilitator.id === user.id

  if (!isFacilitator) {
    return (
      <p className="max-w-xs text-sm text-muted-foreground">
        {meeting.facilitator.name} is running this meeting. Your screen follows
        along.
      </p>
    )
  }

  const idx = meeting.agenda.findIndex(
    (a) => a.section === meeting.current_section
  )
  const next = meeting.agenda[idx + 1]

  return (
    <div className="flex flex-wrap items-center gap-2">
      {next ? (
        <Button
          size="lg"
          className="h-11 px-4 text-base"
          disabled={advance.isPending}
          onClick={() =>
            advance.mutate(
              { meetingId: meeting.id, expected: meeting.current_section },
              {
                onError: (e) =>
                  toast.error(
                    e instanceof ApiError && e.status === 409
                      ? "The meeting already moved on. Showing the current section."
                      : errorMessage(e)
                  ),
              }
            )
          }
        >
          {advance.isPending ? <Spinner data-icon="inline-start" /> : null}
          Go to {SECTION_LABEL[next.section]}
          <ArrowRightIcon data-icon="inline-end" />
        </Button>
      ) : null}
      <AlertDialog>
        <AlertDialogTrigger asChild>
          <Button
            size="lg"
            variant={next ? "outline" : "default"}
            className="h-11 px-4 text-base"
          >
            <SquareIcon data-icon="inline-start" />
            End meeting
          </Button>
        </AlertDialogTrigger>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>End the meeting for everyone?</AlertDialogTitle>
            <AlertDialogDescription>
              Ratings freeze and the summary is saved as it stands. This
              can&apos;t be undone.
              {next
                ? ` You're still in ${SECTION_LABEL[meeting.current_section]}.`
                : ""}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Keep going</AlertDialogCancel>
            <AlertDialogAction
              onClick={() =>
                end.mutate(meeting.id, {
                  onError: (e) => toast.error(errorMessage(e)),
                })
              }
            >
              End meeting
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}
