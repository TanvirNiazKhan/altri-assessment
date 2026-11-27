"use client"

import { useRouter } from "next/navigation"
import { useQueryClient } from "@tanstack/react-query"
import { LogOutIcon, MoonIcon, SunIcon, UsersIcon } from "lucide-react"
import { useTheme } from "next-themes"

import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { api } from "@/lib/api/client"
import { ROLE_LABEL, initials } from "@/lib/format"
import { useTeam } from "@/features/team/team-context"

export function UserMenu() {
  const { user } = useTeam()
  const router = useRouter()
  const client = useQueryClient()
  const { resolvedTheme, setTheme } = useTheme()

  async function signOut() {
    await api("/auth/logout", { method: "POST" }).catch(() => undefined)
    client.clear()
    router.push("/sign-in")
    router.refresh()
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          size="icon-lg"
          className="rounded-full"
          aria-label={`Account: ${user.name}`}
        >
          <Avatar className="size-8">
            <AvatarFallback className="bg-secondary text-xs font-semibold text-secondary-foreground">
              {initials(user.name)}
            </AvatarFallback>
          </Avatar>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="min-w-60">
        <DropdownMenuLabel className="flex flex-col gap-0.5 font-normal">
          <span className="font-semibold text-foreground">{user.name}</span>
          <span className="text-muted-foreground">{ROLE_LABEL[user.role]}</span>
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuGroup>
          <DropdownMenuItem
            onSelect={() =>
              setTheme(resolvedTheme === "dark" ? "light" : "dark")
            }
          >
            {resolvedTheme === "dark" ? <SunIcon /> : <MoonIcon />}
            {resolvedTheme === "dark" ? "Light theme" : "Dark theme"}
          </DropdownMenuItem>
          <DropdownMenuItem onSelect={() => router.push("/sign-in")}>
            <UsersIcon />
            Switch person
          </DropdownMenuItem>
          <DropdownMenuItem onSelect={signOut}>
            <LogOutIcon />
            Sign out
          </DropdownMenuItem>
        </DropdownMenuGroup>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
