import type { CodeState, Control } from '../types'

// Tap-to-log fallback for when the room is too loud or a value must be entered by hand.
// Everything logged here is marked "entered on screen" in the record.
export function QuickLog({ state, send }: { state: CodeState; send: (c: Control) => void }) {
  const cprLabel = state.cpr.running ? 'Pause CPR' : state.status === 'not_started' ? 'Start CPR' : 'Resume CPR'
  return (
    <div className="quick">
      <button className="btn" onClick={() => send({ type: 'manual_event', kind: state.cpr.running ? 'cpr_pause' : state.status === 'not_started' ? 'cpr_start' : 'cpr_resume' })}>
        {cprLabel}
      </button>
      <button className="btn" onClick={() => send({ type: 'manual_event', kind: 'done', action: 'shock', energy_j: 200 })}>
        Shock 200 J
      </button>
      <button className="btn" onClick={() => send({ type: 'manual_event', kind: 'done', action: 'drug', drug: 'epinephrine', dose: 1, unit: 'mg' })}>
        Epi 1 mg given
      </button>
      <button className="btn" onClick={() => send({ type: 'manual_event', kind: 'done', action: 'drug', drug: 'amiodarone', dose: state.last_drugs.amiodarone ? 150 : 300, unit: 'mg' })}>
        Amio {state.last_drugs.amiodarone ? 150 : 300} mg given
      </button>
      {(['VF', 'PEA', 'ASYSTOLE'] as const).map((r) => (
        <button key={r} className="btn" onClick={() => send({ type: 'manual_event', kind: 'rhythm', rhythm: r })}>
          Rhythm {r === 'ASYSTOLE' ? 'asystole' : r}
        </button>
      ))}
    </div>
  )
}
