import { useState, useRef, useEffect } from 'react'

export default function MultiSelect({ label, options, value = [], onChange }) {
  const [open, setOpen] = useState(false)
  const ref = useRef(null)

  useEffect(() => {
    const handler = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false)
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const toggle = (opt) => {
    onChange(
      value.includes(opt) ? value.filter(v => v !== opt) : [...value, opt]
    )
  }

  const labelText = value.length === 0
    ? 'All'
    : value.length === 1
      ? value[0]
      : `${value.length} selected`

  return (
    <div className="filter-group" ref={ref} style={{ position: 'relative' }}>
      <label>{label}</label>
      <button
        className="filter-select"
        onClick={() => setOpen(!open)}
        style={{ cursor: 'pointer', minWidth: '110px', textAlign: 'left', display: 'flex', alignItems: 'center', gap: '0.25rem' }}
      >
        <span style={{ flex: 1 }}>{labelText}</span>
        <span style={{ fontSize: '0.625rem', color: 'var(--color-text-muted)' }}>{open ? '\u25B2' : '\u25BC'}</span>
      </button>
      {open && (
        <div style={{
          position: 'absolute',
          top: '100%',
          left: 0,
          marginTop: '2px',
          background: 'var(--color-surface)',
          border: '1px solid var(--color-border)',
          borderRadius: 'var(--radius-sm)',
          minWidth: '140px',
          zIndex: 100,
          boxShadow: 'var(--shadow-md)'
        }}>
          {options.map(opt => (
            <label key={opt} style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.375rem',
              padding: '0.375rem 0.5rem',
              cursor: 'pointer',
              fontSize: '0.8125rem',
              color: 'var(--color-text)',
            }}>
              <input
                type="checkbox"
                checked={value.includes(opt)}
                onChange={() => toggle(opt)}
                style={{ accentColor: 'var(--color-primary)' }}
              />
              {opt}
            </label>
          ))}
        </div>
      )}
    </div>
  )
}
