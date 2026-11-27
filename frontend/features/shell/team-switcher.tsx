"use client"

import Link from "next/link"
import { CheckIcon, ChevronsUpDownIcon } from "lucide-react"

import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import type { Team } from "@/lib/api/types"
import { useTeam } from "@/features/team/team-context"

export function TeamSwitcher({ teams }: { teams: Team[] }) {
  const { teamId, teamName } = useTeam()
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          className="h-9 gap-1.5 px-2 text-base font-semibold"
          aria-label={`Team: ${teamName}. Switch team`}
        >
          <span className="max-w-[9rem] truncate sm:max-w-none">
            {teamName}
          </span>
          <ChevronsUpDownIcon
            data-icon="inline-end"
            className="text-muted-foreground"
          />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start" className="min-w-56">
        <DropdownMenuGroup>
          <DropdownMenuLabel className="text-muted-foreground">
            Your teams
          </DropdownMenuLabel>
          {teams.map((t) => (
            <DropdownMenuItem key={t.id} asChild>
              <Link
                href={`/teams/${t.id}`}
                aria-current={t.id === teamId ? "page" : undefined}
              >
                <span className="flex-1">{t.name}</span>
                {t.id === teamId ? <CheckIcon aria-hidden /> : null}
              </Link>
            </DropdownMenuItem>
          ))}
        </DropdownMenuGroup>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
