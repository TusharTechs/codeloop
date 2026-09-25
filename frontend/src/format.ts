import type { CodeEvent, Loop } from './types'

export function mmss(seconds: number | null | undefined): string {
  if (seconds == null || !Number.isFinite(seconds)) return '--:--'
  const s = Math.max(0, Math.floor(seconds))
  return `${String(Math.floor(s / 60)).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}`
}

export function num(v: number | string | null | undefined): string {
  if (v == null || v === '') return ''
  const n = typeof v === 'string' ? Number(v) : v
  return Number.isInteger(n) ? String(n) : String(+n.toFixed(2))
}

export function drugName(d: string | null | undefined): string {
  return (d ?? 'drug').replace(/_/g, ' ')
}

export function cap(s: string): string {
  return s ? s[0].toUpperCase() + s.slice(1) : s
}

export function loopTitle(l: Loop): { name: string; value: string; unit: string } {
  if (l.action === 'shock') return { name: 'Shock', value: num(l.ordered_value), unit: l.ordered_value != null ? 'J' : '' }
  return { name: cap(drugName(l.drug)), value: num(l.ordered_value), unit: l.ordered_value != null ? l.unit ?? '' : '' }
}

export function eventChip(e: CodeEvent): { label: string; tone: string } | null {
  const what =
    e.action === 'shock'
      ? `shock ${num(e.energy_j)}${e.energy_j != null ? ' J' : ''}`
      : e.action === 'drug'
        ? `${drugName(e.drug)} ${num(e.dose)} ${e.dose != null ? e.unit ?? '' : ''}`.trim()
        : ''
  const tone = e.unconfirmed ? 'warn' : ''
  switch (e.kind) {
    case 'order':
      return { label: `ORDER ${what}`, tone: tone || 'order' }
    case 'ack':
      return { label: `READ BACK ${what}`.trim(), tone: tone || 'ack' }
    case 'done':
      return { label: `GIVEN ${what}`, tone: tone || 'done' }
    case 'cancel':
      return { label: `CANCEL ${what}`.trim(), tone: 'warn' }
    case 'rhythm':
      return { label: `RHYTHM ${e.rhythm}`, tone: '' }
    case 'rhythm_check':
      return { label: 'RHYTHM CHECK', tone: '' }
    case 'cpr_start':
      return { label: 'CPR START', tone: '' }
    case 'cpr_pause':
      return { label: 'CPR PAUSE', tone: '' }
    case 'cpr_resume':
      return { label: 'CPR RESUME', tone: '' }
    case 'rosc':
      return { label: 'ROSC?', tone: 'warn' }
    case 'terminate':
      return { label: 'TERMINATE?', tone: 'warn' }
    case 'question':
      return { label: 'QUESTION FOR CODELOOP', tone: '' }
    case 'role':
      return { label: `ROLE ${e.name ? e.name + ' → ' : ''}${e.role}`, tone: '' }
    default:
      return null
  }
}

export const ROLES = ['leader', 'meds', 'compressor', 'airway', 'recorder'] as const
