"use client"

import Link from "next/link"
import { TriangleAlertIcon } from "lucide-react"

import { Button } from "@/components/ui/button"

/** Shared body for error.tsx boundaries: say what failed, offer a retry and a way out. */
export function RouteError({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  return (
    <main className="mx-auto flex w-full max-w-xl flex-col items-start gap-4 px-4 py-20 sm:px-6">
      <TriangleAlertIcon aria-hidden className="size-8 text-off-track" />
      <h1 className="type-display text-4xl">This page didn&apos;t load</h1>
      <p className="text-muted-foreground">
        The server didn&apos;t answer as expected. Your data is safe: nothing is
        lost when a page fails to load.
        {error.digest ? (
          <span className="mt-2 block text-sm">Reference: {error.digest}</span>
        ) : null}
      </p>
      <div className="flex gap-2">
        <Button size="lg" onClick={reset}>
          Try again
        </Button>
        <Button size="lg" variant="outline" asChild>
          <Link href="/">Go to my team</Link>
        </Button>
      </div>
    </main>
  )
}
