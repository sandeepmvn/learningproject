import { useState } from "react"

const initialForm = {
  name: "",
  description: "",
  destination: "",
  start_date: "",
  end_date: "",
  currency: "INR",
}

export default function TripForm({ onSubmit, isSubmitting }) {
  const [form, setForm] = useState(initialForm)
  const [error, setError] = useState("")

  function updateField(event) {
    const { name, value } = event.target
    setForm((current) => ({ ...current, [name]: value }))
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setError("")

    if (!form.name.trim()) {
      setError("Trip name is required.")
      return
    }

    if (!/^[A-Za-z]{3}$/.test(form.currency.trim())) {
      setError("Currency must be a 3-letter code like INR or USD.")
      return
    }

    if (form.start_date && form.end_date && form.end_date < form.start_date) {
      setError("End date cannot be earlier than start date.")
      return
    }

    try {
      await onSubmit({
        ...form,
        name: form.name.trim(),
        description: form.description.trim(),
        destination: form.destination.trim(),
        currency: form.currency.trim().toUpperCase(),
      })
      setForm(initialForm)
    } catch (submitError) {
      setError(submitError.message)
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="rounded-3xl border border-slate-800 bg-slate-900/80 p-6 shadow-lg shadow-slate-950/20"
    >
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-xl font-semibold text-white">Create a trip</h2>
          <p className="mt-1 text-sm text-slate-400">
            Add the basics now and keep filling in expenses later.
          </p>
        </div>
        <span className="rounded-full border border-emerald-500/40 bg-emerald-500/10 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-emerald-300">
          POST /trips
        </span>
      </div>

      <div className="mt-6 grid gap-4 md:grid-cols-2">
        <label className="space-y-2 md:col-span-2">
          <span className="text-sm font-medium text-slate-200">Trip name</span>
          <input
            name="name"
            value={form.name}
            onChange={updateField}
            placeholder="Goa Team Trip"
            className="w-full rounded-2xl border border-slate-700 bg-slate-950 px-4 py-3 text-white"
          />
        </label>

        <label className="space-y-2 md:col-span-2">
          <span className="text-sm font-medium text-slate-200">Description</span>
          <textarea
            name="description"
            value={form.description}
            onChange={updateField}
            rows="3"
            placeholder="Engineering offsite"
            className="w-full rounded-2xl border border-slate-700 bg-slate-950 px-4 py-3 text-white"
          />
        </label>

        <label className="space-y-2">
          <span className="text-sm font-medium text-slate-200">Destination</span>
          <input
            name="destination"
            value={form.destination}
            onChange={updateField}
            placeholder="Goa"
            className="w-full rounded-2xl border border-slate-700 bg-slate-950 px-4 py-3 text-white"
          />
        </label>

        <label className="space-y-2">
          <span className="text-sm font-medium text-slate-200">Currency</span>
          <input
            name="currency"
            value={form.currency}
            onChange={updateField}
            maxLength="3"
            placeholder="INR"
            className="w-full rounded-2xl border border-slate-700 bg-slate-950 px-4 py-3 uppercase text-white"
          />
        </label>

        <label className="space-y-2">
          <span className="text-sm font-medium text-slate-200">Start date</span>
          <input
            type="date"
            name="start_date"
            value={form.start_date}
            onChange={updateField}
            className="w-full rounded-2xl border border-slate-700 bg-slate-950 px-4 py-3 text-white"
          />
        </label>

        <label className="space-y-2">
          <span className="text-sm font-medium text-slate-200">End date</span>
          <input
            type="date"
            name="end_date"
            value={form.end_date}
            onChange={updateField}
            className="w-full rounded-2xl border border-slate-700 bg-slate-950 px-4 py-3 text-white"
          />
        </label>
      </div>

      {error ? (
        <p className="mt-4 rounded-2xl border border-rose-500/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">
          {error}
        </p>
      ) : null}

      <button
        type="submit"
        disabled={isSubmitting}
        className="mt-6 inline-flex items-center justify-center rounded-2xl bg-emerald-400 px-5 py-3 text-sm font-semibold text-slate-950 transition hover:bg-emerald-300 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {isSubmitting ? "Creating trip..." : "Create trip"}
      </button>
    </form>
  )
}
