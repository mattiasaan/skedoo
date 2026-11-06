import { useState } from 'react'
import Dashboard from './screens/DashboardShell.jsx'
import Login from './screens/Login.jsx'
import SchoolSetup from './screens/SchoolSetup.jsx'

function App() {
  const [showDashboard, setShowDashboard] = useState(false)
  const [showSchoolSetup, setShowSchoolSetup] = useState(false)

  if (showDashboard) {
    return <Dashboard onLogout={() => setShowDashboard(false)} />
  }

  if (showSchoolSetup) {
    return <SchoolSetup onEnter={() => setShowDashboard(true)} />
  }

  return <Login onEnter={() => setShowSchoolSetup(true)} />
}

export default App
