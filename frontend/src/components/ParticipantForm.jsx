import { useState } from "react"

const initialForm = {
  name: "",
  email: "",
}

export default function ParticipantForm({ onSubmit, isSubmitting }) {
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
      setError("Participant name is required.")
      return
    }

    try {
      await onSubmit({
        name: form.name.trim(),
        email: form.email.trim(),
      })
      setForm(initialForm)
    } catch (submitError) {
      setError(submitError.message)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4 rounded-3xl border border-slate-800 bg-slate-900/80 p-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h3 className="text-lg font-semibold text-white">Add participant</h3>
          <p className="mt-1 text-sm text-slate-400">
            Names must stay unique inside this trip.
          </p>
        </div>
        <span className="rounded-full border border-cyan-500/40 bg-cyan-500/10 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-cyan-300">
          POST /participants
        </span>
      </div>

      <label className="block space-y-2">
        <span className="text-sm font-medium text-slate-200">Name</span>
        <input
          name="name"
          value={form.name}
          onChange={updateField}
          placeholder="Alice"
          className="w-full rounded-2xl border border-slate-700 bg-slate-950 px-4 py-3 text-white"
        />
      </label>

      <label className="block space-y-2">
        <span className="text-sm font-medium text-slate-200">Email</span>
        <input
          type="email"
          name="email"
          value={form.email}
          onChange={updateField}
          placeholder="alice@example.com"
          className="w-full rounded-2xl border border-slate-700 bg-slate-950 px-4 py-3 text-white"
        />
      </label>

      {error ? (
        <p className="rounded-2xl border border-rose-500/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">
          {error}
        </p>
      ) : null}

      <button
        type="submit"
        disabled={isSubmitting}
        className="inline-flex items-center justify-center rounded-2xl bg-cyan-400 px-5 py-3 text-sm font-semibold text-slate-950 transition hover:bg-cyan-300 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {isSubmitting ? "Adding participant..." : "Add participant"}
      </button>
    </form>
  )
}
