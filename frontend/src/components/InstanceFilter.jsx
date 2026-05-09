import MultiSelect from './MultiSelect'

function InstanceFilter({ ranking, filters, onFilterChange, currency, currencyToggle }) {
  if (!ranking || ranking.length === 0) return null

  const arches = [...new Set(ranking.map(r => r.arch))].filter(Boolean).sort()
  const providers = [...new Set(ranking.map(r => r.provider))].filter(Boolean).sort()

  const maxPrice = Math.ceil(Math.max(...ranking.map(r => r.price_monthly)) * 1.2)

  const displayCurrency = currency?.displayCurrency || 'EUR'
  const currencySymbol = displayCurrency === 'EUR' ? '\u20AC' : '$'

  const handleChange = (key, value) => {
    onFilterChange({ ...filters, [key]: value })
  }

  const clearFilters = () => {
    onFilterChange({
      arch: [],
      provider: [],
      vcpu: '',
      ram: '',
      disk: '',
      min_monthly_price: 0,
      max_monthly_price: maxPrice,
      search: '',
      includeDisk: false
    })
  }

  const hasActiveFilters =
    filters.arch?.length > 0 ||
    filters.provider?.length > 0 ||
    filters.vcpu ||
    filters.ram ||
    filters.disk ||
    filters.search ||
    filters.min_monthly_price > 0 ||
    filters.max_monthly_price < maxPrice ||
    filters.includeDisk

  const minPct = (filters.min_monthly_price / maxPrice) * 100
  const maxPct = (filters.max_monthly_price / maxPrice) * 100

  return (
    <div className="filter-bar">
      <MultiSelect
        label="Architecture"
        options={arches}
        value={filters.arch}
        onChange={(v) => handleChange('arch', v)}
      />

      {providers.length > 1 && (
        <MultiSelect
          label="Provider"
          options={providers}
          value={filters.provider}
          onChange={(v) => handleChange('provider', v)}
        />
      )}

      <div className="filter-group">
        <label>vCPU</label>
        <input
          type="text"
          className="filter-input filter-input-narrow"
          placeholder=">2"
          value={filters.vcpu}
          onChange={(e) => handleChange('vcpu', e.target.value)}
        />
      </div>

      <div className="filter-group">
        <label>Memory (GB)</label>
        <input
          type="text"
          className="filter-input filter-input-narrow"
          placeholder="<32"
          value={filters.ram}
          onChange={(e) => handleChange('ram', e.target.value)}
        />
      </div>

      <div className="filter-group">
        <label>Disk (GB)</label>
        <input
          type="text"
          className="filter-input filter-input-narrow"
          placeholder=">50"
          value={filters.disk}
          onChange={(e) => handleChange('disk', e.target.value)}
        />
      </div>

      <div className="filter-group">
        <label>Price: {currencySymbol}{filters.min_monthly_price} {'\u2013'} {currencySymbol}{filters.max_monthly_price}</label>
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
        <label>Include Disk</label>
        <button
          onClick={() => handleChange('includeDisk', !filters.includeDisk)}
          style={{
            padding: '0.25rem 0.5rem',
            fontSize: '0.75rem',
            fontWeight: 500,
            border: '1px solid var(--color-border)',
            borderRadius: 'var(--radius-sm)',
            cursor: 'pointer',
            background: filters.includeDisk ? 'var(--color-primary)' : 'var(--color-surface-light)',
            color: filters.includeDisk ? '#fff' : 'var(--color-text-secondary)',
            minWidth: '48px',
            textAlign: 'center',
          }}
        >
          {filters.includeDisk ? 'ON' : 'OFF'}
        </button>
      </div>

      <div className="filter-group filter-group-grow">
        <label>Search</label>
        <input
          type="text"
          className="filter-input"
          placeholder="Instance type..."
          value={filters.search}
          onChange={(e) => handleChange('search', e.target.value)}
          style={{ width: '100%' }}
        />
      </div>

      {currencyToggle}

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
