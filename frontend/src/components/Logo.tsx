export function Logo({ size = 40 }: { size?: number }) {
  return (
    <svg viewBox="0 0 64 64" width={size} height={size} aria-hidden="true">
      <rect width="64" height="64" rx="14" fill="#111a23" stroke="#243242" />
      <path
        d="M8 34h12l5-12 8 24 6-18 4 6h13"
        fill="none"
        stroke="#35d0b5"
        strokeWidth="5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}
