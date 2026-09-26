import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App'
import './styles.css'
import { setToken } from './api'

// A shared judge link can carry the access code in the fragment (#access=…), which the browser
// never sends to the server. Store it and drop it from the address bar.
const shared = location.hash.match(/^#access=([^&]+)/)
if (shared) {
  setToken(decodeURIComponent(shared[1]))
  history.replaceState(null, '', `${location.pathname}#/`)
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
