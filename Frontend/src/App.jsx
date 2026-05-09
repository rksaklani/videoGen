import { BrowserRouter, Routes, Route } from 'react-router-dom'

// Website pages
import WebsiteLayout from './pages/website/WebsiteLayout'
import Home from './pages/website/Home'
import Pricing from './pages/website/Pricing'
import About from './pages/website/About'
import Contact from './pages/website/Contact'
import Login from './pages/website/Login'
import Signup from './pages/website/Signup'

// Dashboard pages
import DashboardLayout from './pages/dashboard/DashboardLayout'
import Create from './pages/dashboard/Create'
import TextToVideo from './pages/dashboard/TextToVideo'
import AudioToVideo from './pages/dashboard/AudioToVideo'
import DialogueEditor from './pages/dashboard/DialogueEditor'
import MyAvatars from './pages/dashboard/MyAvatars'
import Templates from './pages/dashboard/Templates'
import History from './pages/dashboard/History'
import Settings from './pages/dashboard/Settings'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public Website */}
        <Route element={<WebsiteLayout />}>
          <Route path="/" element={<Home />} />
          <Route path="/pricing" element={<Pricing />} />
          <Route path="/about" element={<About />} />
          <Route path="/contact" element={<Contact />} />
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />
        </Route>

        {/* Dashboard (Protected) */}
        <Route path="/dashboard" element={<DashboardLayout />}>
          <Route index element={<Create />} />
          <Route path="text-to-video" element={<TextToVideo />} />
          <Route path="audio-to-video" element={<AudioToVideo />} />
          <Route path="dialogue" element={<DialogueEditor />} />
          <Route path="my-avatars" element={<MyAvatars />} />
          <Route path="templates" element={<Templates />} />
          <Route path="history" element={<History />} />
          <Route path="settings" element={<Settings />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
