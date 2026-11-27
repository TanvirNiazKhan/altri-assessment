# altri-assessment: Level 10 Meeting App

A team operating system in the EOS style. Teams track weekly **Measurables** (Scorecard), quarterly **Rocks**, **To-Dos** and **Issues**, and run a live, multi-browser **Level 10 Meeting**: Scorecard 5 min → IDS 60 min → Conclude 10 min.

| Part | Stack | Status |
|---|---|---|
| `backend/` | FastAPI, SQLAlchemy 2 (async), Alembic, PostgreSQL 16 | Complete for the spec: every 2.5 action, 2.6 rule, real-time meetings and the rules report |
| `frontend/` | Next.js 16 (App Router), TypeScript, Tailwind 4, shadcn/ui, TanStack Query | Team page, live meeting page, summaries; [design and structure](frontend/README.md) |

API docs: OpenAPI at `/api/docs`

## Setup

Requires Docker.

```bash
docker compose up --build    # Postgres + API + web; migrations and the seed run on boot (rerun-safe)
open http://localhost:3000       # the app
open http://localhost:8000/api/docs
```

Pick a seeded person on the sign-in page (or `POST /api/auth/login {"user_id": "u2"}`). Open a second browser, or a private window, as someone else to join the same meeting. Seeded users:

| Users | Role |
|---|---|
| `u1` | Admin |
| `u2`–`u4`, `u6`, `u8`, `u9` | Team Member |
| `u5`, `u7` | Observer |

Other commands:
- `make reset`: wipe and reseed.
- `make logs`: follow the API logs.

Environment variables:

| Variable | Default | Notes |
|---|---|---|
| `APP_NOW` | `2026-11-11T15:00:00Z` | The app's "now". Nothing reads the system clock. |
| `APP_CLOCK_MODE` | `running` | `running` = `APP_NOW` + elapsed time (meeting timers tick); `frozen` = exactly `APP_NOW` |
| `SESSION_SECRET` | dev value | Required when `ENVIRONMENT=production` |

## Tests

```bash
make test        # unattended: 180+ tests in the API container against Postgres
make check       # lint (ruff) + types (mypy --strict) + tests
```

| Layer | What it proves |
|---|---|
| Rule tests (`tests/domain`) | Every 2.6 rule at its boundaries: goal edges, closed vs. current week with no score, exactly 90%, done one minute either side of a DST week end, milestone due today vs. yesterday, 12.5 → 13, 8.25 → 8.3, Issue order ties and nulls, no ratings → none |
| API tests (`tests/api`) | A Team Member reading another team → 404 (every endpoint, and team-scoped child ids). Every Observer write → 403. **20 concurrent Make it an Issue → exactly one Issue**, one 201. Concurrent meeting starts → one meeting. Facilitator-only, stale-section and rating rules. The summary stays frozen after later edits. |
| Real-time (`tests/api/test_realtime.py`) | Real uvicorn server and real WebSockets: the second browser follows the facilitator through every section, late join recovers state, events stay within the team, sockets need access |
| Rules report (`tests/infra`) | Fresh seed equals the committed `rules_report.json`; spot checks at two other dates |

**Fixture and clock strategy**:
- **Clock**: every app under test uses a `FrozenClock` at `APP_NOW`; timer tests call `clock.advance()`.
- **Database**: once per session a template database is migrated and seeded. Each DB test gets its own copy (`CREATE DATABASE … TEMPLATE`), so tests write freely, run real concurrent transactions and never share state.

```bash
make up && make e2e   # Playwright: facilitator advances the agenda, the second browser follows
```

The e2e test runs against the real stack and is rerunnable: it ends any meeting a previous run left open. Failures keep a trace, screenshots and video in `frontend/test-results/` (`npx playwright show-trace <trace.zip>`).

## Rules report

```bash
make rules-report                               # fresh seeded DB at APP_NOW → rules_report.json
APP_NOW=2026-11-18T15:00:00Z make rules-report  # any other date
```

It runs `python -m src.cli rules-report`: create a throwaway database, migrate, seed, compute, print JSON, drop the database. The default-date output is committed as [`rules_report.json`](rules_report.json), and a test keeps it in sync.

## Assumptions

1. **The report is "as of now".** Timestamped facts count only once they've happened: To-Dos created or done, Issues created or solved, meetings ended. Facts without timestamps (scores, Milestone flags, seeded Rock status) are used as stored.
2. **Completion.** A To-Do counts as done for its week if `done_at` is before the next Monday 00:00 company time and not after now. The current week's rate is provisional.
3. **Scores** can be set or cleared for any week in the 13-week window up to the current week, never for future weeks.
4. **Make it an Issue** works only on `off_track` cells, so not on pending ones. The new Issue has no priority.
5. **Admins can act in every team.** An Issue's owner is its creator (an Admin may not be a member). A To-Do's owner must be an Admin or Team Member who is a member of that team.
6. **Any Admin or Team Member of the team** can set priority, solve, add To-Dos and mark any To-Do done, not only the owner.
7. **Meetings.**
   - Attendance means opening the meeting page while it's active; Observers attend but can't rate.
   - Ratings open in Conclude and freeze when the meeting ends.
   - Issues solved and To-Dos created during the team's active meeting, from either page, belong to that meeting.
8. **A meeting's Scorecard week** is the last closed week when it started.

## Known limitations

- No real authentication: a seeded-user switcher, as the brief allows.
- NOTIFY fan-out is bounded by one Postgres. At scale, I'd move it to Redis or NATS pub/sub.
- `APP_CLOCK_MODE=running` restarts from `APP_NOW` when the API restarts. A meeting started before a restart keeps its `section_started_at`, so its timer can look odd until the next section.
- No online-presence indicator; attendees are the people who joined.
- Bonus items are not done: Make it an Issue from Rocks or To-Dos (the schema and index for Rocks exist), lost-update protection, the audit trail.

## AI tools used

- **Claude Code**:
  - requirement analysis from the brief;
  - finding seed edge cases (DST week ends, the exact 90% boundary);
  - backend architecture and implementation;
  - the frontend: design system, components, realtime client, and the Playwright test;
  - visual checks of every page at phone and desktop widths, light and dark, from Playwright screenshots;
  - tests, and these docs.
- I reviewed every generated part, and verified it with the test suite and an independent re-computation of all 91 seeded scorecard cells.
