import ScoreBar from './ScoreBar'

function formatNumber(num, decimals = 0) {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(decimals) + 'M'
  }
  if (num >= 1000) {
    return (num / 1000).toFixed(decimals) + 'K'
  }
  return num.toFixed(decimals)
}

function ComparisonTable({ ranking, metadata, selectedForComparison, onToggleSelection, maxSelections }) {
  if (!ranking || ranking.length === 0) {
    return (
      <div className="card">
        <h2 className="card-title">Instance Comparison</h2>
        <p style={{ color: 'var(--color-text-muted)' }}>No benchmark data available.</p>
      </div>
    )
  }

  const currency = metadata?.currency || 'EUR'
  const currencySymbol = currency === 'EUR' ? '€' : currency

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('de-DE', {
      style: 'currency',
      currency: currency,
      minimumFractionDigits: 4,
      maximumFractionDigits: 4
    }).format(value)
  }

  const canSelectMore = selectedForComparison.length < maxSelections

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
              <th>Instance</th>
              <th>Architecture</th>
              <th className="cell-numeric">vCPUs</th>
              <th className="cell-numeric">Memory</th>
              <th className="cell-numeric">Disk</th>
              <th className="cell-numeric">CPU Single</th>
              <th className="cell-numeric">CPU Multi</th>
              <th className="cell-numeric">Memory</th>
              <th className="cell-numeric">Disk IOPS</th>
              <th className="cell-numeric">Hourly</th>
              <th className="cell-numeric">Monthly</th>
              <th className="cell-numeric">Value</th>
            </tr>
          </thead>
          <tbody>
            {ranking.map((instance) => {
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
                      <span className="instance-name">{instance.instance_type}</span>
                    </div>
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
                      <span>{formatNumber(metrics.cpu_single_events || 0)}</span>
                    </div>
                  </td>
                  <td className="cell-numeric">
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', justifyContent: 'flex-end' }}>
                      <ScoreBar value={instance.multi_core_score} />
                      <span>{formatNumber(metrics.cpu_multi_events || 0)}</span>
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
                      <span>{formatNumber(metrics.disk_iops || 0)}</span>
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
