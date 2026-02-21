import { useMemo } from 'react'

function InstanceFilter({ ranking, filters, onFilterChange }) {
  const architectures = useMemo(() => {
    const archs = new Set(ranking?.map(r => r.arch) || [])
    return Array.from(archs).sort()
  }, [ranking])

  const vcpuOptions = useMemo(() => {
    const cpus = new Set(ranking?.map(r => r.vcpu) || [])
    return Array.from(cpus).sort((a, b) => a - b)
  }, [ranking])

  const ramOptions = useMemo(() => {
    const rams = new Set(ranking?.map(r => r.ram_gb) || [])
    return Array.from(rams).sort((a, b) => a - b)
  }, [ranking])

  const maxPrice = useMemo(() => {
    if (!ranking?.length) return 100
    return Math.ceil(Math.max(...ranking.map(r => r.price_monthly)) * 1.2)
  }, [ranking])

  const handleReset = () => {
    onFilterChange({
      arch: '',
      min_vcpu: '',
      min_ram: '',
      max_monthly_price: maxPrice,
      search: ''
    })
  }

  const hasActiveFilters = filters.arch || filters.min_vcpu || filters.min_ram || 
    filters.max_monthly_price !== maxPrice || filters.search

  const activeCount = [
    filters.arch,
    filters.min_vcpu,
    filters.min_ram,
    filters.max_monthly_price !== maxPrice ? 'price' : '',
    filters.search
  ].filter(Boolean).length

  return (
    <div className="card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <h2 className="card-title" style={{ margin: 0 }}>
          Filters
          {activeCount > 0 && (
            <span style={{
              marginLeft: '0.5rem',
              fontSize: '0.75rem',
              padding: '0.125rem 0.5rem',
              background: 'var(--color-primary)',
              borderRadius: '9999px'
            }}>
              {activeCount}
            </span>
          )}
        </h2>
        {hasActiveFilters && (
          <button
            onClick={handleReset}
            style={{
              fontSize: '0.875rem',
              color: 'var(--color-text-muted)',
              background: 'none',
              border: 'none',
              cursor: 'pointer'
            }}
            onMouseEnter={(e) => e.target.style.color = 'var(--color-text)'}
            onMouseLeave={(e) => e.target.style.color = 'var(--color-text-muted)'}
          >
            Reset
          </button>
        )}
      </div>

      <div className="filter-grid">
        <div className="filter-group">
          <label>Search</label>
          <input
            type="text"
            value={filters.search}
            onChange={(e) => onFilterChange({ ...filters, search: e.target.value })}
            placeholder="Instance name..."
            className="filter-input"
          />
        </div>

        <div className="filter-group">
          <label>Architecture</label>
          <select
            value={filters.arch}
            onChange={(e) => onFilterChange({ ...filters, arch: e.target.value })}
            className="filter-select"
          >
            <option value="">All</option>
            {architectures.map(arch => (
              <option key={arch} value={arch}>{arch}</option>
            ))}
          </select>
        </div>

        <div className="filter-group">
          <label>Min vCPU</label>
          <select
            value={filters.min_vcpu}
            onChange={(e) => onFilterChange({ ...filters, min_vcpu: e.target.value })}
            className="filter-select"
          >
            <option value="">Any</option>
            {vcpuOptions.map(cpu => (
              <option key={cpu} value={cpu}>{cpu}+</option>
            ))}
          </select>
        </div>

        <div className="filter-group">
          <label>Min RAM (GB)</label>
          <select
            value={filters.min_ram}
            onChange={(e) => onFilterChange({ ...filters, min_ram: e.target.value })}
            className="filter-select"
          >
            <option value="">Any</option>
            {ramOptions.map(ram => (
              <option key={ram} value={ram}>{ram}+</option>
            ))}
          </select>
        </div>

        <div className="filter-group" style={{ gridColumn: 'span 2' }}>
          <label>
            Max Price: €{filters.max_monthly_price}/month
          </label>
          <input
            type="range"
            min="0"
            max={maxPrice}
            step="1"
            value={filters.max_monthly_price}
            onChange={(e) => onFilterChange({ ...filters, max_monthly_price: parseInt(e.target.value) })}
            className="filter-range"
          />
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
            <span>€0</span>
            <span>€{maxPrice}</span>
          </div>
        </div>
      </div>

      {ranking && (
        <div style={{ marginTop: '1rem', fontSize: '0.875rem', color: 'var(--color-text-muted)' }}>
          Showing {ranking.length} instance{ranking.length !== 1 ? 's' : ''}
        </div>
      )}
    </div>
  )
}

export default InstanceFilter
