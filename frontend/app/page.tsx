import { redirect } from "next/navigation"

import { getMe } from "@/lib/api/server"

export default async function Home() {
  const me = await getMe()
  const first = me.teams[0]
  redirect(first ? `/teams/${first.id}` : "/sign-in")
}
