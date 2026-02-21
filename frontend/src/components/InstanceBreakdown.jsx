function InstanceBreakdown({ ranking, metadata }) {
  if (!ranking || ranking.length === 0) return null

  // Sort by value for recommendations
  const byValue = [...ranking].sort((a, b) => b.cpu_value_monthly - a.cpu_value_monthly)
  const bestValue = byValue[0]
  const bestPerformance = ranking.reduce((best, current) =>
    current.overall_score > best.overall_score ? current : best
  )

  const currency = metadata?.currency || 'EUR'
  const currencySymbol = currency === 'EUR' ? '€' : currency

  return (
    <div className="card">
      <h2 className="card-title">Recommendations</h2>

      <div className="grid grid-2" style={{ marginBottom: '1.5rem' }}>
        <div className="recommendation-box" style={{
          background: 'rgba(34, 197, 94, 0.1)',
          border: '1px solid rgba(34, 197, 94, 0.3)',
          borderRadius: '8px',
          padding: '1rem'
        }}>
          <h3 style={{ color: '#22c55e', marginBottom: '0.5rem' }}>Best Value</h3>
          <p><strong>{bestValue.display_name}</strong></p>
          <p style={{ color: 'var(--color-text-muted)', fontSize: '0.875rem' }}>
            {bestValue.cpu_value_monthly.toFixed(1)} CPU points per {currencySymbol}/month
          </p>
        </div>

        <div className="recommendation-box" style={{
          background: 'rgba(59, 130, 246, 0.1)',
          border: '1px solid rgba(59, 130, 246, 0.3)',
          borderRadius: '8px',
          padding: '1rem'
        }}>
          <h3 style={{ color: '#3b82f6', marginBottom: '0.5rem' }}>Best Performance</h3>
          <p><strong>{bestPerformance.display_name}</strong></p>
          <p style={{ color: 'var(--color-text-muted)', fontSize: '0.875rem' }}>
            Overall score: {bestPerformance.overall_score.toFixed(0)}/100
          </p>
        </div>
      </div>

      <h3 style={{ marginBottom: '1rem', fontSize: '1rem' }}>Instance Details</h3>
      <div className="grid grid-3">
        {ranking.map((instance) => {
          return (
            <div key={instance.instance_type} className="stat-card" style={{
              textAlign: 'left',
              borderColor: instance.instance_type === bestValue.instance_type ? '#22c55e' :
                          instance.instance_type === bestPerformance.instance_type ? '#3b82f6' :
                          'var(--color-surface-light)'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                <strong>{instance.instance_type}</strong>
                <span style={{
                  fontSize: '0.7rem',
                  padding: '0.125rem 0.375rem',
                  background: 'rgba(213, 12, 45, 0.2)',
                  color: '#fb7185',
                  borderRadius: '4px'
                }}>
                  {instance.arch}
                </span>
              </div>

              <div style={{ fontSize: '0.8rem', marginTop: '0.75rem' }}>
                <p style={{ marginBottom: '0.25rem' }}>
                  <span style={{ color: 'var(--color-text-muted)' }}>Specs:</span>{' '}
                  {instance.vcpu} vCPU · {instance.ram_gb} GB RAM · {instance.disk_gb} GB Disk
                </p>
                <p style={{ marginBottom: '0.25rem' }}>
                  <span style={{ color: 'var(--color-text-muted)' }}>Score:</span>{' '}
                  {instance.overall_score.toFixed(0)}/100
                </p>
                <p style={{ color: 'var(--color-text-muted)' }}>
                  {currencySymbol}{instance.price_monthly.toFixed(2)}/month
                </p>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default InstanceBreakdown
