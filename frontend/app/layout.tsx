import type { Metadata, Viewport } from "next"
import { Atkinson_Hyperlegible_Next, Big_Shoulders } from "next/font/google"

import "./globals.css"
import { Providers } from "@/components/providers"
import { cn } from "@/lib/utils"

// Body: built for legibility at a glance — the meeting page is read under time pressure.
const body = Atkinson_Hyperlegible_Next({
  subsets: ["latin"],
  variable: "--font-body",
  display: "swap",
})

// Display: Chicago's civic signage face. Section titles, team names, the meeting clock.
const display = Big_Shoulders({
  subsets: ["latin"],
  variable: "--font-display",
  weight: ["700", "800", "900"],
  fallback: ["Arial Narrow", "Roboto Condensed", "sans-serif"],
  adjustFontFallback: false,
  display: "swap",
})

export const metadata: Metadata = {
  title: { default: "Level 10", template: "%s · Level 10" },
  description:
    "Scorecard, Rocks, To-Dos, Issues and the weekly Level 10 Meeting.",
}

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#f3f5f6" },
    { media: "(prefers-color-scheme: dark)", color: "#0e161e" },
  ],
}

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html
      lang="en"
      suppressHydrationWarning
      className={cn("antialiased", body.variable, display.variable)}
    >
      <body className="min-h-dvh">
        <Providers>{children}</Providers>
      </body>
    </html>
  )
}
