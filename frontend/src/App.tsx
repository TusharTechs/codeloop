import { useEffect, useMemo, useState } from 'react'
import { PcmPlayer } from './audio/player'
import { CodeScreen } from './pages/CodeScreen'
import { Dashboard } from './pages/Dashboard'
import { Home } from './pages/Home'
import { RecordPage } from './pages/RecordPage'

function useRoute(): string {
  const [hash, setHash] = useState(location.hash)
  useEffect(() => {
    const on = () => setHash(location.hash)
    window.addEventListener('hashchange', on)
    return () => window.removeEventListener('hashchange', on)
  }, [])
  return hash
}

export default function App() {
  const player = useMemo(() => new PcmPlayer(), [])
  const route = useRoute()
  const code = route.match(/^#\/code\/([a-z0-9]+)/)
  const record = route.match(/^#\/record\/([a-z0-9]+)/)
  if (code) return <CodeScreen key={code[1]} codeId={code[1]} player={player} />
  if (record) return <RecordPage key={record[1]} codeId={record[1]} />
  if (route.startsWith('#/codes')) return <Dashboard />
  return <Home player={player} />
}
