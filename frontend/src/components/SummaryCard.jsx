import { formatCurrency } from "../utils/format"

function getTopPayer(balances) {
  if (!balances.length) {
    return null
  }

  return [...balances].sort((left, right) => Number(right.paid) - Number(left.paid))[0]
}

export default function SummaryCard({ summary, currency }) {
  const balances = summary?.balances || []
  const settlements = summary?.settlements || []
  const topPayer = getTopPayer(balances)

  return (
    <section className="rounded-3xl border border-slate-800 bg-slate-900/80 p-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h3 className="text-lg font-semibold text-white">Balances & settlements</h3>
          <p className="mt-1 text-sm text-slate-400">
            Use this snapshot to settle up quickly at the end of the trip.
          </p>
        </div>
        <span className="rounded-full border border-amber-500/40 bg-amber-500/10 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-amber-300">
          GET /summary
        </span>
      </div>

      <div className="mt-6 grid gap-4 md:grid-cols-3">
        <div className="rounded-2xl bg-slate-950/80 p-4">
          <p className="text-xs uppercase tracking-wide text-slate-500">Total expenses</p>
          <p className="mt-2 text-2xl font-semibold text-white">
            {formatCurrency(summary?.total_expenses || 0, currency)}
          </p>
        </div>
        <div className="rounded-2xl bg-slate-950/80 p-4">
          <p className="text-xs uppercase tracking-wide text-slate-500">Top payer</p>
          <p className="mt-2 text-lg font-semibold text-white">
            {topPayer
              ? `${topPayer.participant_name} (${formatCurrency(topPayer.paid, currency)})`
              : "No expenses yet"}
          </p>
        </div>
        <div className="rounded-2xl bg-slate-950/80 p-4">
          <p className="text-xs uppercase tracking-wide text-slate-500">Participants with balances</p>
          <p className="mt-2 text-2xl font-semibold text-white">{balances.length}</p>
        </div>
      </div>

      <div className="mt-6 overflow-x-auto">
        <table className="min-w-full divide-y divide-slate-800 text-left text-sm text-slate-300">
          <thead>
            <tr className="text-xs uppercase tracking-wide text-slate-500">
              <th className="pb-3 pr-4 font-medium">Participant</th>
              <th className="pb-3 pr-4 font-medium">Paid</th>
              <th className="pb-3 pr-4 font-medium">Owes</th>
              <th className="pb-3 font-medium">Balance</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800">
            {balances.map((balance) => (
              <tr key={balance.participant_id}>
                <td className="py-4 pr-4 font-medium text-white">{balance.participant_name}</td>
                <td className="py-4 pr-4">{formatCurrency(balance.paid, currency)}</td>
                <td className="py-4 pr-4">{formatCurrency(balance.owes, currency)}</td>
                <td
                  className={`py-4 font-semibold ${
                    Number(balance.balance) >= 0 ? "text-emerald-300" : "text-rose-300"
                  }`}
                >
                  {formatCurrency(balance.balance, currency)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="mt-6 space-y-3">
        <h4 className="text-sm font-semibold uppercase tracking-wide text-slate-400">
          Settlement suggestions
        </h4>
        {settlements.length === 0 ? (
          <p className="rounded-2xl border border-dashed border-slate-700 px-4 py-4 text-sm text-slate-400">
            No settlements yet. Once expenses are added, the backend will suggest who pays whom.
          </p>
        ) : (
          settlements.map((settlement, index) => (
            <div
              key={`${settlement.from_participant_id}-${settlement.to_participant_id}-${index}`}
              className="rounded-2xl border border-slate-800 bg-slate-950/80 px-4 py-4 text-sm text-slate-200"
            >
              <span className="font-semibold text-white">{settlement.from_participant_name}</span>{" "}
              pays{" "}
              <span className="font-semibold text-white">{settlement.to_participant_name}</span>{" "}
              {formatCurrency(settlement.amount, currency)}
            </div>
          ))
        )}
      </div>
    </section>
  )
}
