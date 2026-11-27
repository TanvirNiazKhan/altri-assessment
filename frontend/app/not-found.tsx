import Link from "next/link"

import { Wordmark } from "@/components/brand/wordmark"
import { Button } from "@/components/ui/button"

// Missing and inaccessible teams look the same on purpose: ids can't be probed.
export default function NotFound() {
  return (
    <main className="mx-auto flex min-h-dvh w-full max-w-xl flex-col items-start justify-center gap-5 px-4 sm:px-6">
      <Wordmark />
      <h1 className="type-display text-5xl text-balance">
        Nothing here for you
      </h1>
      <p className="text-muted-foreground">
        This team or meeting doesn&apos;t exist, or you&apos;re not on the team.
        Ask an Admin to add you, or pick one of your own teams.
      </p>
      <div className="flex gap-2">
        <Button size="lg" asChild>
          <Link href="/">Go to my teams</Link>
        </Button>
        <Button size="lg" variant="outline" asChild>
          <Link href="/sign-in">Switch person</Link>
        </Button>
      </div>
    </main>
  )
}
