# Frontend

Next.js 16 (App Router) · TypeScript · Tailwind 4 · shadcn/ui (Radix) · TanStack Query.

```bash
npm install
API_INTERNAL_URL=http://localhost:8000 npm run dev   # needs the API running (docker compose up api)
npm run typecheck && npm run lint
npx playwright test                                 # two-browser meeting test, against :3000
```

## How data moves

| Concern | Approach |
|---|---|
| Same origin | The browser only talks to Next. `next.config.ts` rewrites `/api/*` (REST and the WebSocket upgrade) to FastAPI, so the HttpOnly session cookie works everywhere and there is no CORS. |
| First paint | Server Components fetch with the forwarded cookie (`lib/api/server.ts`). Each Team page section fetches in its own `Suspense` boundary, so they stream in parallel. `React.cache` dedupes `me` and the team across layout and page. |
| Access | `proxy.ts` only checks a cookie exists. The API decides: 401 → sign-in, 404 (missing *or* not your team, same answer) → `not-found.tsx`. Observers get no write controls, and the API refuses their writes anyway. |
| Server state | Client islands take server data as `initialData` for TanStack Query (`features/*/queries.ts`, keys in `lib/query-keys.ts`). Mutations invalidate the same keys. Scores and To-Do checkboxes update optimistically and roll back on error. |
| Live updates | One WebSocket per team (`features/realtime/team-realtime.tsx`). `meeting.state` snapshots are written straight into the cache, ignoring older `state_version`s; `data.changed` invalidates the named resources. Reconnects back off and refetch everything on screen. |
| Meeting clock | The server owns time. Every `server_now` (snapshots, command responses, `pong`) sets a clock offset (`lib/server-clock.ts`); only the clock and agenda track re-render each second. |
| Commands | Advance sends `expected_section`; a 409 means another tab moved first, so the cache refetches and a toast says so. |

## Design system

Subject: a leadership team's weekly numbers and the meeting they run on them, for a Chicago company. Job: read the state of the business in seconds, and run a 75-minute meeting under time pressure.

- **Type.** *Big Shoulders* (designed for the City of Chicago's signage) for titles, numbers that matter and the meeting clock; *Atkinson Hyperlegible Next* (built for low-vision legibility) for everything else. Numbers use tabular figures.
- **Color.** Tokens live in `app/globals.css` (light and dark). Cool paper `#f3f5f6`, blue-black ink `#121c26`, lake blue `#0b5c80` for actions, sky `#a9d8ee` for "now". Two signal colors mean one thing each: green `#1f7a4d` on track, red `#c8281e` off track. Pending is a grey hatch, never a color.
- **Status never relies on color.** Circle = on track, triangle = off track, ring = pending (`components/status-mark.tsx`); off-track cells also carry a corner notch, and every cell has a spoken label.
- **Structure.** Sections sit on the page under a heavy rule, not in cards. Numbering appears only where order is the content (Issue order). The agenda track's segment widths are the real 5 / 60 / 10 minute split.
- **Components.** shadcn primitives restyled through tokens and variants (taller controls, 4px radius, white fields on paper), composed into feature components under `features/`.

## Layout

```
app/                 routes: sign-in, teams/[teamId] (Team page), teams/[teamId]/meetings/[meetingId]
features/
  shell/             header, team switcher, user menu, live-meeting pill
  scorecard/         13-week grid, cell editor (score, Make it an Issue)
  issues/            Issue order list, create, priority, solve, add To-Do
  todos/             list, done/undo, last week's completion against 90%
  rocks/             read-only Server Component
  meeting/           agenda track, clock, controls, rating, attendees, summary
  realtime/          WebSocket → query cache
  team/              team context, queries and mutations
lib/                 API clients, types, formatting, status tokens, server clock
components/ui/       shadcn components (customized)
e2e/                 Playwright
```
