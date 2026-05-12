import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, todayIso } from '../api.js'

export default function Dashboard() {
  const [profile, setProfile] = useState(null)
  const [todayLog, setTodayLog] = useState([])

  useEffect(() => {
    api.getProfile().then(setProfile)
    api.listFood(todayIso()).then(setTodayLog).catch(() => setTodayLog([]))
  }, [])

  const goal = profile?.user?.calorie_goal ?? 0
  const consumed = todayLog.reduce((s, r) => s + (r.kcal || 0), 0)
  const protein = todayLog.reduce((s, r) => s + (r.protein_g || 0), 0)
  const carbs = todayLog.reduce((s, r) => s + (r.carbs_g || 0), 0)
  const fat = todayLog.reduce((s, r) => s + (r.fat_g || 0), 0)
  const fiber = todayLog.reduce((s, r) => s + (r.fiber_g || 0), 0)
  const remaining = Math.max(0, goal - consumed)
  const pct = goal ? Math.min(100, (consumed / goal) * 100) : 0

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-semibold">Hi {profile?.user?.name?.split(' ')[0] || 'there'}.</h1>
        <p className="text-subtle">{new Date().toLocaleDateString(undefined, { weekday: 'long', month: 'long', day: 'numeric' })}</p>
      </div>

      <div className="bg-card rounded-2xl border border-muted p-6 space-y-4">
        <div>
          <div className="flex justify-between items-end mb-2">
            <div>
              <div className="text-subtle text-sm">Today</div>
              <div className="text-2xl font-semibold">
                {Math.round(consumed)} <span className="text-subtle text-base">/ {goal} kcal</span>
              </div>
            </div>
            <div className="text-right text-sm text-subtle">{Math.round(remaining)} kcal left</div>
          </div>
          <div className="h-2 bg-muted rounded-full overflow-hidden">
            <div className="h-full bg-accent" style={{ width: `${pct}%` }} />
          </div>
        </div>

        <div className="grid grid-cols-4 gap-3 pt-4 border-t border-muted">
          <MacroStat label="Protein" value={protein} />
          <MacroStat label="Carbs" value={carbs} />
          <MacroStat label="Fats" value={fat} />
          <MacroStat label="Fiber" value={fiber} />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <NavCard to="/tracker" title="Tracker" subtitle="Calories · Weight · Measurements" />
        <NavCard to="/chat" title="Chat" subtitle="Log meals in plain language" />
      </div>
    </div>
  )
}

function MacroStat({ label, value }) {
  return (
    <div className="text-center">
      <div className="text-subtle text-xs uppercase tracking-wide">{label}</div>
      <div className="text-lg font-medium mt-0.5">
        {Math.round(value)}<span className="text-subtle text-sm ml-0.5">g</span>
      </div>
    </div>
  )
}

function NavCard({ to, title, subtitle }) {
  return (
    <Link
      to={to}
      className="bg-card rounded-2xl border border-muted p-6 hover:border-accent hover:bg-accentSoft transition"
    >
      <div className="text-xl font-semibold">{title}</div>
      <div className="text-subtle text-sm mt-1">{subtitle}</div>
    </Link>
  )
}
