"use client"

import { useState } from "react"
import { useQueryClient } from "@tanstack/react-query"
import { ArrowRightIcon } from "lucide-react"
import { toast } from "sonner"

import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Spinner } from "@/components/ui/spinner"
import { api } from "@/lib/api/client"
import { errorMessage } from "@/lib/api/errors"
import type { User } from "@/lib/api/types"
import { initials } from "@/lib/format"

export function SignInList({ users }: { users: User[] }) {
  const client = useQueryClient()
  const [pendingId, setPendingId] = useState<string | null>(null)

  async function signIn(user: User) {
    setPendingId(user.id)
    try {
      await api<User>("/auth/login", {
        method: "POST",
        json: { user_id: user.id },
      })
      client.clear() // nothing cached for the previous person survives
      // Full page load, not router.push: this page prefetched "/" before the cookie
      // existed, and the client router would replay that cached redirect to /sign-in.
      window.location.assign("/")
    } catch (e) {
      setPendingId(null)
      toast.error(errorMessage(e))
    }
  }

  return (
    <ul className="flex flex-col">
      {users.map((u) => {
        const pending = pendingId === u.id
        return (
          <li key={u.id}>
            <button
              type="button"
              onClick={() => signIn(u)}
              disabled={pendingId !== null}
              aria-busy={pending}
              className="group flex w-full items-center gap-3 rounded-md px-2 py-3 text-left outline-none hover:bg-accent focus-visible:ring-3 focus-visible:ring-ring/50 disabled:cursor-wait"
            >
              <Avatar className="size-9">
                <AvatarFallback className="bg-secondary text-sm font-semibold text-secondary-foreground">
                  {initials(u.name)}
                </AvatarFallback>
              </Avatar>
              <span className="flex min-w-0 flex-1 flex-col">
                <span className="truncate font-semibold">{u.name}</span>
                <span className="truncate text-sm text-muted-foreground">
                  {u.email}
                </span>
              </span>
              {pending ? (
                <Spinner aria-label="Signing in" />
              ) : (
                <ArrowRightIcon
                  aria-hidden
                  className="size-4 text-muted-foreground opacity-0 transition-opacity group-hover:opacity-100 group-focus-visible:opacity-100"
                />
              )}
              <span className="sr-only">Sign in as {u.name}</span>
            </button>
          </li>
        )
      })}
    </ul>
  )
}
