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
    <div className="filter-group filter-group-select" ref={ref}>
      <label>{label}</label>
      <button
        className="filter-select filter-select-button"
        onClick={() => setOpen(!open)}
        type="button"
        aria-expanded={open}
      >
        <span>{labelText}</span>
        <span className="filter-select-caret">{open ? '\u25B2' : '\u25BC'}</span>
      </button>
      {open && (
        <div className="filter-select-menu">
          {options.map(opt => (
            <label key={opt} className="filter-select-option">
              <input
                type="checkbox"
                checked={value.includes(opt)}
                onChange={() => toggle(opt)}
              />
              {opt}
            </label>
          ))}
        </div>
      )}
    </div>
  )
}
