import { BrowserRouter, Route, Routes } from "react-router-dom"
import Layout from "./components/Layout"
import DashboardPage from "./pages/DashboardPage"
import TripDetailPage from "./pages/TripDetailPage"

function NotFoundPage() {
  return (
    <div className="rounded-3xl border border-slate-800 bg-slate-900/80 p-8">
      <p className="text-sm font-semibold uppercase tracking-[0.3em] text-slate-400">
        404
      </p>
      <h2 className="mt-3 text-2xl font-bold text-white">Page not found</h2>
      <p className="mt-3 text-sm text-slate-400">
        The route you requested does not exist in this frontend.
      </p>
    </div>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/trips/:tripId" element={<TripDetailPage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
