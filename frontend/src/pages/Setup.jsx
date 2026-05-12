import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api.js'

const FIELDS = [
  { name: 'name', label: 'Name', type: 'text', required: true },
  { name: 'age', label: 'Age', type: 'number', required: true },
  { name: 'height_cm', label: 'Height (cm)', type: 'number', step: '0.1', required: true },
  { name: 'weight_kg', label: 'Weight (kg)', type: 'number', step: '0.1', required: true },
  { name: 'sex', label: 'Biological sex', type: 'select',
    options: ['male', 'female', 'other'], required: true },
  { name: 'activity_level', label: 'Activity level', type: 'select',
    options: ['sedentary', 'light', 'moderate', 'active', 'very active'], required: true },
  { name: 'calorie_goal', label: 'Daily calorie goal (kcal)', type: 'number', required: true },
  { name: 'body_fat_pct', label: 'Body fat % (optional)', type: 'number', step: '0.1' },
  { name: 'bmr', label: 'BMR (optional)', type: 'number' },
]

export default function Setup() {
  const navigate = useNavigate()
  const [form, setForm] = useState({})
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    api.getProfile().then((p) => {
      if (p?.user) {
        const u = p.user
        setForm({
          name: u.name ?? '',
          age: u.age ?? '',
          height_cm: u.height_cm ?? '',
          weight_kg: u.weight_kg ?? '',
          sex: u.sex ?? '',
          activity_level: u.activity_level ?? '',
          calorie_goal: u.calorie_goal ?? '',
          body_fat_pct: u.body_fat_pct ?? '',
          bmr: u.bmr ?? '',
        })
      }
    }).catch(() => {})
  }, [])

  const onChange = (e) => setForm({ ...form, [e.target.name]: e.target.value })

  const onSubmit = async (e) => {
    e.preventDefault()
    setSaving(true)
    setError(null)
    try {
      const payload = {
        name: form.name,
        age: Number(form.age),
        height_cm: Number(form.height_cm),
        weight_kg: Number(form.weight_kg),
        sex: form.sex,
        activity_level: form.activity_level,
        calorie_goal: Number(form.calorie_goal),
        body_fat_pct: form.body_fat_pct ? Number(form.body_fat_pct) : null,
        bmr: form.bmr ? Number(form.bmr) : null,
      }
      await api.setup(payload)
      navigate('/')
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="max-w-xl mx-auto">
      <h1 className="text-3xl font-semibold mb-1">Set up your profile</h1>
      <p className="text-subtle mb-6">Lumen uses this to ground every reply from the local model.</p>
      <form onSubmit={onSubmit} className="space-y-4 bg-card rounded-2xl p-6 border border-muted">
        {FIELDS.map((f) => (
          <div key={f.name} className="grid grid-cols-3 items-center gap-3">
            <label htmlFor={f.name} className="col-span-1 text-sm text-subtle">{f.label}</label>
            {f.type === 'select' ? (
              <select
                id={f.name} name={f.name}
                value={form[f.name] ?? ''}
                onChange={onChange}
                required={f.required}
                className="col-span-2 bg-muted rounded-lg px-3 py-2 outline-none focus:ring-2 focus:ring-accent"
              >
                <option value="" disabled>Select…</option>
                {f.options.map((o) => <option key={o} value={o}>{o}</option>)}
              </select>
            ) : (
              <input
                id={f.name} name={f.name} type={f.type} step={f.step}
                value={form[f.name] ?? ''}
                onChange={onChange}
                required={f.required}
                className="col-span-2 bg-muted rounded-lg px-3 py-2 outline-none focus:ring-2 focus:ring-accent"
              />
            )}
          </div>
        ))}
        {error && <div className="text-red-400 text-sm">{error}</div>}
        <button
          type="submit"
          disabled={saving}
          className="w-full mt-2 bg-accent hover:bg-purple-500 text-white font-medium py-2.5 rounded-lg disabled:opacity-50"
        >
          {saving ? 'Saving…' : 'Save profile'}
        </button>
      </form>
    </div>
  )
}
