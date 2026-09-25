import type { QualityMetric } from '../types'

const MARK: Record<QualityMetric['status'], { cls: string; text: string }> = {
  met: { cls: 'ack', text: 'met' },
  missed: { cls: 'bad', text: 'missed' },
  info: { cls: '', text: '' },
  'n/a': { cls: '', text: '' },
}

/** Resuscitation quality measures against AHA / GWTG-Resuscitation targets. */
export function QualityList({ metrics, compact = false }: { metrics: QualityMetric[]; compact?: boolean }) {
  if (!metrics.length) return <div className="empty">Measures appear once the code starts.</div>
  return (
    <div className={`quality ${compact ? 'compact' : ''}`}>
      {metrics.map((m) => (
        <div key={m.key} className="q-row">
          <span className="q-label">
            {m.label}
            {!compact && m.note && <span className="faint"> · {m.note}</span>}
          </span>
          <span className="q-value mono">{m.display}</span>
          {!compact && <span className="q-target faint">{m.target}</span>}
          <span className="q-status">{MARK[m.status].text && <span className={`chip ${MARK[m.status].cls}`}>{MARK[m.status].text}</span>}</span>
        </div>
      ))}
    </div>
  )
}
