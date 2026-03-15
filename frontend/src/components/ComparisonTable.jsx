import { useState } from 'react'
import ScoreBar from './ScoreBar'
import ProviderBadge from './ProviderBadge'

function ComparisonTable({ ranking, metadata, selectedForComparison, onToggleSelection, maxSelections, currency, onSelectHistory }) {
  const [sortKey, setSortKey] = useState(null)
  const [sortDir, setSortDir] = useState('desc')

  if (!ranking || ranking.length === 0) {
    return (
      <div className="card">
        <h2 className="card-title">Instance Comparison</h2>
        <p style={{ color: 'var(--color-text-muted)' }}>No benchmark data available.</p>
      </div>
    )
  }

  const displayCurrency = currency?.displayCurrency || metadata?.currency || 'EUR'
  const currencySymbol = displayCurrency === 'EUR' ? '\u20AC' : '$'

  const formatCurrency = (value) => {
    const converted = currency?.formatPriceRaw ? currency.formatPriceRaw(value) : value
    return new Intl.NumberFormat(displayCurrency === 'EUR' ? 'de-DE' : 'en-US', {
      style: 'currency',
      currency: displayCurrency,
      minimumFractionDigits: 4,
      maximumFractionDigits: 4
    }).format(converted)
  }

  const canSelectMore = selectedForComparison.length < maxSelections

  const getNestedValue = (obj, key) => {
    if (key.startsWith('metrics.')) {
      return obj.metrics?.[key.slice(8)] ?? 0
    }
    return obj[key] ?? 0
  }

  const sorted = sortKey
    ? [...ranking].sort((a, b) => {
        const av = getNestedValue(a, sortKey)
        const bv = getNestedValue(b, sortKey)
        if (typeof av === 'string') {
          return sortDir === 'asc' ? av.localeCompare(bv) : bv.localeCompare(av)
        }
        return sortDir === 'asc' ? av - bv : bv - av
      })
    : ranking

  const handleSort = (key) => {
    if (sortKey === key) {
      setSortDir(d => d === 'asc' ? 'desc' : 'asc')
    } else {
      setSortKey(key)
      setSortDir('desc')
    }
  }

  const indicator = (key) => sortKey === key ? (sortDir === 'asc' ? ' \u25B2' : ' \u25BC') : ''

  return (
    <div className="card">
      <div className="section-header">
        <h2 className="section-title" style={{ margin: 0 }}>
          Instance Comparison
        </h2>
        {selectedForComparison.length > 0 && (
          <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
            {selectedForComparison.length}/{maxSelections} selected
          </div>
        )}
      </div>

      <div className="table-container">
        <table className="comparison-table">
          <thead>
            <tr>
              <th style={{ width: '40px' }}></th>
              <th className="sortable" onClick={() => handleSort('instance_type')}>Instance{indicator('instance_type')}</th>
              <th className="sortable" onClick={() => handleSort('provider')}>Provider{indicator('provider')}</th>
              <th className="sortable" onClick={() => handleSort('arch')}>Arch{indicator('arch')}</th>
              <th className="cell-numeric sortable" onClick={() => handleSort('vcpu')}>vCPUs{indicator('vcpu')}</th>
              <th className="cell-numeric sortable" onClick={() => handleSort('ram_gb')}>Memory{indicator('ram_gb')}</th>
              <th className="cell-numeric sortable" onClick={() => handleSort('disk_gb')}>Disk{indicator('disk_gb')}</th>
              <th className="cell-numeric sortable" onClick={() => handleSort('metrics.cpu_single_events')}>CPU Single{indicator('metrics.cpu_single_events')}</th>
              <th className="cell-numeric sortable" onClick={() => handleSort('metrics.cpu_multi_events')}>CPU Multi{indicator('metrics.cpu_multi_events')}</th>
              <th className="cell-numeric sortable" onClick={() => handleSort('metrics.memory_mib_per_sec')}>Memory{indicator('metrics.memory_mib_per_sec')}</th>
              <th className="cell-numeric sortable" onClick={() => handleSort('metrics.disk_iops')}>Disk IOPS{indicator('metrics.disk_iops')}</th>
              <th className="cell-numeric sortable" onClick={() => handleSort('price_hourly')}>Hourly{indicator('price_hourly')}</th>
              <th className="cell-numeric sortable" onClick={() => handleSort('price_monthly')}>Monthly{indicator('price_monthly')}</th>
              <th className="cell-numeric sortable" onClick={() => handleSort('cpu_value_monthly')}>Value{indicator('cpu_value_monthly')}</th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((instance) => {
              const isSelected = selectedForComparison.includes(instance.instance_type)
              const canSelect = isSelected || canSelectMore
              const metrics = instance.metrics || {}

              return (
                <tr
                  key={instance.instance_type}
                  className={isSelected ? 'selected' : ''}
                >
                  <td>
                    <input
                      type="checkbox"
                      className="checkbox"
                      checked={isSelected}
                      onChange={() => onToggleSelection?.(instance.instance_type)}
                      disabled={!canSelect}
                      title={isSelected ? 'Remove from comparison' : canSelectMore ? 'Add to comparison' : `Max ${maxSelections} instances`}
                    />
                  </td>
                  <td>
                    <div className="instance-cell">
                      <button
                        className="instance-name-btn"
                        onClick={() => onSelectHistory?.(instance.instance_type)}
                        title="View history"
                      >
                        {instance.instance_type}
                      </button>
                    </div>
                  </td>
                  <td>
                    <ProviderBadge provider={instance.provider} />
                  </td>
                  <td>
                    <span className="arch-badge">{instance.arch}</span>
                  </td>
                  <td className="cell-numeric">{instance.vcpu}</td>
                  <td className="cell-numeric">{instance.ram_gb} <span className="metric-unit">GB</span></td>
                  <td className="cell-numeric">{instance.disk_gb} <span className="metric-unit">GB</span></td>
                  <td className="cell-numeric">
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', justifyContent: 'flex-end' }}>
                      <ScoreBar value={instance.single_core_score} />
                      <span>{Math.round(metrics.cpu_single_events || 0).toLocaleString()}</span>
                    </div>
                  </td>
                  <td className="cell-numeric">
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', justifyContent: 'flex-end' }}>
                      <ScoreBar value={instance.multi_core_score} />
                      <span>{Math.round(metrics.cpu_multi_events || 0).toLocaleString()}</span>
                    </div>
                  </td>
                  <td className="cell-numeric">
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', justifyContent: 'flex-end' }}>
                      <ScoreBar value={instance.memory_score} />
                      <span>{Math.round(metrics.memory_mib_per_sec || 0)} <span className="metric-unit">MiB/s</span></span>
                    </div>
                  </td>
                  <td className="cell-numeric">
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', justifyContent: 'flex-end' }}>
                      <ScoreBar value={instance.disk_score} />
                      <span>{Math.round(metrics.disk_iops || 0).toLocaleString()}</span>
                    </div>
                  </td>
                  <td className="price-cell cell-numeric">
                    {formatCurrency(instance.price_hourly)}
                  </td>
                  <td className="price-cell cell-numeric">
                    {formatCurrency(instance.price_monthly)}
                  </td>
                  <td className="cell-numeric" style={{ color: 'var(--color-primary-light)', fontWeight: 500 }}>
                    {instance.cpu_value_monthly.toFixed(1)}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      <p className="table-note">
        <strong>Value</strong> = CPU Score per {currencySymbol} per Month (higher is better).
        Click checkboxes to compare up to {maxSelections} instances.
      </p>
    </div>
  )
}

export default ComparisonTable
