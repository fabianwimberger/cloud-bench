import MultiSelect from './MultiSelect'

function InstanceFilter({ ranking, filters, onFilterChange, currency, currencyToggle, resultCount }) {
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
      <div className="filter-bar-header">
        <div>
          <h2 className="filter-title">Filters</h2>
          <p className="filter-summary">
            Showing {resultCount ?? ranking.length} of {ranking.length} instances
          </p>
        </div>

        <div className="filter-actions">
          {hasActiveFilters && (
            <button onClick={clearFilters} className="btn btn-ghost btn-small">
              Clear filters
            </button>
          )}
        </div>
      </div>

      <div className="filter-primary">
        <div className="filter-group filter-group-search">
          <label>Search</label>
          <input
            type="text"
            className="filter-input"
            placeholder="Instance type..."
            value={filters.search}
            onChange={(e) => handleChange('search', e.target.value)}
          />
        </div>

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

        {currencyToggle}
      </div>

      <div className="filter-advanced">
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
          <label>Memory</label>
          <input
            type="text"
            className="filter-input filter-input-narrow"
            placeholder="<32"
            value={filters.ram}
            onChange={(e) => handleChange('ram', e.target.value)}
          />
        </div>

        <div className="filter-group">
          <label>Disk</label>
          <input
            type="text"
            className="filter-input filter-input-narrow"
            placeholder=">50"
            value={filters.disk}
            onChange={(e) => handleChange('disk', e.target.value)}
          />
        </div>

        <div className="filter-group filter-group-price">
          <label>Monthly price</label>
          <div className="price-filter">
            <span>{currencySymbol}{filters.min_monthly_price}</span>
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
                aria-label="Minimum monthly price"
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
                aria-label="Maximum monthly price"
                onChange={(e) => {
                  const val = parseInt(e.target.value)
                  if (val >= filters.min_monthly_price) handleChange('max_monthly_price', val)
                }}
              />
            </div>
            <span>{currencySymbol}{filters.max_monthly_price}</span>
          </div>
        </div>

        <div className="filter-group filter-group-toggle">
          <label>Value formula</label>
          <button
            onClick={() => handleChange('includeDisk', !filters.includeDisk)}
            className={`filter-toggle ${filters.includeDisk ? 'active' : ''}`}
            aria-pressed={filters.includeDisk}
          >
            {filters.includeDisk ? 'CPU + memory + disk' : 'CPU + memory'}
          </button>
        </div>
      </div>
    </div>
  )
}

export default InstanceFilter
