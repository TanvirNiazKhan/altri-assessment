import { NextResponse, type NextRequest } from "next/server"

// Optimistic check only: no cookie, no app. The API verifies the signed cookie on every call.
export function proxy(request: NextRequest) {
  if (!request.cookies.has("l10_session")) {
    const url = request.nextUrl.clone()
    url.pathname = "/sign-in"
    url.search = ""
    return NextResponse.redirect(url)
  }
  return NextResponse.next()
}

export const config = {
  matcher: ["/", "/teams/:path*"],
}
