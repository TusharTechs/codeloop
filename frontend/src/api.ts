import type { CodeRecord, Scenario } from './types'

const TOKEN_KEY = 'codeloop.accessCode'

export function getToken(): string {
  try {
    return localStorage.getItem(TOKEN_KEY) ?? ''
  } catch {
    return ''
  }
}

export function setToken(t: string): void {
  try {
    localStorage.setItem(TOKEN_KEY, t)
  } catch {
    /* private mode: keep it in memory only */
  }
}

export class ApiError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

async function call<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getToken()
  const res = await fetch(path, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(init?.headers ?? {}),
    },
  })
  if (!res.ok) {
    let detail = res.statusText
    try {
      detail = (await res.json()).detail ?? detail
    } catch {
      /* not JSON */
    }
    throw new ApiError(res.status, detail)
  }
  return res.json() as Promise<T>
}

export const api = {
  health: () => call<{ ok: boolean; assemblyai_key: boolean; active_codes: number; auth_required: boolean }>('/api/health'),
  scenarios: () => call<Scenario[]>('/api/scenarios'),
  codes: () => call<{ id: string; created_at: string; mode: string; scenario: string | null; status: string; outcome: string | null; summary: Record<string, unknown> | null }[]>('/api/codes'),
  start: (mode: 'live' | 'replay', scenario?: string) =>
    call<{ id: string; mode: string; scenario: string | null }>('/api/codes', { method: 'POST', body: JSON.stringify({ mode, scenario }) }),
  record: (id: string) => call<CodeRecord>(`/api/codes/${id}/record`),
}

export function socketUrl(codeId: string): string {
  const proto = location.protocol === 'https:' ? 'wss' : 'ws'
  const token = getToken()
  return `${proto}://${location.host}/ws/codes/${codeId}${token ? `?token=${encodeURIComponent(token)}` : ''}`
}
