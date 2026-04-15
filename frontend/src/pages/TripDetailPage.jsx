import { useEffect, useMemo, useState } from "react"
import { Link, useParams } from "react-router-dom"
import {
  addExpense,
  addParticipant,
  getExpenses,
  getParticipants,
  getTrip,
  getTripSummary,
} from "../api/trips"
import ExpenseForm from "../components/ExpenseForm"
import ExpenseList from "../components/ExpenseList"
import ParticipantForm from "../components/ParticipantForm"
import SummaryCard from "../components/SummaryCard"
import { formatDate, formatDateTime } from "../utils/format"

function normalizeTripPayload(payload) {
  const tripSource = payload?.trip && typeof payload.trip === "object" ? payload.trip : payload

  return {
    trip: {
      id: tripSource?.id,
      name: tripSource?.name,
      description: tripSource?.description,
      destination: tripSource?.destination,
      start_date: tripSource?.start_date,
      end_date: tripSource?.end_date,
      currency: tripSource?.currency || "INR",
      created_at: tripSource?.created_at,
    },
    participants: Array.isArray(payload?.participants) ? payload.participants : [],
    expenses: Array.isArray(payload?.expenses) ? payload.expenses : [],
  }
}

export default function TripDetailPage() {
  const { tripId } = useParams()
  const [trip, setTrip] = useState(null)
  const [participants, setParticipants] = useState([])
  const [expenses, setExpenses] = useState([])
  const [summary, setSummary] = useState(null)
  const [loading, setLoading] = useState(true)
  const [pageError, setPageError] = useState("")
  const [participantSubmitting, setParticipantSubmitting] = useState(false)
  const [expenseSubmitting, setExpenseSubmitting] = useState(false)

  const currency = useMemo(() => trip?.currency || "INR", [trip])

  useEffect(() => {
    async function loadTripPage() {
      setLoading(true)
      setPageError("")

      try {
        const [tripResponse, summaryResponse] = await Promise.all([
          getTrip(tripId),
          getTripSummary(tripId),
        ])
        const normalized = normalizeTripPayload(tripResponse)

        setTrip(normalized.trip)
        setParticipants(normalized.participants)
        setExpenses(normalized.expenses)
        setSummary(summaryResponse)
      } catch (error) {
        setPageError(error.message)
      } finally {
        setLoading(false)
      }
    }

    loadTripPage()
  }, [tripId])

  async function handleAddParticipant(payload) {
    setParticipantSubmitting(true)

    try {
      await addParticipant(tripId, payload)
      const refreshedParticipants = await getParticipants(tripId)
      setParticipants(refreshedParticipants)
    } finally {
      setParticipantSubmitting(false)
    }
  }

  async function handleAddExpense(payload) {
    setExpenseSubmitting(true)

    try {
      await addExpense(tripId, payload)
      const [refreshedExpenses, refreshedSummary] = await Promise.all([
        getExpenses(tripId),
        getTripSummary(tripId),
      ])

      setExpenses(refreshedExpenses)
      setSummary(refreshedSummary)
    } finally {
      setExpenseSubmitting(false)
    }
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="h-40 animate-pulse rounded-3xl border border-slate-800 bg-slate-900/80" />
        <div className="grid gap-6 xl:grid-cols-2">
          <div className="h-96 animate-pulse rounded-3xl border border-slate-800 bg-slate-900/80" />
          <div className="h-96 animate-pulse rounded-3xl border border-slate-800 bg-slate-900/80" />
        </div>
      </div>
    )
  }

  if (pageError) {
    return (
      <div className="rounded-3xl border border-rose-500/30 bg-rose-500/10 p-8 text-rose-100">
        <p className="text-sm font-semibold uppercase tracking-[0.3em] text-rose-300">
          Unable to load trip
        </p>
        <h2 className="mt-3 text-2xl font-bold text-white">{pageError}</h2>
        <p className="mt-3 text-sm text-rose-100/80">
          This usually means the trip does not exist or the backend is unavailable.
        </p>
        <Link
          to="/"
          className="mt-6 inline-flex rounded-2xl bg-white px-4 py-3 text-sm font-semibold text-slate-950"
        >
          Back to dashboard
        </Link>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      <section className="rounded-3xl border border-slate-800 bg-gradient-to-br from-cyan-500/15 via-slate-900 to-slate-900 p-6">
        <Link to="/" className="text-sm font-semibold text-cyan-300 transition hover:text-cyan-200">
          ← Back to dashboard
        </Link>
        <div className="mt-4 flex flex-col gap-6 xl:flex-row xl:items-end xl:justify-between">
          <div>
            <div className="flex flex-wrap items-center gap-3">
              <span className="rounded-full border border-cyan-500/40 bg-cyan-500/10 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-cyan-300">
                GET /trips/{tripId}
              </span>
              <span className="rounded-full border border-slate-700 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-slate-300">
                {currency}
              </span>
            </div>
            <h2 className="mt-4 text-3xl font-bold text-white">{trip?.name}</h2>
            <p className="mt-3 max-w-3xl text-sm leading-7 text-slate-300">
              {trip?.description || "No trip description available."}
            </p>
          </div>

          <dl className="grid gap-4 sm:grid-cols-3">
            <div className="rounded-2xl bg-slate-950/80 p-4">
              <dt className="text-xs uppercase tracking-wide text-slate-500">Destination</dt>
              <dd className="mt-2 font-semibold text-white">{trip?.destination || "TBD"}</dd>
            </div>
            <div className="rounded-2xl bg-slate-950/80 p-4">
              <dt className="text-xs uppercase tracking-wide text-slate-500">Dates</dt>
              <dd className="mt-2 font-semibold text-white">
                {formatDate(trip?.start_date)} - {formatDate(trip?.end_date)}
              </dd>
            </div>
            <div className="rounded-2xl bg-slate-950/80 p-4">
              <dt className="text-xs uppercase tracking-wide text-slate-500">Created</dt>
              <dd className="mt-2 font-semibold text-white">{formatDateTime(trip?.created_at)}</dd>
            </div>
          </dl>
        </div>
      </section>

      <section className="grid gap-6 xl:grid-cols-[360px_1fr]">
        <div className="space-y-6">
          <ParticipantForm
            onSubmit={handleAddParticipant}
            isSubmitting={participantSubmitting}
          />

          <div className="rounded-3xl border border-slate-800 bg-slate-900/80 p-6">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h3 className="text-lg font-semibold text-white">Participants</h3>
                <p className="mt-1 text-sm text-slate-400">
                  Managed with the participants endpoints for this trip.
                </p>
              </div>
              <span className="rounded-full border border-cyan-500/40 bg-cyan-500/10 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-cyan-300">
                GET /participants
              </span>
            </div>

            {participants.length === 0 ? (
              <div className="mt-6 rounded-2xl border border-dashed border-slate-700 px-4 py-8 text-center text-sm text-slate-400">
                No participants yet. Add the first traveler to start recording expenses.
              </div>
            ) : (
              <div className="mt-6 flex flex-wrap gap-3">
                {participants.map((participant) => (
                  <div
                    key={participant.id}
                    className="rounded-2xl border border-slate-800 bg-slate-950/80 px-4 py-3"
                  >
                    <p className="font-medium text-white">{participant.name}</p>
                    <p className="mt-1 text-sm text-slate-400">
                      {participant.email || "No email provided"}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        <div className="space-y-6">
          <ExpenseForm
            key={participants.map((participant) => participant.id).join("-") || "no-participants"}
            participants={participants}
            onSubmit={handleAddExpense}
            isSubmitting={expenseSubmitting}
            currency={currency}
          />
          <SummaryCard summary={summary} currency={currency} />
          <ExpenseList expenses={expenses} currency={currency} />
        </div>
      </section>
    </div>
  )
}
