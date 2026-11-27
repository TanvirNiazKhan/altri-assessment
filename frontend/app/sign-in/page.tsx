import type { Metadata } from "next"
import { connection } from "next/server"

import { Wordmark } from "@/components/brand/wordmark"
import { getSignInUsers } from "@/lib/api/server"
import type { Role, User } from "@/lib/api/types"
import { SignInList } from "./sign-in-list"

export const metadata: Metadata = { title: "Sign in" }

const GROUPS: { role: Role; title: string; blurb: string }[] = [
  { role: "admin", title: "Admins", blurb: "Every team, every action." },
  {
    role: "team_member",
    title: "Team Members",
    blurb: "Change data and run meetings in their own teams.",
  },
  {
    role: "observer",
    title: "Observers",
    blurb: "Read their teams and join meetings. No changes.",
  },
]

export default async function SignInPage() {
  await connection() // render per request: the user list comes from the API, never from build time
  const users = await getSignInUsers()
  const byRole = Map.groupBy(users, (u: User) => u.role)

  return (
    <main className="mx-auto grid min-h-dvh w-full max-w-5xl gap-10 px-4 py-8 sm:px-8 md:grid-cols-[1fr_1.15fr] md:gap-16 md:py-16">
      <section className="flex flex-col gap-6 md:sticky md:top-16 md:self-start">
        <Wordmark />
        <h1 className="type-display text-5xl text-balance sm:text-6xl">
          Pick who you are this week.
        </h1>
        <p className="max-w-prose text-base text-muted-foreground">
          This build has no passwords. Choose a seeded person to see the app
          with their role and teams. Open a second browser as someone else to
          join the same meeting.
        </p>
      </section>

      <section aria-label="People" className="flex flex-col gap-8">
        {GROUPS.map((g) => {
          const people = byRole.get(g.role) ?? []
          if (people.length === 0) return null
          return (
            <div key={g.role} className="flex flex-col gap-3">
              <div className="flex items-baseline justify-between gap-4 border-b pb-2">
                <h2 className="type-display text-2xl">{g.title}</h2>
                <p className="text-sm text-muted-foreground">{g.blurb}</p>
              </div>
              <SignInList users={people} />
            </div>
          )
        })}
      </section>
    </main>
  )
}
