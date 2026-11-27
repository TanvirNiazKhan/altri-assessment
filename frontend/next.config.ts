import type { NextConfig } from "next"

// FastAPI is reached through this origin: the browser calls /api/*, Next forwards it.
// Same origin means the HttpOnly session cookie works for REST and the WebSocket alike.
const API_URL = process.env.API_INTERNAL_URL ?? "http://localhost:8000"

const nextConfig: NextConfig = {
  output: "standalone",
  poweredByHeader: false,
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${API_URL}/api/:path*` }]
  },
}

export default nextConfig
