import { useState } from 'react'
import Dashboard from './screens/DashboardShell.jsx'
import Login from './screens/Login.jsx'

function App() {
  const [showDashboard, setShowDashboard] = useState(false)

  return showDashboard ? (
    <Dashboard onLogout={() => setShowDashboard(false)} />
  ) : (
    <Login onEnter={() => setShowDashboard(true)} />
  )
}

export default App
