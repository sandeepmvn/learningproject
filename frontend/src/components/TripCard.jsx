import { Link } from "react-router-dom"
import { formatDate, formatDateTime } from "../utils/format"

export default function TripCard({ trip }) {
  return (
    <article className="flex h-full flex-col rounded-3xl border border-slate-800 bg-slate-900/80 p-6 shadow-lg shadow-slate-950/20">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-sm font-medium text-emerald-400">{trip.destination || "TBD"}</p>
          <h3 className="mt-1 text-xl font-semibold text-white">{trip.name}</h3>
        </div>
        <span className="rounded-full bg-slate-800 px-3 py-1 text-xs font-semibold text-slate-300">
          {trip.currency}
        </span>
      </div>

      <p className="mt-4 flex-1 text-sm leading-6 text-slate-300">
        {trip.description || "No description added for this trip yet."}
      </p>

      <dl className="mt-6 grid grid-cols-2 gap-4 text-sm text-slate-300">
        <div className="rounded-2xl bg-slate-800/70 p-4">
          <dt className="text-xs uppercase tracking-wide text-slate-400">Dates</dt>
          <dd className="mt-1 font-medium text-white">
            {formatDate(trip.start_date)} - {formatDate(trip.end_date)}
          </dd>
        </div>
        <div className="rounded-2xl bg-slate-800/70 p-4">
          <dt className="text-xs uppercase tracking-wide text-slate-400">Created</dt>
          <dd className="mt-1 font-medium text-white">{formatDateTime(trip.created_at)}</dd>
        </div>
      </dl>

      <Link
        to={`/trips/${trip.id}`}
        className="mt-6 inline-flex items-center justify-center rounded-2xl bg-emerald-400 px-4 py-3 text-sm font-semibold text-slate-950 transition hover:bg-emerald-300"
      >
        Open trip
      </Link>
    </article>
  )
}
