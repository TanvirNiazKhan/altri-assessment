import pytest

from tests.conftest import LoginAs

pytestmark = pytest.mark.db

ISSUES = "/api/teams/team_lead/issues"
TODOS = "/api/teams/team_lead/todos"


# ------------------------------------------------------------------ issues


async def test_open_issues_in_issue_order(login_as: LoginAs) -> None:
    u2 = await login_as("u2")
    issues = (await u2.get(ISSUES)).json()
    assert [i["id"] for i in issues] == ["i2", "i1", "i5", "i3", "i4"]
    i5 = issues[2]
    assert i5["source"]["measurable_name"] == "New deals closed"
    assert i5["source"]["week_start"] == "2026-11-02"
    assert i5["owner"] == {"id": "u2", "name": "Blake Brooks"}


async def test_solved_issues_listed_separately(login_as: LoginAs) -> None:
    u2 = await login_as("u2")
    solved = (await u2.get(ISSUES, params={"status": "solved"})).json()
    assert [i["id"] for i in solved] == ["i6", "i7"]
    assert all(i["solved_at"] and i["resolution_note"] for i in solved)


async def test_create_issue_owned_by_creator_and_ordered(login_as: LoginAs) -> None:
    u3 = await login_as("u3")
    r = await u3.post(ISSUES, json={"title": "  Server costs up  ", "priority": 5})
    assert r.status_code == 201
    created = r.json()
    assert created["title"] == "Server costs up"
    assert created["owner"]["id"] == "u3"
    assert created["created_at"] == "2026-11-11T15:00:00Z"
    order = [i["id"] for i in (await u3.get(ISSUES)).json()]
    assert order[:3] == ["i2", "i1", created["id"]]  # P5, newest of the three


@pytest.mark.parametrize(
    "body",
    [{"title": ""}, {"title": "   "}, {"title": "x" * 201}, {"title": "x", "priority": 0},
     {"title": "x", "priority": 6}, {"title": "x", "owner_id": "u1"}, {}],
)  # fmt: skip
async def test_create_issue_validation(login_as: LoginAs, body: dict[str, object]) -> None:
    u2 = await login_as("u2")
    r = await u2.post(ISSUES, json=body)
    assert (r.status_code, r.json()["code"]) == (422, "validation_error")


async def test_set_and_clear_priority(login_as: LoginAs) -> None:
    u2 = await login_as("u2")
    assert (await u2.patch(f"{ISSUES}/i4", json={"priority": 5})).json()["priority"] == 5
    assert (await u2.get(ISSUES)).json()[0]["id"] == "i4"  # P5, oldest
    assert (await u2.patch(f"{ISSUES}/i4", json={"priority": None})).json()["priority"] is None
    assert (await u2.patch(f"{ISSUES}/i4", json={})).status_code == 422  # key is required


async def test_solve_requires_note_and_happens_once(login_as: LoginAs) -> None:
    u2 = await login_as("u2")
    blank = await u2.post(f"{ISSUES}/i1/solve", json={"note": "   "})
    assert blank.status_code == 422
    solved = await u2.post(f"{ISSUES}/i1/solve", json={"note": "Hired two recruiters"})
    assert solved.status_code == 200
    body = solved.json()
    assert body["solved_at"] == "2026-11-11T15:00:00Z"
    assert body["resolution_note"] == "Hired two recruiters"
    assert body["solved_in_meeting_id"] is None  # no meeting running
    again = await u2.post(f"{ISSUES}/i1/solve", json={"note": "again"})
    assert (again.status_code, again.json()["code"]) == (409, "issue_already_solved")
    assert "i1" not in [i["id"] for i in (await u2.get(ISSUES)).json()]


# ------------------------------------------------------------------ to-dos


async def test_add_todo_from_issue_due_in_7_days(login_as: LoginAs) -> None:
    u2 = await login_as("u2")
    r = await u2.post(f"{ISSUES}/i1/todos", json={"title": "Call agency", "owner_id": "u4"})
    assert r.status_code == 201
    todo = r.json()
    assert todo["due_date"] == "2026-11-18"
    assert todo["owner"]["id"] == "u4"
    assert todo["source_issue"] == {"id": "i1", "title": "Hiring pipeline is slow"}
    assert todo["overdue"] is False and todo["done_at"] is None


@pytest.mark.parametrize(
    ("owner", "code"),
    [("u5", "invalid_owner"), ("u6", "invalid_owner"), ("nobody", "invalid_owner")],
)  # Observer of the team; Team Member of another team; unknown user
async def test_todo_owner_must_be_team_admin_or_member(
    login_as: LoginAs, owner: str, code: str
) -> None:
    u2 = await login_as("u2")
    r = await u2.post(f"{ISSUES}/i1/todos", json={"title": "x", "owner_id": owner})
    assert (r.status_code, r.json()["code"]) == (422, code)


async def test_todo_list_flags_overdue_and_reports_completion(login_as: LoginAs) -> None:
    u2 = await login_as("u2")
    body = (await u2.get(TODOS)).json()
    overdue = sorted(t["id"] for t in body["items"] if t["overdue"])
    assert overdue == ["t12", "t31"]
    assert next(t for t in body["items"] if t["id"] == "t30")["overdue"] is False  # due today
    assert body["last_closed_week"] == {
        "week_start": "2026-11-02",
        "completion": {"due": 10, "done": 9, "rate_percent": 90, "meets_target": True},
        "target_percent": 90,
    }


async def test_mark_done_and_undo_are_idempotent(login_as: LoginAs) -> None:
    u2 = await login_as("u2")
    first = (await u2.put(f"{TODOS}/t12/done")).json()
    assert first["done_at"] == "2026-11-11T15:00:00Z" and first["overdue"] is False
    assert (await u2.put(f"{TODOS}/t12/done")).json()["done_at"] == first["done_at"]
    undone = (await u2.delete(f"{TODOS}/t12/done")).json()
    assert undone["done_at"] is None and undone["overdue"] is True
    assert (await u2.delete(f"{TODOS}/t12/done")).status_code == 200


async def test_unknown_todo_is_404(login_as: LoginAs) -> None:
    u2 = await login_as("u2")
    r = await u2.put(f"{TODOS}/t9999/done")
    assert (r.status_code, r.json()["code"]) == (404, "todo_not_found")


# ------------------------------------------------------------------ rocks


async def test_rocks_current_quarter_with_computed_status_and_progress(login_as: LoginAs) -> None:
    u2 = await login_as("u2")
    rocks = {r["id"]: r for r in (await u2.get("/api/teams/team_lead/rocks")).json()}
    assert {k: (v["status"], v["progress_percent"]) for k, v in rocks.items()} == {
        "r1": ("on_track", 33),
        "r2": ("off_track", 13),
        "r3": ("complete", 100),
        "r4": ("off_track", 0),
        "r5": ("on_track", 0),
    }
    assert [m["id"] for m in rocks["r1"]["milestones"]] == ["ms1", "ms2", "ms3"]
    assert rocks["r1"]["owner"]["name"]
