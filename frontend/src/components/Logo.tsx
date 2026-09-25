/** CodeLoop mark: a heartbeat held inside a closed loop. Source: docs/brand/codeloop-icon.svg */
export function Logo({ size = 40 }: { size?: number }) {
  return (
    <svg viewBox="0 0 128 128" width={size} height={size} aria-hidden="true">
      <rect width="128" height="128" rx="28" fill="#0b1117" stroke="#243242" strokeWidth="2" />
      <g transform="translate(9.6 9.6) scale(0.85)">
        <path
          d="M22 66 H43 L49.5 49 L58 85 L65.5 55 L70.5 66 H106"
          fill="none"
          stroke="#e8eef4"
          strokeWidth="7.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        <circle cx="64" cy="64" r="44" fill="none" stroke="#35d0b5" strokeWidth="10" />
      </g>
    </svg>
  )
}
