import { useEffect } from 'react'
import type { GuideItem } from '../state'

const SHOW_MS = 14000

/** "What just happened" captions for anyone watching a replay or a demo. */
export function Guide({ items, dismiss }: { items: GuideItem[]; dismiss: (id: string) => void }) {
  useEffect(() => {
    if (!items.length) return
    const next = Math.min(...items.map((g) => g.at + SHOW_MS)) - performance.now()
    const t = window.setTimeout(() => {
      const now = performance.now()
      items.filter((g) => now - g.at >= SHOW_MS - 50).forEach((g) => dismiss(g.id))
    }, Math.max(50, next))
    return () => window.clearTimeout(t)
  }, [items, dismiss])

  if (!items.length) return null
  return (
    <div className="guide noprint" aria-live="polite" aria-label="What just happened">
      {items.map((g) => (
        <div key={g.id} className={`guide-card ${g.tone}`}>
          <div className="guide-head">
            <span className="upper">What just happened</span>
            <button className="guide-x" onClick={() => dismiss(g.id)} aria-label="Dismiss">
              ×
            </button>
          </div>
          <div className="guide-title">{g.title}</div>
          <div className="guide-body">{g.body}</div>
        </div>
      ))}
    </div>
  )
}
