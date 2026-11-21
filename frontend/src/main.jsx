import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './styles/base.css'
import App from './App.jsx'
import { ToastProvider } from './components/Toasts.jsx'
import './styles/feedback.css'
import { applyAccent, readAccent } from './lib/theme.js'

applyAccent(readAccent())

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <ToastProvider>
      <App />
    </ToastProvider>
  </StrictMode>,
)
