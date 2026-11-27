import { expect, test, type Browser, type Page } from "@playwright/test"

/**
 * Two browsers in one Level 10 Meeting: the facilitator advances the agenda and the
 * second browser follows over the WebSocket, without reloading.
 */
const TEAM = "team_lead"
const FACILITATOR = "u2" // Blake Brooks, Team Member
const FOLLOWER = "u3" // Casey Cho, Team Member

async function signedInPage(
  browser: Browser,
  baseURL: string,
  userId: string
): Promise<Page> {
  const context = await browser.newContext({ baseURL })
  const res = await context.request.post("/api/auth/login", {
    data: { user_id: userId },
  })
  expect(res.ok()).toBeTruthy()
  return context.newPage()
}

/** Rerunnable: if an earlier run left a meeting open, its facilitator ends it. */
async function endActiveMeeting(browser: Browser, baseURL: string) {
  const ctx = await browser.newContext({ baseURL })
  await ctx.request.post("/api/auth/login", { data: { user_id: FACILITATOR } })
  const { meeting } = await (
    await ctx.request.get(`/api/teams/${TEAM}/meetings/active`)
  ).json()
  if (meeting) {
    await ctx.request.post("/api/auth/login", {
      data: { user_id: meeting.facilitator.id },
    })
    await ctx.request.post(`/api/teams/${TEAM}/meetings/${meeting.id}/end`)
  }
  await ctx.close()
}

test("the second browser follows the facilitator through the agenda", async ({
  browser,
  baseURL,
}) => {
  await endActiveMeeting(browser, baseURL!)
  const facilitator = await signedInPage(browser, baseURL!, FACILITATOR)
  const follower = await signedInPage(browser, baseURL!, FOLLOWER)

  await follower.goto(`/teams/${TEAM}`)
  await facilitator.goto(`/teams/${TEAM}`)
  await facilitator
    .getByRole("button", { name: "Start Level 10 Meeting" })
    .click()
  await facilitator.waitForURL(/\/meetings\//)

  // The follower learns about the meeting over the socket and joins.
  await follower
    .getByRole("link", { name: /Join meeting/ })
    .first()
    .click()
  await follower.waitForURL(facilitator.url())

  const currentStep = (page: Page) =>
    page.getByRole("list", { name: "Agenda" }).locator('[aria-current="step"]')
  await expect(currentStep(follower)).toContainText("Scorecard")
  await expect(
    follower.getByRole("heading", { name: "In the room" })
  ).toBeVisible()
  // Attendance reached the facilitator.
  await expect(
    facilitator
      .getByRole("region", { name: /In the room/ })
      .getByText("Casey Cho")
  ).toBeVisible()

  // Only the facilitator has the controls.
  await expect(follower.getByRole("button", { name: /Go to/ })).toHaveCount(0)

  await facilitator.getByRole("button", { name: "Go to IDS" }).click()
  await expect(currentStep(follower)).toContainText("IDS", { timeout: 2_000 })
  await expect(follower.getByRole("heading", { name: /^Issues/ })).toBeVisible()

  await facilitator.getByRole("button", { name: "Go to Conclude" }).click()
  await expect(currentStep(follower)).toContainText("Conclude", {
    timeout: 2_000,
  })

  // Both rate; the average reaches both screens.
  await facilitator.getByRole("radio", { name: "Rate 8" }).click()
  await follower.getByRole("radio", { name: "Rate 9" }).click()
  await expect(facilitator.getByText("8.5", { exact: true })).toBeVisible()
  await expect(follower.getByText("8.5", { exact: true })).toBeVisible()

  // A refresh (late join / reconnect) recovers the same state.
  await follower.reload()
  await expect(currentStep(follower)).toContainText("Conclude")

  await facilitator.getByRole("button", { name: "End meeting" }).click()
  await facilitator
    .getByRole("alertdialog")
    .getByRole("button", { name: "End meeting" })
    .click()
  await expect(
    follower.getByText("Later edits don't change this summary")
  ).toBeVisible({ timeout: 2_000 })
  await expect(follower.getByText("Rated 9")).toBeVisible()
})
