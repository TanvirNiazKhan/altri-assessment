"use client"

import { useState } from "react"
import { CheckIcon } from "lucide-react"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import {
  Field,
  FieldDescription,
  FieldError,
  FieldLabel,
} from "@/components/ui/field"
import { Spinner } from "@/components/ui/spinner"
import { Textarea } from "@/components/ui/textarea"
import { errorMessage } from "@/lib/api/errors"
import type { Issue } from "@/lib/api/types"
import { useSolveIssue } from "@/features/team/queries"
import { useTeam } from "@/features/team/team-context"

const NOTE_MAX = 2000

export function SolveDialog({ issue }: { issue: Issue }) {
  const { teamId } = useTeam()
  const solve = useSolveIssue(teamId)
  const [open, setOpen] = useState(false)
  const [note, setNote] = useState("")
  const [error, setError] = useState<string | null>(null)

  function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    const n = note.trim()
    if (!n) return setError("Write down what the team decided.")
    solve.mutate(
      { issueId: issue.id, note: n },
      {
        onSuccess: () => {
          toast.success("Issue solved", { description: issue.title })
          setOpen(false)
          setNote("")
        },
        onError: (err) => setError(errorMessage(err)),
      }
    )
  }

  return (
    <Dialog
      open={open}
      onOpenChange={(o) => {
        setOpen(o)
        if (!o) setError(null)
      }}
    >
      <DialogTrigger asChild>
        <Button variant="outline" size="sm">
          <CheckIcon data-icon="inline-start" />
          Solve
        </Button>
      </DialogTrigger>
      <DialogContent>
        <form onSubmit={onSubmit} noValidate className="flex flex-col gap-4">
          <DialogHeader>
            <DialogTitle>Solve this Issue</DialogTitle>
            <DialogDescription>{issue.title}</DialogDescription>
          </DialogHeader>
          <Field data-invalid={error ? true : undefined}>
            <FieldLabel htmlFor={`solve-${issue.id}`}>Resolution</FieldLabel>
            <Textarea
              id={`solve-${issue.id}`}
              autoFocus
              rows={4}
              maxLength={NOTE_MAX}
              value={note}
              onChange={(e) => {
                setNote(e.target.value)
                if (error) setError(null)
              }}
              aria-invalid={error ? true : undefined}
              placeholder="What did we decide, and who does what?"
            />
            {error ? (
              <FieldError>{error}</FieldError>
            ) : (
              <FieldDescription>
                Required. Add follow-up To-Dos from the Issue after solving, or
                before.
              </FieldDescription>
            )}
          </Field>
          <DialogFooter>
            <DialogClose asChild>
              <Button type="button" variant="outline">
                Keep open
              </Button>
            </DialogClose>
            <Button type="submit" disabled={solve.isPending}>
              {solve.isPending ? <Spinner data-icon="inline-start" /> : null}
              Solve Issue
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
