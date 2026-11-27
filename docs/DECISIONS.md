# Decision record

The decisions the brief (§2.8) leaves open, with what I chose and what it costs.

## 1. Data model and how Issues and To-Dos link to their sources

- **Ids**: seed ids are kept as `TEXT` primary keys (`u1`, `t12`). New rows get ids of the same shape from Postgres sequences that start at 1000 (`i1000`, `t1000`, `mt1000`).
- **Issue sources**: an Issue's source is a nullable `source_type` (`measurable` | `rock`) with one real FK column per kind (`source_measurable_id` + `source_week_start`, `source_rock_id`). A CHECK makes the columns match the type.
  - I chose this over a polymorphic `(source_kind, source_id)` pair, which can't carry a foreign key.
  - Adding another source kind costs one column.
- **To-Do sources**: a To-Do links to its Issue with `source_issue_id`.
- **Team-scoped foreign keys**: every cross-entity link is a composite FK, e.g. `(source_issue_id, team_id) → issues(id, team_id)`. The database itself rejects an Issue or To-Do that points at another team's data.
- **Meeting provenance is stored, not inferred**: `issues.solved_in_meeting_id` and `todos.created_in_meeting_id` are stamped when the action happens during the team's active meeting, from either page. For the two seeded meetings they are derived once, from each meeting's time window.
- **Invariants in Postgres**:
  - CHECKs: goal shape, priority 1–5, rating 1–10, Monday-only `week_start`, solved ⇔ note;
  - partial unique indexes: one open Issue per Measurable-week, one active meeting per team;
  - triggers: Observers can't own or facilitate anything; ratings are frozen once a meeting ends.

  Constraint violations are translated into domain errors with stable codes.
- **Time**:
  - `timestamptz` in UTC; due dates and `week_start` are calendar dates in company time.
  - Week boundaries are computed per date with `zoneinfo`, so the DST change on Nov 1 moves the week end from 05:00Z to 06:00Z. The seed records at 05:30Z and 05:59Z / 06:01Z depend on this.
  - "Now" is an injected `Clock`: `APP_NOW` + elapsed time, or frozen for tests and the report.
- **Cost**: more columns and constraints than a loose schema, and a migration whenever a rule changes. In return, invalid data can't exist whatever the API does.

## 2. API design

- **REST under `/api`**, documented by OpenAPI at `/api/docs`.
- **URLs**: every team resource sits under `/teams/{team_id}/…`, so one dependency (`ReadTeam` / `WriteTeam`) authorizes every route the same way. Child lookups always filter by `team_id`.
- **Actions**: non-CRUD actions are sub-resources (`/solve`, `/done`, `/advance`, `/end`, `/rating`, `/issue`). Retries are idempotent where it matters: done/undo, join, and Make it an Issue (200 for an existing Issue, 201 for a new one).
- **Errors** are RFC 9457 `problem+json` with a stable `code` and a `request_id`. Missing and inaccessible teams both return the same 404, so ids can't be probed.
- **Validation**: bodies reject unknown fields, and limits mirror the DB constraints.
- **Auth**: a seeded-user switcher sets a signed HttpOnly SameSite=Lax cookie.
- **Cost**: action endpoints are less uniform than pure CRUD, but they match the domain's verbs and keep the rules in one place.

## 3. Real-time transport and how meeting state is owned and recovered

- **Commands go over REST; the WebSocket only pushes from server to client.** There is one write path, with the same validation, authorization and tests.
- **Postgres owns all meeting state**: section, `section_started_at`, facilitator, `state_version`. Nothing lives only in memory, so an API restart loses nothing.
- **Transitions are conditional updates** (`… WHERE current_section = :expected AND ended_at IS NULL`). Double clicks and stale tabs get a 409; they can't skip a section.
- **Fan-out**: each write calls `pg_notify` inside its own transaction, so the event fires only on commit. Every API process LISTENs and pushes to its own sockets:
  - `meeting.state`: a full snapshot including `server_now`;
  - `data.changed`: tells the client to refetch that resource over REST.

  This syncs multiple workers without adding Redis. NOTIFY payloads are tiny because clients refetch.
- **Timer**: the server sends `section_started_at`, the section's duration and `server_now`. Clients render from their offset to the server clock, so every browser shows the same time.
  - An overrun shows as over time; the section never auto-advances.
- **Recovery**:
  - Every socket gets the current snapshot on (re)connect, so late joins, refreshes and reconnects all recover the same way.
  - The facilitator is a user, not a socket, so a refresh keeps control.
  - If the LISTEN connection drops, the server pushes a full resync to every connected client after it reconnects.
- **Cost**: events can be missed while a client is disconnected (covered by snapshot-on-connect), and NOTIFY can't scale past one Postgres. Redis or NATS pub/sub would be the next step.

## 4. Make it an Issue stays duplicate-free under concurrent requests

The database guarantees it; the application doesn't need locks.
- A partial unique index on `(source_measurable_id, source_week_start) WHERE source_type = 'measurable' AND solved_at IS NULL` allows at most one open Issue per cell.
- The insert uses `INSERT … ON CONFLICT (…) WHERE … DO NOTHING RETURNING id`. A concurrent duplicate waits for the first transaction to commit, then does nothing; a fresh `SELECT` returns the winner's row.
- **Result**: one 201; every other caller gets 200 with the same id. A test fires 20 requests at once and checks this.
- Solving the Issue frees the slot.
- **Why not SELECT-then-INSERT or app locks**: both race across processes. The index is the actual guarantee.

## 5. Keeping past meeting summaries unchanged

- **Snapshot on end**: the transaction that sets `ended_at` also builds the summary and stores it as JSONB in `meeting_summaries`.
  - It holds Measurable statuses for the reviewed week, with names and values, plus solved Issues, created To-Dos, attendees, ratings and the average.
  - It is written once and never overwritten. The seeded meetings get theirs from the same code, at seed time.
- **Why it stays fixed**: later edits to scores, titles or names can't change it, and the ratings trigger blocks changes after the end. A test edits a score after the end and checks that the summary is unchanged.
- **Cost**: the snapshot is denormalized, so it can disagree with current data. That is the intended behavior.
- **Alternative**: history tables (`valid_from` / `valid_to`, query as of `ended_at`) or event sourcing would rebuild any past view, not just this one, at much higher cost. I'd pick them if audits needed full reconstruction.
