"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { WifiOffIcon } from "lucide-react"

import { Button } from "@/components/ui/button"
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import type { MeetingState } from "@/lib/api/types"
import { SECTION_LABEL } from "@/lib/format"
import { useActiveMeeting } from "@/features/meeting/queries"
import { useSocketStatus } from "@/features/realtime/team-realtime"
import { useTeam } from "@/features/team/team-context"

/** Header status: a live meeting to join, and a warning when live updates drop. */
export function MeetingPill({ initialData }: { initialData: MeetingState }) {
  const { teamId } = useTeam()
  const pathname = usePathname()
  const { data } = useActiveMeeting(teamId, initialData)
  const status = useSocketStatus()
  const meeting = data?.meeting
  const inMeeting = meeting
    ? pathname.endsWith(`/meetings/${meeting.id}`)
    : false

  return (
    <>
      {status === "reconnecting" ? (
        <Tooltip>
          <TooltipTrigger asChild>
            <span
              role="status"
              className="inline-flex items-center gap-1.5 rounded-md px-2 py-1 text-sm text-muted-foreground"
            >
              <WifiOffIcon aria-hidden className="size-4" />
              <span className="hidden sm:inline">Reconnecting</span>
            </span>
          </TooltipTrigger>
          <TooltipContent>
            Live updates paused. Changes you make still save.
          </TooltipContent>
        </Tooltip>
      ) : null}
      {meeting && !inMeeting ? (
        <Button asChild size="lg" className="gap-2">
          <Link href={`/teams/${teamId}/meetings/${meeting.id}`}>
            <span aria-hidden className="relative flex size-2">
              <span className="absolute inline-flex size-full animate-ping rounded-full bg-primary-foreground/70 motion-reduce:hidden" />
              <span className="relative inline-flex size-2 rounded-full bg-primary-foreground" />
            </span>
            <span>
              Join meeting
              <span className="hidden font-normal opacity-85 sm:inline">
                {" "}
                in {SECTION_LABEL[meeting.current_section]}
              </span>
            </span>
          </Link>
        </Button>
      ) : null}
    </>
  )
}
