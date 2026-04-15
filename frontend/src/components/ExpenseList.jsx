import { formatCurrency, formatDate } from "../utils/format"

function formatShares(shares, currency) {
  if (!Array.isArray(shares) || shares.length === 0) {
    return "Share breakdown unavailable"
  }

  return shares
    .map((share) => {
      const name =
        share.participant_name ||
        share.name ||
        `Participant #${share.participant_id || share.id || "?"}`

      return `${name}: ${formatCurrency(share.amount, currency)}`
    })
    .join(", ")
}

export default function ExpenseList({ expenses, currency }) {
  return (
    <section className="rounded-3xl border border-slate-800 bg-slate-900/80 p-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h3 className="text-lg font-semibold text-white">Expenses</h3>
          <p className="mt-1 text-sm text-slate-400">
            Refreshed from the trip expenses endpoints after every new entry.
          </p>
        </div>
        <span className="rounded-full border border-violet-500/40 bg-violet-500/10 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-violet-300">
          GET /expenses
        </span>
      </div>

      {expenses.length === 0 ? (
        <div className="mt-6 rounded-2xl border border-dashed border-slate-700 px-6 py-10 text-center text-sm text-slate-400">
          No expenses yet. Add the first shared cost to unlock balances and settlements.
        </div>
      ) : (
        <div className="mt-6 overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-800 text-left text-sm text-slate-300">
            <thead>
              <tr className="text-xs uppercase tracking-wide text-slate-500">
                <th className="pb-3 pr-4 font-medium">Expense</th>
                <th className="pb-3 pr-4 font-medium">Paid by</th>
                <th className="pb-3 pr-4 font-medium">Spent on</th>
                <th className="pb-3 pr-4 font-medium">Amount</th>
                <th className="pb-3 font-medium">Shares</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {expenses.map((expense) => (
                <tr key={expense.id}>
                  <td className="py-4 pr-4 align-top">
                    <div className="font-medium text-white">{expense.title}</div>
                    <div className="mt-1 text-xs text-slate-500">
                      {[expense.category, expense.notes].filter(Boolean).join(" • ") || "—"}
                    </div>
                  </td>
                  <td className="py-4 pr-4 align-top">
                    {expense.paid_by_participant_name ||
                      expense.payer_name ||
                      `Participant #${expense.paid_by_participant_id || "?"}`}
                  </td>
                  <td className="py-4 pr-4 align-top">{formatDate(expense.spent_on)}</td>
                  <td className="py-4 pr-4 align-top font-medium text-white">
                    {formatCurrency(expense.amount, currency)}
                  </td>
                  <td className="py-4 align-top">{formatShares(expense.shares, currency)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}
