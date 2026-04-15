import { useEffect, useState } from "react"
import { createTrip, getApiInfo, getHealth, getTrips } from "../api/trips"
import TripCard from "../components/TripCard"
import TripForm from "../components/TripForm"

export default function DashboardPage() {
  const [trips, setTrips] = useState([])
  const [apiInfo, setApiInfo] = useState(null)
  const [health, setHealth] = useState(null)
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState("")

  useEffect(() => {
    async function loadDashboard() {
      setLoading(true)
      setError("")

      const [infoResult, healthResult, tripsResult] = await Promise.allSettled([
        getApiInfo(),
        getHealth(),
        getTrips(),
      ])

      if (infoResult.status === "fulfilled") {
        setApiInfo(infoResult.value)
      } else {
        setApiInfo({ error: infoResult.reason.message })
      }

      if (healthResult.status === "fulfilled") {
        setHealth(healthResult.value)
      } else {
        setHealth({ status: "unavailable", detail: healthResult.reason.message })
      }

      if (tripsResult.status === "fulfilled") {
        setTrips(tripsResult.value)
      } else {
        setError(tripsResult.reason.message)
      }

      setLoading(false)
    }

    loadDashboard()
  }, [])

  async function handleCreateTrip(payload) {
    setSubmitting(true)

    try {
      const createdTrip = await createTrip(payload)
      setTrips((current) => [createdTrip, ...current])
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="space-y-8">
      <section className="grid gap-4 lg:grid-cols-[1.4fr_1fr_1fr]">
        <div className="rounded-3xl border border-slate-800 bg-gradient-to-br from-emerald-500/15 via-slate-900 to-slate-900 p-6">
          <p className="text-sm font-semibold uppercase tracking-[0.3em] text-emerald-300">
            Dashboard
          </p>
          <h2 className="mt-3 text-3xl font-bold text-white">
            Plan group trips, track every expense, and settle balances faster.
          </h2>
          <p className="mt-4 max-w-2xl text-sm leading-7 text-slate-300">
            The dashboard loads all trips with <span className="font-semibold">GET /trips</span>{" "}
            and lets your team create a new trip from the same screen.
          </p>
        </div>

        <div className="rounded-3xl border border-slate-800 bg-slate-900/80 p-6">
          <p className="text-xs uppercase tracking-wide text-slate-500">Backend status</p>
          <p
            className={`mt-3 inline-flex rounded-full px-3 py-1 text-sm font-semibold ${
              health?.status === "ok"
                ? "bg-emerald-500/15 text-emerald-300"
                : "bg-rose-500/15 text-rose-200"
            }`}
          >
            {health?.status || "Unknown"}
          </p>
          <p className="mt-4 text-sm text-slate-400">
            {health?.detail || "Health check uses GET /health through the Vite proxy."}
          </p>
        </div>

        <div className="rounded-3xl border border-slate-800 bg-slate-900/80 p-6">
          <p className="text-xs uppercase tracking-wide text-slate-500">API metadata</p>
          <p className="mt-3 text-lg font-semibold text-white">
            {apiInfo?.name || apiInfo?.title || "Backend info unavailable"}
          </p>
          <p className="mt-2 text-sm text-slate-400">
            Version: {apiInfo?.version || "Unknown"}
          </p>
          <p className="mt-2 text-sm text-slate-400">
            Docs: {apiInfo?.docs_url || apiInfo?.docs || "http://127.0.0.1:8000/docs"}
          </p>
        </div>
      </section>

      <section className="grid gap-8 xl:grid-cols-[420px_1fr]">
        <TripForm onSubmit={handleCreateTrip} isSubmitting={submitting} />

        <div className="rounded-3xl border border-slate-800 bg-slate-900/80 p-6 shadow-lg shadow-slate-950/20">
          <div className="flex items-start justify-between gap-4">
            <div>
              <h2 className="text-xl font-semibold text-white">Trips</h2>
              <p className="mt-1 text-sm text-slate-400">
                Browse every saved trip and jump into its expenses and balances.
              </p>
            </div>
            <span className="rounded-full border border-emerald-500/40 bg-emerald-500/10 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-emerald-300">
              GET /trips
            </span>
          </div>

          {error ? (
            <p className="mt-6 rounded-2xl border border-rose-500/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">
              {error}
            </p>
          ) : null}

          {loading ? (
            <div className="mt-6 grid gap-4 md:grid-cols-2">
              {Array.from({ length: 4 }).map((_, index) => (
                <div
                  key={index}
                  className="h-56 animate-pulse rounded-3xl border border-slate-800 bg-slate-950/80"
                />
              ))}
            </div>
          ) : trips.length === 0 ? (
            <div className="mt-6 rounded-2xl border border-dashed border-slate-700 px-6 py-12 text-center text-sm text-slate-400">
              No trips yet. Create the first one to start tracking shared expenses.
            </div>
          ) : (
            <div className="mt-6 grid gap-4 md:grid-cols-2">
              {trips.map((trip) => (
                <TripCard key={trip.id} trip={trip} />
              ))}
            </div>
          )}
        </div>
      </section>
    </div>
  )
}
