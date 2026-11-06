import { useState } from 'react'
import Dashboard from './screens/DashboardShell.jsx'
import Login from './screens/Login.jsx'
import SchoolSetup from './screens/SchoolSetup.jsx'

function App() {
  const [showDashboard, setShowDashboard] = useState(false)
  const [showSchoolSetup, setShowSchoolSetup] = useState(false)

  // Funzione universale per resettare tutto e tornare al Login
  const handleLogout = () => {
    setShowDashboard(false)
    setShowSchoolSetup(false)
  }

  if (showDashboard) {
    // Passiamo handleLogout anche alla Dashboard/DashboardShell se ha un tasto di logout interno
    return <Dashboard onLogout={handleLogout} />
  }

  if (showSchoolSetup) {
    return <SchoolSetup onEnter={() => setShowDashboard(true)} />
  }

  return (
    <Login
      onLoginSuccess={(needsSetup) => {
        if (needsSetup) {
          setShowSchoolSetup(true)
        } else {
          setShowDashboard(true)
        }
      }}
    />
  )
}

export default App