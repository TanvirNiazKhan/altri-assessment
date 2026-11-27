"use client"

import { useSyncExternalStore } from "react"

/**
 * The server owns time (APP_NOW + elapsed), which can be days away from the browser's
 * clock. Every `server_now` we receive updates the offset; the meeting timer renders
 * from `Date.now() + offset`, so every browser shows the same clock.
 */
let offsetMs = 0
let synced = false
const listeners = new Set<() => void>()
let ticker: ReturnType<typeof setInterval> | null = null

export function syncServerClock(serverNowIso: string) {
  const serverNow = Date.parse(serverNowIso)
  if (Number.isNaN(serverNow)) return
  offsetMs = serverNow - Date.now()
  synced = true
  emit()
}

export function serverNow() {
  return Date.now() + offsetMs
}

function emit() {
  listeners.forEach((l) => l())
}

function subscribe(listener: () => void) {
  listeners.add(listener)
  if (!ticker) ticker = setInterval(emit, 250)
  return () => {
    listeners.delete(listener)
    if (listeners.size === 0 && ticker) {
      clearInterval(ticker)
      ticker = null
    }
  }
}

/**
 * Current server time, floored to the second: the store is polled 4×/s but the
 * snapshot only changes once a second, so subscribers re-render once a second.
 * `null` during SSR and before the first sync, so markup never mismatches on hydration.
 */
export function useServerNow(): number | null {
  return useSyncExternalStore(
    subscribe,
    () => (synced ? Math.floor(serverNow() / 1000) * 1000 : null),
    () => null
  )
}
