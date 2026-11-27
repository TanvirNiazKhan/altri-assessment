import { Wordmark } from "@/components/brand/wordmark"
import type { MeetingState, Team } from "@/lib/api/types"
import { MeetingPill } from "./meeting-pill"
import { TeamSwitcher } from "./team-switcher"
import { UserMenu } from "./user-menu"

export function AppHeader({
  teams,
  initialMeeting,
}: {
  teams: Team[]
  initialMeeting: MeetingState
}) {
  return (
    <header className="sticky top-0 z-40 border-b bg-background/90 backdrop-blur supports-[backdrop-filter]:bg-background/75">
      <div className="mx-auto flex h-14 w-full max-w-[1400px] items-center gap-2 px-4 sm:gap-4 sm:px-6">
        <Wordmark />
        <span aria-hidden className="h-6 w-px bg-border" />
        <TeamSwitcher teams={teams} />
        <div className="ml-auto flex items-center gap-2">
          <MeetingPill initialData={initialMeeting} />
          <UserMenu />
        </div>
      </div>
    </header>
  )
}
