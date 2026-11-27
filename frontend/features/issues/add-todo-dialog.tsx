"use client"

import { useState } from "react"
import { ListPlusIcon } from "lucide-react"
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
  FieldGroup,
  FieldLabel,
} from "@/components/ui/field"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Spinner } from "@/components/ui/spinner"
import { errorMessage } from "@/lib/api/errors"
import type { Issue } from "@/lib/api/types"
import { formatDayLong } from "@/lib/format"
import { useAddTodo } from "@/features/team/queries"
import { useTeam } from "@/features/team/team-context"

const TITLE_MAX = 200

function addDays(isoDate: string, days: number) {
  const d = new Date(`${isoDate}T12:00:00Z`)
  d.setUTCDate(d.getUTCDate() + days)
  return d.toISOString().slice(0, 10)
}

export function AddTodoDialog({ issue }: { issue: Issue }) {
  const { teamId, owners, user, calendar } = useTeam()
  const add = useAddTodo(teamId)
  const [open, setOpen] = useState(false)
  const defaultOwner = owners.some((o) => o.id === issue.owner.id)
    ? issue.owner.id
    : owners.some((o) => o.id === user.id)
      ? user.id
      : (owners[0]?.id ?? "")
  const [title, setTitle] = useState("")
  const [ownerId, setOwnerId] = useState(defaultOwner)
  const [errors, setErrors] = useState<{
    title?: string
    owner?: string
    form?: string
  }>({})
  const due = addDays(calendar.today, 7)

  function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    const t = title.trim()
    const next = {
      title: t ? undefined : "Say what needs doing.",
      owner: ownerId ? undefined : "Pick an owner.",
    }
    if (next.title || next.owner) return setErrors(next)
    add.mutate(
      { issueId: issue.id, title: t, ownerId },
      {
        onSuccess: (todo) => {
          toast.success("To-Do added", {
            description: `${todo.title}, ${todo.owner.name}`,
          })
          setTitle("")
          setOpen(false)
        },
        onError: (err) => setErrors({ form: errorMessage(err) }),
      }
    )
  }

  return (
    <Dialog
      open={open}
      onOpenChange={(o) => {
        setOpen(o)
        if (o) setOwnerId(defaultOwner)
        else setErrors({})
      }}
    >
      <DialogTrigger asChild>
        <Button variant="ghost" size="sm">
          <ListPlusIcon data-icon="inline-start" />
          To-Do
        </Button>
      </DialogTrigger>
      <DialogContent>
        <form onSubmit={onSubmit} noValidate className="flex flex-col gap-4">
          <DialogHeader>
            <DialogTitle>Add a To-Do</DialogTitle>
            <DialogDescription>Linked to “{issue.title}”.</DialogDescription>
          </DialogHeader>
          <FieldGroup>
            <Field data-invalid={errors.title ? true : undefined}>
              <FieldLabel htmlFor={`todo-title-${issue.id}`}>
                What needs doing
              </FieldLabel>
              <Input
                id={`todo-title-${issue.id}`}
                autoFocus
                maxLength={TITLE_MAX}
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                aria-invalid={errors.title ? true : undefined}
              />
              {errors.title ? <FieldError>{errors.title}</FieldError> : null}
            </Field>
            <Field data-invalid={errors.owner ? true : undefined}>
              <FieldLabel htmlFor={`todo-owner-${issue.id}`}>Owner</FieldLabel>
              <Select value={ownerId} onValueChange={setOwnerId}>
                <SelectTrigger
                  id={`todo-owner-${issue.id}`}
                  className="w-full"
                  aria-invalid={errors.owner ? true : undefined}
                >
                  <SelectValue placeholder="Pick an owner" />
                </SelectTrigger>
                <SelectContent>
                  <SelectGroup>
                    {owners.map((o) => (
                      <SelectItem key={o.id} value={o.id}>
                        {o.name}
                        {o.id === user.id ? (
                          <span className="text-muted-foreground"> (you)</span>
                        ) : null}
                      </SelectItem>
                    ))}
                  </SelectGroup>
                </SelectContent>
              </Select>
              {errors.owner ? (
                <FieldError>{errors.owner}</FieldError>
              ) : (
                <FieldDescription>
                  Admins and Team Members of this team.
                </FieldDescription>
              )}
            </Field>
            <p className="text-sm text-muted-foreground">
              Due{" "}
              <span className="font-semibold text-foreground">
                {formatDayLong(due)}
              </span>
              , 7 days from today.
            </p>
            {errors.form ? <FieldError>{errors.form}</FieldError> : null}
          </FieldGroup>
          <DialogFooter>
            <DialogClose asChild>
              <Button type="button" variant="outline">
                Cancel
              </Button>
            </DialogClose>
            <Button type="submit" disabled={add.isPending}>
              {add.isPending ? <Spinner data-icon="inline-start" /> : null}
              Add To-Do
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
