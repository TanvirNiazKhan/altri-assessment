// One place for cache keys, so the realtime socket and mutations invalidate the same things.
export const qk = {
  team: (t: string) => ["team", t] as const,
  scorecard: (t: string) => ["team", t, "scorecard"] as const,
  issues: (t: string) => ["team", t, "issues"] as const,
  issueList: (t: string, status: "open" | "solved") =>
    ["team", t, "issues", status] as const,
  todos: (t: string) => ["team", t, "todos"] as const,
  activeMeeting: (t: string) => ["team", t, "meeting", "active"] as const,
  meeting: (t: string, id: string) => ["team", t, "meeting", id] as const,
  summary: (t: string, id: string) => ["team", t, "summary", id] as const,
}
