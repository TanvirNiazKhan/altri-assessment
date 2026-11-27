"use client"

import { useRef, useState } from "react"
import { PlusIcon } from "lucide-react"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import { Field, FieldError, FieldLabel } from "@/components/ui/field"
import { Input } from "@/components/ui/input"
import { Spinner } from "@/components/ui/spinner"
import { errorMessage } from "@/lib/api/errors"
import { useCreateIssue } from "@/features/team/queries"
import { useTeam } from "@/features/team/team-context"
import { PrioritySelect } from "./priority-select"

const TITLE_MAX = 200

export function CreateIssueForm() {
  const { teamId } = useTeam()
  const create = useCreateIssue(teamId)
  const [title, setTitle] = useState("")
  const [priority, setPriority] = useState<number | null>(null)
  const [error, setError] = useState<string | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    const t = title.trim()
    if (!t) {
      setError("Give the Issue a title.")
      inputRef.current?.focus()
      return
    }
    setError(null)
    create.mutate(
      { title: t, priority },
      {
        onSuccess: () => {
          setTitle("")
          setPriority(null)
          toast.success("Issue added")
          inputRef.current?.focus()
        },
        onError: (err) => setError(errorMessage(err)),
      }
    )
  }

  return (
    <form
      onSubmit={onSubmit}
      noValidate
      className="flex flex-col gap-2 sm:flex-row sm:items-start"
    >
      <Field data-invalid={error ? true : undefined} className="flex-1">
        <FieldLabel htmlFor="new-issue" className="sr-only">
          New Issue title
        </FieldLabel>
        <Input
          ref={inputRef}
          id="new-issue"
          value={title}
          maxLength={TITLE_MAX}
          onChange={(e) => {
            setTitle(e.target.value)
            if (error) setError(null)
          }}
          placeholder="Add an Issue: what's in the way?"
          aria-invalid={error ? true : undefined}
          aria-describedby={error ? "new-issue-error" : undefined}
        />
        {error ? <FieldError id="new-issue-error">{error}</FieldError> : null}
      </Field>
      <div className="flex gap-2">
        <PrioritySelect
          value={priority}
          onChange={setPriority}
          aria-label="Priority for the new Issue"
        />
        <Button type="submit" disabled={create.isPending}>
          {create.isPending ? (
            <Spinner data-icon="inline-start" />
          ) : (
            <PlusIcon data-icon="inline-start" />
          )}
          Add Issue
        </Button>
      </div>
    </form>
  )
}
