function InstanceFilter({ ranking, filters, onFilterChange }) {
  if (!ranking || ranking.length === 0) return null

  const arches = [...new Set(ranking.map(r => r.arch))].filter(Boolean).sort()

  const maxPrice = Math.ceil(Math.max(...ranking.map(r => r.price_monthly)) * 1.2)

  const handleChange = (key, value) => {
    onFilterChange({ ...filters, [key]: value })
  }

  const clearFilters = () => {
    onFilterChange({
      arch: '',
      vcpu: '',
      ram: '',
      disk: '',
      min_monthly_price: 0,
      max_monthly_price: maxPrice,
      search: ''
    })
  }

  const hasActiveFilters =
    filters.arch ||
    filters.vcpu ||
    filters.ram ||
    filters.disk ||
    filters.search ||
    filters.min_monthly_price > 0 ||
    filters.max_monthly_price < maxPrice

  const minPct = (filters.min_monthly_price / maxPrice) * 100
  const maxPct = (filters.max_monthly_price / maxPrice) * 100

  return (
    <div className="filter-bar">
      <div className="filter-group">
        <label>Architecture</label>
        <select
          className="filter-select"
          value={filters.arch}
          onChange={(e) => handleChange('arch', e.target.value)}
        >
          <option value="">All</option>
          {arches.map(arch => (
            <option key={arch} value={arch}>{arch}</option>
          ))}
        </select>
      </div>

      <div className="filter-group">
        <label>vCPU</label>
        <input
          type="text"
          className="filter-input"
          placeholder=">2"
          value={filters.vcpu}
          onChange={(e) => handleChange('vcpu', e.target.value)}
          style={{ width: '70px' }}
        />
      </div>

      <div className="filter-group">
        <label>Memory (GB)</label>
        <input
          type="text"
          className="filter-input"
          placeholder="<32"
          value={filters.ram}
          onChange={(e) => handleChange('ram', e.target.value)}
          style={{ width: '70px' }}
        />
      </div>

      <div className="filter-group">
        <label>Disk (GB)</label>
        <input
          type="text"
          className="filter-input"
          placeholder=">50"
          value={filters.disk}
          onChange={(e) => handleChange('disk', e.target.value)}
          style={{ width: '70px' }}
        />
      </div>

      <div className="filter-group">
        <label>Price: €{filters.min_monthly_price} – €{filters.max_monthly_price}</label>
        <div className="range-slider">
          <div
            className="range-slider-track"
            style={{
              background: `linear-gradient(to right,
                var(--color-surface-light) ${minPct}%,
                var(--color-primary) ${minPct}%,
                var(--color-primary) ${maxPct}%,
                var(--color-surface-light) ${maxPct}%)`
            }}
          />
          <input
            type="range"
            className="range-slider-input"
            min={0}
            max={maxPrice}
            step={1}
            value={filters.min_monthly_price}
            onChange={(e) => {
              const val = parseInt(e.target.value)
              if (val <= filters.max_monthly_price) handleChange('min_monthly_price', val)
            }}
          />
          <input
            type="range"
            className="range-slider-input"
            min={0}
            max={maxPrice}
            step={1}
            value={filters.max_monthly_price}
            onChange={(e) => {
              const val = parseInt(e.target.value)
              if (val >= filters.min_monthly_price) handleChange('max_monthly_price', val)
            }}
          />
        </div>
      </div>

      <div className="filter-group">
        <label>Search</label>
        <input
          type="text"
          className="filter-input"
          placeholder="Instance type..."
          value={filters.search}
          onChange={(e) => handleChange('search', e.target.value)}
          style={{ width: '140px' }}
        />
      </div>

      <div className="filter-actions">
        {hasActiveFilters && (
          <button onClick={clearFilters} className="btn btn-ghost btn-small">
            Clear
          </button>
        )}
      </div>
    </div>
  )
}

export default InstanceFilter
