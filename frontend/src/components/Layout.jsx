import { Link, NavLink, Outlet } from "react-router-dom"

function navLinkClass({ isActive }) {
  return isActive
    ? "rounded-full bg-emerald-500 px-4 py-2 text-sm font-semibold text-slate-950"
    : "rounded-full border border-slate-700 px-4 py-2 text-sm font-semibold text-slate-300 transition hover:border-emerald-400 hover:text-white"
}

export default function Layout() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <header className="border-b border-slate-800 bg-slate-950/90 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-5 sm:px-6 lg:px-8">
          <Link to="/" className="space-y-1">
            <p className="text-xs font-semibold uppercase tracking-[0.3em] text-emerald-400">
              Team Trip Expense Tracker
            </p>
            <h1 className="text-xl font-bold text-white">
              Split trip expenses without spreadsheet chaos
            </h1>
          </Link>
          <nav className="flex items-center gap-3">
            <NavLink to="/" end className={navLinkClass}>
              Dashboard
            </NavLink>
          </nav>
        </div>
      </header>

      <main className="mx-auto w-full max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <Outlet />
      </main>
    </div>
  )
}
