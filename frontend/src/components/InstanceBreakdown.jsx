function InstanceBreakdown({ ranking, metadata }) {
  if (!ranking || ranking.length === 0) return null

  // Sort by value for recommendations
  const byValue = [...ranking].sort((a, b) => b.cpu_value_monthly - a.cpu_value_monthly)
  const bestValue = byValue[0]
  const bestPerformance = ranking.reduce((best, current) =>
    current.overall_score > best.overall_score ? current : best
  )
  const fastestCpu = ranking.reduce((fastest, current) =>
    (current.metrics?.cpu_single_events || 0) > (fastest.metrics?.cpu_single_events || 0) ? current : fastest
  )

  const currency = metadata?.currency || 'EUR'
  const currencySymbol = currency === 'EUR' ? '€' : currency

  return (
    <div className="card">
      <h2 className="card-title">Top Performers</h2>

      <div className="grid grid-3" style={{ marginBottom: '1.5rem' }}>
        <div className="stat-card" style={{
          borderColor: 'var(--color-primary)',
          background: 'rgba(139, 92, 246, 0.05)'
        }}>
          <div className="label" style={{ color: 'var(--color-primary-light)' }}>Best Value</div>
          <div className="value" style={{ fontSize: '1.25rem', marginTop: '0.5rem' }}>{bestValue.instance_type}</div>
          <div className="subtext">
            {bestValue.cpu_value_monthly.toFixed(1)} pts/{currencySymbol}/mo
          </div>
        </div>

        <div className="stat-card" style={{
          borderColor: 'var(--color-success)',
          background: 'rgba(34, 197, 94, 0.05)'
        }}>
          <div className="label" style={{ color: 'var(--color-success)' }}>Best Performance</div>
          <div className="value" style={{ fontSize: '1.25rem', marginTop: '0.5rem' }}>{bestPerformance.instance_type}</div>
          <div className="subtext">
            {bestPerformance.overall_score.toFixed(0)}/100 overall score
          </div>
        </div>

        <div className="stat-card" style={{
          borderColor: 'var(--color-info)',
          background: 'rgba(59, 130, 246, 0.05)'
        }}>
          <div className="label" style={{ color: 'var(--color-info)' }}>Fastest CPU</div>
          <div className="value" style={{ fontSize: '1.25rem', marginTop: '0.5rem' }}>{fastestCpu.instance_type}</div>
          <div className="subtext">
            {Math.round(fastestCpu.metrics?.cpu_single_events || 0).toLocaleString()} events/sec
          </div>
        </div>
      </div>

      <h3 style={{ marginBottom: '1rem', fontSize: '0.875rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--color-text-muted)' }}>
        All Instances
      </h3>
      
      <div className="grid grid-3">
        {ranking.map((instance) => {
          const isBestValue = instance.instance_type === bestValue.instance_type
          const isBestPerf = instance.instance_type === bestPerformance.instance_type
          const isFastestCpu = instance.instance_type === fastestCpu.instance_type
          
          let borderColor = 'var(--color-border)'
          if (isBestValue) borderColor = 'var(--color-primary)'
          else if (isBestPerf) borderColor = 'var(--color-success)'
          else if (isFastestCpu) borderColor = 'var(--color-info)'
          
          return (
            <div key={instance.instance_type} className="stat-card" style={{
              textAlign: 'left',
              borderColor: borderColor
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.75rem' }}>
                <div>
                  <strong style={{ fontSize: '1rem' }}>{instance.instance_type}</strong>
                  <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', marginTop: '0.125rem' }}>
                    {instance.vcpu} vCPU · {instance.ram_gb} GB · {instance.disk_gb} GB
                  </div>
                </div>
                <span className="arch-badge">{instance.arch}</span>
              </div>

              <div style={{ fontSize: '0.8125rem', marginTop: '0.5rem', fontFamily: 'var(--font-mono)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                  <span style={{ color: 'var(--color-text-muted)' }}>CPU:</span>
                  <span>{Math.round(instance.metrics?.cpu_single_events || 0).toLocaleString()} evt/s</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                  <span style={{ color: 'var(--color-text-muted)' }}>Memory:</span>
                  <span>{Math.round(instance.metrics?.memory_mib_per_sec || 0)} MiB/s</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                  <span style={{ color: 'var(--color-text-muted)' }}>Disk:</span>
                  <span>{Math.round(instance.metrics?.disk_iops || 0).toLocaleString()} IOPS</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                  <span style={{ color: 'var(--color-text-muted)' }}>Score:</span>
                  <span>{instance.overall_score.toFixed(0)}/100</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', paddingTop: '0.5rem', marginTop: '0.5rem', borderTop: '1px solid var(--color-border)' }}>
                  <span style={{ color: 'var(--color-text-muted)' }}>Price:</span>
                  <span>{currencySymbol}{instance.price_monthly.toFixed(2)}/mo</span>
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default InstanceBreakdown
