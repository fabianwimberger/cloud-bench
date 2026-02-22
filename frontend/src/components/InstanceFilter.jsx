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
      min_vcpu: '',
      min_ram: '',
      max_monthly_price: maxPrice,
      search: ''
    })
  }

  const hasActiveFilters = filters.arch || filters.min_vcpu || filters.min_ram || filters.search || filters.max_monthly_price < maxPrice

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
        <label>Min vCPUs</label>
        <input
          type="number"
          className="filter-input"
          placeholder="0"
          value={filters.min_vcpu}
          onChange={(e) => handleChange('min_vcpu', e.target.value)}
          min="0"
          style={{ width: '70px' }}
        />
      </div>

      <div className="filter-group">
        <label>Min RAM (GB)</label>
        <input
          type="number"
          className="filter-input"
          placeholder="0"
          value={filters.min_ram}
          onChange={(e) => handleChange('min_ram', e.target.value)}
          min="0"
          style={{ width: '70px' }}
        />
      </div>

      <div className="filter-group">
        <label>Max Price: €{filters.max_monthly_price}</label>
        <input
          type="range"
          className="filter-range"
          min="0"
          max={maxPrice}
          step="1"
          value={filters.max_monthly_price}
          onChange={(e) => handleChange('max_monthly_price', parseInt(e.target.value))}
        />
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
