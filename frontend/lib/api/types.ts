// Response and request shapes of the FastAPI backend (see /api/docs).
// Dates are ISO strings: `IsoDate` = calendar date in company time, `IsoDateTime` = UTC instant.

export type IsoDate = string
export type IsoDateTime = string

export type Role = "admin" | "team_member" | "observer"
export type MeasurableStatus = "on_track" | "off_track" | "pending"
export type RockStatus = "on_track" | "off_track" | "complete"
export type GoalType = "at_least" | "at_most" | "between" | "exactly"
export type MeetingSection = "scorecard" | "ids" | "conclude"

export interface UserRef {
  id: string
  name: string
}

export interface User extends UserRef {
  email: string
  role: Role
}

export interface Team {
  id: string
  name: string
}

export interface TeamDetail extends Team {
  can_write: boolean
}

export interface Calendar {
  now: IsoDateTime
  today: IsoDate
  current_week: IsoDate
  last_closed_week: IsoDate
  quarter: string
  timezone: string
}

export interface Me {
  user: User
  teams: Team[]
  calendar: Calendar
}

// Scorecard
export interface Goal {
  type: GoalType
  value: number | null
  min: number | null
  max: number | null
}

export interface ScoreCell {
  week_start: IsoDate
  value: number | null
  status: MeasurableStatus
  open_issue_id: string | null
}

export interface ScorecardRow {
  id: string
  name: string
  unit: string
  owner: UserRef
  goal: Goal
  cells: ScoreCell[]
}

export interface Scorecard {
  weeks: IsoDate[]
  current_week: IsoDate
  rows: ScorecardRow[]
}

// Issues
export interface IssueSource {
  type: "measurable" | "rock"
  measurable_id: string | null
  measurable_name: string | null
  week_start: IsoDate | null
  rock_id: string | null
}

export interface Issue {
  id: string
  title: string
  owner: UserRef
  priority: number | null
  created_at: IsoDateTime
  solved_at: IsoDateTime | null
  resolution_note: string | null
  source: IssueSource | null
  solved_in_meeting_id: string | null
}

// To-Dos
export interface Todo {
  id: string
  title: string
  owner: UserRef
  due_date: IsoDate
  done_at: IsoDateTime | null
  overdue: boolean
  created_at: IsoDateTime
  source_issue: { id: string; title: string | null } | null
  created_in_meeting_id: string | null
}

export interface Completion {
  due: number
  done: number
  rate_percent: number
  meets_target: boolean
}

export interface TodoList {
  items: Todo[]
  last_closed_week: {
    week_start: IsoDate
    completion: Completion | null
    target_percent: number
  }
}

// Rocks
export interface Milestone {
  id: string
  title: string
  due_date: IsoDate
  done: boolean
}

export interface Rock {
  id: string
  title: string
  quarter: string
  owner: UserRef
  status: RockStatus
  progress_percent: number
  milestones: Milestone[]
}

// Meetings
export interface AgendaItem {
  section: MeetingSection
  duration_s: number
}

export interface Attendee {
  id: string
  name: string
  role: Role
  joined_at: IsoDateTime
  can_rate: boolean
}

export interface Meeting {
  id: string
  team_id: string
  facilitator: UserRef
  started_at: IsoDateTime
  ended_at: IsoDateTime | null
  current_section: MeetingSection
  section_started_at: IsoDateTime
  section_duration_s: number
  state_version: number
  agenda: AgendaItem[]
  attendees: Attendee[]
  ratings: { user_id: string; rating: number }[]
  average_rating: number | null
}

export interface MeetingState {
  meeting: Meeting | null
  server_now: IsoDateTime
}

export interface MeetingListItem {
  id: string
  started_at: IsoDateTime
  ended_at: IsoDateTime | null
}

export interface MeetingSummary {
  meeting_id: string
  team_id: string
  facilitator: UserRef
  started_at: IsoDateTime
  ended_at: IsoDateTime
  scorecard_week: IsoDate
  measurables: {
    id: string
    name: string
    unit: string
    value: number | null
    status: MeasurableStatus
  }[]
  issues_solved: { id: string; title: string; resolution_note: string | null }[]
  todos_created: {
    id: string
    title: string
    owner: UserRef
    due_date: IsoDate
  }[]
  attendees: UserRef[]
  ratings: { user: UserRef; rating: number }[]
  average_rating: number | null
}

/** RFC 9457 problem details with the backend's stable `code`. */
export interface Problem {
  title: string
  status: number
  code: string
  detail?: string | null
  request_id?: string | null
  errors?: { loc?: (string | number)[]; msg?: string }[] | null
}

// WebSocket messages (server -> client)
export type RealtimeResource = "scorecard" | "issues" | "todos"

export type SocketMessage =
  | { type: "meeting.state"; data: MeetingState }
  | { type: "data.changed"; resources: RealtimeResource[] }
  | { type: "pong"; server_now: IsoDateTime }
