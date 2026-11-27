import { AppHeader } from "@/features/shell/app-header"
import { TeamRealtime } from "@/features/realtime/team-realtime"
import { TeamProvider } from "@/features/team/team-context"
import { getActiveMeeting, getMe, getOwners, getTeam } from "@/lib/api/server"

export default async function TeamLayout({
  children,
  params,
}: LayoutProps<"/teams/[teamId]">) {
  const { teamId } = await params
  // Independent requests: start together. A team the person can't read is a 404 → not-found page.
  const [me, team, owners, active] = await Promise.all([
    getMe(),
    getTeam(teamId),
    getOwners(teamId),
    getActiveMeeting(teamId),
  ])

  return (
    <TeamProvider
      value={{
        teamId: team.id,
        teamName: team.name,
        canWrite: team.can_write,
        user: me.user,
        calendar: me.calendar,
        owners: owners.map((o) => ({ id: o.id, name: o.name })),
      }}
    >
      <TeamRealtime teamId={team.id}>
        <AppHeader teams={me.teams} initialMeeting={active} />
        {children}
      </TeamRealtime>
    </TeamProvider>
  )
}
