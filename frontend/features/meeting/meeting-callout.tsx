"use client"

import Link from "next/link"
import { useRouter } from "next/navigation"
import { PlayIcon, RadioIcon } from "lucide-react"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import { Spinner } from "@/components/ui/spinner"
import { ApiError, errorMessage } from "@/lib/api/errors"
import { SECTION_LABEL } from "@/lib/format"
import { useActiveMeeting, useStartMeeting } from "./queries"
import { useTeam } from "@/features/team/team-context"

/** Team page entry to the Level 10 Meeting: start one, or join the one running. */
export function MeetingCallout() {
  const { teamId, canWrite } = useTeam()
  const router = useRouter()
  const { data } = useActiveMeeting(teamId)
  const start = useStartMeeting(teamId)
  const meeting = data?.meeting

  if (meeting) {
    return (
      <div className="flex flex-wrap items-center gap-3">
        <p className="flex items-center gap-2 text-sm">
          <RadioIcon aria-hidden className="size-4 text-primary" />
          <span>
            <span className="font-semibold">
              Meeting in {SECTION_LABEL[meeting.current_section]}
            </span>
            <span className="text-muted-foreground">
              , run by {meeting.facilitator.name}
            </span>
          </span>
        </p>
        <Button asChild size="lg">
          <Link href={`/teams/${teamId}/meetings/${meeting.id}`}>
            Join meeting
          </Link>
        </Button>
      </div>
    )
  }

  if (!canWrite) {
    return (
      <p className="text-sm text-muted-foreground">
        No meeting running. You&apos;ll see a Join button when one starts.
      </p>
    )
  }

  return (
    <Button
      size="lg"
      className="h-11 px-4 text-base"
      disabled={start.isPending}
      onClick={() =>
        start.mutate(undefined, {
          onSuccess: (s) =>
            s.meeting &&
            router.push(`/teams/${teamId}/meetings/${s.meeting.id}`),
          onError: (e) =>
            toast.error(
              e instanceof ApiError && e.status === 409
                ? "A meeting already started. Join it from the header."
                : errorMessage(e)
            ),
        })
      }
    >
      {start.isPending ? (
        <Spinner data-icon="inline-start" />
      ) : (
        <PlayIcon data-icon="inline-start" />
      )}
      Start Level 10 Meeting
    </Button>
  )
}
