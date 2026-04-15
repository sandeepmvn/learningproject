import { useMemo, useState } from "react"

const initialForm = {
  title: "",
  amount: "",
  paid_by_participant_id: "",
  category: "",
  notes: "",
  spent_on: "",
  split_mode: "equal",
}

function toParticipantMap(participants) {
  return Object.fromEntries(participants.map((participant) => [participant.id, ""]))
}

export default function ExpenseForm({ participants, onSubmit, isSubmitting, currency }) {
  const [form, setForm] = useState(initialForm)
  const [selectedParticipants, setSelectedParticipants] = useState([])
  const [customShares, setCustomShares] = useState(() => toParticipantMap(participants))
  const [error, setError] = useState("")

  const hasParticipants = participants.length > 0

  const customShareTotal = useMemo(
    () =>
      Object.values(customShares).reduce((total, amount) => total + (Number(amount) || 0), 0),
    [customShares],
  )

  function updateField(event) {
    const { name, value } = event.target
    setForm((current) => ({ ...current, [name]: value }))
  }

  function toggleParticipant(participantId) {
    setSelectedParticipants((current) =>
      current.includes(participantId)
        ? current.filter((value) => value !== participantId)
        : [...current, participantId],
    )
  }

  function updateCustomShare(participantId, value) {
    setCustomShares((current) => ({
      ...current,
      [participantId]: value,
    }))
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setError("")

    if (!hasParticipants) {
      setError("Add at least one participant before creating expenses.")
      return
    }

    if (!form.title.trim()) {
      setError("Expense title is required.")
      return
    }

    if (!form.paid_by_participant_id) {
      setError("Choose who paid for this expense.")
      return
    }

    const amount = Number(form.amount)

    if (!Number.isFinite(amount) || amount <= 0) {
      setError("Amount must be greater than 0.")
      return
    }

    const payload = {
      title: form.title.trim(),
      amount,
      paid_by_participant_id: Number(form.paid_by_participant_id),
    }

    if (form.category.trim()) {
      payload.category = form.category.trim()
    }

    if (form.notes.trim()) {
      payload.notes = form.notes.trim()
    }

    if (form.spent_on) {
      payload.spent_on = form.spent_on
    }

    if (form.split_mode === "custom") {
      const shares = participants
        .map((participant) => ({
          participant_id: participant.id,
          amount: Number(customShares[participant.id]) || 0,
        }))
        .filter((share) => share.amount > 0)

      if (shares.length === 0) {
        setError("Custom split needs at least one participant share.")
        return
      }

      if (Math.abs(customShareTotal - amount) > 0.001) {
        setError("Custom shares must add up exactly to the expense amount.")
        return
      }

      payload.split_mode = "custom"
      payload.custom_shares = shares
    } else if (selectedParticipants.length > 0) {
      payload.split_participant_ids = selectedParticipants.map(Number)
    }

    try {
      await onSubmit(payload)
      setForm(initialForm)
      setSelectedParticipants([])
      setCustomShares(toParticipantMap(participants))
    } catch (submitError) {
      setError(submitError.message)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-5 rounded-3xl border border-slate-800 bg-slate-900/80 p-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h3 className="text-lg font-semibold text-white">Add expense</h3>
          <p className="mt-1 text-sm text-slate-400">
            Support equal, selected-member, or custom share splits.
          </p>
        </div>
        <span className="rounded-full border border-fuchsia-500/40 bg-fuchsia-500/10 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-fuchsia-300">
          POST /expenses
        </span>
      </div>

      {!hasParticipants ? (
        <p className="rounded-2xl border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-sm text-amber-200">
          Add participants first so you can assign a payer and split the amount.
        </p>
      ) : null}

      <div className="grid gap-4 md:grid-cols-2">
        <label className="space-y-2 md:col-span-2">
          <span className="text-sm font-medium text-slate-200">Title</span>
          <input
            name="title"
            value={form.title}
            onChange={updateField}
            placeholder="Team Dinner"
            className="w-full rounded-2xl border border-slate-700 bg-slate-950 px-4 py-3 text-white"
          />
        </label>

        <label className="space-y-2">
          <span className="text-sm font-medium text-slate-200">Amount ({currency})</span>
          <input
            type="number"
            min="0"
            step="0.01"
            name="amount"
            value={form.amount}
            onChange={updateField}
            placeholder="3000"
            className="w-full rounded-2xl border border-slate-700 bg-slate-950 px-4 py-3 text-white"
          />
        </label>

        <label className="space-y-2">
          <span className="text-sm font-medium text-slate-200">Paid by</span>
          <select
            name="paid_by_participant_id"
            value={form.paid_by_participant_id}
            onChange={updateField}
            className="w-full rounded-2xl border border-slate-700 bg-slate-950 px-4 py-3 text-white"
          >
            <option value="">Select participant</option>
            {participants.map((participant) => (
              <option key={participant.id} value={participant.id}>
                {participant.name}
              </option>
            ))}
          </select>
        </label>

        <label className="space-y-2">
          <span className="text-sm font-medium text-slate-200">Category</span>
          <input
            name="category"
            value={form.category}
            onChange={updateField}
            placeholder="Food"
            className="w-full rounded-2xl border border-slate-700 bg-slate-950 px-4 py-3 text-white"
          />
        </label>

        <label className="space-y-2">
          <span className="text-sm font-medium text-slate-200">Spent on</span>
          <input
            type="date"
            name="spent_on"
            value={form.spent_on}
            onChange={updateField}
            className="w-full rounded-2xl border border-slate-700 bg-slate-950 px-4 py-3 text-white"
          />
        </label>

        <label className="space-y-2 md:col-span-2">
          <span className="text-sm font-medium text-slate-200">Notes</span>
          <textarea
            name="notes"
            value={form.notes}
            onChange={updateField}
            rows="3"
            placeholder="Dinner at beach shack"
            className="w-full rounded-2xl border border-slate-700 bg-slate-950 px-4 py-3 text-white"
          />
        </label>
      </div>

      <div className="rounded-2xl border border-slate-800 bg-slate-950/80 p-4">
        <div className="flex flex-wrap gap-3">
          <label className="inline-flex items-center gap-2 rounded-full border border-slate-700 px-4 py-2 text-sm text-slate-200">
            <input
              type="radio"
              name="split_mode"
              value="equal"
              checked={form.split_mode === "equal"}
              onChange={updateField}
            />
            Equal split
          </label>
          <label className="inline-flex items-center gap-2 rounded-full border border-slate-700 px-4 py-2 text-sm text-slate-200">
            <input
              type="radio"
              name="split_mode"
              value="custom"
              checked={form.split_mode === "custom"}
              onChange={updateField}
            />
            Custom split
          </label>
        </div>

        {form.split_mode === "equal" ? (
          <div className="mt-4 space-y-3">
            <p className="text-sm text-slate-400">
              Leave everyone unchecked to split across all trip members, or pick the specific
              participants who should share this expense.
            </p>
            <div className="grid gap-3 sm:grid-cols-2">
              {participants.map((participant) => (
                <label
                  key={participant.id}
                  className="flex items-center justify-between rounded-2xl border border-slate-800 bg-slate-900 px-4 py-3 text-sm text-slate-200"
                >
                  <span>{participant.name}</span>
                  <input
                    type="checkbox"
                    checked={selectedParticipants.includes(participant.id)}
                    onChange={() => toggleParticipant(participant.id)}
                  />
                </label>
              ))}
            </div>
          </div>
        ) : (
          <div className="mt-4 space-y-3">
            <div className="flex items-center justify-between text-sm text-slate-300">
              <p>Set the exact amount owed by each participant.</p>
              <p className="font-semibold text-white">
                Total shares: {currency} {customShareTotal.toFixed(2)}
              </p>
            </div>
            <div className="grid gap-3 sm:grid-cols-2">
              {participants.map((participant) => (
                <label
                  key={participant.id}
                  className="space-y-2 rounded-2xl border border-slate-800 bg-slate-900 px-4 py-3"
                >
                  <span className="text-sm font-medium text-slate-200">{participant.name}</span>
                  <input
                    type="number"
                    min="0"
                    step="0.01"
                    value={customShares[participant.id] ?? ""}
                    onChange={(event) => updateCustomShare(participant.id, event.target.value)}
                    placeholder="0.00"
                    className="w-full rounded-2xl border border-slate-700 bg-slate-950 px-4 py-3 text-white"
                  />
                </label>
              ))}
            </div>
          </div>
        )}
      </div>

      {error ? (
        <p className="rounded-2xl border border-rose-500/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">
          {error}
        </p>
      ) : null}

      <button
        type="submit"
        disabled={isSubmitting || !hasParticipants}
        className="inline-flex items-center justify-center rounded-2xl bg-fuchsia-400 px-5 py-3 text-sm font-semibold text-slate-950 transition hover:bg-fuchsia-300 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {isSubmitting ? "Saving expense..." : "Add expense"}
      </button>
    </form>
  )
}
