import ScoreBar from './ScoreBar'

function getScoreColor(score) {
  if (score >= 80) return '#22c55e'
  if (score >= 60) return '#f59e0b'
  return '#ef4444'
}

function ComparisonTable({ ranking, metadata, selectedForComparison, onToggleSelection, maxSelections }) {
  if (!ranking || ranking.length === 0) {
    return (
      <div className="card">
        <h2 className="card-title">Performance Comparison</h2>
        <p>No benchmark data available.</p>
      </div>
    )
  }

  const currency = metadata?.currency || 'EUR'
  const currencySymbol = currency === 'EUR' ? '€' : currency

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('de-DE', {
      style: 'currency',
      currency: currency,
      minimumFractionDigits: 2
    }).format(value)
  }

  const canSelectMore = selectedForComparison.length < maxSelections

  return (
    <div className="card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <h2 className="card-title" style={{ margin: 0 }}>
          Performance & Value Comparison
        </h2>
        {selectedForComparison.length > 0 && (
          <div style={{ fontSize: '0.875rem', color: 'var(--color-text-muted)' }}>
            {selectedForComparison.length}/{maxSelections} selected for comparison
          </div>
        )}
      </div>
      
      <div className="table-container">
        <table className="comparison-table">
          <thead>
            <tr>
              <th>Compare</th>
              <th>Rank</th>
              <th>Instance</th>
              <th>Single Core</th>
              <th>Multi Core</th>
              <th>RAM Speed</th>
              <th>Disk IOPS</th>
              <th>Overall</th>
              <th>Price/Hour</th>
              <th>Price/Month</th>
              <th>CPU Value*</th>
            </tr>
          </thead>
          <tbody>
            {ranking.map((instance, index) => {
              const isSelected = selectedForComparison.includes(instance.instance_type)
              const canSelect = isSelected || canSelectMore
              
              return (
                <tr 
                  key={instance.instance_type}
                  style={isSelected ? { background: 'rgba(59, 130, 246, 0.1)' } : {}}
                >
                  <td>
                    <input
                      type="checkbox"
                      checked={isSelected}
                      onChange={() => onToggleSelection?.(instance.instance_type)}
                      disabled={!canSelect}
                      style={{ 
                        cursor: canSelect ? 'pointer' : 'not-allowed',
                        width: '18px',
                        height: '18px'
                      }}
                      title={isSelected ? 'Click to remove from comparison' : canSelectMore ? 'Click to compare' : `Max ${maxSelections} instances`}
                    />
                  </td>
                  <td className="rank">{index + 1}</td>
                  <td>
                    <div className="instance-name">
                      <strong>{instance.instance_type}</strong>
                      <span className="arch-badge">{instance.arch}</span>
                    </div>
                    <small className="specs">{instance.vcpu} vCPU • {instance.ram_gb} GB</small>
                  </td>
                  <td>
                    <div className="score-cell">
                      <ScoreBar value={instance.single_core_score} />
                      <span className="score-value">{instance.single_core_score.toFixed(0)}</span>
                    </div>
                  </td>
                  <td>
                    <div className="score-cell">
                      <ScoreBar value={instance.multi_core_score} />
                      <span className="score-value">{instance.multi_core_score.toFixed(0)}</span>
                    </div>
                  </td>
                  <td>
                    <div className="score-cell">
                      <ScoreBar value={instance.memory_score} />
                      <span className="score-value">{instance.memory_score.toFixed(0)}</span>
                    </div>
                  </td>
                  <td>
                    <div className="score-cell">
                      <ScoreBar value={instance.disk_score} />
                      <span className="score-value">{instance.disk_score.toFixed(0)}</span>
                    </div>
                  </td>
                  <td>
                    <span className="overall-score" style={{ color: getScoreColor(instance.overall_score) }}>
                      {instance.overall_score.toFixed(0)}
                    </span>
                  </td>
                  <td className="price">
                    {formatCurrency(instance.price_hourly)}
                  </td>
                  <td className="price">
                    {formatCurrency(instance.price_monthly)}
                  </td>
                  <td>
                    <span className="value-score" title={`CPU Score per ${currencySymbol} per Month`}>
                      {instance.cpu_value_monthly.toFixed(1)}
                    </span>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
      <p className="table-note">
        <small>
          * <strong>CPU Value</strong> = CPU Score per {currencySymbol} per Month (higher is better).
          Based on single + multi-core performance vs monthly price.
          {onToggleSelection && (
            <span style={{ marginLeft: '1rem', color: 'var(--color-text-muted)' }}>
              Click checkboxes to compare up to {maxSelections} instances side-by-side.
            </span>
          )}
        </small>
      </p>
    </div>
  )
}

export default ComparisonTable
